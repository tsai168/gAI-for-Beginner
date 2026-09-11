# CPO AI

台灣 CPO／矽光子產業情報、公司事件、生態系卡位與市值重估之 AI Agent 研究系統。

## 權威文件

實作前必讀 `CLAUDE.md` 與 `/docs`：

| 文件 | 內容 |
|---|---|
| `docs/CHARTER_FREEZE_V1.md` | Project Charter Freeze V1.0（FROZEN）— CF-01～46、GP-01～21 |
| `docs/WORK1_TECH_SPEC_BASELINE_V1.md` | 十層模組架構（D/P/K/M/A/W/R/G/U/I） |
| `docs/WORK2_CONTRACT_FREEZE_V1.md` | DATA_MODEL／EVENT_CONTRACT／CFL_CONTRACT／API_SPEC／AGENT_SPEC |
| `docs/WORK3_IMPLEMENTATION_BLUEPRINT_V1.md` | Dependency DAG／WBS／Acceptance Tests |
| `docs/decisions/ADR-*.md` | 工程決策記錄 |
| `docs/audit/` | 唯讀盤點報告與 §6 結案對照表 |

## 現況

**B0.5 — 基礎環境**（依 `docs/decisions/ADR-0005-batch-allocation.md`）。尚無 business code；WBS-B1 起才建 K01–K06 + §2.9 migration。

- 語言 Python 3.12｜PostgreSQL 16 + pgvector｜Temporal｜Alembic（`infra/db/migrations/`）
- 詳見 `docs/decisions/ADR-0001-toolchain.md`

## 開發

```bash
uv sync                 # 安裝依賴
cp .env.example .env     # 填入本機值（.env 不進版控）
make up                  # 啟動 Postgres 16 + Temporal dev（docker compose）
make check               # ruff + mypy + 單元測試（CLAUDE.md §7）
make migrate             # alembic upgrade head（B1 起有 migration）
make down
```

Temporal UI：<http://localhost:8233>

## 施工規則

一次一批（1–3 個高度相關模組），順序見 `docs/WORK3_IMPLEMENTATION_BLUEPRINT_V1.md` §2。B1 開工前尚需 `docs/audit/DATA_AVAILABILITY_AUDIT.md`（B2 前置）。
