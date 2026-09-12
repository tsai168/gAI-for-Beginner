"""U05 — API layer (WBS-B9/B11, ADR-0021/ADR-0023, Work-2 §4.2).

All 11 endpoints are real as of WBS-B11. `GET /exports` alone stays 501
— export FORMAT design (U05's own remaining scope) never had a module to
wire it to, unlike R01-R06 which now do.
"""

from __future__ import annotations

import os
import uuid

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from api.deps import get_session, require
from api.errors import (
    ApiError,
    BadRequestError,
    CflBlockedError,
    NotFoundError,
    format_error_code,
)
from api.errors import NotImplementedYetError as NotBuiltYet
from api.schemas import (
    CflDecisionRequest,
    CflDecisionResponse,
    CompanyDetailOut,
    CompanyOut,
    CompanyScoreSummaryOut,
    EventDetailOut,
    EventOut,
    EventStudyOut,
    ResearchReportOut,
    ValuationEventWindowOut,
)
from governance.cfl import NO_AUTO_PASS, CflId, default_cfl_service
from governance.publication import PublicationBlocked
from governance.rbac import FunctionGroup
from knowledge.db.base import CflStatus, RefEntityType, ReportType
from knowledge.db.models import CFL_GOVERNED_TABLES
from knowledge.repository.company import get_company, list_companies_by_universe
from knowledge.repository.event import get_event, list_events, list_revision_chain
from knowledge.repository.evidence import list_evidence_for_entity
from knowledge.repository.research_report import get_report, list_reports
from models.event_window import list_event_windows
from reports.dashboard import get_seco_cmi_dashboard
from reports.external_publication import approve_external_publication

app = FastAPI(title="CPO AI API", version="0.1.0")

# WBS-B10: the React frontend runs on its own origin (dev server or a
# separate deployment). CORS stays OFF unless API_CORS_ORIGINS is set
# (comma-separated) — never wildcard-open by default (CLAUDE.md §9).
_cors_origins = [o.strip() for o in os.environ.get("API_CORS_ORIGINS", "").split(",") if o.strip()]
if _cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.exception_handler(ApiError)
async def _handle_api_error(request: Request, exc: ApiError) -> JSONResponse:
    body: dict[str, str] = {"error_code": exc.error_code, "message": exc.message}
    if exc.correlation_id is not None:
        body["correlation_id"] = str(exc.correlation_id)
    return JSONResponse(status_code=exc.status_code, content=body)


@app.exception_handler(RequestValidationError)
async def _handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"error_code": format_error_code("API", 422), "message": exc.errors()},
    )


# --- K01 Company (real) ------------------------------------------------------


@app.get("/companies", response_model=list[CompanyOut])
def list_companies_endpoint(
    universe: str | None = None,
    q: str | None = None,
    cfl_status: str | None = None,
    session: Session = Depends(get_session),
    _role: object = Depends(require(FunctionGroup.READ_SUMMARY)),
) -> list[CompanyOut]:
    """`q` (WBS-B10, U02 search) is a case-insensitive substring match on
    `company_name`; `cfl_status` (U04 CFL queue) an exact match."""
    companies = list_companies_by_universe(
        session, universe, name_contains=q, cfl_status=cfl_status
    )
    return [CompanyOut.model_validate(c) for c in companies]


@app.get("/companies/{company_id}", response_model=CompanyDetailOut)
def get_company_endpoint(
    company_id: uuid.UUID,
    session: Session = Depends(get_session),
    _role: object = Depends(require(FunctionGroup.READ)),
) -> CompanyDetailOut:
    company = get_company(session, company_id)
    if company is None:
        raise NotFoundError("K01", f"company {company_id} not found")
    evidence = list_evidence_for_entity(
        session, entity_ref=company_id, entity_ref_type=RefEntityType.COMPANY.value
    )
    return CompanyDetailOut(
        **CompanyOut.model_validate(company).model_dump(),
        evidence_ids=[e.evidence_id for e in evidence],
    )


# --- K05 Event (real) ---------------------------------------------------------


@app.get("/events", response_model=list[EventOut])
def list_events_endpoint(
    pipeline_status: str | None = None,
    min_materiality: float | None = None,
    correlation_id: uuid.UUID | None = None,
    cfl_status: str | None = None,
    entity_id: uuid.UUID | None = None,
    session: Session = Depends(get_session),
    _role: object = Depends(require(FunctionGroup.READ_SUMMARY)),
) -> list[EventOut]:
    """`cfl_status` (WBS-B10, U04 CFL queue) / `entity_id` (U03
    company-scoped event list) added on top of B9's filters."""
    events = list_events(
        session,
        pipeline_status=pipeline_status,
        min_materiality=min_materiality,
        correlation_id=correlation_id,
        cfl_status=cfl_status,
        entity_id=entity_id,
    )
    return [EventOut.model_validate(e) for e in events]


@app.get("/events/{event_id}", response_model=EventDetailOut)
def get_event_endpoint(
    event_id: uuid.UUID,
    session: Session = Depends(get_session),
    _role: object = Depends(require(FunctionGroup.READ)),
) -> EventDetailOut:
    event = get_event(session, event_id)
    if event is None:
        raise NotFoundError("K05", f"event {event_id} not found")
    chain = list_revision_chain(session, event_id)
    return EventDetailOut(
        **EventOut.model_validate(event).model_dump(),
        revision_chain=[e.event_id for e in chain],
    )


# --- G01 CFL manual decision (real) -------------------------------------------


@app.post("/cfl/{cfl_id}/decision", response_model=CflDecisionResponse)
def decide_cfl_endpoint(
    cfl_id: str,
    body: CflDecisionRequest,
    session: Session = Depends(get_session),
    _role: object = Depends(require(FunctionGroup.REVIEW_QUEUE)),
) -> CflDecisionResponse:
    try:
        parsed_cfl_id = CflId(cfl_id)
    except ValueError as exc:
        raise BadRequestError("G01", f"unknown cfl_id {cfl_id!r}") from exc
    try:
        parsed_target = CflStatus(body.target)
    except ValueError as exc:
        raise BadRequestError("G01", f"unknown target status {body.target!r}") from exc
    if body.table not in CFL_GOVERNED_TABLES:
        raise BadRequestError("G01", f"table {body.table!r} is not CFL-governed")

    try:
        current = default_cfl_service.query_status(session, table=body.table, row_id=body.row_id)
    except LookupError as exc:
        raise NotFoundError("G01", str(exc)) from exc

    if current is CflStatus.BLOCKED and parsed_target not in (
        CflStatus.REVIEW_REQUIRED,
        CflStatus.SUPERSEDED,
    ):
        raise CflBlockedError(f"{body.table} {body.row_id} is BLOCKED", status_code=423)
    if parsed_target is CflStatus.AUTO_PASS and parsed_cfl_id in NO_AUTO_PASS:
        raise CflBlockedError(f"{parsed_cfl_id.value} must not AUTO-PASS", status_code=409)

    try:
        default_cfl_service.set_status(
            session,
            table=body.table,
            row_id=body.row_id,
            target=parsed_target,
            cfl_id=parsed_cfl_id,
        )
    except ValueError as exc:
        raise BadRequestError("G01", str(exc)) from exc

    return CflDecisionResponse(table=body.table, row_id=body.row_id, cfl_status=parsed_target.value)


# --- R01-R06 (WBS-B11, ADR-0023) ----------------------------------------------


@app.get("/dashboard/seco-cmi", response_model=list[CompanyScoreSummaryOut])
def dashboard_seco_cmi_endpoint(
    session: Session = Depends(get_session),
    _role: object = Depends(require(FunctionGroup.READ_SUMMARY)),
) -> list[CompanyScoreSummaryOut]:
    return [CompanyScoreSummaryOut.model_validate(s) for s in get_seco_cmi_dashboard(session)]


@app.get("/reports/{report_id}", response_model=ResearchReportOut)
def get_report_endpoint(
    report_id: uuid.UUID,
    session: Session = Depends(get_session),
    _role: object = Depends(require(FunctionGroup.READ)),
) -> ResearchReportOut:
    report = get_report(session, report_id)
    if report is None:
        raise NotFoundError("R02", f"research_report {report_id} not found")
    return ResearchReportOut.model_validate(report)


@app.get("/event-studies/{event_id}", response_model=EventStudyOut)
def get_event_study_endpoint(
    event_id: uuid.UUID,
    session: Session = Depends(get_session),
    _role: object = Depends(require(FunctionGroup.READ)),
) -> EventStudyOut:
    event = get_event(session, event_id)
    if event is None:
        raise NotFoundError("R04", f"event {event_id} not found")
    windows = list_event_windows(session, event_id)
    reports = list_reports(session, report_type=ReportType.EVENT_STUDY.value, subject_ref=event_id)
    return EventStudyOut(
        event_id=event_id,
        windows=[ValuationEventWindowOut.model_validate(w) for w in windows],
        report=ResearchReportOut.model_validate(reports[0]) if reports else None,
    )


@app.get("/comparisons/{comparison_id}", response_model=ResearchReportOut)
def get_comparison_endpoint(
    comparison_id: uuid.UUID,
    session: Session = Depends(get_session),
    _role: object = Depends(require(FunctionGroup.READ)),
) -> ResearchReportOut:
    report = get_report(session, comparison_id)
    if report is None or report.report_type != ReportType.COMPARISON.value:
        raise NotFoundError("R05", f"comparison report {comparison_id} not found")
    return ResearchReportOut.model_validate(report)


@app.post("/publications/{publication_id}/approve", response_model=ResearchReportOut)
def approve_publication_endpoint(
    publication_id: uuid.UUID,
    session: Session = Depends(get_session),
    _role: object = Depends(require(FunctionGroup.APPROVAL_PUBLISH)),
) -> ResearchReportOut:
    try:
        report = approve_external_publication(session, publication_id)
    except LookupError as exc:
        raise NotFoundError("R06", str(exc)) from exc
    except PublicationBlocked as exc:
        raise BadRequestError("G06", str(exc)) from exc
    except ValueError as exc:
        raise BadRequestError("G01", str(exc)) from exc
    return ResearchReportOut.model_validate(report)


@app.get("/exports")
def exports_endpoint(_role: object = Depends(require(FunctionGroup.READ))) -> None:
    raise NotBuiltYet("U05", "export format design is not built yet (WBS-B11 follow-up)")
