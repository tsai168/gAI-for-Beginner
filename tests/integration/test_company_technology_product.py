"""WBS-B4a integration tests (ADR-0011): Company CFL-02 gate, Technology
bitemporal primitives, Product CRUD. Needs Postgres + migrations."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from knowledge.db.base import CflStatus
from knowledge.repository.company import (
    create_company,
    get_company,
    list_companies_by_universe,
    set_universe,
)
from knowledge.repository.product import create_product, get_product, update_evidence_stage
from knowledge.repository.technology import (
    close_technology_version,
    current_technology_versions,
    open_technology_version,
)

pytestmark = pytest.mark.integration


def test_create_and_get_company(db_session) -> None:  # type: ignore[no-untyped-def]
    c = create_company(db_session, company_name="Beacon Photonics", universe="Watchlist")
    got = get_company(db_session, c.company_id)
    assert got is not None
    assert got.company_name == "Beacon Photonics"
    assert got.cfl_status == "PENDING"


def test_list_companies_by_universe(db_session) -> None:  # type: ignore[no-untyped-def]
    create_company(db_session, company_name="Core Co", universe="Core")
    create_company(db_session, company_name="Watch Co", universe="Watchlist")
    core = list_companies_by_universe(db_session, "Core")
    assert any(c.company_name == "Core Co" for c in core)
    assert all(c.universe == "Core" for c in core)


def test_first_upgrade_to_core_raises_cfl02(db_session) -> None:  # type: ignore[no-untyped-def]
    c = create_company(db_session, company_name="Rising Co", universe="Adjacent")
    status = set_universe(db_session, c, "Core")
    assert status is CflStatus.REVIEW_REQUIRED  # WBS-B8: first Core upgrade always needs Review
    assert c.universe == "Core"


def test_non_first_core_set_does_not_raise(db_session) -> None:  # type: ignore[no-untyped-def]
    c = create_company(db_session, company_name="Already Core Co", universe="Core")
    status = set_universe(db_session, c, "Core")
    assert status is None  # not a *first* upgrade -> no CFL-02 candidate


def test_downgrade_from_core_does_not_raise(db_session) -> None:  # type: ignore[no-untyped-def]
    c = create_company(db_session, company_name="Falling Co", universe="Core")
    status = set_universe(db_session, c, "Adjacent")
    assert status is None


def test_technology_open_close_leaves_old_row_data_intact(db_session) -> None:  # type: ignore[no-untyped-def]
    t0 = datetime(2026, 1, 1, tzinfo=UTC)
    t1 = datetime(2026, 6, 1, tzinfo=UTC)
    tech = open_technology_version(db_session, category="CPO", valid_from=t0)
    assert tech.valid_to is None
    assert tech in current_technology_versions(db_session, category="CPO")

    close_technology_version(db_session, tech, valid_to=t1)
    assert tech.valid_to == t1
    assert tech.category == "CPO"  # untouched
    assert tech not in current_technology_versions(db_session, category="CPO")


def test_product_crud(db_session) -> None:  # type: ignore[no-untyped-def]
    c = create_company(db_session, company_name="Prod Co", universe="Core")
    p = create_product(db_session, company_id=c.company_id, spec_summary="1.6T optical engine")
    assert get_product(db_session, p.product_id) is not None

    update_evidence_stage(db_session, p, "E2")
    assert p.evidence_stage == "E2"
