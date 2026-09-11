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
    # 🟢 核心修正：外鍵必須精準對應到 source 表的 id 欄位，而不是 source_id
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
    # 🟢 核心修正：外鍵必須精準對應到 source 表的 id 欄位，而不是 source_id
    source_id = Column(Integer, ForeignKey("source.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=True,
    )

    source = relationship("Source", back_populates="events")
