# 盤點報告 §6 待確認清單 — 結案對照表

- 日期：2026-09-10
- 核可：Research Director／Executive User
- 原始清單：`docs/audit/CPO_AI_ReadOnly_Audit_Report.md` §6（38 項，A–H 群組）
- 決策記錄：`docs/decisions/ADR-0001` ～ `ADR-0006`

**狀態定義**
- **RESOLVED** — 已做出決策，並已寫入 ADR ＋（必要時）Work-2／Work-3／CLAUDE.md。
- **SCHEDULED** — 已指定由某一批次（含具名產出物）處理；非 B1 阻擋項。

---

## A. 前置與文件結構

| # | 項目 | 狀態 | 依據 |
|---|---|---|---|
| A-1 | `.docx`→`/docs/*.md`、`git init`、`/src`·`/infra`·`/tests` | RESOLVED | commit `fe68fd8`、`c07229d` |
| A-2 | 0828/0829 封存 `docs/legacy/` ＋ `CFL_MAPPING_LEGACY_0828.md` | RESOLVED | commit `263eb8a` |
| A-3 | §5／§7「待補充」由誰補、是否 Charter §31 CR | RESOLVED | ADR-0001 |

## B. 編號與命名消歧

| # | 項目 | 狀態 | 依據 |
|---|---|---|---|
| B-4 | `S1–S5` 重載（Seco 構面 vs Source Tier） | RESOLVED | ADR-0002 C-1 |
| B-5 | `CF` 前綴重載（`CF1..5` vs `CF-01..46`） | RESOLVED | ADR-0002 C-2 |
| B-6 | Event `status` → `pipeline_status` + `lifecycle_status` | RESOLVED | ADR-0002 C-3；Work-2 §2.6／§3.1／§3.2；CLAUDE.md §6 |
| B-7 | Bitemporal 欄名統一 `valid_from/valid_to` | RESOLVED | ADR-0002 C-4；Work-2 §2.3 |
| B-8 | Frozen Decision 計數（無 `CF-34`；`CF-34R`＋`CF-21A`；共 47） | RESOLVED | ADR-0002 C-5 |
| B-9 | `project_id` 僅在事件／稽核層，不入 K01–K06 | RESOLVED | ADR-0002 C-6 |

## C. 資料模型缺口

| # | 項目 | 狀態 | 依據 |
|---|---|---|---|
| C-10 | 7 個 Core Research Object 無 schema | RESOLVED | ADR-0003 G-1；Work-2 §2.9（8 表） |
| C-11 | `shares_outstanding`（PIT，CF-24） | RESOLVED | ADR-0003 G-2；`market_data` |
| C-12 | `available_at`（CF-26／GP-09） | RESOLVED | ADR-0003 G-3；Work-2 §2.1；CLAUDE.md §4 |
| C-13 | `person` 表 | RESOLVED | ADR-0003 G-4 |
| C-14 | `model_version`（G04）欄位 | RESOLVED | ADR-0003 G-5 |
| C-15 | K05 `revision_seq` | RESOLVED | ADR-0003 G-6；Work-2 §2.6 |

## D. CFL 與 Agent

| # | 項目 | 狀態 | 依據 |
|---|---|---|---|
| D-16 | CFL-04：M05 算分/raise、A04 只建議、G01 判定 | RESOLVED | ADR-0004 決策 1 |
| D-17 | Seco/CMI 大幅變動 → G08 Material Review 旗標（非新 CFL） | RESOLVED | ADR-0005 G4-1 |
| D-18 | G01 時序：B1 介面樁、B8 規則引擎 | RESOLVED | ADR-0004 決策 2；Work-3 §2 B1／B8 |
| D-19 | 模組間傳輸：Temporal + `event` 表 outbox，V1 不加 broker | RESOLVED | ADR-0004 決策 3 |

## E. 依賴圖與批次

| # | 項目 | 狀態 | 依據 |
|---|---|---|---|
| E-20 | I06 → 新增 B0.5；I03 → B5 | RESOLVED | ADR-0005 G4-6；Work-3 §2 |
| E-21 | I05 pgvector → B1 | RESOLVED | ADR-0005 G4-6；Work-3 §2 B1 |
| E-22 | G04 `model_version` 表 → B1 建、B4 起寫 | RESOLVED | ADR-0005 G4-6 |
| E-23 | P03 拆入 B2、其餘 P 層 B3 — 確認無誤 | RESOLVED | ADR-0006 §4C |
| E-24 | DAG 線性順序（B0→B0.5→…→B12）以 Work-3 §2 為準 | RESOLVED | ADR-0006 §4C |

## F. 技術選型與 Deferred

| # | 項目 | 狀態 | 依據 |
|---|---|---|---|
| F-25 | I04 Temporal／I05 pgvector 正式定案 | RESOLVED | ADR-0001 §2 |
| F-26 | Temporal 自架 vs Cloud | SCHEDULED（部署階段；程式讀 env） | ADR-0006 G4-10 |
| F-27 | TQ-03 Kappa — 不納入 V1 | RESOLVED | ADR-0005 G4-3 |
| F-28 | TQ-04 γ 迴歸 — Phase 2；B5 僅 V1 範圍 | RESOLVED | ADR-0006 G4-9 |
| F-29 | 各資料集 earliest reliable date（CF-25） | SCHEDULED（B2 前置 `docs/audit/DATA_AVAILABILITY_AUDIT.md`） | ADR-0005 G4-4 |

## G. Environment Variables／外部來源認證

| # | 項目 | 狀態 | 依據 |
|---|---|---|---|
| G-30 | I02 物件儲存產品 | SCHEDULED（部署；env） | ADR-0006 G4-10 |
| G-31 | I03 快取產品 | SCHEDULED（B5） | ADR-0005 G4-6／ADR-0006 |
| G-32 | LLM 供應商＝Claude；`model id`／token budget | RESOLVED（供應商）／SCHEDULED（model id、budget：部署／Deferred） | ADR-0001 §3.1；ADR-0006 G4-10 |
| G-33 | D05 市場資料商與認證 | SCHEDULED（部署 ＋ B2 availability audit） | ADR-0006 G4-10；ADR-0005 G4-4 |
| G-34 | D06 TDCC 取得與認證 | SCHEDULED（同上） | ADR-0006 G4-10；ADR-0005 G4-4 |
| G-35 | API 認證機制（OIDC/JWT）＋ RBAC 六角色矩陣 | RESOLVED | ADR-0004 決策 4；Work-2 §4.4 |
| G-36 | `.env.example`（列名不填值） | SCHEDULED（B0.5／B1 產出） | ADR-0005 G4-6；ADR-0006 G4-10 |

## H. API 契約細節

| # | 項目 | 狀態 | 依據 |
|---|---|---|---|
| H-37 | 端點 path/query/body schema、`error_code` 列舉 | SCHEDULED（B9 → `API_SPEC.yaml`） | ADR-0006 G4-8 |
| H-38 | Event 型別明細目錄 | SCHEDULED（B7 → `docs/EVENT_CATALOGUE.md`） | ADR-0006 G4-7；Work-2 §3.3 |

---

## 結論

38 項全部 **RESOLVED 或 SCHEDULED**，無「未指派」項。

- **RESOLVED：26 項** — 決策已入 ADR-0001～0006 並回寫 CLAUDE.md（V1.4）／Work-2（V1.4）／Work-3（V1.2）。
- **SCHEDULED：12 項** — 皆為型別細節或部署值，已指定批次與具名產出物；非 B1 阻擋項。

**B1 開工前尚需之一次性前置**：
1. B0.5：`docker-compose.yml` + CI + `.env.example`
2. （B2 前）`docs/audit/DATA_AVAILABILITY_AUDIT.md`

依 CLAUDE.md §10／Work-3 §8，§6 清單既已結案，**可授權自 B0.5 → WBS-B1 開始施工**；ADR 內標為「待確認」之逐欄型別，由 B1 migration PR 逐項定並回填對應 ADR。
