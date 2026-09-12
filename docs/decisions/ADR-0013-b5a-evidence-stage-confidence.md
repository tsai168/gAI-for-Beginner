# ADR-0013 — WBS-B5a：Schema 補漏（Evidence.confidence）+ M01 Evidence Stage + M02 Confidence

- 狀態：**ACCEPTED（B5a 實作決議）**
- 日期：2026-09-12
- 核可：Research Director／Executive User（隨 B5a PR 審閱）
- 來源：Work-3 WBS-B5（M01／M02）、Charter §11.1（E0–E6）、§16（CF1–CF5）、CF-05／CF-29／CF-30、GP-02／GP-05／GP-11
- 影響：`knowledge/db/models.py`（`Evidence` schema 修正）、新 migration 0003、`src/models/evidence_stage.py`、`src/models/confidence.py`。

---

## 0. Schema 修正：`evidence.confidence` / `evidence.model_version_id`（B1 遺漏）

實作 M02 時發現：Work-2 §2.1「此外，所有實體共用以下稽核／治理欄位：`confidence`、`cfl_status`、`model_version_id`…」明文**所有實體**皆應具備 `confidence`／`model_version_id`，但 B1（`ADR-0007` §4）把 `Evidence` 掛在 `CflStatusMixin`（僅 `cfl_status`），漏了 `GovernedMixin` 的 `confidence`／`model_version_id`——與 Work-2 §2.1 不符，且 M02 的計算結果無處可寫。

**修正**：`Evidence` 改用 `GovernedMixin`（含 `CflStatusMixin`）；新增 migration `0003_evidence_confidence.py` 對既有 `evidence` 表 `ADD COLUMN confidence numeric(5,4)`、`ADD COLUMN model_version_id uuid`（皆 nullable，不影響既有資料；不改寫、不刪除既有 migration，符合 CLAUDE.md §3／§4）。`tests/test_schema_contract.py` 之 `evidence` 契約清單同步補上。

**已知風險並已修正（2026-09-12，CI `alembic round-trip`／`integration` 失敗後診斷）**：migration 0001／0002 用 `Base.metadata.create_all(tables=[...])` 建表，其 DDL 來自**當下即時**的 ORM metadata，不是凍結的歷史快照——`Evidence` 改用 `GovernedMixin` 後，migration 0001 重跑時**已經**會建出 `confidence`／`model_version_id` 兩欄，導致 0003 的 `ADD COLUMN` 直接撞上 `DuplicateColumn`。0003 已改為 `ADD COLUMN IF NOT EXISTS`／`DROP COLUMN IF EXISTS`，無論 0001 是否已建出該欄都能正確 round-trip。**後續政策**：任何在既有表上新增欄位的 migration，一律用 `IF NOT EXISTS`／`IF EXISTS` 寫，不假設「上游 migration 一定沒建過」。

## 1. 範圍（B5，8 模組，依 CLAUDE.md §8 拆批）

B5a（本 ADR）：M01、M02。後續：B5b（M03 Seco／M04 CMI，含 §2.9 模型輸出表）、B5c（M05 Materiality／M07 PIT 市值）、B5d（M06 事件窗口／AR-CAR／M08 穩健性檢核）。

## 2. M01 — Evidence Stage 分類器（`src/models/evidence_stage.py`）

Charter §11.1 只定義 E0–E6 階梯本身，**未給「如何從證據文字判斷屬於哪一階」的演算法**——那需要語意判斷（L1，A01，WBS-B6 才做）。M01 在 L0 確定性範圍內能做的是**聚合與單調性守門**，不做文字分類：

- `aggregate_evidence_stage(tags) -> EvidenceStage | None`：輸入一組已標記 `(stage, evidence_type)` 的證據（`stage` 由上游／人工／未來 A01 標記，M01 不猜）。取 **SUPPORT** 證據中最高之 stage，但若**同一階**存在 **CONTRADICT**（反證 E6 不代表反證 E2——只擋同階，不向下擴散），該階視為未確認，降階至下一個未被反證阻擋之 SUPPORT 階；全無 SUPPORT 則回傳 `None`（GP-02：沒有證據不等於反面已證實，不得預設 E0）。
- `validate_stage_transition(old, new, *, allow_regression=False)`：階梯只能上升，除非明確標記 `allow_regression=True`（對應「修正」情境，比照 K05 Revision Chain 之「只有明確修正才能變更既有結論」精神）；否則 `ValueError`。體現 Charter §11.1「『有 CPO 技術』≠『進入供應鏈』≠『量產』≠『營收貢獻』」。

## 3. M02 — Confidence 引擎（`src/models/confidence.py`）

Charter §16 列出 CF1–CF5 五構面（Source Authority／Evidence Directness／Independent Corroboration／Temporal Quality／Conflict Penalty），**未給權重公式**（不同於 Seco／CMI，Charter 沒有凍結 Confidence 的數值權重）——V1「Rule-based／Expert Prior」。

**本 ADR 之權重（實作慣例，非 Frozen Decision，可調整）**：

| 構面 | 對應既有欄位（Work-2 §2.7 K06 CF-10） | 權重 |
|---|---|---|
| CF1 Source Authority | `evidence.authority` | 0.30 |
| CF2 Evidence Directness | `evidence.directness` | 0.25 |
| CF3 Independent Corroboration | `evidence.independence` | 0.25 |
| CF4 Temporal Quality | `evidence.time_`（DB 欄名 `time`） | 0.20 |
| CF5 Conflict Penalty | 由呼叫端提供（是否有未解 CFL-07 矛盾），非本 ADR 自動判定 | 扣分項，非權重內 |

`compute_confidence(*, authority, directness, independence, temporal_quality, conflict_penalty=0.0) -> float`：加權和後扣 `conflict_penalty`，clamp 至 `[0,1]`。四個輸入分數本身須落在 `[0,1]`（Work-2 CF-10 欄位定義域），否則 `ValueError`。

`score_evidence_confidence(evidence, *, conflict_penalty=0.0) -> float | None`：直接讀 `Evidence` 物件之 CF-10 四欄；**任一為 `None` 則回傳 `None`（不得用預設值頂替，GP-11：LLM Confidence ≠ Research Confidence，缺值就是缺值）**。

**明確不做的事（待確認／後續）**：CF5 Conflict Penalty 之自動判定（搜尋同一 `entity_ref` 是否存在有效 CONTRADICT 證據）需要實體關聯與矛盾分析邏輯，屬 A06／K04 職責（WBS-B6），本 ADR 只開放 `conflict_penalty` 參數讓上游傳入，不在 M02 內部搜尋。

## 4. 驗收

- M01：`aggregate_evidence_stage` 各種 SUPPORT/CONTRADICT 組合、無 SUPPORT 回 `None`、`validate_stage_transition` 阻擋非法降階。
- M02：`compute_confidence` 邊界值（0/1）、越界拋錯、`score_evidence_confidence` 缺值回 `None`。
- Schema 修正：`test_schema_contract.py` 更新 `evidence` 契約欄位；migration round-trip（CI）。
- 皆為純 Python 單元測試（不需 DB），schema 修正另有 migration 驗證。
