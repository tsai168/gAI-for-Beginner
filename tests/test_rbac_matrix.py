"""WBS-B9 unit tests: G05 human-role RBAC matrix (ADR-0021 §1, Work-2 §4.4)."""

from __future__ import annotations

import pytest

from governance.rbac import (
    USER_RBAC_MATRIX,
    FunctionGroup,
    UserRbacViolation,
    UserRole,
    assert_no_cross_power_role,
    role_satisfies,
)


def test_all_six_charter_5_roles_present() -> None:
    assert len(list(UserRole)) == 6
    assert set(USER_RBAC_MATRIX) == set(UserRole)


@pytest.mark.parametrize(
    "role,groups",
    [
        (
            UserRole.RESEARCH_DIRECTOR,
            {FunctionGroup.READ, FunctionGroup.REVIEW_QUEUE, FunctionGroup.APPROVAL_PUBLISH},
        ),
        (
            UserRole.SEMICONDUCTOR_ANALYST,
            {FunctionGroup.READ, FunctionGroup.EVIDENCE_WRITE},
        ),
        (UserRole.QUANT_RESEARCHER, {FunctionGroup.READ, FunctionGroup.MODEL_EXEC}),
        (UserRole.RESEARCH_REVIEWER, {FunctionGroup.READ, FunctionGroup.REVIEW_QUEUE}),
        (UserRole.EXECUTIVE_USER, {FunctionGroup.READ_SUMMARY}),
        (
            UserRole.SYSTEM_ADMINISTRATOR,
            {FunctionGroup.READ, FunctionGroup.OPS_CONFIG},
        ),
    ],
)
def test_matrix_matches_work2_4_4(role: UserRole, groups: set[FunctionGroup]) -> None:
    assert USER_RBAC_MATRIX[role] == frozenset(groups)


def test_no_role_holds_both_evidence_write_and_approval_publish() -> None:
    assert_no_cross_power_role()  # does not raise


def test_cross_power_combination_is_rejected() -> None:
    bad_matrix = dict(USER_RBAC_MATRIX)
    bad_matrix[UserRole.SEMICONDUCTOR_ANALYST] = frozenset(
        {FunctionGroup.EVIDENCE_WRITE, FunctionGroup.APPROVAL_PUBLISH}
    )
    with pytest.raises(UserRbacViolation):
        assert_no_cross_power_role(bad_matrix)


def test_full_read_satisfies_read_summary_requirement() -> None:
    assert role_satisfies(UserRole.RESEARCH_DIRECTOR, FunctionGroup.READ_SUMMARY) is True


def test_read_summary_does_not_satisfy_full_read_requirement() -> None:
    assert role_satisfies(UserRole.EXECUTIVE_USER, FunctionGroup.READ) is False


def test_read_summary_satisfies_itself() -> None:
    assert role_satisfies(UserRole.EXECUTIVE_USER, FunctionGroup.READ_SUMMARY) is True


def test_role_without_group_is_denied() -> None:
    assert role_satisfies(UserRole.SEMICONDUCTOR_ANALYST, FunctionGroup.APPROVAL_PUBLISH) is False
