import sys
# 🟢 核心黑魔法：將 src.models 路由動態導向 src.knowledge.db，完美相容舊的測試代碼引進
from src.knowledge.db import base

sys.modules["src.models"] = sys.modules["src.knowledge.db"]
sys.modules["src.models.base"] = base

Base = base.Base
