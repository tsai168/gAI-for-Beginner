# ADR-0009 — WBS-B3a：P01 擷取器框架 + P02 hash 去重

- 狀態：**ACCEPTED（B3a 實作決議）**
- 日期：2026-09-11
- 核可：Research Director／Executive User（隨 B3a PR 審閱）
- 來源：Work-3 WBS-B3、Work-1 §3.2（P01/P02）、Charter §19（Deterministic First）、`ADR-0006` G4-11（P02 = hash only）、`ADR-0008`（source/source_snapshot）
- 影響：`src/ingestion/fetch.py`、`src/ingestion/dedup.py`、`src/knowledge/db/session.py`、`tests/integration/`、`.github/workflows/ci.yml`（+integration job）。無新資料表、無 migration。

---

## 1. 範圍（B3a，B3 五模組拆分之前半）

- **P01**：擷取器框架 —— `SourceAdapter` 協定、`FetchResult`、`AdapterRegistry`、`fetch_and_register()` 編排（P01→P02→P03）。
- **P02**：hash 去重 —— `DedupVerdict`、`classify()`、`is_duplicate()`。
- **不在 B3a**：P04 時間標準化、P05 可信度評分、P06 交易日對齊（→ B3b）。

## 2. 具體來源 adapter 一律 Deferred

TWSE／TPEx／MOPS／TDCC 等 concrete adapter **不在 B3a 實作**，因端點／認證／earliest date 皆待 `docs/audit/DATA_AVAILABILITY_AUDIT.md` 回填（CF-25、ADR-0006 G4-10）。

B3a 提供：
- `FixtureAdapter`（測試／本機：回傳給定 bytes，無 I/O）。
- `HttpAdapter`（可重用 GET base：base_url + User-Agent + `min_interval_s` 節流；`fetch()` 未實作，`NotImplementedError`）。

concrete adapter 於審計完成後逐一新增，各自 PR。

## 3. P02 去重語意

- **僅 hash**（sha256 hex，`ingestion.snapshot.content_hash`）。語意相似度 → K04／實體解析，不在 P02（ADR-0006 G4-11）。
- `DedupVerdict`：`NEW` / `DUPLICATE_SAME_SOURCE` / `DUPLICATE_OTHER_SOURCE`。
- 用途：讓 W04 管線在 `verdict != NEW` 時略過 LLM（Charter §19）。
- 跨來源相同 bytes（鏡像轉載）判為 `DUPLICATE_OTHER_SOURCE`——保留該筆 `source` 與其 `source_snapshot`（稽核），但可標記不再進 Batch AI。

## 4. `fetch_and_register()` 流程

`adapter.fetch(params)` → `classify()`（P02）→ 建 `source` 列 → `record_snapshot()`（P03，idempotent on `source_id + content_hash`）→ 回傳 `Registered(source, snapshot, verdict)`。

每次擷取都落一筆 `source`（稽核完整）；`source_snapshot` 由 P03 去重。

## 5. Session 工廠（`knowledge/db/session.py`）

`get_engine()`／`session_scope()`，URL 僅取自 `DATABASE_URL`（CLAUDE.md §9），lazy（import 不需 DB）。

## 6. 測試策略

- **單元**（`pytest -m "not integration and not migration"`）：adapter 契約、registry、`DedupVerdict` 值 —— 純 Python，CI `check` job。
- **整合**（`pytest -m integration`）：**新增 CI `integration` job**（Postgres service + `alembic upgrade head`）。涵蓋 D01–D08 seed、`fetch_and_register` idempotency/verdict、`source_snapshot` append-only trigger、G01 `cfl_status` 直寫 guard、`DefaultCflService.set_status` 經 guard 寫入成功。
- `db_session` fixture：外層交易 + `join_transaction_mode="create_savepoint"`，每測試結束 rollback。無 `DATABASE_URL` 時整合測試自動 skip。

## 7. 待確認 / 後續

1. concrete adapter（每個 `D0x`）—— 待 `DATA_AVAILABILITY_AUDIT` 回填後逐一 PR。
2. 擷取排程／重試／逾時 —— W01／W05（B7），不在 B3a。
3. `snapshot_ref` 物件儲存寫入（I02）—— ADR-0006 G4-10 未定，B3a 只落 DB metadata。
4. B3b：P04／P05／P06。
