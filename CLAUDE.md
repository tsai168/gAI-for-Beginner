# CLAUDE.md — CPO AI 工程代理工作邊界與規則

> 本檔案定義 Claude Code 在本 repository 中的工作邊界。任何實作前，請先完整讀取本檔案與 `/docs` 目錄下所有規格文件。

## 0. 上游規格文件（權威來源，依優先順序）

1. `/docs/CHARTER_FREEZE_V1.md` — Project Charter Freeze V1.0（FROZEN，2026-09-05）：CF-01～CF-46、GP-01～GP-21 之唯一權威來源
2. `/docs/WORK1_TECH_SPEC_BASELINE_V1.md` — 十層模組架構（D/P/K/M/A/W/R/G/U/I）
3. `/docs/WORK2_CONTRACT_FREEZE_V1.md` — DATA_MODEL／EVENT_CONTRACT／CFL_CONTRACT／API_SPEC／AGENT_SPEC
4. `/docs/WORK3_IMPLEMENTATION_BLUEPRINT_V1.md` — Dependency DAG、WBS、Acceptance Tests、I04/I05 技術選型決議

**優先順序原則：下游文件不得與上游文件矛盾。若發現矛盾，停止實作並提出問題，不得自行選擇其中一份為準。**

## 1. 專案簡介

CPO AI 是台灣 CPO／矽光子產業情報、公司事件、生態系卡位與市值重估之 AI Agent 研究系統。核心研究物件為 Company／Technology／Product／Relationship／Event／Evidence（對應知識庫模組 K01–K06）。系統採十層模組架構，並以 CFL-01～08 人工核准與矛盾回饋規則、Agent Autonomy L0–L4 四權分離作為治理骨幹。

## 2. 目錄結構（建議）

```
/docs           規格文件（本檔案與上述規格文件皆存放於此，唯讀，非經 Change Request 不得修改）
/src
  /ingestion    P01–P06
  /knowledge    K01–K06
  /models       M01–M08
  /agents       A01–A08
  /workflows    W01–W06
  /reports      R01–R06
  /governance   G01–G08
  /api          U05／對外 API 層
  /ui           U01–U04
/infra          I01–I06（部署設定、docker-compose、CI）
  /db/migrations Alembic migration（`alembic.ini` 於 repo 根，script_location = infra/db/migrations）
/tests          單元／整合／E2E 測試
/docs/decisions ADR（工程決策記錄，ADR-0001 起）
```

> §2 路徑於 V1.4 補實（migration 目錄、ADR 目錄），依 `/docs/decisions/ADR-0005-batch-allocation.md`。

## 3. 允許執行的操作

- 依 `/docs` 規格實作對應模組之程式碼
- 撰寫並執行單元測試、整合測試、migration 測試
- 建立**可回溯**的資料庫 migration（新增 migration 檔案，不得改寫或刪除既有 migration）
- 在既有規格允許範圍內修正明顯的程式錯誤

## 4. 明確禁止的操作

- **不得修改** `/docs` 下任何已凍結之契約文件（DATA_MODEL、EVENT_CONTRACT、CFL_CONTRACT、API_SPEC、AGENT_SPEC），除非收到明確的 Change Request 核准記錄
- **不得刪除**既有 migration 檔案
- **不得跳過測試**直接 commit 或視為完成
- **不得繞過 G01** CFL 規則引擎直接寫入或修改任一實體之 `cfl_status`
- **不得違反四權分離（GP-21）**：任一 Agent／角色帳號不得同時具備 Evidence 寫入與 Approval／Publication 權限
- **不得在 CMI／Seco 等計算中使用未來資料**（No Future Data，GP-08／CF-26），即禁止 backward filling
- **不得覆寫既有 Model Version 的計算結果**（GP-10）；任何權重或公式變更須建立新版本
- **不得將 Deferred Items**（Wake-up Window、Batch 參數、Token Budget 等，見 Work-1 §8／Work-3 §1）**當作已凍結參數寫死**於程式碼中；應以設定值／掛勾點形式保留
- **不得**將時間欄位（occurred_at／published_at／market_known_at／available_at 等）在缺失時填入猜測值，一律保持 `NULL`（`available_at` 於低頻資料為必填，缺失即不得進入 M04 CMI，見 Work-2 §2.1／ADR-0003）

## 5. 程式語言、框架與技術選型

> 語言／框架／Lint 於 2026-09-10 定案，見 `/docs/decisions/ADR-0001-toolchain.md`（不構成 Charter §31 CR；CLAUDE.md 升 V1.1）。

- I04 工作流程引擎：Temporal（或 Temporal Cloud）— 依 Work-3 §5.1 決議
- I05 向量／語意儲存：pgvector（PostgreSQL 擴充）— 依 Work-3 §5.2 決議
- 語言：**Python 3.12**
- 關聯式資料庫：**PostgreSQL 16**；Migration：**Alembic**（新增檔，不得改寫／刪除既有）
- 工作流程 SDK：**`temporalio`（Python）**
- API 框架（B9／U05）：**FastAPI + Pydantic v2**（schema 對映 Work-2 DATA_MODEL／EVENT_CONTRACT 欄位名，不得另創別名）
- 科學計算（M06／M07／M08）：`numpy`、`pandas`、`statsmodels`、`scipy`
- LLM 供應商：**Claude（Anthropic）**，`anthropic` Python SDK；model id／token budget／wake-up 參數一律以環境變數／設定值注入（Deferred，不寫死）
- 型別檢查：**Mypy**（`src/` strict）
- 低風險預設（team 可替換，不影響契約）：依賴管理 **uv**（可換 Poetry）；Lint／格式化 **Ruff**（可換 Black + isort）
- UI 技術堆疊（B10／U01–U04）：**暫定** React + TypeScript + Vite，B10 前另立 ADR 再議

## 6. 資料契約與命名規則

- 所有欄位命名必須與 `/docs/WORK2_CONTRACT_FREEZE_V1.md` 之 DATA_MODEL／EVENT_CONTRACT 一致，不得另創別名
- 任一核心實體唯一鍵一律為 `<entity>_id`（如 `company_id`、`event_id`），禁止以 `name`／`code`／`display_name` 作為模組間關聯依據
- 事件欄位固定為：`event_id / project_id / entity_id / source_id / occurred_at / published_at / retrieved_at / pipeline_status / version / correlation_id / causation_id / confidence / evidence_ids / cfl_status / created_at`
  - `pipeline_status`（V1.2 由 `status` 更名）＝事件處理管線狀態（Work-2 §3.2）；K05 實體另有 `lifecycle_status`（`ACTIVE/CORRECTED/SUPERSEDED/WITHDRAWN/DISPUTED`，Work-2 §2.6，CF-36）——兩者為不同欄位，不得混用
  - Bitemporal 有效時間欄位全庫統一 `valid_from / valid_to`（Knowledge Time 用 `created_at`）
  - 命名慣例詳見 `/docs/decisions/ADR-0002-naming.md`（Seco 六構面、Confidence 五構面一律用具名欄位，不用 `S1..S6` / `CF1..CF5`；Source Tier 值維持 `S1..S5`；Frozen Decision 一律 `CF-01` 連字號）

## 7. 測試指令與驗收標準

- 每完成一個 WBS 批次（見 Work-3 §2、§3），須依序執行：單元測試 → 整合測試 → migration 測試 → lint／型別檢查，全數通過才可 commit
- 完整驗收標準見 `/docs/WORK3_IMPLEMENTATION_BLUEPRINT_V1.md` 第 4 節 Acceptance Tests（TEST-DATA-01 起）
- 測試指令（定案 2026-09-10，見 `/docs/decisions/ADR-0001-toolchain.md`）：
  - 單元：`pytest -m "not integration and not migration"`
  - 整合：`pytest -m integration`（需 Postgres + Temporal dev）
  - migration：`pytest -m migration` 並 `alembic upgrade head && alembic downgrade base && alembic upgrade head`
  - lint／型別：`ruff check . && ruff format --check . && mypy src`
  - 一鍵：`make check`（依上述順序，全綠才可 commit）

## 8. 分批施工規則

- **一次只能實作 1～3 個高度相關模組**，完成並通過測試後才可提交、再進入下一批
- 施工順序固定為：Shared Contracts → 資料庫 → Source Registry → Ingestion → 知識庫 → 分析引擎 → Agent → 工作流程引擎 → API → UI → Reporting → Governance → Tests（詳見 Work-3 §2 Dependency DAG）
- 不得從 Dashboard（U01）或其他吸睛模組開始施工，也不得同時展開多個不相依批次

## 9. 安全與權限邊界

- 所有 API 金鑰、資料庫連線字串等機密資訊一律透過環境變數注入，不得寫入程式碼或提交至版本控制
- 不得對外發送個資或任何未經 CFL-08 核准之研究結論（R06 正式外部發布）
- D08（授權付費來源）在 V1 維持停用狀態，不得自行啟用（Work-1 TQ-05）

## 10. 何時必須停下來詢問人類

- 任何規格文件之間出現矛盾或缺口
- 任何 CFL-04／05／06／07／08 判定為 `REVIEW-REQUIRED` 或 `BLOCKED` 之情形
- 任何涉及新增或變更 Frozen Decision（CF-01～46、GP-01～21）之情形
- 任何環境變數、外部 API 金鑰、資料庫 migration 需求不明確之情形
- 任何 Deferred Items（見第 4 節）被要求提前決策之情形

## 11. 何時可以自行決策

- L0（Deterministic Automation）與 L1（AI Extraction，僅建立 Candidate）範圍內、不涉及 Approval／Publication 的操作
- 依既有規格撰寫測試、修正明確的程式錯誤、補齊本文件第 5、7 節標示「待補充」之工具鏈細節（不涉及契約內容變更）

---
*本檔案為 Work-3 Implementation Blueprint 之隨附文件，任何修改須依 Charter §31 Change Control 流程處理，並同步更新 Work-3 規格書。*

**版本沿革**（皆為 Charter §7／§31「小幅且不改變研究契約的調整」，非 Charter §31 CR；V1.0 → 見 git 歷史）
- **V1.1（2026-09-10）** — §5／§7 工具鏈與測試指令補充，依 `/docs/decisions/ADR-0001-toolchain.md`
- **V1.2（2026-09-10）** — §6 欄位消歧（`status`→`pipeline_status`＋`lifecycle_status`、`valid_from/valid_to` 統一、命名慣例），依 `/docs/decisions/ADR-0002-naming.md`；Work-2 同步升 V1.1
- **V1.3（2026-09-10）** — §4 新增 `available_at`（低頻資料必填、缺失不入 CMI），依 `/docs/decisions/ADR-0003-schema-gaps.md`；Work-2 同步升 V1.2（新增 §2.9 八張補充表、`available_at`、`revision_seq`）
- **V1.4（2026-09-10）** — §2 補實 migration／ADR 目錄路徑，依 `/docs/decisions/ADR-0005-batch-allocation.md`。相關：Work-2 → V1.4、Work-3 → V1.2（B0.5、I03/I05/I06/G04 批次歸屬）。ADR-0004（CFL-04 分工／G01 樁／傳輸／RBAC）與 ADR-0006（B7/B9 展開項確認）亦於同日核可。
