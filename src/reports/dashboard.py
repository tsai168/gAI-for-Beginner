"""R03 — Seco/CMI dashboard data (WBS-B11, ADR-0023 §3, Charter §18
Internal Auto, "供 U01 消費").

Never persisted as a `research_report` row (see ADR-0023 §1): this is live
data for U01, not a discrete report artifact. "Live" now means "I03-cached
with a short TTL" (ADR-0025 §3) rather than "always a fresh query" —
Work-1 §3.10 names this exact data ("高頻讀取（Dashboard／Seco/CMI）加速")
as I03's reason to exist.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from knowledge.db.models import CmiScore, Company, SecoScore
from models.cmi import current_cmi_score, list_current_cmi_scores
from models.seco import current_seco_score, list_current_seco_scores
from reports.cache import CacheBackend, get_cache_backend

# I03 low-risk default (ADR-0025 §3) — adjustable, not Frozen. Short enough
# that the lack of invalidate-on-write (see cache.py's module docstring)
# stays a minor, bounded staleness window rather than a real correctness
# problem.
_DASHBOARD_CACHE_TTL_SECONDS = 60
_DASHBOARD_CACHE_KEY = "reports:dashboard:seco-cmi"
_COMPANY_SCORE_KEY_PREFIX = "reports:dashboard:company:"


@dataclass(slots=True, frozen=True)
class CompanyScoreSummary:
    company_id: uuid.UUID
    company_name: str
    seco_score: float | None
    cmi_score: float | None


def _to_dict(summary: CompanyScoreSummary) -> dict[str, object]:
    return {
        "company_id": str(summary.company_id),
        "company_name": summary.company_name,
        "seco_score": summary.seco_score,
        "cmi_score": summary.cmi_score,
    }


def _from_dict(row: dict[str, object]) -> CompanyScoreSummary:
    return CompanyScoreSummary(
        company_id=uuid.UUID(str(row["company_id"])),
        company_name=str(row["company_name"]),
        seco_score=row["seco_score"],  # type: ignore[arg-type]
        cmi_score=row["cmi_score"],  # type: ignore[arg-type]
    )


def _compute_seco_cmi_dashboard(session: Session) -> list[CompanyScoreSummary]:
    seco_by_company: dict[uuid.UUID, SecoScore] = {
        s.company_id: s for s in list_current_seco_scores(session)
    }
    cmi_by_company: dict[uuid.UUID, CmiScore] = {
        c.company_id: c for c in list_current_cmi_scores(session)
    }
    company_ids = set(seco_by_company) | set(cmi_by_company)
    summaries = []
    for company_id in company_ids:
        company = session.get(Company, company_id)
        if company is None:
            continue
        summaries.append(
            CompanyScoreSummary(
                company_id=company_id,
                company_name=company.company_name,
                seco_score=float(seco_by_company[company_id].score)
                if company_id in seco_by_company
                else None,
                cmi_score=float(cmi_by_company[company_id].score)
                if company_id in cmi_by_company
                else None,
            )
        )
    return summaries


def get_seco_cmi_dashboard(
    session: Session, *, cache: CacheBackend | None = None
) -> list[CompanyScoreSummary]:
    cache = cache if cache is not None else get_cache_backend()
    cached = cache.get(_DASHBOARD_CACHE_KEY)
    if cached is not None:
        return [_from_dict(row) for row in json.loads(cached)]
    summaries = _compute_seco_cmi_dashboard(session)
    cache.set(
        _DASHBOARD_CACHE_KEY,
        json.dumps([_to_dict(s) for s in summaries]),
        ttl_seconds=_DASHBOARD_CACHE_TTL_SECONDS,
    )
    return summaries


def _compute_company_scores(session: Session, company_id: uuid.UUID) -> CompanyScoreSummary | None:
    company = session.get(Company, company_id)
    if company is None:
        return None
    seco = current_seco_score(session, company_id)
    cmi = current_cmi_score(session, company_id)
    return CompanyScoreSummary(
        company_id=company_id,
        company_name=company.company_name,
        seco_score=float(seco.score) if seco is not None else None,
        cmi_score=float(cmi.score) if cmi is not None else None,
    )


def get_company_scores(
    session: Session, company_id: uuid.UUID, *, cache: CacheBackend | None = None
) -> CompanyScoreSummary | None:
    cache = cache if cache is not None else get_cache_backend()
    key = f"{_COMPANY_SCORE_KEY_PREFIX}{company_id}"
    cached = cache.get(key)
    if cached is not None:
        row = json.loads(cached)
        return None if row is None else _from_dict(row)
    summary = _compute_company_scores(session, company_id)
    cache.set(
        key,
        json.dumps(_to_dict(summary) if summary is not None else None),
        ttl_seconds=_DASHBOARD_CACHE_TTL_SECONDS,
    )
    return summary
