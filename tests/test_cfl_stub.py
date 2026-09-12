"""G01 structural contract (ADR-0004 / ADR-0007 §6): CFL id set, lifecycle
transitions, NO_AUTO_PASS. Unchanged by the WBS-B8 rule-engine swap
(ADR-0020) — see test_cfl_rules_db.py for the real per-CFL decisions.

The DB direct-write guard is exercised in the `migration` job (needs Postgres);
here we cover the pure-Python contract.
"""

from __future__ import annotations

import pytest

from governance.cfl import (
    CFL_TRANSITIONS,
    NO_AUTO_PASS,
    CflId,
    is_valid_transition,
)
from knowledge.db.base import CflStatus


def test_all_cfl_ids_present() -> None:
    assert [c.value for c in CflId] == [f"CFL-0{i}" for i in range(1, 9)]


def test_lifecycle_shape() -> None:
    # PENDING is the only entry point; SUPERSEDED is terminal.
    assert CflStatus.PENDING in CFL_TRANSITIONS
    assert CFL_TRANSITIONS[CflStatus.SUPERSEDED] == frozenset()
    assert not is_valid_transition(CflStatus.APPROVED, CflStatus.PENDING)
    assert is_valid_transition(CflStatus.PENDING, CflStatus.REVIEW_REQUIRED)


def test_pending_cannot_jump_to_approved() -> None:
    assert not is_valid_transition(CflStatus.PENDING, CflStatus.APPROVED)


@pytest.mark.parametrize("cfl_id", sorted(NO_AUTO_PASS))
def test_no_auto_pass_ids(cfl_id: CflId) -> None:
    assert cfl_id in {CflId.CFL_07, CflId.CFL_08}
