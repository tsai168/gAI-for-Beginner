"""WBS-B8 unit tests: G06 publication state machine (ADR-0020 §3)."""

from __future__ import annotations

import pytest

from governance.publication import (
    PublicationBlocked,
    PublicationContentKind,
    PublicationTier,
    assert_publication_allowed,
    classify_publication_tier,
    requires_cfl_gate,
)
from knowledge.db.base import CflStatus


@pytest.mark.parametrize(
    "content_kind,expected_tier",
    [
        (PublicationContentKind.DAILY_SOURCE_DIGEST, PublicationTier.INTERNAL_AUTO),
        (PublicationContentKind.EVENT_LIST, PublicationTier.INTERNAL_AUTO),
        (PublicationContentKind.WATCHLIST_CHANGES, PublicationTier.INTERNAL_AUTO),
        (PublicationContentKind.EVIDENCE_UPDATES, PublicationTier.INTERNAL_AUTO),
        (PublicationContentKind.DATA_QUALITY_ALERT, PublicationTier.INTERNAL_AUTO),
        (PublicationContentKind.CORE_UPGRADE, PublicationTier.MATERIAL_REVIEW),
        (PublicationContentKind.CONFIRMED_CUSTOMER, PublicationTier.MATERIAL_REVIEW),
        (PublicationContentKind.SECO_MAJOR_CHANGE, PublicationTier.MATERIAL_REVIEW),
        (PublicationContentKind.MATERIAL_CMI_SIGNAL, PublicationTier.MATERIAL_REVIEW),
        (PublicationContentKind.SIGNIFICANT_CAR, PublicationTier.MATERIAL_REVIEW),
        (PublicationContentKind.FORMAL_COMPETITIVE_CONCLUSION, PublicationTier.MATERIAL_REVIEW),
        (PublicationContentKind.FORMAL_EXTERNAL_RESEARCH, PublicationTier.EXTERNAL_APPROVAL),
    ],
)
def test_classify_publication_tier_matches_charter_18(
    content_kind: PublicationContentKind, expected_tier: PublicationTier
) -> None:
    assert classify_publication_tier(content_kind) is expected_tier


def test_internal_auto_requires_no_gate() -> None:
    assert requires_cfl_gate(PublicationTier.INTERNAL_AUTO) is False
    assert_publication_allowed(PublicationTier.INTERNAL_AUTO, None)  # does not raise


@pytest.mark.parametrize(
    "tier", [PublicationTier.MATERIAL_REVIEW, PublicationTier.EXTERNAL_APPROVAL]
)
def test_gated_tiers_require_cfl_gate(tier: PublicationTier) -> None:
    assert requires_cfl_gate(tier) is True


def test_gated_tier_without_approval_raises() -> None:
    with pytest.raises(PublicationBlocked):
        assert_publication_allowed(PublicationTier.EXTERNAL_APPROVAL, CflStatus.REVIEW_REQUIRED)


def test_gated_tier_without_any_cfl_status_raises() -> None:
    with pytest.raises(PublicationBlocked):
        assert_publication_allowed(PublicationTier.MATERIAL_REVIEW, None)


def test_gated_tier_with_approval_passes() -> None:
    assert_publication_allowed(PublicationTier.MATERIAL_REVIEW, CflStatus.APPROVED)
    assert_publication_allowed(PublicationTier.EXTERNAL_APPROVAL, CflStatus.APPROVED)
