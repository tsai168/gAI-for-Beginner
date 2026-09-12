"""WBS-B9 integration tests: U05 API endpoints (ADR-0021 §3, Work-2 §4.2/§4.3).
Needs Postgres + migrations.

`get_session`/`get_current_role` are overridden per Work-2 §4.4's own
separation of concerns: JWT verification has its own dedicated real-crypto
tests (`test_api_auth.py`); these tests exercise routing, RBAC enforcement,
and each endpoint's actual (or honestly-stubbed) behaviour.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from api.app import app
from api.deps import get_current_role, get_session
from governance.cfl import CflId, RuleBasedCflService
from governance.rbac import UserRole
from knowledge.db.models import Company
from knowledge.repository.event import create_event as _create_event

pytestmark = pytest.mark.integration

RETRIEVED = datetime(2026, 9, 12, 8, 0, tzinfo=UTC)


@pytest.fixture
def client(db_session) -> Iterator[TestClient]:  # type: ignore[no-untyped-def]
    # Must be an actual generator function (not a lambda returning an
    # iterator) — FastAPI detects yield-dependencies via
    # inspect.isgeneratorfunction and only then unwraps the yielded value.
    def _override_session():  # type: ignore[no-untyped-def]
        yield db_session

    app.dependency_overrides[get_session] = _override_session
    app.dependency_overrides[get_current_role] = lambda: UserRole.RESEARCH_DIRECTOR
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def _company(db_session, **overrides):  # type: ignore[no-untyped-def]
    fields = {"company_name": "API Test Co", "universe": "Watchlist"}
    fields.update(overrides)
    c = Company(**fields)
    db_session.add(c)
    db_session.flush()
    return c


def test_list_companies(client: TestClient, db_session) -> None:  # type: ignore[no-untyped-def]
    _company(db_session, company_name="Alpha Co")
    resp = client.get("/companies")
    assert resp.status_code == 200
    assert "Alpha Co" in [c["company_name"] for c in resp.json()]


def test_list_companies_search_by_name(client: TestClient, db_session) -> None:  # type: ignore[no-untyped-def]
    _company(db_session, company_name="Beacon Photonics")
    _company(db_session, company_name="Zenith Semiconductor")
    resp = client.get("/companies", params={"q": "photon"})
    assert resp.status_code == 200
    names = [c["company_name"] for c in resp.json()]
    assert names == ["Beacon Photonics"]


def test_list_companies_filter_by_cfl_status(client: TestClient, db_session) -> None:  # type: ignore[no-untyped-def]
    reviewed = _company(db_session, company_name="Needs Review Co", universe="Adjacent")
    _company(db_session, company_name="Untouched Co")
    RuleBasedCflService().submit_candidate(
        db_session, table="company", row_id=reviewed.company_id, cfl_id=CflId.CFL_02
    )
    resp = client.get("/companies", params={"cfl_status": "REVIEW-REQUIRED"})
    assert resp.status_code == 200
    names = [c["company_name"] for c in resp.json()]
    assert names == ["Needs Review Co"]


def test_get_company_found(client: TestClient, db_session) -> None:  # type: ignore[no-untyped-def]
    company = _company(db_session)
    resp = client.get(f"/companies/{company.company_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["company_id"] == str(company.company_id)
    assert body["cfl_status"] == "PENDING"
    assert body["evidence_ids"] == []


def test_get_company_not_found(client: TestClient) -> None:
    resp = client.get(f"/companies/{uuid.uuid4()}")
    assert resp.status_code == 404
    assert resp.json()["error_code"] == "K01-ERR-404"


def test_list_events(client: TestClient, db_session) -> None:  # type: ignore[no-untyped-def]
    ev = _create_event(db_session, retrieved_at=RETRIEVED, event_taxonomy_code="EV01")
    resp = client.get("/events", params={"pipeline_status": "DISCOVERED"})
    assert resp.status_code == 200
    assert str(ev.event_id) in [e["event_id"] for e in resp.json()]


def test_list_events_filter_by_entity_id(client: TestClient, db_session) -> None:  # type: ignore[no-untyped-def]
    company = _company(db_session)
    ev = _create_event(
        db_session,
        retrieved_at=RETRIEVED,
        event_taxonomy_code="EV01",
        entity_id=company.company_id,
    )
    _create_event(db_session, retrieved_at=RETRIEVED, event_taxonomy_code="EV02")
    resp = client.get("/events", params={"entity_id": str(company.company_id)})
    assert resp.status_code == 200
    assert [e["event_id"] for e in resp.json()] == [str(ev.event_id)]


def test_list_events_filter_by_cfl_status(client: TestClient, db_session) -> None:  # type: ignore[no-untyped-def]
    ev = _create_event(db_session, retrieved_at=RETRIEVED, event_taxonomy_code="EV01")
    RuleBasedCflService().submit_candidate(
        db_session, table="event", row_id=ev.event_id, cfl_id=CflId.CFL_07
    )  # -> REVIEW-REQUIRED (CFL-07 never auto-passes)
    _create_event(db_session, retrieved_at=RETRIEVED, event_taxonomy_code="EV02")
    resp = client.get("/events", params={"cfl_status": "REVIEW-REQUIRED"})
    assert resp.status_code == 200
    assert [e["event_id"] for e in resp.json()] == [str(ev.event_id)]


def test_get_event_found(client: TestClient, db_session) -> None:  # type: ignore[no-untyped-def]
    ev = _create_event(db_session, retrieved_at=RETRIEVED, event_taxonomy_code="EV01")
    resp = client.get(f"/events/{ev.event_id}")
    assert resp.status_code == 200
    assert resp.json()["revision_chain"] == [str(ev.event_id)]


def test_get_event_not_found(client: TestClient) -> None:
    resp = client.get(f"/events/{uuid.uuid4()}")
    assert resp.status_code == 404
    assert resp.json()["error_code"] == "K05-ERR-404"


def test_cfl_decision_success(client: TestClient, db_session) -> None:  # type: ignore[no-untyped-def]
    company = _company(db_session)
    RuleBasedCflService().submit_candidate(
        db_session, table="company", row_id=company.company_id, cfl_id=CflId.CFL_02
    )  # -> REVIEW-REQUIRED (always, for CFL-02)
    resp = client.post(
        "/cfl/CFL-02/decision",
        json={"table": "company", "row_id": str(company.company_id), "target": "APPROVED"},
    )
    assert resp.status_code == 200
    assert resp.json()["cfl_status"] == "APPROVED"


def test_cfl_decision_unknown_table_is_400(client: TestClient) -> None:
    resp = client.post(
        "/cfl/CFL-02/decision",
        json={"table": "not_a_table", "row_id": str(uuid.uuid4()), "target": "APPROVED"},
    )
    assert resp.status_code == 400
    assert resp.json()["error_code"] == "G01-ERR-400"


def test_cfl_decision_row_not_found_is_404(client: TestClient) -> None:
    resp = client.post(
        "/cfl/CFL-02/decision",
        json={"table": "company", "row_id": str(uuid.uuid4()), "target": "APPROVED"},
    )
    assert resp.status_code == 404


def test_cfl_decision_illegal_transition_is_400(client: TestClient, db_session) -> None:  # type: ignore[no-untyped-def]
    company = _company(db_session)  # still PENDING
    resp = client.post(
        "/cfl/CFL-02/decision",
        json={"table": "company", "row_id": str(company.company_id), "target": "APPROVED"},
    )
    assert resp.status_code == 400  # PENDING -> APPROVED skips AUTO-PASS/REVIEW-REQUIRED
    assert resp.json()["error_code"] == "G01-ERR-400"


def test_cfl_decision_auto_pass_on_cfl07_is_409(client: TestClient, db_session) -> None:  # type: ignore[no-untyped-def]
    ev = _create_event(db_session, retrieved_at=RETRIEVED, event_taxonomy_code="EV01")
    resp = client.post(
        "/cfl/CFL-07/decision",
        json={"table": "event", "row_id": str(ev.event_id), "target": "AUTO-PASS"},
    )
    assert resp.status_code == 409
    assert resp.json()["error_code"] == "G01-ERR-409"


def test_rbac_denies_review_queue_to_analyst(client: TestClient, db_session) -> None:  # type: ignore[no-untyped-def]
    company = _company(db_session)
    app.dependency_overrides[get_current_role] = lambda: UserRole.SEMICONDUCTOR_ANALYST
    resp = client.post(
        "/cfl/CFL-02/decision",
        json={"table": "company", "row_id": str(company.company_id), "target": "APPROVED"},
    )
    assert resp.status_code == 403
    assert resp.json()["error_code"] == "G05-ERR-403"


def test_dashboard_stub_returns_501(client: TestClient) -> None:
    resp = client.get("/dashboard/seco-cmi")
    assert resp.status_code == 501
    assert resp.json()["error_code"] == "R03-ERR-501"


def test_publications_approve_stub_returns_501(client: TestClient) -> None:
    resp = client.post(f"/publications/{uuid.uuid4()}/approve")
    assert resp.status_code == 501
    assert resp.json()["error_code"] == "R06-ERR-501"
