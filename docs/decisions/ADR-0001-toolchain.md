# ADR-0001 — 語言與工具鏈選型（CLAUDE.md §5／§7 補充）

- 狀態：**ACCEPTED**
- 日期：2026-09-10
- 核可：Research Director／Executive User（本專案人工授權）
- 影響檔案：`CLAUDE.md` §5／§7（→ V1.1）、`docs/WORK3_IMPLEMENTATION_BLUEPRINT_V1.md` §5.3／§6（→ V1.1）
- 依據：CLAUDE.md §5／§7 之「待補充」欄位、CLAUDE.md §11（工具鏈細節可自行決策、不涉及契約內容變更）、Work-3 §5、Charter §7（Out of Scope：Charter 不固定語言／框架／repo 細節）、Charter §31。

## 1. 決策範圍與治理定性

CLAUDE.md §5／§7 標示「待團隊於 Claude Code-1 開工時補充」之項目，於此定案。

**此補充不構成 Charter §31 Change Request**：未觸及 Charter 凍結面（Universe／Taxonomy／Evidence Stage／Source Tier／Relationship／Seco／CMI／Event Timing／Event Window／Confidence／CFL／Publication Policy／Agent Autonomy），亦未變更 Work-2 任何契約欄位或狀態機。

依 CLAUDE.md 檔尾條款「任何修改須…同步更新 Work-3」，本 ADR 同步更新 Work-3 §5.3／§6，並將 CLAUDE.md 與 Work-3 標記為 **V1.1**（Charter §31 所稱「小幅且不改變研究契約的調整」；不開新 Charter 版本、不升 V2.0）。

## 2. 既有凍結約束（不在本 ADR 變動）

| 項目 | 來源 | 決定 |
|---|---|---|
| I04 工作流程引擎 | Work-3 §5.1 | Temporal（自架或 Temporal Cloud） |
| I05 向量／語意儲存 | Work-3 §5.2 | pgvector（PostgreSQL 擴充） |

## 3. 決策

### 3.1 已確認（core，變更需經核可）

| 項目 | 選型 | 理由 |
|---|---|---|
| 語言 | **Python 3.12** | Temporal 有官方 Python SDK；事件研究統計（AR/CAR、Market Model 迴歸、Phase 2 γ 迴歸）與 LLM SDK 生態最完整 |
| 關聯式資料庫 | **PostgreSQL 16** + `pgvector` | Work-3 §5.2；I01 與 I05 共用同一實例 |
| Migration | **Alembic** | 可 upgrade/downgrade、可回溯（CLAUDE.md §3；不得改寫／刪除既有 migration） |
| 工作流程 SDK | **`temporalio`（Python）**；本機以 `temporal server start-dev` 或 docker-compose | Work-3 §5.1；W03 Fan-out/Fan-in、W05 重試/逾時、W06 Batch Parsing |
| API 框架（B9／U05） | **FastAPI + Pydantic v2** | Work-2 §4 已指定 OpenAPI；Pydantic schema 直接對映 DATA_MODEL／EVENT_CONTRACT 欄位名（CLAUDE.md §6 禁別名） |
| 科學計算（M06／M07／M08） | `numpy`、`pandas`、`statsmodels`、`scipy` | Market-adjusted／Market Model、CAR、Robustness Check |
| LLM 供應商 | **Claude（Anthropic）**，官方 `anthropic` Python SDK | 補 Work-3 §3.2 G-7、§4 env vars 之缺口；model 名稱、token budget、wake-up 參數一律以**設定值／環境變數**注入，Deferred Items 不寫死（CLAUDE.md §4、Charter §29） |
| 型別檢查 | **Mypy**（`src/` strict） | Reproducibility／可維護性 |

### 3.2 低風險預設（team 可替換，不影響契約、不需重開 ADR）

| 項目 | 預設 | 可替換為 |
|---|---|---|
| 套件／依賴管理 | **uv** + `pyproject.toml` | Poetry |
| Lint／格式化 | **Ruff**（lint + format） | Black + isort（+ flake8） |

### 3.3 暫定（B10 前再議，不阻擋 B1）

| 項目 | 暫定 | 備註 |
|---|---|---|
| UI 技術堆疊（B10／U01–U04） | React + TypeScript + Vite | B10 距今尚遠；正式決定另立 ADR |

## 4. 測試指令（CLAUDE.md §7）

對齊 CLAUDE.md §7 順序「單元 → 整合 → migration → lint／型別」，全綠才可 commit：

```bash
# 1) 單元
pytest -m "not integration and not migration"
# 2) 整合（需 Postgres + Temporal dev；docker-compose up -d）
pytest -m integration
# 3) migration（round-trip）
pytest -m migration
alembic upgrade head && alembic downgrade base && alembic upgrade head
# 4) lint / 型別
ruff check . && ruff format --check . && mypy src
```

一鍵彙總：`make check`（或 `nox -s check`）依上述順序執行。

完整驗收標準見 `docs/WORK3_IMPLEMENTATION_BLUEPRINT_V1.md` §4（TEST-DATA-01 起）。

## 5. 仍為待確認（不由本 ADR 決定）

- LLM **model id** 與 token/cost 上限：屬 Charter §29 Deferred（Operations Specification）；本 ADR 只固定「供應商＝Claude、以設定值注入」。
- 部署拓撲、CI 平台、容器編排（I06）：留待部署階段 ADR。
- 盤點報告 `docs/audit/CPO_AI_ReadOnly_Audit_Report.md` §6 其餘 37 項，仍需在授權 WBS-B1 前逐項回覆。

## 6. 後果

- CLAUDE.md §5／§7 由本 ADR 之 §3、§4 內容取代「待補充」字樣。
- Work-3 §5 新增 §5.3 指向本 ADR；§6 摘要補一列。
- 兩檔標記 V1.1。此為 B0 收尾動作，仍早於 WBS-B1。
