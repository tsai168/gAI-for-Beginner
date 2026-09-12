"""U05 — Response/request schemas (WBS-B9, ADR-0021, Work-2 §4.1).

Field names match the Data Contract (Work-2 §2) / Event Contract (Work-2
§3.1, CLAUDE.md §6) verbatim — no aliases. Only resources that actually
carry `version`/`cfl_status` include them (§4.3): Company has `cfl_status`
but no `version` field (that's an Event-only column); Event has both.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CompanyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    company_id: uuid.UUID
    company_name: str
    universe: str
    stock_code: str | None
    listing_market: str | None
    is_overseas: bool
    cfl_status: str
    confidence: float | None


class CompanyDetailOut(CompanyOut):
    evidence_ids: list[uuid.UUID]


class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    # CLAUDE.md §6 EVENT_CONTRACT field list, verbatim order.
    event_id: uuid.UUID
    project_id: str
    entity_id: uuid.UUID | None
    source_id: uuid.UUID | None
    occurred_at: datetime | None
    published_at: datetime | None
    retrieved_at: datetime
    pipeline_status: str
    version: int
    correlation_id: uuid.UUID | None
    causation_id: uuid.UUID | None
    confidence: float | None
    evidence_ids: list[uuid.UUID]
    cfl_status: str
    created_at: datetime


class EventDetailOut(EventOut):
    revision_chain: list[uuid.UUID]


class CflDecisionRequest(BaseModel):
    table: str
    row_id: uuid.UUID
    target: str  # a human-settable CflStatus: APPROVED / REJECTED / BLOCKED


class CflDecisionResponse(BaseModel):
    table: str
    row_id: uuid.UUID
    cfl_status: str
