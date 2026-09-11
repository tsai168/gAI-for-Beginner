"""ORM models — WBS-B1.

K01–K06 (Work-2 §2.2–2.7) + §2.9 raw-data tables (person, market_data,
institutional_trading, shareholding) + model_version (G04).

Column names are the contract (CLAUDE.md §6): they match Work-2 V1.4
verbatim. Shared columns come from mixins (ADR-0007 §4).
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    ARRAY,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    Table,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from knowledge.db.base import (
    AuditMixin,
    Base,
    BitemporalMixin,
    CflStatusMixin,
    EventLifecycleStatus,
    EventTaxonomyCode,
    EvidenceStage,
    EvidenceType,
    GovernedMixin,
    InvestorType,
    ListingMarket,
    ModelKind,
    ModelVersionStatus,
    ObservedTimeMixin,
    PipelineStatus,
    RefEntityType,
    RelationshipEndType,
    RelationshipStatus,
    RelationshipType,
    SourceTier,
    TaxonomyCategory,
    Universe,
    enum_default,
    pg_enum,
)

_PROJECT_ID_DEFAULT = "cpo-ai"
_MONEY = Numeric(20, 4)
_QTY = Numeric(20, 0)
_SCORE = Numeric(6, 3)
_UNIT = Numeric(5, 4)
_TS = DateTime(timezone=True)  # timestamptz (ADR-0007 §2)


def _uuid_pk(name: str) -> Mapped[uuid.UUID]:
    return mapped_column(
        name, UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )


# --- G04 model_version -----------------------------------------------------------


class ModelVersion(Base):
    __tablename__ = "model_version"

    model_version_id: Mapped[uuid.UUID] = _uuid_pk("model_version_id")
    model_kind: Mapped[str] = mapped_column(pg_enum(ModelKind, "model_kind"), nullable=False)
    version_label: Mapped[str] = mapped_column(nullable=False)
    params_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    formula_ref: Mapped[str | None] = mapped_column(nullable=True)
    valid_from: Mapped[datetime] = mapped_column(_TS, nullable=False)
    supersedes_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("model_version.model_version_id", ondelete="RESTRICT"), nullable=True
    )
    status: Mapped[str] = mapped_column(
        pg_enum(ModelVersionStatus, "model_version_status"),
        nullable=False,
        server_default=enum_default(ModelVersionStatus.DRAFT),
    )
    created_at: Mapped[datetime] = mapped_column(_TS, nullable=False, server_default=text("now()"))
    created_by: Mapped[str | None] = mapped_column(nullable=True)

    __table_args__ = (
        UniqueConstraint("model_kind", "version_label", name="model_kind_version_label"),
    )


# --- K02 association: Company.taxonomy_refs (ADR-0007 §5) --------------------

company_taxonomy = Table(
    "company_taxonomy",
    Base.metadata,
    Column("company_id", ForeignKey("company.company_id", ondelete="CASCADE"), primary_key=True),
    Column(
        "technology_id",
        ForeignKey("technology.technology_id", ondelete="RESTRICT"),
        primary_key=True,
    ),
)


# --- K01 Company -----------------------------------------------------------------


class Company(GovernedMixin, AuditMixin, Base):
    __tablename__ = "company"

    company_id: Mapped[uuid.UUID] = _uuid_pk("company_id")
    stock_code: Mapped[str | None] = mapped_column(nullable=True)
    company_name: Mapped[str] = mapped_column(nullable=False)
    universe: Mapped[str] = mapped_column(pg_enum(Universe, "universe"), nullable=False)
    listing_market: Mapped[str | None] = mapped_column(
        pg_enum(ListingMarket, "listing_market"), nullable=True
    )
    is_overseas: Mapped[bool] = mapped_column(nullable=False, server_default=text("false"))

    taxonomy_refs: Mapped[list[Technology]] = relationship(
        secondary=company_taxonomy, lazy="selectin"
    )

    __table_args__ = (UniqueConstraint("stock_code", name="stock_code"),)


# --- K02 Technology / Taxonomy -------------------------------------------------


class Technology(BitemporalMixin, AuditMixin, Base):
    __tablename__ = "technology"

    technology_id: Mapped[uuid.UUID] = _uuid_pk("technology_id")
    taxonomy_version_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("model_version.model_version_id", ondelete="RESTRICT"), nullable=True
    )
    category: Mapped[str] = mapped_column(
        pg_enum(TaxonomyCategory, "taxonomy_category"), nullable=False
    )
    parent_technology_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("technology.technology_id", ondelete="RESTRICT"), nullable=True
    )


# --- K03 Product -------------------------------------------------------------


class Product(AuditMixin, Base):
    __tablename__ = "product"

    product_id: Mapped[uuid.UUID] = _uuid_pk("product_id")
    company_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("company.company_id", ondelete="CASCADE"), nullable=False
    )
    technology_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("technology.technology_id", ondelete="RESTRICT"), nullable=True
    )
    evidence_stage: Mapped[str | None] = mapped_column(
        pg_enum(EvidenceStage, "evidence_stage"), nullable=True
    )
    spec_summary: Mapped[str | None] = mapped_column(Text, nullable=True)


# --- K04 Relationship -------------------------------------------------------------


class Relationship(GovernedMixin, AuditMixin, Base):
    __tablename__ = "relationship"

    relationship_id: Mapped[uuid.UUID] = _uuid_pk("relationship_id")
    source_entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    source_entity_type: Mapped[str] = mapped_column(
        pg_enum(RelationshipEndType, "rel_end_type_src"), nullable=False
    )
    target_entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    target_entity_type: Mapped[str] = mapped_column(
        pg_enum(RelationshipEndType, "rel_end_type_tgt"), nullable=False
    )
    relationship_type: Mapped[str] = mapped_column(
        pg_enum(RelationshipType, "relationship_type"), nullable=False
    )
    is_named: Mapped[bool] = mapped_column(nullable=False, server_default=text("false"))
    status: Mapped[str] = mapped_column(
        pg_enum(RelationshipStatus, "relationship_status"),
        nullable=False,
        server_default=enum_default(RelationshipStatus.CANDIDATE),
    )
    evidence_ids: Mapped[list[uuid.UUID]] = mapped_column(
        ARRAY(UUID(as_uuid=True)), nullable=False, server_default=text("'{}'::uuid[]")
    )

    __table_args__ = (
        Index("ix_relationship_source", "source_entity_id"),
        Index("ix_relationship_target", "target_entity_id"),
    )


# --- §2.9 Person -------------------------------------------------------------


class Person(AuditMixin, Base):
    __tablename__ = "person"

    person_id: Mapped[uuid.UUID] = _uuid_pk("person_id")
    full_name: Mapped[str] = mapped_column(nullable=False)
    role_title: Mapped[str | None] = mapped_column(nullable=True)
    affiliation_company_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("company.company_id", ondelete="SET NULL"), nullable=True
    )


# --- K05 Event (K05 entity + EVENT_CONTRACT common fields; ADR-0007 §5) ------


class Event(ObservedTimeMixin, BitemporalMixin, GovernedMixin, AuditMixin, Base):
    __tablename__ = "event"

    event_id: Mapped[uuid.UUID] = _uuid_pk("event_id")
    project_id: Mapped[str] = mapped_column(
        nullable=False, server_default=text(f"'{_PROJECT_ID_DEFAULT}'")
    )
    entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    source_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    revision_of_event_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("event.event_id", ondelete="RESTRICT"), nullable=True
    )
    revision_seq: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    lifecycle_status: Mapped[str] = mapped_column(
        pg_enum(EventLifecycleStatus, "event_lifecycle_status"),
        nullable=False,
        server_default=enum_default(EventLifecycleStatus.ACTIVE),
    )
    pipeline_status: Mapped[str] = mapped_column(
        pg_enum(PipelineStatus, "pipeline_status"),
        nullable=False,
        server_default=enum_default(PipelineStatus.DISCOVERED),
    )
    event_taxonomy_code: Mapped[str] = mapped_column(
        pg_enum(EventTaxonomyCode, "event_taxonomy_code"), nullable=False
    )
    materiality_score: Mapped[float | None] = mapped_column(_SCORE, nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    correlation_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    causation_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    evidence_ids: Mapped[list[uuid.UUID]] = mapped_column(
        ARRAY(UUID(as_uuid=True)), nullable=False, server_default=text("'{}'::uuid[]")
    )

    __table_args__ = (
        Index("ix_event_revision_of_event_id", "revision_of_event_id"),
        Index("ix_event_event_taxonomy_code", "event_taxonomy_code"),
        Index("ix_event_event_trading_date", "event_trading_date"),
        Index("ix_event_correlation_id", "correlation_id"),
        UniqueConstraint("event_id", "revision_seq", name="event_revision_seq"),
        CheckConstraint("revision_seq >= 1", name="revision_seq_positive"),
    )


# --- K06 Evidence / Source / Citation --------------------------------------------


class Evidence(ObservedTimeMixin, CflStatusMixin, AuditMixin, Base):
    __tablename__ = "evidence"

    evidence_id: Mapped[uuid.UUID] = _uuid_pk("evidence_id")
    source_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    entity_ref: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    entity_ref_type: Mapped[str | None] = mapped_column(
        pg_enum(RefEntityType, "ref_entity_type_evd"), nullable=True
    )
    event_ref: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("event.event_id", ondelete="SET NULL"), nullable=True
    )
    evidence_type: Mapped[str] = mapped_column(
        pg_enum(EvidenceType, "evidence_type"), nullable=False
    )
    evidence_stage: Mapped[str | None] = mapped_column(
        pg_enum(EvidenceStage, "evidence_stage"), nullable=True
    )
    source_credibility_tier: Mapped[str | None] = mapped_column(
        pg_enum(SourceTier, "source_tier"), nullable=True
    )
    # CF-10 five discriminators. DB column "time" kept verbatim (Work-2 §2.7);
    # Python attr is time_ to avoid the SQL type-name clash (ADR-0007 §5).
    authority: Mapped[float | None] = mapped_column(_UNIT, nullable=True)
    directness: Mapped[float | None] = mapped_column(_UNIT, nullable=True)
    time_: Mapped[float | None] = mapped_column("time", _UNIT, nullable=True)
    specificity: Mapped[float | None] = mapped_column(_UNIT, nullable=True)
    independence: Mapped[float | None] = mapped_column(_UNIT, nullable=True)
    content_hash: Mapped[str] = mapped_column(nullable=False)
    snapshot_ref: Mapped[str | None] = mapped_column(nullable=True)

    __table_args__ = (
        Index("ix_evidence_content_hash", "content_hash"),
        Index("ix_evidence_source_id", "source_id"),
        Index("ix_evidence_entity_ref", "entity_ref"),
    )


# --- §2.9 market_data -------------------------------------------------------------


class MarketData(BitemporalMixin, AuditMixin, Base):
    __tablename__ = "market_data"

    market_data_id: Mapped[uuid.UUID] = _uuid_pk("market_data_id")
    company_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("company.company_id", ondelete="CASCADE"), nullable=False
    )
    trade_date: Mapped[date] = mapped_column(Date, nullable=False)
    close_price: Mapped[float | None] = mapped_column(_MONEY, nullable=True)
    volume: Mapped[int | None] = mapped_column(_QTY, nullable=True)
    shares_outstanding: Mapped[int | None] = mapped_column(_QTY, nullable=True)  # PIT (CF-24)
    retrieved_at: Mapped[datetime] = mapped_column(_TS, nullable=False)
    available_at: Mapped[datetime | None] = mapped_column(_TS, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "company_id", "trade_date", "valid_from", name="company_trade_date_valid_from"
        ),
        Index("ix_market_data_company_trade_date", "company_id", "trade_date"),
    )


# --- §2.9 institutional_trading -------------------------------------------------


class InstitutionalTrading(AuditMixin, Base):
    __tablename__ = "institutional_trading"

    institutional_trading_id: Mapped[uuid.UUID] = _uuid_pk("institutional_trading_id")
    company_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("company.company_id", ondelete="CASCADE"), nullable=False
    )
    trade_date: Mapped[date] = mapped_column(Date, nullable=False)
    investor_type: Mapped[str] = mapped_column(
        pg_enum(InvestorType, "investor_type"), nullable=False
    )
    net_buy_sell: Mapped[int | None] = mapped_column(_QTY, nullable=True)
    retrieved_at: Mapped[datetime] = mapped_column(_TS, nullable=False)
    available_at: Mapped[datetime | None] = mapped_column(_TS, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "company_id", "trade_date", "investor_type", name="company_trade_date_investor"
        ),
    )


# --- §2.9 shareholding (D06 TDCC; available_at NOT NULL, ADR-0003 G-3) ------


class Shareholding(AuditMixin, Base):
    __tablename__ = "shareholding"

    shareholding_id: Mapped[uuid.UUID] = _uuid_pk("shareholding_id")
    company_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("company.company_id", ondelete="CASCADE"), nullable=False
    )
    as_of_date: Mapped[date] = mapped_column(Date, nullable=False)
    bucket: Mapped[str] = mapped_column(nullable=False)
    holders: Mapped[int | None] = mapped_column(_QTY, nullable=True)
    shares: Mapped[int | None] = mapped_column(_QTY, nullable=True)
    pct: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True)
    retrieved_at: Mapped[datetime] = mapped_column(_TS, nullable=False)
    available_at: Mapped[datetime] = mapped_column(_TS, nullable=False)  # CF-26 / GP-08/09

    __table_args__ = (
        UniqueConstraint("company_id", "as_of_date", "bucket", name="company_as_of_bucket"),
    )


CFL_GOVERNED_TABLES: tuple[str, ...] = ("company", "relationship", "event", "evidence")
