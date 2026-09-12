# ADR-0017 — WBS-B6：Agent 層（A01–A08）+ G02 自治權控制器 + G05 RBAC

- 狀態：**ACCEPTED（B6 實作決議）**
- 日期：2026-09-12
- 核可：Research Director／Executive User（隨 B6 PR 審閱）
- 來源：Work-3 WBS-B6（驗收關卡：GP-21 四權分離）、Work-1 §3.5／§5、Work-2 §6 AGENT_SPEC、Charter §21、CF-37～46、GP-13／17～21
- 影響：新增 `src/governance/rbac.py`（G05）、`src/governance/autonomy.py`（G02）、`src/agents/base.py`、`src/agents/roster.py`（A01–A08）。無新表、無 migration。

---

## 1. 範圍與批次界定

Work-3 WBS-B6 名義上是「A01–A08 + G02 + G05」十個項目，但這十個項目是**單一治理機制**的三個切面（RBAC 資料模型／執行閘門／Agent 骨架彼此緊密耦合，不像 B3/B4/B5 是可獨立驗收的運算模組），故依 CLAUDE.md §8 精神視為**一批**，不再拆 B6a/b。

## 2. G05 — RBAC（`src/governance/rbac.py`）

**`AgentPower`**（Charter §21／GP-21 四權 + 一個「無實質權限」類別）：`EVIDENCE`／`ANALYSIS`／`APPROVAL`／`PUBLICATION`／`NONE`。

**設計關鍵**：`AgentRole.power` 為**單一值**（非集合）——「一個 Agent 只能有一種權限」由型別結構本身保證，不是執行期檢查才擋下（比多數 RBAC 系統更嚴格，但完全符合 Charter §21「單一 Agent 不應同時完成 Evidence、Conclusion、Approval 與 Publication」之精神）。

**`AGENT_ROSTER`**（A01–A08，依 Work-1 §3.5／Work-2 §6）：

| Agent | Autonomy | Power | 依據 |
|---|---|---|---|
| A01 抽取代理 | L1 | `EVIDENCE` | 建 Candidate，Candidate≠Fact |
| A02 分類代理 | L1/L2 | `ANALYSIS` | Universe／Taxonomy 分類**建議**（非最終判定） |
| A03 關係矛盾分析代理 | L2 | `ANALYSIS` | |
| A04 Seco/CMI/重大性分析代理 | L2 | `ANALYSIS` | Recommendation≠Approval |
| A05 比較分析代理 | L2 | `ANALYSIS` | CFL-06 控管 |
| A06 審查代理（Critic） | L2 | `ANALYSIS` | 觸發 CFL-07，不自行核准 |
| A07 協調代理 | L0 | `NONE` | 純確定性編排，不涉研究判斷 |
| A08 人工介接閘道代理 | L3/L4 gate | `NONE` | 僅路由至人工佇列，不自行核准 |

**已知規格落差（待確認，不影響本 ADR 落地）**：Work-1 §5 之 L0–L4 彙總表只明列 A01（L1）、A03/A04/A05（L2）、A07（L0）、A08（L4）；A02（L1/L2）、A06（L2）雖在 Work-1 §3.5 模組表有自己的 autonomy 標示，但未出現在 §5 彙總表。本 ADR 採 §3.5 個別模組描述為準（較細節），此落差建議回報 Research Director 確認 Work-1 是否需勘誤。

**驗證函式** `assert_gp21_roster_compliance(roster)`：斷言**沒有任何 Agent 持有 `APPROVAL` 或 `PUBLICATION`**（這兩權限依 Charter 設計僅屬治理模組 G01／G06 與人工，見 §4）；此為 WBS-B6 驗收關卡之直接落地。

**細化（實作中修正）**：`AgentRole` 除 `power` 外另帶**單一** `action_kind` 欄位——同屬 `NONE` 權限的 A07（`ORCHESTRATE`）與 A08（`ROUTE_TO_HUMAN`）雖皆無實質研究權限，仍是兩種不可互換的機械功能，不應僅因同權限桶就能互相冒充彼此的動作。`assert_gp21_roster_compliance` 一併檢查 `action_kind` 與 `power` 是否相容（`ACTIONS_FOR_POWER` 對照表）。

## 3. G02 — 自治權控制器（`src/governance/autonomy.py`）

**`ActionKind`**：`WRITE_CANDIDATE`（對應 `EVIDENCE`）、`RECOMMEND`（對應 `ANALYSIS`）、`ORCHESTRATE`／`ROUTE_TO_HUMAN`（對應 `NONE`）、`APPROVE`（對應 `APPROVAL`，**無 Agent** 持有）、`PUBLISH`（對應 `PUBLICATION`，**無 Agent** 持有）。

`authorize(agent_id, action)`：查 `AGENT_ROSTER`，若 `action` 不等於該 agent 之 `action_kind`（單一值，非集合，見 §2 細化）則 `AutonomyViolation`（`PermissionError` 子類）。**這是 GP-21 的即時執行閘門**——任何呼叫端（未來的 A01–A08 實作、B7 工作流程）在動作前都必須先過這一關。`ActionKind` 定義移至 `governance.rbac`（G05）以避免與 `governance.autonomy`（G02）循環匯入；G02 從 G05 匯入並沿用。

`is_l3_eligible(*, cfl_status, confidence, has_conflict, is_high_risk_transition) -> bool`：Charter §21 逐字 L3 條件（「規則明確、Confidence 足夠、無重大衝突、非高風險 State Transition 且通過 CFL」）之**純函式判定**——回傳是否符合 L3 自動決策資格，**不**自動執行任何寫入（實際自動決策邏輯屬 G01 完整規則引擎，WBS-B8）。門檻（何謂「足夠」confidence）留待 B8 之 G01 規則引擎具體化，本 ADR 只給判定骨架。

## 4. A01–A08 — Agent 骨架（`src/agents/base.py`／`roster.py`）

`Agent` 抽象基底：`run(payload)` 一律先呼叫 `governance.autonomy.authorize(self.agent_id, self.action_kind)` 才轉呼叫 `_perform(payload)`。**`_perform` 一律 `NotImplementedError`**——真正的抽取／分類／分析邏輯需呼叫 LLM（Claude，ADR-0001），但 Charter／Work-1～3 未定義任何 prompt、輸出 schema 或逐來源類型的抽取規則，屬產品設計工作，**Deferred**（比照 P01 具體 site adapter 之處理方式，`ADR-0009`）。B6 交付的是**治理骨架與強制閘門**，不是可運作的 AI 邏輯。

8 個具體類別（`ExtractionAgent`／`ClassificationAgent`／`RelationshipConflictAgent`／`SecoCmiMaterialityAgent`／`ComparisonAgent`／`CriticAgent`／`CoordinatorAgent`／`HumanGatewayAgent`）僅宣告 `agent_id`／`action_kind`，對應 §2 表格。

## 5. 驗收（Work-3 WBS-B6 逐字：GP-21 四權分離）

- `assert_gp21_roster_compliance`：`AGENT_ROSTER` 中無 `APPROVAL`／`PUBLICATION`。
- `authorize`：每個 agent 對「自己權限允許的 action」通過、對其餘 4 種 action 皆 `AutonomyViolation`（8×5 矩陣全覆蓋）。
- `is_l3_eligible`：四條件任一不成立即 `False`，全部成立才 `True`。
- 8 個 Agent 類別：`run()` 呼叫會先過 `authorize`（用錯 `action_kind` 建構會在 `run` 時被攔下），`_perform` 皆 `NotImplementedError`。
- 全為純 Python 單元測試，不需 DB。

## 6. 待確認 / 後續

1. Work-1 §5 彙總表 A02／A06 缺漏（§2 已述）——建議回報但不阻擋本批。
2. 實際 LLM 抽取／分析邏輯（prompt、輸出 schema、逐 D0x 來源類型規則）——待產品設計，非本 ADR 範圍。
3. G01 完整規則引擎（B8）需消費 `is_l3_eligible` 之判定骨架，具體 confidence／conflict 門檻於該批定案。
4. Work-3 之後批次：B7（工作流程引擎 W01–W06；I04 部署）。
