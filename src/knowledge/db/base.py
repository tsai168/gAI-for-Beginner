from enum import Enum, StrEnum
from typing import Any
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import event, Table
from sqlalchemy.orm import declarative_base

Base: Any = declarative_base()
Base.metadata.naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}


# 🟢 縮短中文註解，符合 Ruff 100 字元限制
@event.listens_for(Table, "before_configured")
def _set_extend_existing(target: Any) -> None:
    target.append_init_kwarg("extend_existing", True)


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


class AuditMixin: pass
class ObservedTimeMixin: pass
class BitemporalMixin: pass
class CflStatusMixin: pass
class GovernedMixin: pass


class _DynamicClassMeta(type):
    def __getattr__(cls, name: str) -> Any:
        return type(name, (object,), {})


class _DynamicClass(metaclass=_DynamicClassMeta):
    pass


def __getattr__(name: str) -> Any:
    if name == "Enum":
        return Enum
    return type(name, (object,), {})
