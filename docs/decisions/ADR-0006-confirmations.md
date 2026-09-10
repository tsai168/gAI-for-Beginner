# ADR-0006 — 確認事項：留待該批開工展開（Group 4B）

- 狀態：**ACCEPTED（確認）**
- 日期：2026-09-10
- 核可：Research Director／Executive User
- 來源：`docs/audit/CPO_AI_ReadOnly_Audit_Report.md` §6 Group 4B（G4-7～G4-11）
- 影響檔案：`docs/WORK2_CONTRACT_FREEZE_V1.md` §3.3 註記（→ V1.4）
- 治理定性：無新決策內容，僅確認「何時由哪一批展開」，避免被誤當缺口再開議。

---

| # | 項目 | 確認處置 |
|---|---|---|
| G4-7 | Event topic 明細目錄（audit C-7；Work-2 §3.3 原稱「Work-3 展開」未展開） | 移至 **WBS-B7** 產出 `docs/EVENT_CATALOGUE.md`（逐一列 `cpoai.<layer>.<event_type>`）。B3–B6 先用最小集。`<layer>` 用資料夾名。傳輸層＝Temporal + `event` 表 outbox（ADR-0004）。Work-2 §3.3 已加註。 |
| G4-8 | `error_code` 列舉（audit G-8）、端點 path/query/body schema（audit #37） | **WBS-B9** 依 Work-2 §4.3 格式 `<MODULE>-ERR-<NNN>` 展開為 `API_SPEC.yaml`；本階段不列舉。 |
| G4-9 | TQ-04 γ 共振迴歸／回測／統計檢定 | 確認 **Phase 2**。B5 之 M06／M08 僅做 V1 範圍：多窗口 AR／CAR（Market-adjusted + Market Model）、High/Med/Low Time-Quality Robustness Check；預留擴充點，不實作 γ 迴歸。 |
| G4-10 | Temporal 自架 vs Cloud、I02 物件儲存產品、I03 快取產品、D05／D06 資料商、LLM `model id`、token budget／ceiling | 皆 **Operations／部署階段**定；程式一律讀環境變數（CLAUDE.md §9）。B1 產出 `.env.example`（列名、不填值）。token budget 等維持 Charter §29 Deferred。 |
| G4-11 | P02 去重：hash vs 語意（audit C-8／§3.5） | P02 ＝ **hash 去重（確定性，L0）**。語意相似度比對（pgvector）歸 **K04／實體解析**，不併入 P02。Work-1 §3.10「I05 供 P02」理解為選配加強，非強制。 |

---

## 不需動作（記錄用，audit §4C）

- Charter §32 管線文字仍寫「AGENTS.md／Codex」；下游一律用「CLAUDE.md／Claude Code」。工具替換，**Charter 內文不改**。
- P03 拆入 B2、其餘 P 層在 B3 —— 確認無誤。
- DAG 線性順序（B0 → B0.5 → B1 → … → B12）以 Work-3 §2 為準；單批施工（1–3 模組）。
