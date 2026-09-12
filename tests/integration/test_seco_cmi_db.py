"""WBS-B5b integration tests (ADR-0014): Seco/CMI bitemporal read/write.
Needs Postgres + migrations."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from knowledge.db.models import Company, ModelVersion
from models.cmi import CmiAvailability, CmiDimensions, correct_cmi_score, record_cmi_score
from models.seco import SecoDimensions, correct_seco_score, record_seco_score

pytestmark = pytest.mark.integration

AS_OF = datetime(2026, 9, 12, 8, 0, tzinfo=UTC)
BEFORE = AS_OF - timedelta(days=1)


def _company(db_session):  # type: ignore[no-untyped-def]
    c = Company(company_name="Seco/CMI Test Co", universe="Core")
    db_session.add(c)
    db_session.flush()
    return c


def _model_version(db_session, kind: str, label: str):  # type: ignore[no-untyped-def]
    mv = ModelVersion(model_kind=kind, version_label=label, valid_from=BEFORE)
    db_session.add(mv)
    db_session.flush()
    return mv


def test_record_and_correct_seco_score_preserves_old_row(db_session) -> None:  # type: ignore[no-untyped-def]
    company = _company(db_session)
    mv1 = _model_version(db_session, "seco", "v1")
    dims1 = SecoDimensions(50, 50, 50, 50, 50, 50)

    v1 = record_seco_score(
        db_session,
        company_id=company.company_id,
        as_of=AS_OF,
        dims=dims1,
        confidence=0.8,
        model_version_id=mv1.model_version_id,
        valid_from=BEFORE,
    )
    assert v1.score == pytest.approx(50.0)
    assert v1.valid_to is None

    mv2 = _model_version(db_session, "seco", "v2")
    dims2 = SecoDimensions(80, 80, 80, 80, 80, 80)
    v2 = correct_seco_score(
        db_session,
        v1,
        dims=dims2,
        confidence=0.9,
        model_version_id=mv2.model_version_id,
        valid_from=AS_OF,
    )

    db_session.refresh(v1)
    assert v1.valid_to == AS_OF
    assert v1.score == pytest.approx(50.0)  # old row untouched otherwise
    assert v1.model_version_id == mv1.model_version_id  # old row keeps old version

    assert v2.score == pytest.approx(80.0)
    assert v2.valid_to is None
    assert v2.model_version_id == mv2.model_version_id
    assert v2.company_id == company.company_id
    assert v2.as_of == v1.as_of


def test_seco_confidence_out_of_range_rejected(db_session) -> None:  # type: ignore[no-untyped-def]
    company = _company(db_session)
    mv = _model_version(db_session, "seco", "bad-confidence")
    with pytest.raises(ValueError, match="confidence"):
        record_seco_score(
            db_session,
            company_id=company.company_id,
            as_of=AS_OF,
            dims=SecoDimensions(50, 50, 50, 50, 50, 50),
            confidence=1.5,
            model_version_id=mv.model_version_id,
            valid_from=BEFORE,
        )


def test_record_and_correct_cmi_score_preserves_old_row(db_session) -> None:  # type: ignore[no-untyped-def]
    company = _company(db_session)
    mv1 = _model_version(db_session, "cmi", "v1")
    dims1 = CmiDimensions(40, 40, 40, 40, 40)
    avail = CmiAvailability(BEFORE, BEFORE, BEFORE, BEFORE, BEFORE)

    v1 = record_cmi_score(
        db_session,
        company_id=company.company_id,
        as_of=AS_OF,
        dims=dims1,
        availability=avail,
        model_version_id=mv1.model_version_id,
        valid_from=BEFORE,
    )
    assert v1.score == pytest.approx(40.0)

    mv2 = _model_version(db_session, "cmi", "v2")
    dims2 = CmiDimensions(60, 60, 60, 60, 60)
    v2 = correct_cmi_score(
        db_session,
        v1,
        dims=dims2,
        availability=avail,
        model_version_id=mv2.model_version_id,
        valid_from=AS_OF,
    )

    db_session.refresh(v1)
    assert v1.valid_to == AS_OF
    assert v1.score == pytest.approx(40.0)
    assert v2.score == pytest.approx(60.0)
    assert v2.valid_to is None


def test_record_cmi_score_rejects_future_data(db_session) -> None:  # type: ignore[no-untyped-def]
    company = _company(db_session)
    mv = _model_version(db_session, "cmi", "future-data")
    future_avail = CmiAvailability(BEFORE, BEFORE, BEFORE, BEFORE, AS_OF + timedelta(days=1))
    with pytest.raises(ValueError, match="GP-08"):
        record_cmi_score(
            db_session,
            company_id=company.company_id,
            as_of=AS_OF,
            dims=CmiDimensions(50, 50, 50, 50, 50),
            availability=future_avail,
            model_version_id=mv.model_version_id,
            valid_from=BEFORE,
        )
