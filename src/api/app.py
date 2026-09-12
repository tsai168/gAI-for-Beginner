"""U05 — API layer (WBS-B9, ADR-0021, Work-2 §4.2).

Endpoints backed by modules that already exist (K01 Company, K05 Event,
G01 CFL decision) are real. Endpoints attributed to R01-R06 (Reporting,
WBS-B11) or R05 (Comparison, not built) return 501 `NotImplementedYetError`
— never fake data (same posture as `agents/roster.py`, `workflows/
daily_pipeline.py`).
"""

from __future__ import annotations

import uuid

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
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
    EventDetailOut,
    EventOut,
)
from governance.cfl import NO_AUTO_PASS, CflId, default_cfl_service
from governance.rbac import FunctionGroup
from knowledge.db.base import CflStatus, RefEntityType
from knowledge.db.models import CFL_GOVERNED_TABLES
from knowledge.repository.company import get_company, list_companies_by_universe
from knowledge.repository.event import get_event, list_events, list_revision_chain
from knowledge.repository.evidence import list_evidence_for_entity

app = FastAPI(title="CPO AI API", version="0.1.0")


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
    session: Session = Depends(get_session),
    _role: object = Depends(require(FunctionGroup.READ_SUMMARY)),
) -> list[CompanyOut]:
    companies = list_companies_by_universe(session, universe)
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
    session: Session = Depends(get_session),
    _role: object = Depends(require(FunctionGroup.READ_SUMMARY)),
) -> list[EventOut]:
    events = list_events(
        session,
        pipeline_status=pipeline_status,
        min_materiality=min_materiality,
        correlation_id=correlation_id,
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


# --- R01-R06 (WBS-B11, not built yet) -----------------------------------------


@app.get("/dashboard/seco-cmi")
def dashboard_seco_cmi_endpoint(
    _role: object = Depends(require(FunctionGroup.READ_SUMMARY)),
) -> None:
    raise NotBuiltYet("R03", "R03 dashboard aggregation is not built yet (WBS-B11)")


@app.get("/reports/{report_id}")
def get_report_endpoint(
    report_id: uuid.UUID, _role: object = Depends(require(FunctionGroup.READ))
) -> None:
    raise NotBuiltYet("R02", "research_report (R02) is not built yet (WBS-B11)")


@app.get("/event-studies/{event_id}")
def get_event_study_endpoint(
    event_id: uuid.UUID, _role: object = Depends(require(FunctionGroup.READ))
) -> None:
    raise NotBuiltYet("R04", "R04 event-study report is not built yet (WBS-B11)")


@app.get("/comparisons/{comparison_id}")
def get_comparison_endpoint(
    comparison_id: uuid.UUID, _role: object = Depends(require(FunctionGroup.READ))
) -> None:
    raise NotBuiltYet("R05", "R05 comparison analysis is not built yet (WBS-B11)")


@app.post("/publications/{publication_id}/approve")
def approve_publication_endpoint(
    publication_id: uuid.UUID,
    _role: object = Depends(require(FunctionGroup.APPROVAL_PUBLISH)),
) -> None:
    raise NotBuiltYet(
        "R06",
        "research_report / publish flow (R06) is not built yet (WBS-B11); "
        "governance.publication's CFL-08 gate is ready for when it is",
    )


@app.get("/exports")
def exports_endpoint(_role: object = Depends(require(FunctionGroup.READ))) -> None:
    raise NotBuiltYet("U05", "export formats depend on R01-R06 (WBS-B11)")
