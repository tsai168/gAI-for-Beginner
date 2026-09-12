"""G06 — Publication state machine (WBS-B8, ADR-0020, Charter §18, CF-33).

Charter §18 fixes three publication tiers — Internal Auto／Material
Review／External Approval — and names, verbatim, which content kinds fall
into each. `research_report` (R02, WBS-B11) will carry a
`publication_tier`/`cfl_status` pair per ADR-0003 G-1; this module supplies
the tier classification and the CFL gate now so K05's pipeline_status
advance (`knowledge.repository.event.advance_pipeline_status`, also B8)
and R06 (later, B11) share one implementation instead of duplicating it.

Only External Approval is gated by CFL-08 specifically; Material Review
content is already gated by whichever CFL governs *that* content (CFL-02
Core upgrade, CFL-05 Confirmed customer, ...) — this module doesn't
re-encode that mapping (Work-2 §5 CFL_CONTRACT already owns it), it just
asks the caller for the resulting `cfl_status` and enforces APPROVED before
anything beyond Internal Auto proceeds.
"""

from __future__ import annotations

import enum

from knowledge.db.base import CflStatus


class PublicationTier(enum.StrEnum):
    INTERNAL_AUTO = "INTERNAL_AUTO"
    MATERIAL_REVIEW = "MATERIAL_REVIEW"
    EXTERNAL_APPROVAL = "EXTERNAL_APPROVAL"


class PublicationContentKind(enum.StrEnum):
    """Charter §18, transcribed verbatim — the only content kinds Charter
    actually names. Anything else is OPEN (no invented tier — GP-07
    spirit): callers must classify by one of these, not guess a tier
    directly."""

    DAILY_SOURCE_DIGEST = "DAILY_SOURCE_DIGEST"
    EVENT_LIST = "EVENT_LIST"
    WATCHLIST_CHANGES = "WATCHLIST_CHANGES"
    EVIDENCE_UPDATES = "EVIDENCE_UPDATES"
    DATA_QUALITY_ALERT = "DATA_QUALITY_ALERT"
    CORE_UPGRADE = "CORE_UPGRADE"
    CONFIRMED_CUSTOMER = "CONFIRMED_CUSTOMER"
    SECO_MAJOR_CHANGE = "SECO_MAJOR_CHANGE"
    MATERIAL_CMI_SIGNAL = "MATERIAL_CMI_SIGNAL"
    SIGNIFICANT_CAR = "SIGNIFICANT_CAR"
    FORMAL_COMPETITIVE_CONCLUSION = "FORMAL_COMPETITIVE_CONCLUSION"
    FORMAL_EXTERNAL_RESEARCH = "FORMAL_EXTERNAL_RESEARCH"


_TIER_BY_CONTENT_KIND: dict[PublicationContentKind, PublicationTier] = {
    PublicationContentKind.DAILY_SOURCE_DIGEST: PublicationTier.INTERNAL_AUTO,
    PublicationContentKind.EVENT_LIST: PublicationTier.INTERNAL_AUTO,
    PublicationContentKind.WATCHLIST_CHANGES: PublicationTier.INTERNAL_AUTO,
    PublicationContentKind.EVIDENCE_UPDATES: PublicationTier.INTERNAL_AUTO,
    PublicationContentKind.DATA_QUALITY_ALERT: PublicationTier.INTERNAL_AUTO,
    PublicationContentKind.CORE_UPGRADE: PublicationTier.MATERIAL_REVIEW,
    PublicationContentKind.CONFIRMED_CUSTOMER: PublicationTier.MATERIAL_REVIEW,
    PublicationContentKind.SECO_MAJOR_CHANGE: PublicationTier.MATERIAL_REVIEW,
    PublicationContentKind.MATERIAL_CMI_SIGNAL: PublicationTier.MATERIAL_REVIEW,
    PublicationContentKind.SIGNIFICANT_CAR: PublicationTier.MATERIAL_REVIEW,
    PublicationContentKind.FORMAL_COMPETITIVE_CONCLUSION: PublicationTier.MATERIAL_REVIEW,
    PublicationContentKind.FORMAL_EXTERNAL_RESEARCH: PublicationTier.EXTERNAL_APPROVAL,
}


def classify_publication_tier(content_kind: PublicationContentKind) -> PublicationTier:
    return _TIER_BY_CONTENT_KIND[content_kind]


def requires_cfl_gate(tier: PublicationTier) -> bool:
    """Internal Auto proceeds after basic validation only (Charter §18);
    Material Review and External Approval both need an APPROVED CFL
    decision before publication."""
    return tier is not PublicationTier.INTERNAL_AUTO


class PublicationBlocked(PermissionError):
    """Raised when a publish is attempted before its required CFL gate has
    resolved to APPROVED (CF-33; Work-3 TEST-CFL-02)."""


def assert_publication_allowed(tier: PublicationTier, cfl_status: CflStatus | None) -> None:
    if not requires_cfl_gate(tier):
        return
    if cfl_status is not CflStatus.APPROVED:
        raise PublicationBlocked(
            f"{tier} publication requires an APPROVED CFL decision "
            f"(CFL-08 for EXTERNAL_APPROVAL); got {cfl_status}"
        )
