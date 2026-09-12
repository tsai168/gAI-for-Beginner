"""TEST-API-01 (Work-3 §4, WBS-B12): §4.2 endpoint responses carry
`version`/`cfl_status` where the resource actually has them (Company has
no `version` field — Event-only, ADR-0021); every 4xx response carries a
uniform `<MODULE>-ERR-<NNN>` error_code. Needs Postgres + migrations.

Per-endpoint behaviour already has dedicated coverage
(test_api_endpoints.py, test_api_reports_endpoints.py); this file is the
one place that sweeps the *contract-wide* invariant across all of them.
"""

from __future__ import annotations

import re
import uuid
from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from api.app import app
from api.deps import get_current_role, get_session
from governance.rbac import UserRole
from knowledge.db.models import Company
from knowledge.repository.event import create_event as _create_event

pytestmark = pytest.mark.integration

_ERROR_CODE_RE = re.compile(r"^[A-Z0-9]+-ERR-\d{3}$")
RETRIEVED = datetime(2026, 9, 12, 9, 0, tzinfo=UTC)


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


def test_event_responses_carry_version_and_cfl_status(client: TestClient, db_session) -> None:  # type: ignore[no-untyped-def]
    ev = _create_event(db_session, retrieved_at=RETRIEVED, event_taxonomy_code="EV01")

    detail = client.get(f"/events/{ev.event_id}").json()
    assert "version" in detail and "cfl_status" in detail

    listing = client.get("/events").json()
    assert all("version" in e and "cfl_status" in e for e in listing)


def test_company_responses_carry_cfl_status_but_have_no_version_field(
    client: TestClient, db_session
) -> None:  # type: ignore[no-untyped-def]
    company = Company(company_name="API-01 Co", universe="Watchlist")
    db_session.add(company)
    db_session.flush()

    detail = client.get(f"/companies/{company.company_id}").json()
    assert "cfl_status" in detail
    assert "version" not in detail  # Company has no version field (ADR-0021)


def test_cfl_decision_response_carries_cfl_status(client: TestClient, db_session) -> None:  # type: ignore[no-untyped-def]
    company = Company(company_name="API-01 CFL Co", universe="Watchlist")
    db_session.add(company)
    db_session.flush()
    # PENDING -> REVIEW-REQUIRED is a legal direct transition (Charter §17).
    resp = client.post(
        "/cfl/CFL-02/decision",
        json={
            "table": "company",
            "row_id": str(company.company_id),
            "target": "REVIEW-REQUIRED",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["cfl_status"] == "REVIEW-REQUIRED"


@pytest.mark.parametrize(
    "method,path",
    [
        ("get", "companies"),
        ("get", "events"),
        ("get", "reports"),
        ("get", "event-studies"),
        ("get", "comparisons"),
        ("post", "publications"),
    ],
)
def test_all_not_found_responses_have_uniform_error_code(
    client: TestClient, method: str, path: str
) -> None:
    random_id = uuid.uuid4()
    url = f"/{path}/{random_id}" if path != "publications" else f"/{path}/{random_id}/approve"
    resp = getattr(client, method)(url)
    assert resp.status_code == 404
    body = resp.json()
    assert "error_code" in body
    assert _ERROR_CODE_RE.match(body["error_code"]), body["error_code"]
