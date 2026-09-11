# ADR-0003 — DATA_MODEL 契約缺口補齊（盤點報告 §3.2 / §6 Group 2：G-1～G-6）

- 狀態：**ACCEPTED（結構）／逐欄型別待 B1 訂定**
- 日期：2026-09-10
- 核可：Research Director／Executive User（本專案人工授權）
- 來源：`docs/audit/CPO_AI_ReadOnly_Audit_Report.md` §3.2、§6
- 影響檔案：`docs/WORK2_CONTRACT_FREEZE_V1.md` → V1.2（新增 §2.9、§2.1 `available_at`、§2.6 `revision_seq`）；`CLAUDE.md` §4 → V1.3；`docs/WORK3_IMPLEMENTATION_BLUEPRINT_V1.md` 註記
- 治理定性：**新增**契約實體與欄位（不改既有欄位語意或 enum），依 Work-2 §2.8／Charter §31 屬需 Change Request 之調整；由本 ADR 兼任 CR 記錄，經 RD／EU 核可後 Work-2 升 V1.2。未觸及 Charter 凍結面之研究邏輯。

---

## G-1 — 7 個 Core Research Object 無 schema

Charter §9 列 16 物件，Work-2 §2.2–2.7 僅 K01–K06。補齊如下（K01–K06 編號與 Work-1 §3.3 不變；新表不佔用 K 編號，統一收於 Work-2 §2.9）。

### 原始資料實體（B1／B2／B3）

| 表 | 主鍵 | 關鍵欄位（型別待確認） | 來源／依據 |
|---|---|---|---|
| `market_data` | `market_data_id` | `company_id`(FK)、`trade_date`、`close_price`、`volume`、**`shares_outstanding`**（PIT）、通用時間／稽核欄位 | D05；CF-24 |
| `institutional_trading` | `institutional_trading_id` | `company_id`(FK)、`trade_date`、`investor_type`、`net_buy_sell`、`available_at`、通用欄位 | D05 |
| `shareholding` | `shareholding_id` | `company_id`(FK)、`as_of_date`、`bucket`、`holders`、`shares`、`pct`、**`available_at`**（必填）、通用欄位 | D06 TDCC；CF-26；GP-08/09 |
| `person` | `person_id` | `full_name`、`role_title`、`affiliation_company_id`(FK, nullable)、通用欄位 | Charter §9；CF-06 |

### 模型輸出／報告實體（B5／B11；皆 Bitemporal、隨 `model_version_id`）

| 表 | 主鍵 | 關鍵欄位（型別待確認） | 模組／依據 |
|---|---|---|---|
| `seco_score` | `seco_score_id` | `company_id`(FK)、`as_of`、`score`(0–100)、`tech_relevance`、`product_readiness`、`customer_validation`、`ecosystem_position`、`commercialization`、`strategic_defensibility`、`confidence`、`valid_from/valid_to`、`model_version_id` | M03；CF-12～17 |
| `cmi_score` | `cmi_score_id` | `company_id`(FK)、`as_of`、`score`、`foreign_inst_momentum`、`domestic_inst_momentum`、`margin_short`、`ownership_concentration`、`trading_structure`、`valid_from/valid_to`、`model_version_id` | M04；CF-18/19；GP-08 |
| `valuation_event_window` | `valuation_event_window_id` | `event_id`(FK)、`window`（`[-N,+M]`）、`benchmark_model`、`ar`、`car`、`market_cap`、`model_version_id` | M06；CF-20/23/24 |
| `research_report` | `research_report_id` | `report_type`、`subject_ref`、`version`、`publication_tier`、`cfl_status`、`content_ref`、`model_version_id`、通用稽核欄位 | R02；CF-33；Charter §18 |

構面欄位命名依 ADR-0002（具名，不用 `S1..S6` / `CF1..CF5`）。

## G-2 — `shares_outstanding`（CF-24 / TEST-PIT-01）

放入 `market_data`，Point-in-Time（隨 `valid_from/valid_to`）。M07 市值＝`close_price × shares_outstanding`（對應時點值，不得以今日股本回算）。

## G-3 — `available_at`（CF-26 / GP-09 / TEST-CMI-01）

於 Work-2 §2.1 通用時間欄位**新增 `available_at`**＝「資料在市場／公開實際可取得之時間」。

- 低頻資料（`shareholding` TDCC、部分 `institutional_trading`）**必填**。
- M04 CMI 僅能使用 `available_at ≤ 計算基準時點` 之資料（No-Future-Data）。
- 與 `market_known_at`（Optional，僅 Evidence 使用）為不同欄位、不同用途。
- 缺失時保持 `NULL`；低頻資料缺 `available_at` 即不得進入 CMI。

## G-4 — `person`

獨立 `person` 表（見 G-1）。K04 `relationship` 的 `source_entity_id` / `target_entity_id` 可指向 `company` 或 `person`（多型參照，型別待確認）。

## G-5 — `model_version`（G04 版本註冊表）

| 欄位 | 說明（型別待確認） |
|---|---|
| `model_version_id` | PK |
| `model_kind` | `seco` / `cmi` / `materiality` / `confidence` / `benchmark` / `taxonomy` / `cfl` |
| `version_label` | 人可讀版本標籤 |
| `params_json` | 權重／參數快照 |
| `formula_ref` | 公式定義引用 |
| `valid_from` | 生效時間 |
| `supersedes_id` | 前一版本（nullable，自參照） |
| `status` | `ACTIVE` / `SUPERSEDED` / `DRAFT` |
| `created_at` / `created_by` | 稽核 |

任一權重／公式變更 = 新增一列，不得覆寫既有列（GP-10）。B1 建表；B5 起各模型寫入時帶 `model_version_id`。

## G-6 — `revision_seq`

K05 新增 `revision_seq`（整數，同一 `event_id` 修正鏈內遞增，起始 1）。與 `revision_of_event_id`（自參照）併用：`revision_seq` 給人／查詢用的線性序，`revision_of_event_id` 給鏈結構。

---

## 待確認

| # | 項目 | 狀態 |
|---|---|---|
| 1 | 所有欄位之 SQL 型別／nullability／精度、PK 型別 | **RESOLVED** — `ADR-0007` §2（uuid PK `gen_random_uuid()`、`timestamptz`、numeric 精度表） |
| 2 | enum 實作方式 | **RESOLVED** — `ADR-0007` §2：非原生 `varchar + CHECK` |
| 3 | 各資料集 earliest reliable date（CF-25） | OPEN — B2 前置 `docs/audit/DATA_AVAILABILITY_AUDIT.md`（ADR-0005 G4-4） |
| 4 | `research_report.content_ref` 儲存位置 | OPEN — B11 前定 |
| 5 | K04 多型參照實作 | **RESOLVED** — `ADR-0007` §5：單欄 + `*_entity_type`（`{company, person}` CHECK） |

## 後續

- Group 3：CFL-04 之 M05／A04 分工（audit §3.3）、G01 建置時序 D-1、API 認證與 RBAC G-7。
