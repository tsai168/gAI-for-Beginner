# ADR-0008 — WBS-B2 schema：Source Registry (D01–D08) + P03 snapshot

- 狀態：**ACCEPTED（B2 實作決議）**
- 日期：2026-09-11
- 核可：Research Director／Executive User（隨 B2 PR 審閱）
- 來源：Work-3 WBS-B2、Work-2 §2.7（K06 `source_id`）、Charter CF-08／GP-15、`ADR-0003`（§2.9 `source`/`source_snapshot` 未細化）、`ADR-0007`（型別基準）
- 影響：`src/knowledge/db/models.py`（+3 表）、`src/ingestion/snapshot.py`、`infra/db/migrations/versions/0002_source_registry.py`。不改既有欄位語意；`event`/`evidence.source_id` 由 plain UUID 變為 FK（新增約束，非改語意）。

---

## 1. 範圍

`data_source`（D01–D08 目錄）＋ `source`（單筆擷取來源）＋ `source_snapshot`（P03 不可變內容快照）＋ 跨模組 FK `event.source_id` / `evidence.source_id → source`。

## 2. `data_source` — 固定目錄

| 欄位 | 型別 | 說明 |
|---|---|---|
| `source_code` | text **PK** | `D01`…`D08`（Work-1 §3.1） |
| `name` | text | 中文名稱 |
| `source_tier` | enum(S1–S5) null | D01=S1、D02=S2、D03=S3、D04=S4；D05/D06/D07 null |
| `is_enabled` | bool | **D08 = false**（Work-1 TQ-05、CLAUDE.md §9）；其餘 true |
| `earliest_reliable_date` | date null | CF-25 — **一律 NULL**，待 `docs/audit/DATA_AVAILABILITY_AUDIT.md` 確認後以新 migration `UPDATE` 回填 |
| `auth_method` | text null | 待確認（同上） |
| `license_note` | text null | 待確認 |
| `created_at` | timestamptz | |

以 migration 0002 seed 8 列。目錄不由程式新增／刪除列（固定枚舉）。

## 3. `source` — 單筆擷取來源

uuid PK `source_id`；`data_source_code` FK→`data_source`（RESTRICT）；`url`／`title`／`publisher`／`source_ref`（外部 accession id）／`published_at`（null）／`retrieved_at`（NOT NULL）／`parser_version`／`source_version`（P03）＋ AuditMixin。可被更正（parser_version 等），故**可變**。

## 4. `source_snapshot` — P03 不可變快照

uuid PK；`source_id` FK→`source`（RESTRICT）；`content_hash`（sha256 hex，NOT NULL）；`snapshot_ref`（I02 物件鍵，null）；`content_type`／`byte_size`／`parser_version`／`source_version`／`retrieved_at`（NOT NULL）／`created_at`。

- **Unique `(source_id, content_hash)`** — 同來源同內容重擷取為 idempotent；亦供 P02 去重。
- **Append-only**：migration 0002 之 `cpoai_append_only()` trigger 對 `UPDATE`／`DELETE` `RAISE EXCEPTION`（CF-08、GP-15）。修正走「新增一列」。
- `APPEND_ONLY_TABLES = ("source_snapshot",)`（models.py 常數，供 B12 稽核）。

## 5. 跨模組 FK（`event`／`evidence.source_id → source`）

B1 時 `source` 尚未存在，故 B1 之 `event`/`evidence.source_id` 為 plain UUID。

- ORM：改為 `ForeignKey("source.source_id", ondelete="SET NULL", use_alter=True)` — `use_alter` 使 `create_all` 不在建表時 inline 此 FK。
- migration 0002：`op.create_foreign_key("fk_event_source_id_source", ...)`、`fk_evidence_source_id_source`（兩端此時皆存在）。
- `DEFERRED_FKS` 常數記錄於 models.py。

## 6. Migration 分批策略（延續 ADR-0007）

每個 migration 以**明確表清單** `create_all(tables=[...])`，不 blanket `create_all`（`Base.metadata` 永遠是全量）。
- 0001：`_B1_TABLES`（12 表）
- 0002：`_B2_TABLES`（`data_source`、`source`、`source_snapshot`）＋ 2 個 deferred FK ＋ append-only trigger ＋ seed

## 7. P03 API（`src/ingestion/snapshot.py`）

- `content_hash(raw: bytes) -> str` — sha256 hex（確定性，L0）。
- `record_snapshot(session, *, source_id, raw, retrieved_at, content_type?, parser_version?, source_version?, snapshot_ref?) -> SourceSnapshot` — 已存在同 `(source_id, content_hash)` 則回傳既有列，否則插入。
- 實際物件儲存寫入（I02，`snapshot_ref`）留待 B2 後續或 B3 串接；本 helper 只落 DB metadata。

## 8. 驗收（Work-3 §4 / WBS-B2 驗收關卡）

- **「任一來源可回溯至 `content_hash` 與 `snapshot_ref`」**：`source_snapshot` schema + `record_snapshot` idempotency（`tests/test_source_registry.py`）。
- append-only trigger、D01–D08 seed、FK enforcement：CI `migration` job（`alembic upgrade head` 後）。
- TEST-EVID-01（Work-3 §4）之 `content_hash` 可追溯：evidence.content_hash + source_snapshot.content_hash 雙軌，B3 串接。

## 9. 待確認

1. `docs/audit/DATA_AVAILABILITY_AUDIT.md` 各列回填後，以新 migration `UPDATE data_source SET earliest_reliable_date/auth_method/license_note`。
2. `available_at` 對映規則（D05/D06）→ 另立 ADR，B3 P04 依據。
3. `snapshot_ref` 物件儲存實作（I02 產品未定，ADR-0006 G4-10）。
