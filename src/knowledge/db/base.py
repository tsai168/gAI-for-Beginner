from enum import StrEnum
from typing import Any
from sqlalchemy.orm import declarative_base

# 建立標準宣告
Base: Any = declarative_base()


# 補回測試框架需要的狀態列舉（改用最標準的 StrEnum）
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
