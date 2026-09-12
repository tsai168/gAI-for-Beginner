# ADR-0024 — WBS-B12：Tests／Hardening（驗收與強化，B0–B11 收尾）

- 狀態：**ACCEPTED（B12 實作決議，全案 B0–B11 收尾）**
- 日期：2026-09-12
- 核可：Research Director／Executive User（隨 B12 PR 審閱）
- 來源：Work-3 §2 DAG B12 列（"跨模組整合測試、E2E 每日管線測試、CFL 全流程測試、負載與異常演練"）、§4 Acceptance Tests 全表、§12（`ACCEPTANCE_TESTS.md` 為 Work-3 交付物）

---

## 1. 範圍

B12 是 Work-3 §2 DAG 的最後一批（"B0–B11 全部完成"才能開工），任務是**驗收**，不是新功能。交付物：`docs/ACCEPTANCE_TESTS.md`（Work-2 §12／Work-3 §0 皆要求的文件，本批首次產出）＋ 補齊先前批次未覆蓋的測項。

逐一檢視 Work-3 §4 的 15 個 TEST-XXX-NN 後，13 項已由 B1–B11 既有測試覆蓋（詳見 `docs/ACCEPTANCE_TESTS.md` 對照表，不重複建置）；genuinely 缺的只有 **TEST-WF-01**（重試/不重複寫入）與 **TEST-E2E-01**（完整每日管線），本批補上；另外 B12 自己要求的「跨模組整合測試」由 TEST-E2E-01 本身承擔（一次串接 P/K/M/G/R 五層已經就是跨模組整合測試，不另建重複的測試檔案），「負載與異常演練」以誠實縮小範圍的方式交付（見 §4）。

## 2. TEST-WF-01 拆成兩個測試檔案的理由

「模擬下游失敗後可正確重試」需要真的 Temporal test server；「不重複寫入」需要真的 Postgres。這個 repo 目前**沒有任何一個 CI job 同時具備兩者**（`check` job 有 Temporal 環境但沒有 Postgres service；`integration` job 有 Postgres 但沒特別為 Temporal 準備）。與其為了單一測試新增一個「兩者都要」的 CI job，拆成兩個各自獨立、各自真實驗證的測試更合理：

- `tests/test_acceptance_workflow_retry.py`（`@pytest.mark.temporal`）：一個會失敗兩次、第三次才成功的 activity，包在用 W05 `retry_policy_for` 設定的 workflow 裡，透過 `WorkflowEnvironment.start_time_skipping()` **真的執行**並驗證重試次數與最終結果——同 B7b 的一貫作法，環境不支援時 skip 不 fail（`ADR-0019` §1）。本機驗證時**真的執行成功**（1 passed，非 skip）。
- `tests/integration/test_acceptance_idempotent_writes.py`：直接呼叫 P03 `record_snapshot`（既有的冪等寫入實作，`source_id + content_hash` 唯一）兩次，驗證回傳同一列、DB 只有一列——這就是「重試後不重複寫入」在資料庫層面的真實驗證，不需要真的透過 Temporal 重試才能證明。

## 3. TEST-E2E-01：A01 是唯一模擬的一步

`tests/integration/test_acceptance_e2e.py` 串接 DISCOVERED→...→PUBLISHED 全部八個階段，除了 EXTRACTED（A01 LLM 抽取，WBS-B6 尚無真實實作，`agents/roster.py` 仍是 `NotImplementedError`）之外，每一步都呼叫**真正的** production 函式：P01 `fetch_and_register`、P04 `normalize_observed_time`、P05 `score_evidence_credibility`（+ CFL-03）、M05 `score_event_materiality`（+ CFL-04）、G01 人工核准、R02 `publish_company_event_report`（+ G06 閘門，順帶把 Event 推到 PUBLISHED——`ADR-0023` §3 的那個環）。EXTRACTED 階段直接建構 A01 理論上會產出的 Evidence 列，而非假裝呼叫一個不存在的模組。

## 4. 「負載與異常演練」的誠實範圍

本專案從未部署 I01–I06（CLAUDE.md §2：基礎設施層，部署設定／docker-compose／CI，與應用程式層分開）；沒有任何實際跑起來的服務可以做真正的併發／吞吐量負載測試。硬做一個假的「負載測試」（例如在單一 pytest 行程裡開多個執行緒打同一個 SQLite/Postgres）只會產出一個測不出任何真實負載特性的假象。

因此 B12 對這一項的交付誠實縮小為**異常演練**：`tests/integration/test_acceptance_exception_drill.py` 驗證「被拒絕的治理操作（非法 CFL 轉移、缺 AR/CAR 資料的發布請求）不會留下部分寫入，session 在被拒絕後仍可正常進行下一個合法操作」——這是本專案在沒有部署基礎設施前提下，能誠實驗證的韌性層面。真正的負載測試留待實際部署（Deferred，`Work-1 §8`／`Charter §29` 精神延續）。

## 5. TEST-API-01／TEST-EVID-01 補上的「橫向掃描」測試

前 11 批已經對每個端點／Evidence 欄位個別測試過，但沒有一份**橫向**檢查「所有端點都遵守同一份契約規則」的測試。B12 補上：

- `tests/integration/test_acceptance_api_contract.py`：掃過 Company／Event 兩種回應形狀（分別驗證有無 `version` 欄位符合 ADR-0021 §1 的既有事實）、CFL 決策回應、以及六個端點的 404 是否都帶統一格式的 `error_code`。
- `tests/integration/test_acceptance_evidence_traceability.py`：`evidence_type`／`source_credibility_tier`／`content_hash` 三者同時到位且可追溯，含「未知來源保持 `None`、不猜測」（GP-07）的反例。

## 6. 驗收

本地驗證（新鮮 venv）：`ruff check .`／`ruff format --check .`／`mypy src`（strict，62 檔案，無變動——B12 不改 `src/`，純測試與文件）／`pytest`：346 passed（含 `test_acceptance_workflow_retry.py` 在本機**真實執行**通過，非 skip）、116 integration/migration skipped（本機無 `DATABASE_URL`）。`alembic upgrade head --sql` 不變（B12 無新 migration）。

`docs/ACCEPTANCE_TESTS.md` 逐項列出 Work-3 §4 全部 15 項測項的覆蓋位置與狀態，供 Projects 最終驗收使用。

## 7. 後續

Work-3 §2 DAG 的 B0–B12 全部完成。後續非本批範圍、留待 Projects 決定是否／何時展開：

1. A01–A06 LLM 整合（真正的 Agent 實作）。
2. I01–I06 部署基礎設施（含真正的負載測試環境）。
3. U05 匯出格式設計（`GET /exports` 目前仍 501）。
4. `research_report.content_ref`／I02 物件儲存客戶端（目前仍是掛勾點，`ADR-0023` §1）。
5. OIDC 登入流程（前端 `TokenInput` 目前是誠實的過渡方案，`ADR-0022` §3）。
6. ESLint／`package-lock.json`（前端工具鏈的兩個已知待補項，`ADR-0022` §1／§5）。
