from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, text
from sqlalchemy.orm import relationship

from src.models.base import Base


class Source(Base):
    __tablename__ = "source"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=True,
    )

    evidences = relationship("Evidence", back_populates="source", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="source", cascade="all, delete-orphan")


class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey("source.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=True,
    )

    source = relationship("Source", back_populates="evidences")


class Event(Base):
    __tablename__ = "event"

    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey("source.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    
    # 🟢 終極修正：精準補上專案索引要求的核心交易日期欄位，粉碎 ConstraintColumnNotFoundError
    event_trading_date = Column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    created_at = Column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=True,
    )

    source = relationship("Source", back_populates="events")

