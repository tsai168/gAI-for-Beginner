"""DB-backed WBS-B1/B2/B3a checks. Needs Postgres + migrations (integration).

Covers: D01–D08 seed, P01->P02->P03 flow + idempotency, source_snapshot
append-only trigger (CF-08/GP-15), G01 cfl_status direct-write guard.
"""

from __future__ import annotations

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import DBAPIError

from governance.cfl import CflId, DefaultCflService
from ingestion.dedup import DedupVerdict
from ingestion.fetch import FixtureAdapter, fetch_and_register
from knowledge.db.base import CflStatus
from knowledge.db.models import Company, DataSource, SourceSnapshot

pytestmark = pytest.mark.integration


def test_data_source_seed(db_session) -> None:  # type: ignore[no-untyped-def]
    codes = set(db_session.execute(select(DataSource.source_code)).scalars())
    assert codes == {f"D0{i}" for i in range(1, 9)}
    assert db_session.get(DataSource, "D08").is_enabled is False
    assert db_session.get(DataSource, "D01").source_tier == "S1"
    assert db_session.get(DataSource, "D01").earliest_reliable_date is None


def test_fetch_and_register_and_dedup(db_session) -> None:  # type: ignore[no-untyped-def]
    ad = FixtureAdapter("D01", payloads={"doc": b"TWSE daily 2026-09-11"})

    first = fetch_and_register(db_session, ad, {"key": "doc"})
    assert first.verdict is DedupVerdict.NEW

    second = fetch_and_register(db_session, ad, {"key": "doc"})
    assert second.verdict is DedupVerdict.DUPLICATE_OTHER_SOURCE
    assert second.source.source_id != first.source.source_id

    # one snapshot row per (source_id, content_hash)
    count = db_session.execute(
        select(func.count())
        .select_from(SourceSnapshot)
        .where(SourceSnapshot.content_hash == first.snapshot.content_hash)
    ).scalar_one()
    assert count == 2


def test_source_snapshot_append_only(db_session) -> None:  # type: ignore[no-untyped-def]
    ad = FixtureAdapter("D04", payloads={"x": b"immutable"})
    reg = fetch_and_register(db_session, ad, {"key": "x"})
    db_session.flush()
    with pytest.raises(DBAPIError):
        db_session.execute(
            text("UPDATE source_snapshot SET snapshot_ref = 'x' WHERE source_snapshot_id = :i"),
            {"i": reg.snapshot.source_snapshot_id},
        )
    db_session.rollback()


def test_cfl_status_direct_write_blocked(db_session) -> None:  # type: ignore[no-untyped-def]
    c = Company(company_name="ACME Optical", universe="Watchlist")
    db_session.add(c)
    db_session.flush()
    with pytest.raises(DBAPIError):
        db_session.execute(
            text("UPDATE company SET cfl_status = 'APPROVED' WHERE company_id = :i"),
            {"i": c.company_id},
        )
    db_session.rollback()


def test_cfl_status_write_via_guard_ok(db_session) -> None:  # type: ignore[no-untyped-def]
    c = Company(company_name="Beacon Photonics", universe="Adjacent")
    db_session.add(c)
    db_session.flush()
    DefaultCflService().set_status(
        db_session,
        table="company",
        row_id=c.company_id,
        target=CflStatus.REVIEW_REQUIRED,
        cfl_id=CflId.CFL_01,
    )
    got = db_session.execute(
        text("SELECT cfl_status FROM company WHERE company_id = :i"), {"i": c.company_id}
    ).scalar_one()
    assert got == "REVIEW-REQUIRED"
