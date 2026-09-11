# 直接引入原專案最真實、欄位最齊全的正式模型
from src.knowledge.db.models import Event, Evidence, Source

# 保持對外接口一致，讓測試框架能正常 import 這些模型
__all__ = ["Source", "Evidence", "Event"]
