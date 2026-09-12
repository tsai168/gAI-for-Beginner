"""R01 — Daily source digest / Watchlist change report (WBS-B11, ADR-0023
§3, Charter §18 Internal Auto).

Internal Auto: "基本驗證後內部自動產生" (Charter §18) — no CFL/publication
gate; this module only aggregates already-governed data, it makes no new
governance decisions of its own.

"Watchlist 異動" is only partially observable: `company.universe` isn't
Bitemporal (unlike Technology/SecoScore), so a plain Watchlist<->Adjacent
move leaves no history. The one universe transition this *can* report is a
first upgrade to Core, because that always raises a CFL-02 candidate
(`knowledge.repository.company.set_universe`) and G01 now logs every
decision to `audit_log` (WBS-B8) — so this digest surfaces CFL-02 grants
in the window, not a full change log. Documented, not silently dropped
(ADR-0023 §5).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from governance.audit import list_decisions_since
from governance.publication import PublicationTier
from knowledge.db.base import ReportType
from knowledge.db.models import ResearchReport, Source
from knowledge.repository.research_report import create_report


@dataclass(slots=True, frozen=True)
class DailySourceDigest:
    window_start: datetime
    window_end: datetime
    new_source_ids: list[uuid.UUID] = field(default_factory=list)
    core_upgrade_company_ids: list[uuid.UUID] = field(default_factory=list)


def build_daily_digest(
    session: Session, *, window_start: datetime, window_end: datetime
) -> DailySourceDigest:
    new_sources = session.execute(
        select(Source.source_id).where(
            Source.retrieved_at >= window_start, Source.retrieved_at < window_end
        )
    ).scalars()
    core_upgrades = list_decisions_since(
        session, since=window_start, until=window_end, rule_ref="CFL-02"
    )
    return DailySourceDigest(
        window_start=window_start,
        window_end=window_end,
        new_source_ids=list(new_sources),
        core_upgrade_company_ids=[d.row_id for d in core_upgrades],
    )


def record_daily_digest(session: Session, digest: DailySourceDigest) -> ResearchReport:
    """Internal Auto — no CFL gate, no cfl_status write. `content_ref` is a
    hook (see module docstring / ADR-0023 §1); the digest content itself
    lives only in the `DailySourceDigest` this call was given, not
    persisted verbatim."""
    return create_report(
        session,
        report_type=ReportType.DAILY_DIGEST,
        publication_tier=PublicationTier.INTERNAL_AUTO,
    )
