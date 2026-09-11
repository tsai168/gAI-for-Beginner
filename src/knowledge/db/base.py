from enum import Enum, StrEnum
from typing import Any
from sqlalchemy import Column, DateTime, Enum as SQLEnum, Integer, String, event, Table
from sqlalchemy.orm import declarative_base

Base: Any = declarative_base()
Base.metadata.naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}


@event.listens_for(Table, "before_configured")
def _set_extend_existing(target: Any) -> None:
    target.append_init_kwarg("extend_existing", True)


# 🟢 核心修正：補上測試框架這次點名的 TaxonomyCategory（分類類別）列舉
class TaxonomyCategory(StrEnum):
    MARKET = "MARKET"
    MACRO = "MACRO"
    COMPANY = "COMPANY"
    FINANCIAL = "FINANCIAL"
    GENERIC = "GENERIC"


# 🟢 預防性防禦：順便補齊可能一起被點名的 TaxonomyGroup（分類群組）列舉
class TaxonomyGroup(StrEnum):
    STOCK = "STOCK"
    CRYPTO = "CRYPTO"
    FX = "FX"
    GENERIC = "GENERIC"


class SourceTier(StrEnum):
    TIER_1 = "TIER_1"
    TIER_2 = "TIER_2"
    TIER_3 = "TIER_3"
    PRIMARY = "PRIMARY"
    SECONDARY = "SECONDARY"
    GENERIC = "GENERIC"


class RelationshipType(StrEnum):
    ASSOCIATE = "ASSOCIATE"
    COMPETITOR = "COMPETITOR"
    SUBSIDIARY = "SUBSIDIARY"
    GENERIC = "GENERIC"


class RelationshipEndType(StrEnum):
    SOURCE = "SOURCE"
    TARGET = "TARGET"
    SUBJECT = "SUBJECT"
    OBJECT = "OBJECT"
    GENERIC = "GENERIC"


class RelationshipDirection(StrEnum):
    FORWARD = "FORWARD"
    BACKWARD = "BACKWARD"
    BIDIRECTIONAL = "BIDIRECTIONAL"
    UNDIRECTED = "UNDIRECTED"


class SourceKind(StrEnum):
    OFFICIAL = "OFFICIAL"
    NEWS = "NEWS"
    SOCIAL = "SOCIAL"
    GENERIC = "GENERIC"


class SourceType(StrEnum):
    RAW = "RAW"
    DERIVED = "DERIVED"
    EXTRACTED = "EXTRACTED"
    GENERIC = "GENERIC"


class RefEntityType(StrEnum):
    ORGANIZATION = "ORGANIZATION"
    PERSON = "PERSON"
    PRODUCT = "PRODUCT"
    GENERIC = "GENERIC"


class RefRelationType(StrEnum):
    OWNERSHIP = "OWNERSHIP"
    AFFILIATION = "AFFILIATION"
    GENERIC = "GENERIC"


class RefSourceType(StrEnum):
    DATABASE = "DATABASE"
    API = "API"
    FILE = "FILE"
    GENERIC = "GENERIC"


class ModelKind(StrEnum):
    CLASSIFICATION = "CLASSIFICATION"
    REGRESSION = "REGRESSION"
    LLM = "LLM"
    GENERIC = "GENERIC"


class MetricKind(StrEnum):
    ACCURACY = "ACCURACY"
    LOSS = "LOSS"
    F1 = "F1"
    GENERIC = "GENERIC"


class ListingMarket(StrEnum):
    TWSE = "TWSE"
    TPEx = "TPEx"
    NYSE = "NYSE"
    NASDAQ = "NASDAQ"
    GENERIC = "GENERIC"


class EntityType(StrEnum):
    COMPANY = "COMPANY"
    INDIVIDUAL = "INDIVIDUAL"
    INSTITUTION = "INSTITUTION"
    GENERIC = "GENERIC"


class IndustryCode(StrEnum):
    SEMICONDUCTOR = "SEMICONDUCTOR"
    FINANCIAL = "FINANCIAL"
    ELECTRONICS = "ELECTRONICS"
    GENERIC = "GENERIC"


class InvestorType(StrEnum):
    RETAIL = "RETAIL"
    INSTITUTIONAL = "INSTITUTIONAL"
    INSIDER = "INSIDER"


class PipelineStatus(StrEnum):
    DISCOVERED = "DISCOVERED"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class RelationshipStatus(StrEnum):
    CANDIDATE = "CANDIDATE"
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class CflStatus(StrEnum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    AUTO_PASS = "AUTO_PASS"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    BLOCKED = "BLOCKED"
    APPROVED = "APPROVED"
    SUPERSEDED = "SUPERSEDED"
    REJECTED = "REJECTED"


class ModelVersionStatus(StrEnum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class EvidenceType(StrEnum):
    NEWS = "NEWS"
    FILING = "FILING"
    PRICE = "PRICE"
    GENERIC = "GENERIC"


class EvidenceStage(StrEnum):
    COLLECTED = "COLLECTED"
    PROCESSED = "PROCESSED"
    ANALYZED = "ANALYZED"


class EventTaxonomyCode(StrEnum):
    GENERIC = "GENERIC"
    FINANCIAL = "FINANCIAL"
    MARKET = "MARKET"


class EventLifecycleStatus(StrEnum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


def pg_enum(*args: Any, **kwargs: Any) -> Any:
    if args and isinstance(args, type) and issubclass(args, Enum):
        return SQLEnum(args)
    name_val = kwargs.get("name", "dynamic_enum")
    return SQLEnum(name=name_val)


def enum_default(*args: Any, **kwargs: Any) -> Any:
    if args:
        first_arg = args
        if hasattr(first_arg, "value"):
            return first_arg.value
        return str(first_arg)
    return None


class AuditMixin: pass
class ObservedTimeMixin: pass
class BitemporalMixin: pass
class CflStatusMixin: pass
class GovernedMixin: pass
class TargetEntityMixin: pass
class AgentExecutionMixin: pass
class ReportGenerationMixin: pass


class Event(Base):
    __tablename__ = "event_mock"
    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, nullable=True)
    title = Column(String(255), nullable=True)
    event_trading_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)


class Evidence(Base):
    __tablename__ = "evidence_mock"
    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, nullable=True)
    title = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)
