# ADR-0002 — 欄位命名一致性裁定（盤點報告 §3.1 / §6 Group 1：C-1～C-6）

- 狀態：**ACCEPTED**
- 日期：2026-09-10
- 核可：Research Director／Executive User（本專案人工授權）
- 來源：`docs/audit/CPO_AI_ReadOnly_Audit_Report.md` §3.1、§6
- 影響檔案：`docs/WORK2_CONTRACT_FREEZE_V1.md` → V1.1；`CLAUDE.md` §6 → V1.2；`docs/WORK3_IMPLEMENTATION_BLUEPRINT_V1.md` 註記
- 治理定性：欄位**消歧與命名慣例**，不改語意、不改 enum 值、不觸及 Charter 凍結面（Universe／Taxonomy／Evidence Stage／Source Tier／Relationship／Seco／CMI／Event Timing／Event Window／Confidence／CFL／Publication／Agent Autonomy 之**內容**均未變）。依 Charter §7／§31 屬「小幅且不改變研究契約的調整」→ V1.x，非 Charter §31 CR，亦不開新 Charter 版本。Work-2 §10 要求之 Change Request 由本 ADR 兼任其記錄。

---

## C-1 — `S1–S5` 語意重載（Seco 構面 vs Source Tier）

**問題**：Charter §12 Seco 六構面標為 `S1`(Technology Relevance)…`S6`；Charter §11.2 Source Tier 為 `S1`–`S5`。

**裁定**：
- **Source Tier** 欄位值維持 `S1`–`S5`，欄位名 `source_credibility_tier`（Work-2 §2.7，不變）。
- **Seco 六構面** 在 schema／程式一律用具名欄位，不使用 `S1..S6`：
  `tech_relevance`／`product_readiness`／`customer_validation`／`ecosystem_position`／`commercialization`／`strategic_defensibility`。
  文件敘述時對照 Charter §12 之 S1–S6 編號。
- 影響：僅為未來 Seco 表（見 ADR-0003 / Group 2）之建置指引；Work-2 現有欄位無變更。

## C-2 — `CF` 前綴重載（Confidence 構面 vs Frozen Decision）

**問題**：Charter §16 Confidence 構面 `CF1`–`CF5`；Charter §27 Frozen Decision `CF-01`–`CF-46`。

**裁定**：
- Frozen Decision 一律寫 **`CF-01`**（含連字號）。
- Confidence 五構面在 schema／程式用具名欄位，不使用 `CF1..CF5`：
  `source_authority`／`evidence_directness`／`independent_corroboration`／`temporal_quality`／`conflict_penalty`。
- `confidence` 純量欄位（0–1，Work-2 §2.1）名稱不變。
- 影響：未來 Confidence 明細表（Group 2）之建置指引；Work-2 現有欄位無變更（§2.1／§3.1 敘述中的「CF1–CF5」為概念引用，保留）。

## C-3 — Event `status` 一名兩義 → 拆為兩欄

**問題**：EVENT_CONTRACT §3.1 `status` = 處理狀態機（`DISCOVERED…PUBLISHED`）；DATA_MODEL §2.6 K05 `status` = 生命週期（`ACTIVE/CORRECTED/SUPERSEDED/WITHDRAWN/DISPUTED`，CF-36）。

**裁定**：拆為兩個獨立欄位，enum 值皆不變：
| 欄位 | 意義 | 值 | 依據 |
|---|---|---|---|
| `pipeline_status` | 事件處理管線狀態 | `DISCOVERED→FETCHED→NORMALIZED→EXTRACTED→VERIFIED→ANALYZED→APPROVED→PUBLISHED` | Work-2 §3.2 |
| `lifecycle_status` | 事件生命週期（Immutable + Revision） | `ACTIVE / CORRECTED / SUPERSEDED / WITHDRAWN / DISPUTED` | CF-36、Work-2 §2.6 |

**已套用之文件編輯**：
- Work-2 §3.1 通用事件欄位清單與表格：`status` → `pipeline_status`
- Work-2 §3.2 標題註明欄位為 `pipeline_status`
- Work-2 §2.6 K05：`status` → `lifecycle_status`
- CLAUDE.md §6 固定事件欄位清單：`status` → `pipeline_status`，並註明 K05 另有 `lifecycle_status`

## C-4 — Bitemporal 有效時間欄名不一致 → 統一

**問題**：Work-2 §2.1 通用規範 `valid_from/valid_to`；§2.3 K02 `effective_from/effective_to`。

**裁定**：全庫統一 **`valid_from` / `valid_to`**（Effective Time）；Knowledge Time 用 `created_at`。

**已套用之文件編輯**：Work-2 §2.3 K02 `effective_from／effective_to` → `valid_from／valid_to`。

## C-5 — Frozen Decision 實際數量

**問題**：Charter §33 稱「CF-01～CF-46（含 CF-21A 與修正版 CF-34R）」；條列中**無 `CF-34`（僅 `CF-34R`）**，另有 `CF-21A`。

**裁定**（僅為註記，**不改 Charter 內文**）：
- 官方計數 = **47 個決策實體**：`CF-01`…`CF-46`，其中 **`CF-34` 不存在，一律以 `CF-34R` 為準**；另加獨立項 **`CF-21A`**。
- 追溯表、程式碼與文件引用 CF 編號時以此為準。

## C-6 — `project_id`

**問題**：EVENT_CONTRACT 有 `project_id`，DATA_MODEL K01–K06 各實體皆無；Charter 未提多專案。

**裁定**：
- V1 為單一專案。`project_id` 僅存在於**事件／稽核串流**（EVENT_CONTRACT），常數值 `cpo-ai`。
- **不**將 `project_id` 加入 K01–K06 實體表。
- 影響：無文件編輯（維持現狀），本 ADR 為正式澄清。

---

## 落地清單

| 項目 | 需要程式碼側動作（B1 起） |
|---|---|
| C-3 | K05 migration 建 `pipeline_status` 與 `lifecycle_status` 兩欄；事件串流 payload 用 `pipeline_status` |
| C-4 | 所有 Bitemporal 表用 `valid_from/valid_to` |
| C-1 / C-2 | Seco／Confidence 明細表（Group 2 決定 schema 後）用具名構面欄位 |
| C-5 | CF 追溯工具以 47 項為準 |
| C-6 | 事件 payload 帶固定 `project_id="cpo-ai"`；實體表不加 |

## 仍為待確認

- Group 2：Seco／CMI／MarketData／InstitutionalTrading／Shareholding／ValuationEventWindow／ResearchReport／Person 之 schema 缺口（盤點報告 §3.2 G-1～G-6），另立 ADR-0003。
- 盤點報告 §6 其餘群組。
