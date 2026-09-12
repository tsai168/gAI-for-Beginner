"""WBS-B1 acceptance: schema vs Work-2 V1.4 contract.

TEST-DATA-01 — every contract field name is present on the ORM model,
verbatim, with no synonym (CLAUDE.md §6, Work-3 §4).
TEST-DATA-02 — missing Observed-Time fields stay NULL (CF-21 / GP-07):
nullable, no server_default guess.
"""

from __future__ import annotations

import pytest

from knowledge.db import models as m
from knowledge.db.base import Base
from knowledge.db.models import Event, Evidence, InstitutionalTrading, MarketData, Shareholding

# Column names transcribed from Work-2 V1.4 §2.2–2.7 / §2.9 (+ ADR-0002/03/05/07).
CONTRACT_COLUMNS: dict[str, set[str]] = {
    "company": {
        "company_id",
        "stock_code",
        "company_name",
        "universe",
        "listing_market",
        "is_overseas",
        "cfl_status",
        "confidence",
        "model_version_id",
        "created_at",
        "updated_at",
    },
    "technology": {
        "technology_id",
        "taxonomy_version_id",
        "category",
        "parent_technology_id",
        "valid_from",
        "valid_to",
        "created_at",
        "updated_at",
    },
    "product": {
        "product_id",
        "company_id",
        "technology_id",
        "evidence_stage",
        "spec_summary",
        "created_at",
        "updated_at",
    },
    "relationship": {
        "relationship_id",
        "source_entity_id",
        "source_entity_type",
        "target_entity_id",
        "target_entity_type",
        "relationship_type",
        "is_named",
        "status",
        "evidence_ids",
        "cfl_status",
        "confidence",
        "model_version_id",
        "created_at",
        "updated_at",
    },
    "person": {
        "person_id",
        "full_name",
        "role_title",
        "affiliation_company_id",
        "created_at",
        "updated_at",
    },
    "event": {
        # K05 entity
        "event_id",
        "revision_of_event_id",
        "revision_seq",
        "lifecycle_status",
        "event_taxonomy_code",
        "materiality_score",
        # EVENT_CONTRACT common
        "project_id",
        "entity_id",
        "source_id",
        "pipeline_status",
        "version",
        "correlation_id",
        "causation_id",
        "confidence",
        "evidence_ids",
        "cfl_status",
        # Observed-Time + bitemporal + audit
        "occurred_at",
        "published_at",
        "retrieved_at",
        "market_known_at",
        "available_at",
        "event_trading_date",
        "time_basis",
        "time_precision",
        "time_confidence",
        "valid_from",
        "valid_to",
        "model_version_id",
        "created_at",
        "updated_at",
    },
    "evidence": {
        "evidence_id",
        "source_id",
        "entity_ref",
        "entity_ref_type",
        "event_ref",
        "evidence_type",
        "evidence_stage",
        "source_credibility_tier",
        "authority",
        "directness",
        "time",
        "specificity",
        "independence",
        "content_hash",
        "snapshot_ref",
        "cfl_status",
        "confidence",  # ADR-0013 §0 (B1 gap fix: Work-2 §2.1 "all entities")
        "model_version_id",  # ADR-0013 §0
        "occurred_at",
        "published_at",
        "retrieved_at",
        "market_known_at",
        "available_at",
        "event_trading_date",
        "time_basis",
        "time_precision",
        "time_confidence",
        "created_at",
        "updated_at",
    },
    "market_data": {
        "market_data_id",
        "company_id",
        "trade_date",
        "close_price",
        "volume",
        "shares_outstanding",
        "retrieved_at",
        "available_at",
        "valid_from",
        "valid_to",
        "created_at",
        "updated_at",
    },
    "institutional_trading": {
        "institutional_trading_id",
        "company_id",
        "trade_date",
        "investor_type",
        "net_buy_sell",
        "retrieved_at",
        "available_at",
        "created_at",
        "updated_at",
    },
    "shareholding": {
        "shareholding_id",
        "company_id",
        "as_of_date",
        "bucket",
        "holders",
        "shares",
        "pct",
        "retrieved_at",
        "available_at",
        "created_at",
        "updated_at",
    },
    "model_version": {
        "model_version_id",
        "model_kind",
        "version_label",
        "params_json",
        "formula_ref",
        "valid_from",
        "supersedes_id",
        "status",
        "created_at",
        "created_by",
    },
    # --- WBS-B2 (ADR-0008) ---
    "data_source": {
        "source_code",
        "name",
        "source_tier",
        "is_enabled",
        "earliest_reliable_date",
        "auth_method",
        "license_note",
        "created_at",
    },
    "source": {
        "source_id",
        "data_source_code",
        "url",
        "title",
        "publisher",
        "source_ref",
        "published_at",
        "retrieved_at",
        "parser_version",
        "source_version",
        "created_at",
        "updated_at",
    },
    "source_snapshot": {
        "source_snapshot_id",
        "source_id",
        "content_hash",
        "snapshot_ref",
        "content_type",
        "byte_size",
        "parser_version",
        "source_version",
        "retrieved_at",
        "created_at",
    },
    # --- WBS-B5b (ADR-0003 G-1, ADR-0014) ---
    "seco_score": {
        "seco_score_id",
        "company_id",
        "as_of",
        "score",
        "tech_relevance",
        "product_readiness",
        "customer_validation",
        "ecosystem_position",
        "commercialization",
        "strategic_defensibility",
        "confidence",
        "valid_from",
        "valid_to",
        "model_version_id",
        "created_at",
        "updated_at",
    },
    "cmi_score": {
        "cmi_score_id",
        "company_id",
        "as_of",
        "score",
        "foreign_inst_momentum",
        "domestic_inst_momentum",
        "margin_short",
        "ownership_concentration",
        "trading_structure",
        "valid_from",
        "valid_to",
        "model_version_id",
        "created_at",
        "updated_at",
    },
    # --- WBS-B5d (ADR-0003 G-1, ADR-0016) ---
    "valuation_event_window": {
        "valuation_event_window_id",
        "event_id",
        "window_pre",
        "window_post",
        "benchmark_model",
        "ar_series",
        "car",
        "market_cap",
        "model_version_id",
        "created_at",
        "updated_at",
    },
    # --- WBS-B8 (ADR-0020 — G03 audit log, not part of Work-2's frozen
    # contract; same gap-filling posture as source_snapshot) ---
    "audit_log": {
        "audit_log_id",
        "agent_id",
        "rule_ref",
        "table_name",
        "row_id",
        "decision",
        "evidence_ids",
        "confidence",
        "model_version_id",
        "correlation_id",
        "created_at",
    },
    # --- WBS-B11 (ADR-0023 — research_report, ADR-0003 G-1) ---
    "research_report": {
        "research_report_id",
        "report_type",
        "subject_ref",
        "subject_ref_type",
        "version",
        "publication_tier",
        "cfl_status",
        "confidence",
        "model_version_id",
        "content_ref",
        "created_at",
        "updated_at",
    },
}

EXPECTED_TABLES = set(CONTRACT_COLUMNS) | {"company_taxonomy"}


def test_metadata_table_set() -> None:
    assert set(Base.metadata.tables) == EXPECTED_TABLES


@pytest.mark.parametrize("table", sorted(CONTRACT_COLUMNS))
def test_contract_columns_present(table: str) -> None:
    actual = set(Base.metadata.tables[table].columns.keys())
    missing = CONTRACT_COLUMNS[table] - actual
    assert not missing, f"{table} missing contract columns: {sorted(missing)}"


def test_company_taxonomy_refs_relationship() -> None:
    assert "taxonomy_refs" in m.Company.__mapper__.relationships


OBSERVED_TIME_NULLABLE = (
    "occurred_at",
    "published_at",
    "market_known_at",
    "event_trading_date",
    "time_basis",
    "time_precision",
    "time_confidence",
)


@pytest.mark.parametrize("model", [Event, Evidence, MarketData, InstitutionalTrading, Shareholding])
def test_observed_time_missing_stays_null(model: type) -> None:
    cols = model.__table__.columns
    for name in OBSERVED_TIME_NULLABLE:
        if name not in cols:
            continue
        col = cols[name]
        assert col.nullable is True, f"{model.__tablename__}.{name} must be NULL-able"
        assert col.server_default is None, f"{model.__tablename__}.{name} must not guess a default"
    # retrieved_at is Required (Charter §14.4)
    assert cols["retrieved_at"].nullable is False


def test_shareholding_available_at_required() -> None:
    # CF-26 / GP-08/09 — low-frequency data must carry availability time
    assert Shareholding.__table__.columns["available_at"].nullable is False
