# ADR-0012 — WBS-B4b：Relationship／Event Revision Chain／Evidence 知識庫層

- 狀態：**ACCEPTED（B4b 實作決議）**
- 日期：2026-09-12
- 核可：Research Director／Executive User（隨 B4b PR 審閱）
- 來源：Work-3 WBS-B4（K04／K05／K06；驗收關卡「K05 Event 修正鏈測試：CORRECTED 不覆寫 ACTIVE 舊版本」）、Charter §17 CFL-05／CFL-07、§20 Event Revision、CF-35／CF-36；`ADR-0004`、`ADR-0011`（B4a）
- 影響：`src/knowledge/repository/relationship.py`、`event.py`、`evidence.py`。無新資料表、無 migration。

---

## 1. 範圍

延續 B4a。本批完成 WBS-B4 全部（K01–K06）。

## 2. K04 — Relationship Repository（CFL-05 掛勾）

`create_relationship`（預設 `status=CANDIDATE`，沿用 DB default）、`get_relationship`。

`confirm_relationship(session, relationship, *, cfl_service)`：`status: CANDIDATE → CONFIRMED`。若 **`is_named=True` 且原本非 CONFIRMED**（首次確認），經 G01 提交 CFL-05 候選。

**簡化聲明（待確認）**：Charter §17 CFL-05 原文「**重大**具名 Customer 首次 Confirmed 需 Human Review」含「重大」與「Customer」兩個限定詞，但 K04 schema（Work-2 §2.5）**沒有** materiality 欄位，也未限定僅 `relationship_type=CUSTOMER` 才需審查。本 ADR 採**寬鬆解讀**：任一 `is_named=True` 關係首次確認皆觸發 CFL-05（不分 relationship_type、不判斷「重大」）。若 Research Director 要求收斂為僅 Customer 或需先過 materiality 門檻，屬本 ADR 之修訂，不需動 Work-2 契約。

## 3. K05 — Event Repository（Revision Chain，本批核心）

### 3.1 資料模型回顧（Work-2 §2.6，B1 已建）
`revision_of_event_id`（自參照，指向被修正之「上一版」）、`revision_seq`（鏈內序號，從 1 起）、`lifecycle_status`（`ACTIVE/CORRECTED/SUPERSEDED/WITHDRAWN/DISPUTED`）。

### 3.2 狀態機（本 ADR 定義，Charter §20 未給逐步演算法，屬工程實作決策）

| 動作 | 舊列（原 head） | 新列 |
|---|---|---|
| `create_event` | — | `revision_seq=1`、`lifecycle_status=ACTIVE`、`revision_of_event_id=NULL` |
| `correct_event` | `lifecycle_status → SUPERSEDED`（**僅此欄位變更，其餘欄位原樣保留**） | 新列：`revision_of_event_id=舊列.event_id`、`revision_seq=舊.revision_seq+1`、`lifecycle_status=CORRECTED`、套用 `changes` |
| `withdraw_event` | `lifecycle_status → SUPERSEDED` | 新列：同上但 `lifecycle_status=WITHDRAWN`，內容與舊列相同（撤回不改變事實，只改變狀態；Charter §20「撤回不代表歷史上未曾存在」） |

**只能對「目前 head」動作**：`lifecycle_status ∈ {ACTIVE, CORRECTED}` 之列才能被 `correct`/`withdraw`；已是 `SUPERSEDED/WITHDRAWN/DISPUTED` 者呼叫會 `ValueError`（不得對非 head 節點再生新修正，須先取得 head）。

**新列不繼承治理欄位**：`cfl_status`（一律回到 `PENDING`，須重新走 G01）、`confidence`／`model_version_id`（一律 `NULL`，等 M02 對新內容重新計算，不沿用舊分數）。其餘欄位（時間、`event_taxonomy_code`、`materiality_score`、`evidence_ids` 等）原樣複製並可被 `changes` 覆蓋。

**驗收關鍵（Work-3 WBS-B4 驗收關卡逐字）**：`correct_event` 後，**舊列**（原 `ACTIVE`）除 `lifecycle_status` 外之欄位（`materiality_score`、`event_taxonomy_code`、時間欄位等）**位元組不變**——新資料寫入新列，不覆寫舊列。

### 3.3 查詢輔助

- `get_root(session, event_id) -> Event`：沿 `revision_of_event_id` 往回走到 `revision_seq=1`。
- `get_latest(session, event_id) -> Event`：沿「誰的 `revision_of_event_id` 指向我」往前走到沒有下一棒為止。
- `list_revision_chain(session, event_id) -> list[Event]`：合併前兩者，回傳 root→latest 依 `revision_seq` 排序之完整鏈。

## 4. K06 — Evidence Repository（CFL-07 掛勾）

`create_evidence`、`get_evidence`。

`record_contradiction(session, evidence, *, cfl_service)`：對 `evidence_type=CONTRADICT` 之列提交 CFL-07 候選。`governance.cfl.NO_AUTO_PASS` 已含 `CFL-07`（B1 起即禁止 auto-pass，B8 規則引擎沿用此常數，見 `ADR-0004`／`ADR-0007` §6）。

## 5. 驗收

- CFL-05：具名首次 Confirmed 觸發、非首次／匿名不觸發。
- Event Revision Chain：`correct_event` 後舊列欄位不變（逐欄比對）、`revision_seq` 遞增、`get_root`／`get_latest`／`list_revision_chain` 正確；對非 head 節點呼叫 `correct_event`／`withdraw_event` 拋錯。
- CFL-07：CONTRADICT evidence 提交候選，`cfl_id in NO_AUTO_PASS`。
- 皆為 DB-backed（`pytest -m integration`）。

## 6. 後續（WBS-B4 完成後）

B5：M01–M08 分析引擎（含 §2.9 模型輸出表 `seco_score`／`cmi_score`／`valuation_event_window`）。
