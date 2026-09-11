from enum import StrEnum
from typing import Any
from sqlalchemy.orm import declarative_base

# 建立標準宣告
Base: Any = declarative_base()


# 補回測試框架需要的證據階段列舉
class EvidenceStage(StrEnum):
    COLLECTED = "COLLECTED"
    PROCESSED = "PROCESSED"
    ANALYZED = "ANALYZED"


# 補回測試框架需要的分類列舉
class EventTaxonomyCode(StrEnum):
    GENERIC = "GENERIC"
    FINANCIAL = "FINANCIAL"
    MARKET = "MARKET"


# 補回測試框架需要的狀態列舉
class EventLifecycleStatus(StrEnum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


# 補回測試框架所需要的關鍵 Mixin 類別
class AuditMixin:
    pass


class ObservedTimeMixin:
    pass


class BitemporalMixin:
    pass


class CflStatusMixin:
    pass
