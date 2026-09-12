"""Declarative Base, shared column mixins and Charter-frozen enumerations.

Enum *values* are transcribed verbatim from the Charter / Work-2 and MUST NOT
be renamed (CLAUDE.md §6). Representation = varchar + CHECK (ADR-0007 §2).
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, MetaData, Numeric, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql.elements import TextClause

# Deterministic constraint/index names -> clean Alembic diffs.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


# --- Charter / Work-2 frozen enumerations -------------------------------------


class CflStatus(enum.StrEnum):
    PENDING = "PENDING"
    AUTO_PASS = "AUTO-PASS"
    REVIEW_REQUIRED = "REVIEW-REQUIRED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    BLOCKED = "BLOCKED"
    SUPERSEDED = "SUPERSEDED"


class PipelineStatus(enum.StrEnum):
    DISCOVERED = "DISCOVERED"
    FETCHED = "FETCHED"
    NORMALIZED = "NORMALIZED"
    EXTRACTED = "EXTRACTED"
    VERIFIED = "VERIFIED"
    ANALYZED = "ANALYZED"
    APPROVED = "APPROVED"
    PUBLISHED = "PUBLISHED"


class EventLifecycleStatus(enum.StrEnum):
    ACTIVE = "ACTIVE"
    CORRECTED = "CORRECTED"
    SUPERSEDED = "SUPERSEDED"
    WITHDRAWN = "WITHDRAWN"
    DISPUTED = "DISPUTED"


class EvidenceStage(enum.StrEnum):
    E0 = "E0"
    E1 = "E1"
    E2 = "E2"
    E3 = "E3"
    E4 = "E4"
    E5 = "E5"
    E6 = "E6"


class SourceTier(enum.StrEnum):
    S1 = "S1"
    S2 = "S2"
    S3 = "S3"
    S4 = "S4"
    S5 = "S5"


class EvidenceType(enum.StrEnum):
    SUPPORT = "SUPPORT"
    CONTRADICT = "CONTRADICT"
    NEUTRAL_CONTEXT = "NEUTRAL-CONTEXT"


class EventTaxonomyCode(enum.StrEnum):
    EV01 = "EV01"
    EV02 = "EV02"
    EV03 = "EV03"
    EV04 = "EV04"
    EV05 = "EV05"
    EV06 = "EV06"
    EV07 = "EV07"
    EV08 = "EV08"
    EV09 = "EV09"
    EV10 = "EV10"
    EV11 = "EV11"
    EV12 = "EV12"


class Universe(enum.StrEnum):
    CORE = "Core"
    ADJACENT = "Adjacent"
    WATCHLIST = "Watchlist"


class ListingMarket(enum.StrEnum):
    LISTED = "LISTED"  # 上市 (TWSE)
    OTC = "OTC"  # 上櫃 (TPEx)
    EMERGING = "EMERGING"  # 興櫃


class TaxonomyCategory(enum.StrEnum):
    CPO = "CPO"
    OPTICAL_IO = "Optical I/O"
    ELSFP = "ELSFP"
    PLUGGABLE_OPTICS = "Pluggable Optics"


class RelationshipType(enum.StrEnum):
    CUSTOMER = "CUSTOMER"
    SUPPLIER = "SUPPLIER"
    PARTNER = "PARTNER"
    COMPETITOR = "COMPETITOR"


class RelationshipStatus(enum.StrEnum):
    CANDIDATE = "CANDIDATE"
    CONFIRMED = "CONFIRMED"


class RefEntityType(enum.StrEnum):
    COMPANY = "company"
    PERSON = "person"
    PRODUCT = "product"
    TECHNOLOGY = "technology"
    RELATIONSHIP = "relationship"
    EVENT = "event"


class RelationshipEndType(enum.StrEnum):
    """K04 relationship endpoints — {company, person} only (ADR-0005 G4-2)."""

    COMPANY = "company"
    PERSON = "person"


class InvestorType(enum.StrEnum):
    FOREIGN = "FOREIGN"  # 外資 (C1)
    INVESTMENT_TRUST = "INVESTMENT_TRUST"  # 投信 (C2)
    DEALER = "DEALER"  # 自營商


class ModelKind(enum.StrEnum):
    SECO = "seco"
    CMI = "cmi"
    MATERIALITY = "materiality"
    CONFIDENCE = "confidence"
    BENCHMARK = "benchmark"
    TAXONOMY = "taxonomy"
    CFL = "cfl"


class ModelVersionStatus(enum.StrEnum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"


class BenchmarkModel(enum.StrEnum):
    """Charter §14.2 CF-23: at least these two benchmarks."""

    MARKET_ADJUSTED = "MARKET_ADJUSTED"
    MARKET_MODEL = "MARKET_MODEL"


def pg_enum(py_enum: type[enum.Enum], name: str) -> Enum:
    """varchar + CHECK (native_enum=False), per ADR-0007 §2."""
    return Enum(
        py_enum,
        name=name,
        native_enum=False,
        create_constraint=True,
        values_callable=lambda e: [m.value for m in e],
    )


def enum_default(member: enum.Enum) -> TextClause:
    """server_default for a non-native enum column: a quoted SQL literal."""
    return text(f"'{member.value}'")


# --- shared column mixins ----------------------------------------------------

_CONF = Numeric(5, 4)  # 0..1


def _uuid_pk(col_name: str) -> Mapped[uuid.UUID]:
    return mapped_column(
        col_name,
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )


class AuditMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class BitemporalMixin:
    valid_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    valid_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class CflStatusMixin:
    """cfl_status is written only via G01 (governance.cfl); a DB trigger
    (migration 0001) blocks direct updates. See ADR-0004 / ADR-0007 §6."""

    cfl_status: Mapped[str] = mapped_column(
        pg_enum(CflStatus, "cfl_status"),
        nullable=False,
        server_default=text(f"'{CflStatus.PENDING.value}'"),
    )


class GovernedMixin(CflStatusMixin):
    """CflStatusMixin + the confidence / model-version columns (Work-2 §2.1)."""

    confidence: Mapped[float | None] = mapped_column(_CONF, nullable=True)
    model_version_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)


class ObservedTimeMixin:
    """Charter §14.4 / CF-21 / CF-21A. Missing values stay NULL (GP-07);
    only retrieved_at is Required."""

    occurred_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    market_known_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    available_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    event_trading_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    time_basis: Mapped[str | None] = mapped_column(nullable=True)
    time_precision: Mapped[str | None] = mapped_column(nullable=True)
    time_confidence: Mapped[float | None] = mapped_column(_CONF, nullable=True)
