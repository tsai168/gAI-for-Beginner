from typing import Any
from sqlalchemy.orm import declarative_base

# 獨立宣告自己的 Base，徹底跟 knowledge 劃清界線，斬斷循環引用
Base: Any = declarative_base()
