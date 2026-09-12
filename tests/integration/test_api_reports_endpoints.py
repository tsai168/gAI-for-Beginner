"""WBS-B11 integration tests: U05 endpoints backed by R01-R06 (ADR-0023 §4).
Needs Postgres + migrations.

Follows the same dependency-override pattern as test_api_endpoints.py
(B9/B10) — see that file for why `get_session`/`get_current_role` are
overridden rather than exercised through real auth here.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from api.app import app
from api.deps import get_current_role, get_session
from governance.rbac import UserRole
from knowledge.db.base import BenchmarkModel, RefEntityType
from knowledge.db.models import Company, Event, ModelVersion
from models.event_window import record_valuation_event_window
from models.seco import SecoDimensions, record_seco_score
from reports.comparison_report import submit_comparison_report
from reports.external_publication import submit_for_external_publication

pytestmark = pytest.mark.integration

RETRIEVED = datetime(2026, 9, 12, 8, 0, tzinfo=UTC)


@pytest.fixture
def client(db_session) -> Iterator[TestClient]:  # type: ignore[no-untyped-def]
    def _override_session():  # type: ignore[no-untyped-def]
        yield db_session

    app.dependency_overrides[get_session] = _override_session
    app.dependency_overrides[get_current_role] = lambda: UserRole.RESEARCH_DIRECTOR
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def test_dashboard_returns_company_scores(client: TestClient, db_session) -> None:  # type: ignore[no-untyped-def]
    company = Company(company_name="Dashboard Co", universe="Core")
    db_session.add(company)
    mv = ModelVersion(model_kind="seco", version_label="api-r03-v1", valid_from=RETRIEVED)
    db_session.add(mv)
    db_session.flush()
    record_seco_score(
        db_session,
        company_id=company.company_id,
        as_of=RETRIEVED,
        dims=SecoDimensions(55, 55, 55, 55, 55, 55),
        confidence=0.7,
        model_version_id=mv.model_version_id,
        valid_from=RETRIEVED,
    )

    resp = client.get("/dashboard/seco-cmi")
    assert resp.status_code == 200
    rows = {r["company_id"]: r for r in resp.json()}
    assert rows[str(company.company_id)]["seco_score"] == pytest.approx(55.0)


def test_get_report_found_and_not_found(client: TestClient, db_session) -> None:  # type: ignore[no-untyped-def]
    report, _status = submit_comparison_report(db_session, subject_ref=uuid.uuid4())

    resp = client.get(f"/reports/{report.research_report_id}")
    assert resp.status_code == 200
    assert resp.json()["report_type"] == "COMPARISON"

    missing = client.get(f"/reports/{uuid.uuid4()}")
    assert missing.status_code == 404
    assert missing.json()["error_code"] == "R02-ERR-404"


def test_get_event_study_includes_windows(client: TestClient, db_session) -> None:  # type: ignore[no-untyped-def]
    ev = Event(event_taxonomy_code="EV06", retrieved_at=RETRIEVED)
    db_session.add(ev)
    mv = ModelVersion(model_kind="benchmark", version_label="api-r04-v1", valid_from=RETRIEVED)
    db_session.add(mv)
    db_session.flush()
    record_valuation_event_window(
        db_session,
        event_id=ev.event_id,
        window_pre=1,
        window_post=1,
        benchmark_model=BenchmarkModel.MARKET_ADJUSTED,
        ar_series=[0.01, -0.01],
        model_version_id=mv.model_version_id,
    )

    resp = client.get(f"/event-studies/{ev.event_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["windows"]) == 1
    assert body["report"] is None  # no EVENT_STUDY research_report created yet


def test_get_event_study_missing_event_is_404(client: TestClient) -> None:
    resp = client.get(f"/event-studies/{uuid.uuid4()}")
    assert resp.status_code == 404
    assert resp.json()["error_code"] == "R04-ERR-404"


def test_get_comparison_found_and_wrong_type_is_404(client: TestClient, db_session) -> None:  # type: ignore[no-untyped-def]
    report, _status = submit_comparison_report(db_session, subject_ref=uuid.uuid4())
    resp = client.get(f"/comparisons/{report.research_report_id}")
    assert resp.status_code == 200

    # a real report_id that isn't a COMPARISON should 404, not leak its data
    other_report, _s = submit_for_external_publication(
        db_session, subject_ref=uuid.uuid4(), subject_ref_type=RefEntityType.EVENT.value
    )
    resp2 = client.get(f"/comparisons/{other_report.research_report_id}")
    assert resp2.status_code == 404
    assert resp2.json()["error_code"] == "R05-ERR-404"


def test_approve_publication_endpoint(client: TestClient, db_session) -> None:  # type: ignore[no-untyped-def]
    ev = Event(event_taxonomy_code="EV01", retrieved_at=RETRIEVED, pipeline_status="APPROVED")
    db_session.add(ev)
    db_session.flush()
    report, _status = submit_for_external_publication(
        db_session, subject_ref=ev.event_id, subject_ref_type=RefEntityType.EVENT.value
    )

    resp = client.post(f"/publications/{report.research_report_id}/approve")
    assert resp.status_code == 200
    assert resp.json()["cfl_status"] == "APPROVED"


def test_approve_publication_endpoint_not_found(client: TestClient) -> None:
    resp = client.post(f"/publications/{uuid.uuid4()}/approve")
    assert resp.status_code == 404
    assert resp.json()["error_code"] == "R06-ERR-404"


def test_approve_publication_rbac_denies_non_director(client: TestClient, db_session) -> None:  # type: ignore[no-untyped-def]
    ev = Event(event_taxonomy_code="EV01", retrieved_at=RETRIEVED, pipeline_status="APPROVED")
    db_session.add(ev)
    db_session.flush()
    report, _status = submit_for_external_publication(
        db_session, subject_ref=ev.event_id, subject_ref_type=RefEntityType.EVENT.value
    )
    app.dependency_overrides[get_current_role] = lambda: UserRole.SEMICONDUCTOR_ANALYST

    resp = client.post(f"/publications/{report.research_report_id}/approve")
    assert resp.status_code == 403
