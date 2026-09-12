"""WBS-B2: source registry + P03 snapshot (ADR-0008).

DB-level behaviour (append-only trigger, D01–D08 seed, FK enforcement) is
covered by the `migration` job; here we cover the pure-Python contract.
"""

from __future__ import annotations

import hashlib

from ingestion.snapshot import content_hash
from knowledge.db.base import Base
from knowledge.db.models import (
    APPEND_ONLY_TABLES,
    DEFERRED_FKS,
    Event,
    Evidence,
    SourceSnapshot,
)


def test_content_hash_is_sha256_hex() -> None:
    raw = b"CPO AI snapshot payload"
    assert content_hash(raw) == hashlib.sha256(raw).hexdigest()
    assert content_hash(raw) == content_hash(raw)  # deterministic
    assert content_hash(b"a") != content_hash(b"b")


def test_snapshot_idempotency_key() -> None:
    uqs = {
        tuple(c.name for c in con.columns)
        for con in SourceSnapshot.__table__.constraints
        if con.__class__.__name__ == "UniqueConstraint"
    }
    assert ("source_id", "content_hash") in uqs


def test_snapshot_is_append_only() -> None:
    assert APPEND_ONLY_TABLES == ("source_snapshot",)


def test_source_fk_chain() -> None:
    src = Base.metadata.tables["source"]
    snap = Base.metadata.tables["source_snapshot"]
    assert any(fk.column.table.name == "data_source" for fk in src.c.data_source_code.foreign_keys)
    assert any(fk.column.table.name == "source" for fk in snap.c.source_id.foreign_keys)


def test_event_evidence_source_fk_deferred() -> None:
    # No ORM-level FK on purpose (ADR-0008 §5, corrected): SQLAlchemy would
    # emit a use_alter FK's ALTER within the *same* create_all() call that
    # builds event/evidence in migration 0001, before `source` exists. The
    # constraint is added purely via op.create_foreign_key in migration 0002;
    # DEFERRED_FKS documents that intent.
    assert DEFERRED_FKS == (
        ("event", "source_id", "source", "source_id"),
        ("evidence", "source_id", "source", "source_id"),
    )
    for model in (Event, Evidence):
        col = model.__table__.c.source_id
        assert col.foreign_keys == set()
        assert col.nullable is True
