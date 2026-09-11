# ADR-0007 — WBS-B1 schema：型別、佈局與 G01 介面樁

- 狀態：**ACCEPTED（B1 實作決議）**
- 日期：2026-09-11
- 核可：Research Director／Executive User（隨 B1 PR 審閱）
- 來源：`ADR-0002`（命名）、`ADR-0003`（§2.9 待確認 #1–#5）、`ADR-0004`（G01 樁）、`ADR-0005`（K04 多型參照、migration 路徑）
- 影響：`src/knowledge/db/`、`src/governance/cfl.py`、`infra/db/migrations/versions/0001_initial_schema.py`。不改 `/docs` 契約欄位語意。

---

## 1. B1 範圍（Work-3 §2 / ADR-0003）

建置：K01–K06（`company`／`technology`／`product`／`relationship`／`event`／`evidence`）＋ §2.9 原始資料 4 表（`person`／`market_data`／`institutional_trading`／`shareholding`）＋ `model_version`（G04）＋ G01 介面樁。
**不在 B1**：`seco_score`／`cmi_score`／`valuation_event_window`／`research_report`（B5）；`source`／`source_snapshot`（B2）。

## 2. 型別決議（解 ADR-0003 待確認 #1、#2）

| 類別 | 決議 |
|---|---|
| 主鍵 | `uuid`，欄名 `<entity>_id`，`server_default=gen_random_uuid()`（pgcrypto/PG16 內建） |
| 時間戳 | `timestamptz`；日期 `date` |
| 金額／價格 | `numeric(20,4)` |
| 股數／量 | `numeric(20,0)` |
| 分數 0–100（materiality 等） | `numeric(6,3)` |
| 分數 0–1（confidence、CF-10 五判準、time_confidence） | `numeric(5,4)` |
| 百分比（持股 pct） | `numeric(9,6)` |
| enum | **非原生**：`sa.Enum(PyEnum, native_enum=False)` → `varchar` + `CHECK`。理由：Charter 凍結之列舉雖穩定，但 CHECK 較易隨 Change Request 演進；避免 `ALTER TYPE` 遷移痛點 |
| JSON | `jsonb`（`model_version.params_json`） |
| ID 清單（`evidence_ids`） | `ARRAY(uuid)`（保留契約欄名；FK 完整性由應用層保證，B12 加稽核） |

nullability：Work-2「Required」欄位 `NOT NULL`；Observed-Time 階層除 `retrieved_at`（Required）外一律 `NULL`（CF-21／GP-07）；`shareholding.available_at` `NOT NULL`（ADR-0003 G-3）。

## 3. 佈局

- 所有 ORM 模型置於 `src/knowledge/db/`（`base.py` 共用 Base／mixin／enum；`models.py` 全實體）。B2 起其他層 `from knowledge.db.models import ...`。
- `src/governance/cfl.py`：G01 介面樁。

## 4. Mixin 適用範圍（Work-2 §2.1「共用」之工程落地）

| Mixin | 欄位 | 套用於 |
|---|---|---|
| `AuditMixin` | `created_at`、`updated_at` | 全部表 |
| `GovernedMixin` | `cfl_status`（default `PENDING`）、`confidence`、`model_version_id` | `company`、`relationship`、`event`、`evidence` |
| `BitemporalMixin` | `valid_from`、`valid_to` | `technology`、`event`、`market_data`（PIT 股本） |
| `ObservedTimeMixin` | `occurred_at`、`published_at`、`retrieved_at`、`market_known_at`、`available_at`、`event_trading_date`、`time_basis`、`time_precision`、`time_confidence` | `event`、`evidence`、`market_data`、`institutional_trading`、`shareholding` |

**待確認（human）**：`company`／`technology`／`product`／`person` 為主資料，未套 `ObservedTimeMixin`（無事件研究時間語意）。若 RD 要求嚴格「所有實體皆含」，回報後再加。

## 5. 個別決議

- **`event` 表 = K05 + EVENT_CONTRACT 合一**：同時帶 K05 實體欄位（`revision_of_event_id`、`revision_seq`、`lifecycle_status`、`event_taxonomy_code`、`materiality_score`）與 EVENT_CONTRACT 共用欄位（`project_id` default `'cpo-ai'`、`entity_id`、`source_id`、`pipeline_status`、`version`、`correlation_id`、`causation_id`、`evidence_ids`）。
- **K04 多型參照**（ADR-0005 G4-2）：`source_entity_id`/`source_entity_type`、`target_entity_id`/`target_entity_type`，`*_entity_type ∈ {company, person}`（CHECK）。
- **`evidence` 之 `time` 欄位**（Work-2 §2.7 CF-10 五判準之一，與 SQL 型別名衝突）：DB 欄名維持 `time`（合法識別字），Python 屬性 `time_`（`Column("time", ...)`）。**待確認**：是否改名 `time_score`（會動契約欄名，需 RD 決）。
- **`evidence.entity_ref` / `event_ref`**：`entity_ref`(uuid)+`entity_ref_type`(enum)；`event_ref`(uuid, FK→event)。
- **`taxonomy_refs`（K01）**：以關聯表 `company_taxonomy`（`company_id`,`technology_id`）實作，ORM 以 `Company.taxonomy_refs` relationship 暴露。契約欄名 `taxonomy_refs` 保留為 ORM 屬性。**待確認**：可接受關聯表實作否。
- **`source_id`（event/evidence）**：B1 為 `uuid` 可空、**尚無 FK**；B2 建 `source` 表後補 FK migration。

## 6. G01 介面樁（ADR-0004 決策 2）

`src/governance/cfl.py`：
- `CflStatus`、`CflId`（`CFL-01`…`CFL-08`）、`CFL_TRANSITIONS`（合法轉換表）。
- `CflService` Protocol：`submit_candidate(session, table, row_id, cfl_id, payload) -> None`、`query_status(session, table, row_id) -> CflStatus`。
- `DefaultCflService`：insert 時 `cfl_status=PENDING`；**無 auto-pass**；寫 `cfl_status` 前呼叫 `with cfl_write(session):` 設 `SET LOCAL cpoai.cfl_engine = 'on'`。
- **DB guard**（migration 0001）：對帶 `cfl_status` 之表加 trigger，`UPDATE` 若 `current_setting('cpoai.cfl_engine', true) <> 'on'` 且 `cfl_status` 有變更 → `RAISE EXCEPTION`。滿足 CLAUDE.md §4「不得繞過 G01」與 TEST-CFL-03。
- B8 以完整規則引擎替換 `DefaultCflService`，trigger 與呼叫端不動。

## 7. 回填 ADR-0003 待確認

| # | 原待確認 | 本 ADR 決議 |
|---|---|---|
| 1 | 逐欄型別／nullability／PK | §2（uuid PK、numeric 精度表、timestamptz） |
| 2 | enum 實作 | 非原生（varchar + CHECK） |
| 3 | 資料集 earliest reliable date | 仍為 B2 前置 `DATA_AVAILABILITY_AUDIT.md`（不變） |
| 4 | `research_report.content_ref` | B11（不變） |
| 5 | K04 多型參照 | 單欄 + `*_entity_type`（§5） |

## 8. 驗收（Work-3 §4）

- **TEST-DATA-01**：`tests/test_schema_contract.py` 以逐表欄名清單（轉錄自 Work-2 V1.4 §2.2–2.7／§2.9）比對 ORM 模型欄位，契約欄位須全數存在且無同義異名。
- **TEST-DATA-02**：Observed-Time 欄位（除 `retrieved_at`）皆 `nullable=True`，無 server_default 猜測值。
- Migration round-trip：`alembic upgrade head → downgrade base → upgrade head`（CI `migration` job）。
