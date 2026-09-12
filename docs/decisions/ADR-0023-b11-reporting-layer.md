# ADR-0023 — WBS-B11：報告／輸出層（R01–R06）

- 狀態：**ACCEPTED（B11 實作決議）**
- 日期：2026-09-12
- 核可：Research Director／Executive User（隨 B11 PR 審閱）
- 來源：Work-3 §2 DAG B11 列、§4 TEST（R06 正式外部發布須先通過 CFL-08）、Work-1 §3.7 R01–R06、Charter §18（三層發布）、Work-2 §5 CFL_CONTRACT（CFL-06→R05、CFL-08→R06）、`ADR-0003` G-1（`research_report` 欄位、`content_ref` "OPEN — B11 前定"）、`ADR-0020`（G06）、`ADR-0021`（B9 的 6 個 501 佔位端點）

---

## 1. `research_report` 表（新，非 K01–K06 編號）

沿用 `ADR-0003` 已定的欄位（`report_type/subject_ref/version/publication_tier/cfl_status/content_ref/model_version_id`＋通用稽核欄位），另加 `subject_ref_type`（沿用既有 `RefEntityType`，比照 K04/K06 多型參照的既有作法，非新發明）。Migration 0007，CFL-governed（`research_report_cfl_guard` 重用既有 `cpoai_cfl_guard()`）。

`content_ref` 維持**掛勾點、不寫入**——本 repo 沒有任何 I02 物件儲存客戶端（`source_snapshot.snapshot_ref` 從 B1 到現在也是同樣狀態，從未真正寫過），report 內容一律在讀取當下即時查底層表計算，不預先渲染存檔。R03（Seco／CMI 儀表板資料）完全不落地成 `research_report` 列——它是即時資料，不是一份「報告」產出物。

## 2. 治理：只有 R05／R06 走 G01 數字化 CFL

Work-2 §5 CFL_CONTRACT 只把 CFL-06（候選 A05）與 CFL-08（候選 R06）指定給 R05／R06；R01–R04 沒有對應到任何一個 CFL-01～08 編號。因此：

- **R05（比較分析）**：`submit_comparison_report` 對 `research_report` 自己這一列提交 CFL-06 候選（G01 永遠回 REVIEW-REQUIRED，`governance/cfl.py` 既有規則）。
- **R06（正式外部發布）**：`submit_for_external_publication` 對 `research_report` 自己這一列提交 CFL-08 候選；`approve_external_publication` 是 `POST /publications/{id}/approve`（B9 已建的 501 佔位）背後的真正邏輯——本質上就是把 CFL-08 從 REVIEW-REQUIRED 轉到 APPROVED，只是給 R06 一個專用、範圍更窄的入口（駁回仍走通用的 `POST /cfl/CFL-08/decision`）。
- **R01（Internal Auto）**：完全不經 G01，`cfl_status` 保持預設 PENDING、從不寫入——Charter §18 對 Internal Auto 的要求就是「基本驗證後自動產生」，不需要任何 CFL 判定。
- **R02／R04（Material Review 時）**：**不**發明新的 CFL 編號，改成檢查**底層 Event 自己的** `cfl_status` 是否已經 APPROVED（R02 依 `event.materiality_score` 是否達到 G01 CFL-04 用的同一個門檻 `governance.cfl.HIGH_MATERIALITY_THRESHOLD`——沒有另外訂一個新數字；R04「顯著 CAR」則固定視為 Material Review）。邏輯上說得通：你不能先發一份「重大性事件報告」，而該事件本身都還沒通過 CFL-04 核准。

`PublicationTier` 本身搬到 `knowledge.db.base`（原本在 `governance.publication`，B8 建的）——因為現在它也是 `research_report.publication_tier` 這個 DB 欄位的型別，跟 `CflStatus` 一樣的道理；`governance.publication` 改成從那裡 re-export，舊的 `from governance.publication import PublicationTier` 呼叫端完全不用改。

## 3. 六個模組（`src/reports/`）

| 模組 | 檔案 | 真實內容 |
|---|---|---|
| R01 | `daily_digest.py` | 彙整時間窗內新 `source` 列＋G03 稽核日誌裡的 CFL-02（首次升 Core）決策。「Watchlist 異動」只能看到 CFL-02 這一種——`company.universe` 不是 Bitemporal，一般 Watchlist↔Adjacent 移動沒有歷史可查，頁面／文件明講這個限制，不是漏掉 |
| R02 | `company_event_report.py` | tier 依事件 `materiality_score` 分流；Material Review 時檢查事件自己的 `cfl_status` |
| R03 | `dashboard.py` | 即時查 `seco_score`／`cmi_score` 當前 Bitemporal 版本（`valid_to IS NULL`），不落地 |
| R04 | `event_study_report.py` | 固定 Material Review；讀 `valuation_event_window`（M06），沒有任何窗口資料就拒絕（不可能生成一份沒有 CAR 數字的「CAR 報告」） |
| R05 | `comparison_report.py` | CFL-06 治理殼——A05（比較分析代理）還沒真正產生內容（WBS-B6 仍是 `NotImplementedError`），本模組只負責 report 列建立＋CFL-06 提交，`content_ref` 完全是呼叫端給什麼就存什麼，不在此處捏造內容 |
| R06 | `external_publication.py` | CFL-08 治理殼＋`approve_external_publication` |

`reports/_common.py`：`maybe_advance_event_to_published`——R02／R04／R05／R06 發布成功後，若對應 Event 剛好停在 `APPROVED`，順手推進到 `PUBLISHED`（Work-2 §3.2："PUBLISHED — G06／R01–R06"，這條連結本來就該接上）；Event 不在 `APPROVED` 就不動它，不強迫狀態機跳轉。

## 4. API（`src/api/app.py`，`ADR-0021` 的 6 個 501 全部換成真實邏輯）

- `GET /dashboard/seco-cmi` → R03 即時查詢
- `GET /reports/{report_id}` → 泛用查詢，回傳任一 `research_report` 列（主要給 R01／R02 用）
- `GET /event-studies/{event_id}`（注意路徑參數是 **event_id**，不是 report_id）→ 該事件全部 `valuation_event_window`＋（如果有）對應的 R04 report 列
- `GET /comparisons/{comparison_id}` → 限定 `report_type == COMPARISON`，型別不符視同不存在（404，不洩漏其他類型 report 的存在）
- `POST /publications/{id}/approve` → `approve_external_publication`

`GET /exports` 維持 501——它是「R01–R06 匯出格式」本身的設計，不是任何一個 R 模組能接上的邏輯，留待後續。

## 5. 驗收

- `research_report` repository CRUD＋CFL guard trigger（`tests/integration/test_research_report_db.py`）。
- R01／R03（Internal Auto，無需 CFL 閘門）（`tests/integration/test_reports_internal_auto.py`）。
- R02／R04（依底層 Event 自己的 cfl_status 判斷是否放行；事件未核准時擋下 `PublicationBlocked`）（`tests/integration/test_reports_material_review.py`）。
- R05／R06（CFL-06／CFL-08 全流程，含 `approve_external_publication` 連帶把 Event 推到 PUBLISHED）（`tests/integration/test_reports_cfl_gated.py`）。
- 上述 6 個 API 端點的真實回應與 404／403 分支（`tests/integration/test_api_reports_endpoints.py`）。

本地驗證：新鮮 venv，`ruff check .`／`ruff format --check .`／`mypy src`（strict，62 檔案）／`pytest`（345 unit passed；103 integration/migration skipped，本機無 `DATABASE_URL`）；`alembic upgrade head --sql`／`downgrade --sql head:base` 皆完整渲染至 `0007_research_report`。

## 6. 待確認 / 後續

1. R05 的實際比較分析內容（A05 candidate 產生）仍待 A05 開工；本批只交付治理殼。
2. `content_ref`／I02 物件儲存客戶端從未真正建置——`source_snapshot.snapshot_ref` 與 `research_report.content_ref` 都還是空掛勾點，留待需要真正匯出/渲染報告檔案時一併設計。
3. `GET /exports` 之匯出格式設計——U05 剩餘範圍，非 R 模組本身。
4. Work-3 之後：**B12**（Tests／Hardening——跨模組整合測試、E2E 每日管線測試、CFL 全流程測試、負載與異常演練；B0–B11 全部完成後的最後一批）。
