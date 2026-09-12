"""K03 — Product repository (WBS-B4a, ADR-0011 §4).

No CFL gate here: Product.evidence_stage is computed/judged by M01 (CF-05,
WBS-B5). B4 only provides data access.
"""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from knowledge.db.models import Product


def create_product(
    session: Session,
    *,
    company_id: uuid.UUID,
    technology_id: uuid.UUID | None = None,
    evidence_stage: str | None = None,
    spec_summary: str | None = None,
) -> Product:
    product = Product(
        company_id=company_id,
        technology_id=technology_id,
        evidence_stage=evidence_stage,
        spec_summary=spec_summary,
    )
    session.add(product)
    session.flush()
    return product


def get_product(session: Session, product_id: uuid.UUID) -> Product | None:
    return session.get(Product, product_id)


def update_evidence_stage(session: Session, product: Product, evidence_stage: str) -> None:
    product.evidence_stage = evidence_stage
    session.flush()
