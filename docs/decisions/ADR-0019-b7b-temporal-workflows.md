# ADR-0019 — WBS-B7b：W03 Fan-out/Fan-in + W04 每日管線 + W05 重試/逾時（Temporal）

- 狀態：**ACCEPTED（B7b 實作決議）**
- 日期：2026-09-12
- 核可：Research Director／Executive User（隨 B7b PR 審閱）
- 來源：Work-3 WBS-B7（W03/W04/W05；I04 部署）、Charter §26.3（每日管線階段）、§22（Auditability，可重試可追蹤）、SOP 步驟 12；`ADR-0001` §2（I04=Temporal）、`ADR-0018` §1（B7a/B7b 拆分理由）

---

## 1. 範圍與驗證方式（風險說明）

本批是第一次真正引入 Temporal（`temporalio`）程式碼，跟先前所有批次（純 SQLAlchemy／純函式）性質不同：Workflow 程式碼有**確定性限制**（不可用 `datetime.now()`／未播種亂數等），且完整驗證需要 Temporal test server。

**驗證策略**：
1. 商業邏輯（各階段實際要做的事）一律寫成**一般同步／非同步函式**，可直接單元測試，不需 Temporal runtime。
2. Workflow／Activity 只是這些函式的**薄包裝**（`@workflow.defn`／`@activity.defn`），本身不含邏輯。
3. 新增 `tests/test_workflows_temporal.py`（`@pytest.mark.temporal`），用 `temporalio.testing.WorkflowEnvironment.start_time_skipping()` 做**真正**的 workflow 執行測試；**若環境無法啟動（例如 CI runner 無法下載 test server 執行檔），測試自動 skip 而非 fail**，避免重演先前 CI 反覆失敗的狀況。此為**本 repo 第一次**用這個 marker，先觀察 CI 實際能否啟動，再決定是否值得投資更完整的 Temporal CI（例如專用 job）。

## 2. W03 — Fan-out／Fan-in 編排器（`src/workflows/fanout.py`）

`FanOutFanInWorkflow`：接收 `FanOutItem`（`activity_name` + `args`）清單，以 `asyncio.gather` 平行 `workflow.execute_activity`（按 W05 之 `RetryPolicy`）後回傳結果清單——SOP 步驟 12「選定 N 個對象平行處理後匯流」之通用實作，**不知道**扇出的是什麼工作（呼叫端決定 activity）。

## 3. W05 — 重試／逾時（`src/workflows/retry_policy.py`）

`retry_policy_for(*, max_attempts=5, initial_interval_seconds=1.0) -> RetryPolicy`：指數退避（係數 2.0，上限 5 分鐘）。**「重試不重複寫入」已由既有模組的冪等設計保證**，非本 ADR 新發明：P03 `record_snapshot`（source_id+content_hash 唯一）、CFL `set_status`（狀態機驗證非法轉換）、Event Revision Chain（只認目前 head）皆天生冪等或會在重複呼叫時報錯而非產生髒資料。W05 只負責重試排程本身。

## 4. W04 — 每日研究管線工作流（`src/workflows/daily_pipeline.py`，骨架）

`DailyResearchPipelineWorkflow` 依 Charter §26.3 循序呼叫各階段 activity：`discover → fetch → normalize → extract → verify → analyze → approve → publish`。**與 A01–A08 骨架（`ADR-0017`）同樣立場**：能對應到既有已完成模組的階段（`fetch`→P01 `fetch_and_register`、部分 `normalize`→P04/P06）給出真實呼叫；`extract`（A01 LLM）等需要產品設計（prompt／schema）之階段维持 `NotImplementedError`，**不假裝完成**。本批交付管線**骨架與階段順序**，不是可上線運作的每日管線。

## 5. 驗收

- `retry_policy_for`：不同輸入產生正確 `RetryPolicy` 欄位。
- Fan-out 之扇出/扇入邏輯：以純 Python（不經 Temporal）測試 `FanOutItem`／`FanOutRequest` 資料結構正確性；實際平行執行行為交給 `test_workflows_temporal.py`（見 §1，可能 skip）。
- 管線階段函式：能對應既有模組者直接單元測試；`NotImplementedError` 階段測試其明確拋錯而非靜默通過。

## 6. 待確認 / 後續

1. Temporal 自架 vs Cloud（ADR-0006 G4-10，仍待部署階段）。
2. `test_workflows_temporal.py` 若在 CI 持續 skip（環境無法啟動），需評估是否投資自架 Temporal test service 或改用其他驗證手段。
3. W04 之 `extract`／`analyze`（A01–A06 LLM 呼叫）待產品設計完成後補上真實 activity。
4. Work-3 之後：B8（治理層完整版——G01 CFL 規則引擎、G03 稽核日誌、G06 發布狀態機、G07/G08）。
