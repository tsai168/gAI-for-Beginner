"""R03 — Seco/CMI dashboard data (WBS-B11, ADR-0023 §3, Charter §18
Internal Auto, "供 U01 消費").

Never persisted as a `research_report` row (see ADR-0023 §1): this is live
data for U01, not a discrete report artifact — every call re-reads the
current Bitemporal Seco/CMI versions.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from knowledge.db.models import CmiScore, Company, SecoScore
from models.cmi import current_cmi_score, list_current_cmi_scores
from models.seco import current_seco_score, list_current_seco_scores


@dataclass(slots=True, frozen=True)
class CompanyScoreSummary:
    company_id: uuid.UUID
    company_name: str
    seco_score: float | None
    cmi_score: float | None


def get_seco_cmi_dashboard(session: Session) -> list[CompanyScoreSummary]:
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


def get_company_scores(session: Session, company_id: uuid.UUID) -> CompanyScoreSummary | None:
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
