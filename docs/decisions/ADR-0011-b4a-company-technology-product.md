# ADR-0011 — WBS-B4a：Company／Technology／Product 知識庫 CRUD 層

- 狀態：**ACCEPTED（B4a 實作決議）**
- 日期：2026-09-12
- 核可：Research Director／Executive User（隨 B4a PR 審閱）
- 來源：Work-3 WBS-B4（K01／K02／K03）、Charter §17 CFL-02、GP-10；`ADR-0004`（CFL 候選/G01 樁模式）
- 影響：`src/knowledge/repository/company.py`、`technology.py`、`product.py`。無新資料表、無 migration（沿用 B1 schema）。

---

## 1. 範圍

WBS-B4 涵蓋 K01–K06＋G04，依 CLAUDE.md §8（一次 1–3 個高度相關模組）拆為兩批：
**B4a**（本 ADR）：K01 Company、K02 Technology（Bitemporal 基礎機制）、K03 Product。
**B4b**（`ADR-0012`）：K04 Relationship、K05 Event（Revision Chain）、K06 Evidence。

## 2. K01 — Company Repository

`create_company` / `get_company` / `list_companies_by_universe`。

**CFL-02 掛勾**：`set_universe(session, company, new_universe, *, cfl_service)`——當 `new_universe == Core` 且原本不是 `Core`（**首次升級**）時，經 G01 提交 `CFL-02` 候選（沿用 M05／P05 的「本模組算/改，G01 判定」模式，ADR-0004）。非首次升級 Core（已經是 Core）或降級／平移不觸發候選（Charter §17 CFL-02 僅要求「首次升 Core」）。

## 3. K02 — Technology Repository（Bitemporal 基礎機制）

Work-2 §2.3 僅定義單列的 `valid_from`／`valid_to`（Effective Time 區間），**未定義**「同一分類節點跨版本」的穩定識別鍵（例如某種 `taxonomy_node_id`）——`technology_id` 本身即是列主鍵，每個版本是獨立列。

**本 ADR 提供之機制（非發明新契約欄位）**：
- `open_technology_version(session, *, category, parent_technology_id=None, taxonomy_version_id=None, valid_from) -> Technology`：建新列，`valid_to=None`（開放中）。
- `close_technology_version(session, technology, *, valid_to) -> None`：把既有列的 `valid_to` 設定為給定時間，標記其不再是目前版本（**不**刪除、不覆寫其餘欄位——歷史內容原樣保留）。
- `current_technology_versions(session, *, category=None) -> list[Technology]`：查詢 `valid_to IS NULL` 之列。

**待確認（不由本 ADR 決定）**：新舊版本之間是否需要一個顯式「supersedes」欄位（比照 K05 `revision_of_event_id`）以串連版本鏈——Work-2 未定義此欄位，本 ADR **不**擅自新增契約欄位；若 Research Director 認為需要，應走 Work-2 Change Request（比照 ADR-0003 之流程），而非在 repository 層用旁路手段模擬。

## 4. K03 — Product Repository

`create_product` / `get_product` / `update_evidence_stage`。無 CFL 掛勾（Product 的 Evidence Stage 屬 M01／CF-05，B5 才計算判定；B4 僅提供資料存取層）。

## 5. 驗收

- CFL-02：`test_set_universe_to_core_raises_cfl02_once`（首次升 Core 才觸發，重複設回 Core 不重複觸發）。
- Technology bitemporal：`test_close_then_open_leaves_old_row_data_intact`（closed 列除 `valid_to` 外欄位不變，符合「歷史不可覆寫」精神）。
- 皆為 DB-backed（`pytest -m integration`）。

## 6. 後續

B4b：K04／K05／K06，含 K05 Event Revision Chain（Work-3 WBS-B4 驗收關卡：CORRECTED 不覆寫 ACTIVE 舊版本）。
