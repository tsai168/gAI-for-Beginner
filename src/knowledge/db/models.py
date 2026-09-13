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
    BenchmarkModel,
    BitemporalMixin,
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
    PublicationTier,
    RefEntityType,
    RelationshipEndType,
    RelationshipStatus,
    RelationshipType,
    ReportType,
    SourceTier,
    TaxonomyCategory,
    Universe,
    enum_default,
    pg_enum,
)

_PROJECT_ID_DEFAULT = "cpo-ai"
_MONEY = Numeric(20, 4)
_QTY = Numeric(20, 0)
_SCORE = Numeric(6, 3)  # 0..100 scale (Seco/CMI/Materiality)
_UNIT = Numeric(5, 4)
_RETURN = Numeric(12, 6)  # AR/CAR — fractional returns, not the 0..100 scale
_TS = DateTime(timezone=True)  # timestamptz (ADR-0007 §2)


def _uuid_pk(name: str) -> Mapped[uuid.UUID]:
    return mapped_column(
        name, UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )


def _range_check(column: str, lo: float, hi: float, *, nullable: bool = True) -> CheckConstraint:
    """DB-level backstop for score/confidence columns (WBS-B12 addendum,
    ADR-0025 §2) — [0,1] for `_UNIT`/`_CONF`-typed columns, [0,100] for
    `_SCORE`-typed ones, matching the bounds each M0x module's own
    `_check_scale`/range check already enforces in Python (M02/M03/M04/M05).
    Defense in depth, not a new business rule — the numbers here are read
    off the existing application-level constants, not invented.

    `name` is deliberately unprefixed: the naming_convention
    (`"ck": "ck_%(table_name)s_%(constraint_name)s"`) adds the `ck_<table>_`
    prefix itself, same as the existing `revision_seq_positive` constraint.
    """
    condition = f"{column} >= {lo} AND {column} <= {hi}"
    if nullable:
        condition = f"{column} IS NULL OR ({condition})"
    return CheckConstraint(condition, name=f"{column}_range")


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

    __table_args__ = (
        UniqueConstraint("stock_code", name="stock_code"),
        Index("ix_company_universe", "universe"),
        Index("ix_company_company_name", "company_name"),
        Index("ix_company_cfl_status", "cfl_status"),
        _range_check("confidence", 0, 1),
    )


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
        Index("ix_relationship_cfl_status", "cfl_status"),
        _range_check("confidence", 0, 1),
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
    # No ORM-level FK: `source` doesn't exist yet when B1's create_all runs,
    # and SQLAlchemy emits use_alter FKs within the *same* create_all call
    # regardless of the `tables=` filter, which fails with "relation source
    # does not exist". The real constraint is added purely via
    # op.create_foreign_key in migration 0002 (ADR-0008 §5, corrected).
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
        Index("ix_event_pipeline_status", "pipeline_status"),
        Index("ix_event_cfl_status", "cfl_status"),
        Index("ix_event_entity_id", "entity_id"),
        UniqueConstraint("event_id", "revision_seq", name="event_revision_seq"),
        CheckConstraint("revision_seq >= 1", name="revision_seq_positive"),
        _range_check("confidence", 0, 1),
        _range_check("materiality_score", 0, 100),
    )


# --- K06 Evidence / Source / Citation --------------------------------------------


class Evidence(ObservedTimeMixin, GovernedMixin, AuditMixin, Base):
    __tablename__ = "evidence"

    evidence_id: Mapped[uuid.UUID] = _uuid_pk("evidence_id")
    # See Event.source_id above: no ORM-level FK, added via migration 0002.
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
        Index("ix_evidence_cfl_status", "cfl_status"),
        _range_check("confidence", 0, 1),
        _range_check("authority", 0, 1),
        _range_check("directness", 0, 1),
        _range_check("time", 0, 1),  # DB column name (Python attr is time_, ADR-0007 §5)
        _range_check("specificity", 0, 1),
        _range_check("independence", 0, 1),
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


# =====================================================================
# WBS-B2 — Source Registry (D01–D08 catalogue) + P03 snapshot/version
# ADR-0008. `source` is referenced by event.source_id / evidence.source_id
# (cross-module FKs added in migration 0002, use_alter).
# =====================================================================


class DataSource(Base):
    """D01–D08 fixed catalogue (seeded in migration 0002). PK = the code."""

    __tablename__ = "data_source"

    source_code: Mapped[str] = mapped_column(primary_key=True)  # "D01".."D08"
    name: Mapped[str] = mapped_column(nullable=False)
    source_tier: Mapped[str | None] = mapped_column(
        pg_enum(SourceTier, "data_source_tier"), nullable=True
    )
    is_enabled: Mapped[bool] = mapped_column(nullable=False, server_default=text("true"))
    earliest_reliable_date: Mapped[date | None] = mapped_column(Date, nullable=True)  # CF-25
    auth_method: Mapped[str | None] = mapped_column(nullable=True)
    license_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(_TS, nullable=False, server_default=text("now()"))


class Source(AuditMixin, Base):
    """One retrieved source instance (a URL / document / dataset row batch)."""

    __tablename__ = "source"

    source_id: Mapped[uuid.UUID] = _uuid_pk("source_id")
    data_source_code: Mapped[str] = mapped_column(
        ForeignKey("data_source.source_code", ondelete="RESTRICT"), nullable=False
    )
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    publisher: Mapped[str | None] = mapped_column(nullable=True)
    source_ref: Mapped[str | None] = mapped_column(nullable=True)  # external accession id
    published_at: Mapped[datetime | None] = mapped_column(_TS, nullable=True)
    retrieved_at: Mapped[datetime] = mapped_column(_TS, nullable=False)
    parser_version: Mapped[str | None] = mapped_column(nullable=True)  # P03
    source_version: Mapped[str | None] = mapped_column(nullable=True)  # P03

    __table_args__ = (
        Index("ix_source_data_source_code", "data_source_code"),
        Index("ix_source_url", "url"),
    )


class SourceSnapshot(Base):
    """P03 — immutable content capture (CF-08 / GP-15). Append-only: a DB
    trigger (migration 0002) rejects UPDATE and DELETE."""

    __tablename__ = "source_snapshot"

    source_snapshot_id: Mapped[uuid.UUID] = _uuid_pk("source_snapshot_id")
    source_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("source.source_id", ondelete="RESTRICT"), nullable=False
    )
    content_hash: Mapped[str] = mapped_column(nullable=False)  # sha256 hex
    snapshot_ref: Mapped[str | None] = mapped_column(Text, nullable=True)  # I02 object key
    content_type: Mapped[str | None] = mapped_column(nullable=True)
    byte_size: Mapped[int | None] = mapped_column(_QTY, nullable=True)
    parser_version: Mapped[str | None] = mapped_column(nullable=True)
    source_version: Mapped[str | None] = mapped_column(nullable=True)
    retrieved_at: Mapped[datetime] = mapped_column(_TS, nullable=False)
    created_at: Mapped[datetime] = mapped_column(_TS, nullable=False, server_default=text("now()"))

    __table_args__ = (
        UniqueConstraint("source_id", "content_hash", name="source_content_hash"),
        Index("ix_source_snapshot_content_hash", "content_hash"),
    )


class AuditLogEntry(Base):
    """G03 — append-only decision trail (WBS-B8, ADR-0020, CF-45 / Charter
    §22 Auditability). Not part of Work-2 §2/§2.9 (no frozen schema exists
    for it — a genuine gap, closed the same way ADR-0003 closed the K01–K06
    gaps). A DB trigger (migration 0006) rejects UPDATE/DELETE, reusing the
    same `cpoai_append_only()` guard as `source_snapshot` (CF-08/GP-15)."""

    __tablename__ = "audit_log"

    audit_log_id: Mapped[uuid.UUID] = _uuid_pk("audit_log_id")
    agent_id: Mapped[str | None] = mapped_column(nullable=True)
    rule_ref: Mapped[str] = mapped_column(nullable=False)  # e.g. "CFL-04"
    table_name: Mapped[str] = mapped_column(nullable=False)
    row_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    decision: Mapped[str] = mapped_column(nullable=False)
    evidence_ids: Mapped[list[uuid.UUID]] = mapped_column(
        ARRAY(UUID(as_uuid=True)), nullable=False, server_default=text("'{}'::uuid[]")
    )
    confidence: Mapped[float | None] = mapped_column(_UNIT, nullable=True)
    model_version_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    correlation_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(_TS, nullable=False, server_default=text("now()"))

    __table_args__ = (
        Index("ix_audit_log_table_row", "table_name", "row_id"),
        Index("ix_audit_log_correlation_id", "correlation_id"),
    )


# =====================================================================
# WBS-B5b — §2.9 model-output tables (deferred from B1/B2, ADR-0003 G-1):
# seco_score (M03) / cmi_score (M04). Bitemporal (valid_from/valid_to),
# model_version_id mandatory (GP-10). ADR-0014.
# =====================================================================


class SecoScore(BitemporalMixin, AuditMixin, Base):
    __tablename__ = "seco_score"

    seco_score_id: Mapped[uuid.UUID] = _uuid_pk("seco_score_id")
    company_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("company.company_id", ondelete="CASCADE"), nullable=False
    )
    as_of: Mapped[datetime] = mapped_column(_TS, nullable=False)
    score: Mapped[float] = mapped_column(_SCORE, nullable=False)
    tech_relevance: Mapped[float] = mapped_column(_SCORE, nullable=False)
    product_readiness: Mapped[float] = mapped_column(_SCORE, nullable=False)
    customer_validation: Mapped[float] = mapped_column(_SCORE, nullable=False)
    ecosystem_position: Mapped[float] = mapped_column(_SCORE, nullable=False)
    commercialization: Mapped[float] = mapped_column(_SCORE, nullable=False)
    strategic_defensibility: Mapped[float] = mapped_column(_SCORE, nullable=False)
    confidence: Mapped[float] = mapped_column(_UNIT, nullable=False)  # CF-15: mandatory
    model_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("model_version.model_version_id", ondelete="RESTRICT"), nullable=False
    )

    __table_args__ = (
        Index("ix_seco_score_company_as_of", "company_id", "as_of"),
        _range_check("score", 0, 100, nullable=False),
        _range_check("tech_relevance", 0, 100, nullable=False),
        _range_check("product_readiness", 0, 100, nullable=False),
        _range_check("customer_validation", 0, 100, nullable=False),
        _range_check("ecosystem_position", 0, 100, nullable=False),
        _range_check("commercialization", 0, 100, nullable=False),
        _range_check("strategic_defensibility", 0, 100, nullable=False),
        _range_check("confidence", 0, 1, nullable=False),
    )


class CmiScore(BitemporalMixin, AuditMixin, Base):
    __tablename__ = "cmi_score"

    cmi_score_id: Mapped[uuid.UUID] = _uuid_pk("cmi_score_id")
    company_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("company.company_id", ondelete="CASCADE"), nullable=False
    )
    as_of: Mapped[datetime] = mapped_column(_TS, nullable=False)
    score: Mapped[float] = mapped_column(_SCORE, nullable=False)
    foreign_inst_momentum: Mapped[float] = mapped_column(_SCORE, nullable=False)
    domestic_inst_momentum: Mapped[float] = mapped_column(_SCORE, nullable=False)
    margin_short: Mapped[float] = mapped_column(_SCORE, nullable=False)
    ownership_concentration: Mapped[float] = mapped_column(_SCORE, nullable=False)
    trading_structure: Mapped[float] = mapped_column(_SCORE, nullable=False)
    model_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("model_version.model_version_id", ondelete="RESTRICT"), nullable=False
    )

    __table_args__ = (
        Index("ix_cmi_score_company_as_of", "company_id", "as_of"),
        _range_check("score", 0, 100, nullable=False),
        _range_check("foreign_inst_momentum", 0, 100, nullable=False),
        _range_check("domestic_inst_momentum", 0, 100, nullable=False),
        _range_check("margin_short", 0, 100, nullable=False),
        _range_check("ownership_concentration", 0, 100, nullable=False),
        _range_check("trading_structure", 0, 100, nullable=False),
    )


# =====================================================================
# WBS-B5d — §2.9 valuation_event_window (M06). ADR-0016.
# =====================================================================


class ValuationEventWindow(AuditMixin, Base):
    __tablename__ = "valuation_event_window"

    valuation_event_window_id: Mapped[uuid.UUID] = _uuid_pk("valuation_event_window_id")
    event_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("event.event_id", ondelete="CASCADE"), nullable=False
    )
    window_pre: Mapped[int] = mapped_column(Integer, nullable=False)
    window_post: Mapped[int] = mapped_column(Integer, nullable=False)
    benchmark_model: Mapped[str] = mapped_column(
        pg_enum(BenchmarkModel, "benchmark_model"), nullable=False
    )
    ar_series: Mapped[list[Any]] = mapped_column(JSONB, nullable=False)  # ordered daily AR
    car: Mapped[float] = mapped_column(_RETURN, nullable=False)
    market_cap: Mapped[float | None] = mapped_column(_MONEY, nullable=True)  # M07, CF-24
    model_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("model_version.model_version_id", ondelete="RESTRICT"), nullable=False
    )

    __table_args__ = (
        Index("ix_valuation_event_window_event_id", "event_id"),
        UniqueConstraint(
            "event_id",
            "benchmark_model",
            "model_version_id",
            name="event_benchmark_model_version",
        ),
    )


class ResearchReport(GovernedMixin, AuditMixin, Base):
    """R01-R06 (WBS-B11, ADR-0023 G-1 — not part of Work-2 §2/§2.9's frozen
    schema either, same gap-filling posture as `audit_log`, ADR-0003).

    `cfl_status` (from GovernedMixin) is only meaningfully driven by G01
    for report_type COMPARISON (CFL-06) and EXTERNAL_PUBLICATION (CFL-08)
    — the two report types Work-2 §5 CFL_CONTRACT actually names. Other
    report types are gated by their *subject*'s own governance state
    instead of inventing a new CFL id (ADR-0023 §2).

    `content_ref` stays a bare pointer (no I02 object-storage client exists
    in this codebase — same deferred-hook posture as
    `source_snapshot.snapshot_ref`, ADR-0003 §4 "OPEN — B11 前定" resolved
    here as "not resolved yet, still a hook"). Report content is computed
    live from the underlying tables at read time, not pre-rendered.
    """

    __tablename__ = "research_report"

    research_report_id: Mapped[uuid.UUID] = _uuid_pk("research_report_id")
    report_type: Mapped[str] = mapped_column(pg_enum(ReportType, "report_type"), nullable=False)
    subject_ref: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    subject_ref_type: Mapped[str | None] = mapped_column(
        pg_enum(RefEntityType, "ref_entity_type_report"), nullable=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    publication_tier: Mapped[str] = mapped_column(
        pg_enum(PublicationTier, "publication_tier"), nullable=False
    )
    content_ref: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_research_report_subject_ref", "subject_ref"),
        Index("ix_research_report_report_type", "report_type"),
        Index("ix_research_report_cfl_status", "cfl_status"),
        _range_check("confidence", 0, 1),
    )


CFL_GOVERNED_TABLES: tuple[str, ...] = (
    "company",
    "relationship",
    "event",
    "evidence",
    "research_report",
)
APPEND_ONLY_TABLES: tuple[str, ...] = ("source_snapshot", "audit_log")

# Cross-module FKs created in migration 0002 (both ends already exist by then).
DEFERRED_FKS: tuple[tuple[str, str, str, str], ...] = (
    ("event", "source_id", "source", "source_id"),
    ("evidence", "source_id", "source", "source_id"),
)
