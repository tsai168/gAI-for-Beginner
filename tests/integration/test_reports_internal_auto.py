"""WBS-B11 integration tests (ADR-0023 §3): R01 daily digest + R03
dashboard — both Internal Auto, no CFL gate. Needs Postgres + migrations."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest

from governance.cfl import CflId, RuleBasedCflService
from knowledge.db.models import Company, ModelVersion, Source
from models.seco import SecoDimensions, record_seco_score
from reports.daily_digest import build_daily_digest, record_daily_digest
from reports.dashboard import get_company_scores, get_seco_cmi_dashboard

pytestmark = pytest.mark.integration

NOW = datetime(2026, 9, 12, 8, 0, tzinfo=UTC)
YESTERDAY = NOW - timedelta(days=1)
TOMORROW = NOW + timedelta(days=1)


def _company(db_session, **overrides):  # type: ignore[no-untyped-def]
    fields = {"company_name": "R01/R03 Test Co", "universe": "Watchlist"}
    fields.update(overrides)
    c = Company(**fields)
    db_session.add(c)
    db_session.flush()
    return c


# --- R01 ----------------------------------------------------------------------


def test_daily_digest_finds_new_sources_in_window(db_session) -> None:  # type: ignore[no-untyped-def]
    src = Source(data_source_code="D01", retrieved_at=NOW)
    db_session.add(src)
    old_src = Source(data_source_code="D01", retrieved_at=YESTERDAY - timedelta(days=5))
    db_session.add(old_src)
    db_session.flush()

    digest = build_daily_digest(db_session, window_start=YESTERDAY, window_end=TOMORROW)

    assert src.source_id in digest.new_source_ids
    assert old_src.source_id not in digest.new_source_ids


def test_daily_digest_finds_cfl02_grants_in_window(db_session) -> None:  # type: ignore[no-untyped-def]
    # audit_log.created_at is the DB's own now() (server_default), not a
    # value this test controls — bracket real wall-clock time, not the
    # fixed NOW/YESTERDAY/TOMORROW constants used elsewhere in this file.
    real_before = datetime.now(UTC) - timedelta(minutes=5)
    company = _company(db_session, universe="Adjacent")
    RuleBasedCflService().submit_candidate(
        db_session, table="company", row_id=company.company_id, cfl_id=CflId.CFL_02
    )
    real_after = datetime.now(UTC) + timedelta(minutes=5)

    digest = build_daily_digest(db_session, window_start=real_before, window_end=real_after)

    assert company.company_id in digest.core_upgrade_company_ids


def test_record_daily_digest_is_internal_auto_no_cfl_write(db_session) -> None:  # type: ignore[no-untyped-def]
    digest = build_daily_digest(db_session, window_start=YESTERDAY, window_end=TOMORROW)
    report = record_daily_digest(db_session, digest)
    assert report.publication_tier == "INTERNAL_AUTO"
    assert report.cfl_status == "PENDING"  # never submitted to G01 — Internal Auto needs no gate


# --- R03 ------------------------------------------------------------------------


def _model_version(db_session, kind: str, label: str):  # type: ignore[no-untyped-def]
    mv = ModelVersion(model_kind=kind, version_label=label, valid_from=YESTERDAY)
    db_session.add(mv)
    db_session.flush()
    return mv


def test_get_company_scores_reads_current_seco(db_session) -> None:  # type: ignore[no-untyped-def]
    company = _company(db_session)
    mv = _model_version(db_session, "seco", "r03-v1")
    record_seco_score(
        db_session,
        company_id=company.company_id,
        as_of=NOW,
        dims=SecoDimensions(60, 60, 60, 60, 60, 60),
        confidence=0.8,
        model_version_id=mv.model_version_id,
        valid_from=YESTERDAY,
    )

    summary = get_company_scores(db_session, company.company_id)
    assert summary is not None
    assert summary.seco_score == pytest.approx(60.0)
    assert summary.cmi_score is None


def test_get_company_scores_missing_company_returns_none(db_session) -> None:  # type: ignore[no-untyped-def]
    assert get_company_scores(db_session, uuid.uuid4()) is None


def test_dashboard_lists_companies_with_a_current_score(db_session) -> None:  # type: ignore[no-untyped-def]
    with_score = _company(db_session, company_name="Has Score Co")
    _company(db_session, company_name="No Score Co")
    mv = _model_version(db_session, "seco", "r03-dashboard")
    record_seco_score(
        db_session,
        company_id=with_score.company_id,
        as_of=NOW,
        dims=SecoDimensions(70, 70, 70, 70, 70, 70),
        confidence=0.9,
        model_version_id=mv.model_version_id,
        valid_from=YESTERDAY,
    )

    dashboard = get_seco_cmi_dashboard(db_session)
    ids = {s.company_id for s in dashboard}
    assert with_score.company_id in ids
    matching = [s for s in dashboard if s.company_id == with_score.company_id]
    assert matching[0].seco_score is not None
