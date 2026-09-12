"""WBS-B4b integration tests (ADR-0012): Relationship CFL-05 gate, Event
Revision Chain, Evidence CFL-07 gate. Needs Postgres + migrations."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest

from governance.cfl import NO_AUTO_PASS, CflId
from knowledge.db.base import CflStatus
from knowledge.repository.event import (
    correct_event,
    get_event,
    get_latest,
    get_root,
    list_revision_chain,
    withdraw_event,
)
from knowledge.repository.event import create_event as _create_event
from knowledge.repository.evidence import create_evidence, record_contradiction
from knowledge.repository.relationship import confirm_relationship, create_relationship

pytestmark = pytest.mark.integration

RETRIEVED = datetime(2026, 9, 12, 8, 0, tzinfo=UTC)


def create_event(db_session, **overrides):  # type: ignore[no-untyped-def]
    fields = {"retrieved_at": RETRIEVED, "event_taxonomy_code": "EV01"}
    fields.update(overrides)
    return _create_event(db_session, **fields)


# --- K04 Relationship -------------------------------------------------------


def test_create_relationship_defaults_to_candidate(db_session) -> None:  # type: ignore[no-untyped-def]
    rel = create_relationship(
        db_session,
        source_entity_id=uuid.uuid4(),
        source_entity_type="company",
        target_entity_id=uuid.uuid4(),
        target_entity_type="company",
        relationship_type="CUSTOMER",
    )
    assert rel.status == "CANDIDATE"


def test_confirm_named_relationship_raises_cfl05_first_time(db_session) -> None:  # type: ignore[no-untyped-def]
    rel = create_relationship(
        db_session,
        source_entity_id=uuid.uuid4(),
        source_entity_type="company",
        target_entity_id=uuid.uuid4(),
        target_entity_type="company",
        relationship_type="SUPPLIER",
        is_named=True,
    )
    status = confirm_relationship(db_session, rel)
    assert rel.status == "CONFIRMED"
    assert status is CflStatus.PENDING


def test_confirm_unnamed_relationship_does_not_raise(db_session) -> None:  # type: ignore[no-untyped-def]
    rel = create_relationship(
        db_session,
        source_entity_id=uuid.uuid4(),
        source_entity_type="company",
        target_entity_id=uuid.uuid4(),
        target_entity_type="person",
        relationship_type="PARTNER",
        is_named=False,
    )
    assert confirm_relationship(db_session, rel) is None


def test_reconfirm_does_not_raise_again(db_session) -> None:  # type: ignore[no-untyped-def]
    rel = create_relationship(
        db_session,
        source_entity_id=uuid.uuid4(),
        source_entity_type="company",
        target_entity_id=uuid.uuid4(),
        target_entity_type="company",
        relationship_type="COMPETITOR",
        is_named=True,
    )
    confirm_relationship(db_session, rel)
    assert confirm_relationship(db_session, rel) is None


# --- K05 Event Revision Chain -------------------------------------------------


def test_create_event_starts_chain_at_seq1_active(db_session) -> None:  # type: ignore[no-untyped-def]
    ev = create_event(db_session)
    assert ev.revision_seq == 1
    assert ev.lifecycle_status == "ACTIVE"
    assert ev.revision_of_event_id is None


def test_correct_event_preserves_old_row_data(db_session) -> None:  # type: ignore[no-untyped-def]
    ev = create_event(db_session, materiality_score=40)
    original_score = ev.materiality_score
    original_taxonomy = ev.event_taxonomy_code
    original_retrieved_at = ev.retrieved_at

    new = correct_event(db_session, ev, changes={"materiality_score": 85})

    db_session.refresh(ev)
    # old row: only lifecycle_status changed, everything else untouched
    assert ev.lifecycle_status == "SUPERSEDED"
    assert ev.materiality_score == original_score
    assert ev.event_taxonomy_code == original_taxonomy
    assert ev.retrieved_at == original_retrieved_at

    # new row: revised data, linked, seq incremented
    assert new.materiality_score == 85
    assert new.lifecycle_status == "CORRECTED"
    assert new.revision_of_event_id == ev.event_id
    assert new.revision_seq == ev.revision_seq + 1
    assert new.event_taxonomy_code == original_taxonomy  # carried over unchanged


def test_correct_event_on_non_head_raises(db_session) -> None:  # type: ignore[no-untyped-def]
    ev = create_event(db_session)
    correct_event(db_session, ev, changes={})
    with pytest.raises(ValueError, match="not a chain head"):
        correct_event(db_session, ev, changes={})


def test_withdraw_event_creates_new_revision_same_data(db_session) -> None:  # type: ignore[no-untyped-def]
    ev = create_event(db_session, materiality_score=60)
    withdrawn = withdraw_event(db_session, ev)
    assert withdrawn.lifecycle_status == "WITHDRAWN"
    assert withdrawn.materiality_score == 60
    assert withdrawn.revision_of_event_id == ev.event_id


def test_get_root_and_get_latest(db_session) -> None:  # type: ignore[no-untyped-def]
    v1 = create_event(db_session, materiality_score=10)
    v2 = correct_event(db_session, v1, changes={"materiality_score": 20})
    v3 = correct_event(db_session, v2, changes={"materiality_score": 30})

    assert get_root(db_session, v3.event_id).event_id == v1.event_id
    assert get_latest(db_session, v1.event_id).event_id == v3.event_id
    assert get_latest(db_session, v2.event_id).event_id == v3.event_id


def test_list_revision_chain_order(db_session) -> None:  # type: ignore[no-untyped-def]
    v1 = create_event(db_session, materiality_score=10)
    v2 = correct_event(db_session, v1, changes={"materiality_score": 20})
    v3 = correct_event(db_session, v2, changes={"materiality_score": 30})

    chain = list_revision_chain(db_session, v2.event_id)
    assert [e.event_id for e in chain] == [v1.event_id, v2.event_id, v3.event_id]
    assert [e.revision_seq for e in chain] == [1, 2, 3]


def test_get_event(db_session) -> None:  # type: ignore[no-untyped-def]
    ev = create_event(db_session)
    assert get_event(db_session, ev.event_id) is not None
    assert get_event(db_session, uuid.uuid4()) is None


# --- K06 Evidence -------------------------------------------------------------


def test_record_contradiction_raises_cfl07(db_session) -> None:  # type: ignore[no-untyped-def]
    ev = create_evidence(
        db_session, evidence_type="CONTRADICT", content_hash="abc123", retrieved_at=RETRIEVED
    )
    status = record_contradiction(db_session, ev)
    assert status is CflStatus.PENDING
    assert CflId.CFL_07 in NO_AUTO_PASS


def test_record_contradiction_requires_contradict_type(db_session) -> None:  # type: ignore[no-untyped-def]
    ev = create_evidence(
        db_session, evidence_type="SUPPORT", content_hash="def456", retrieved_at=RETRIEVED
    )
    with pytest.raises(ValueError, match="CONTRADICT"):
        record_contradiction(db_session, ev)
