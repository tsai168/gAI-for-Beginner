# ADR-0005 — 批次歸屬、審查路徑、K04 參照、TQ-03、資料可用性、migration 路徑（Group 4A）

- 狀態：**ACCEPTED**
- 日期：2026-09-10
- 核可：Research Director／Executive User
- 來源：`docs/audit/CPO_AI_ReadOnly_Audit_Report.md` §6 Group 4A（G4-1～G4-6）
- 影響檔案：`docs/WORK3_IMPLEMENTATION_BLUEPRINT_V1.md` §2（→ V1.2）；`CLAUDE.md` §2（→ V1.4）
- 治理定性：施工排程與模組職責細化，不改 Charter 凍結面、不改 Work-2 契約欄位（Charter §7／§31「小幅調整」）。

---

## G4-1 — Seco/CMI 大幅變動之審查路徑

不新增 CFL 編號（維持 Charter §17 之 CFL-01～08）。

- `seco_score` / `cmi_score` 寫入時，**G08 合規監控**依門檻（`Δscore`、跨等級邊界）產生 **Material Review 旗標**，進 U04 審查佇列，與 CFL 流程平行。
- 門檻值為 **Deferred**（設定值／掛勾點，Charter §29；不寫死）。
- 對應 Charter §18「Seco 大幅變動、重大 CMI Signal 需 Review」。

## G4-2 — K04 多型參照實作

`relationship.source_entity_id` / `target_entity_id` 採**單欄 + 辨別欄**：
`source_entity_type` / `target_entity_type` ∈ {`company`, `person`}。
不使用兩組 FK。解參照由知識庫查詢層封裝。B4 落地。

## G4-3 — TQ-03 Kappa 一致性稽核器

**不納入 V1。** 列為 Phase 2 選配 QA 模組。理由：Charter 無任何 CF／GP 要求雙人編碼一致性；MVP 目標為走通 Source→Report。B5 不含此模組，M-層不預留必建擴充點（可於 Phase 2 另立）。

## G4-4 — 資料集 earliest reliable date（CF-25）

**B2 開工第一步**產出 `docs/audit/DATA_AVAILABILITY_AUDIT.md`：逐一列 D01–D06 各資料集之實際最早可靠日期、已知缺漏區間、抓取／授權限制。此文件為 **B2 驗收前置**（B2 migration 之 seed 依它），非 B1 阻擋項。CF-25 在該審計完成前維持 Deferred。

## G4-5 — Migration 檔案位置

- Alembic 目錄：**`infra/db/migrations/`**
- `alembic.ini` 置於 repo 根，`script_location = infra/db/migrations`
- 維持 CLAUDE.md §2「migration 屬 /infra」之意圖；新增 migration 檔，不得改寫／刪除既有（CLAUDE.md §3／§4）。

## G4-6 — DAG 批次歸屬

| 模組 | 批次 | 說明 |
|---|---|---|
| I06（容器化／CI） | **新增 B0.5** | B1 前先建最小 `docker-compose.yml`（Postgres 16 + Temporal dev）與 CI（lint／型別／測試 workflow）、`.env.example`（列名不填值）。屬 Foundation。 |
| I05（pgvector） | **B1** | 與 I01 同一 PostgreSQL 實例建 extension |
| I03（快取） | **B5** | Seco/CMI 儀表板讀取需要時才加 |
| G04 `model_version` 表 | **B1 建表**，B4 起寫入 | 消解「B1 產出 vs B4 涵蓋」歧義 |

DAG 更新後序列：`B0 → B0.5 → B1 → B2 → … → B12`（仍線性、單批施工）。

---

## 待確認（下游批次定）
- B0.5：CI 平台（GitHub Actions／其他）、容器 registry。
- I03 快取具體技術（Redis／其他）——B5 定。
