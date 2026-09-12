"""WBS-B8 unit tests: G07 Change Control record shape (ADR-0020 §4)."""

from __future__ import annotations

import pytest

from governance.change_control import (
    ChangeRequest,
    FrozenContractArea,
    IncompleteChangeRequestError,
    VersionBump,
    classify_version_bump,
    validate_change_request,
)

_COMPLETE_FIELDS = {
    "cr_id": "CR-0001",
    "area": FrozenContractArea.CFL,
    "reason": "close a rule-engine gap",
    "impact": "CFL-04 candidates now resolve automatically",
    "backward_compatibility": "callers unchanged",
    "recompute_required": "none",
    "acceptance_method": "unit + integration tests",
    "version_bump": VersionBump.MINOR,
}


def test_complete_change_request_validates() -> None:
    cr = ChangeRequest(**_COMPLETE_FIELDS)
    validate_change_request(cr)  # does not raise


def test_missing_reason_is_rejected() -> None:
    fields = dict(_COMPLETE_FIELDS)
    fields["reason"] = "   "
    cr = ChangeRequest(**fields)
    with pytest.raises(IncompleteChangeRequestError, match="reason"):
        validate_change_request(cr)


def test_missing_multiple_fields_lists_all() -> None:
    fields = dict(_COMPLETE_FIELDS)
    fields["impact"] = ""
    fields["recompute_required"] = ""
    cr = ChangeRequest(**fields)
    with pytest.raises(IncompleteChangeRequestError, match="impact.*recompute_required"):
        validate_change_request(cr)


def test_classify_version_bump() -> None:
    assert classify_version_bump(changes_core_logic=False) is VersionBump.MINOR
    assert classify_version_bump(changes_core_logic=True) is VersionBump.MAJOR


def test_all_frozen_contract_areas_present() -> None:
    assert len(list(FrozenContractArea)) == 13
