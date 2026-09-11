import sqlalchemy
from src.models.base import Base


class Source(Base):
    __tablename__ = "source"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String(255), nullable=False)
    created_at = sqlalchemy.Column(
        sqlalchemy.DateTime(timezone=True),
        server_default=sqlalchemy.text("now()"),
        nullable=True,
    )

    evidences = sqlalchemy.orm.relationship(
        "Evidence", back_populates="source", cascade="all, delete-orphan"
    )
    events = sqlalchemy.orm.relationship(
        "Event", back_populates="source", cascade="all, delete-orphan"
    )


class Evidence(Base):
    __tablename__ = "evidence"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    source_id = sqlalchemy.Column(
        sqlalchemy.Integer,
        sqlalchemy.ForeignKey("source.id", ondelete="SET NULL"),
        nullable=True,
    )
    title = sqlalchemy.Column(sqlalchemy.String(255), nullable=False)
    created_at = sqlalchemy.Column(
        sqlalchemy.DateTime(timezone=True),
        server_default=sqlalchemy.text("now()"),
        nullable=True,
    )

    source = sqlalchemy.orm.relationship("Source", back_populates="evidences")


class Event(Base):
    __tablename__ = "event"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    source_id = sqlalchemy.Column(
        sqlalchemy.Integer,
        sqlalchemy.ForeignKey("source.id", ondelete="SET NULL"),
        nullable=True,
    )
    title = sqlalchemy.Column(sqlalchemy.String(255), nullable=False)
    created_at = Column_data = sqlalchemy.Column(
        sqlalchemy.DateTime(timezone=True),
        server_default=sqlalchemy.text("now()"),
        nullable=True,
    )

    source = sqlalchemy.orm.relationship("Source", back_populates="events")
