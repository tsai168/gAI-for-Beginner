"""K01 — Company repository (WBS-B4a, ADR-0011 §2).

`set_universe` is the CFL-02 gate: the first upgrade to Core raises the
CFL-02 candidate via G01 (ADR-0004 pattern — this module decides/raises,
G01 judges; PENDING under the B1 stub, B8 supplies the real rule).
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from governance.cfl import CflId, CflService, default_cfl_service
from knowledge.db.base import CflStatus, Universe
from knowledge.db.models import Company


def create_company(
    session: Session,
    *,
    company_name: str,
    universe: str,
    listing_market: str | None = None,
    stock_code: str | None = None,
    is_overseas: bool = False,
) -> Company:
    company = Company(
        company_name=company_name,
        universe=universe,
        listing_market=listing_market,
        stock_code=stock_code,
        is_overseas=is_overseas,
    )
    session.add(company)
    session.flush()
    return company


def get_company(session: Session, company_id: uuid.UUID) -> Company | None:
    return session.get(Company, company_id)


def list_companies_by_universe(session: Session, universe: str) -> list[Company]:
    return list(session.execute(select(Company).where(Company.universe == universe)).scalars())


def set_universe(
    session: Session,
    company: Company,
    new_universe: str,
    *,
    cfl_service: CflService = default_cfl_service,
) -> CflStatus | None:
    """Charter §17 CFL-02: only the *first* upgrade to Core needs Human
    Review. Returns the CFL-02 status when raised, else None (no gate hit)."""
    first_upgrade_to_core = (
        new_universe == Universe.CORE.value and company.universe != Universe.CORE.value
    )
    company.universe = new_universe
    session.flush()
    if not first_upgrade_to_core:
        return None
    return cfl_service.submit_candidate(
        session, table="company", row_id=company.company_id, cfl_id=CflId.CFL_02
    )
