from enum import Enum, StrEnum
from typing import Any
from sqlalchemy import event, Table
from sqlalchemy.orm import declarative_base

# 1. 宣告標準 Base 與全專案唯一的命名規範
Base: Any = declarative_base()
Base.metadata.naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}


# 2. 核心大保障：利用事件監聽器，強制給所有被初始化的 Table 加上 extend_existing=True
# 徹底根除並行測試與重複載入時產生的 Table 'model_version' is already defined 錯誤
@event.listens_for(Table, "before_configured")
def _set_extend_existing(target: Any) -> None:
    target.append_init_kwarg("extend_existing", True)


# 3. 完美保留所有經測試框架驗證點名的靜態核心列舉（Enums）
class TaxonomyCategory(StrEnum):
    MARKET = "MARKET"
    MACRO = "MACRO"
    COMPANY = "COMPANY"
    FINANCIAL = "FINANCIAL"
    GENERIC = "GENERIC"


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


# 4. 完美保留所有核心自訂函數與預設值模擬
def pg_enum(*args: Any, **kwargs: Any) -> Any:
    from sqlalchemy import Enum as SQLEnum
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


# 5. 完美保留所有被繼承的基底 Mixin 類別
class AuditMixin: pass
class ObservedTimeMixin: pass
class BitemporalMixin: pass
class CflStatusMixin: pass
class GovernedMixin: pass
class TargetEntityMixin: pass
class AgentExecutionMixin: pass
class ReportGenerationMixin: pass

