# ACCEPTANCE_TESTS.md — WBS-B12 驗收對照表

依 Work-3 §4（Acceptance Tests 大綱）逐項列出：測試內容、依據、對應本 repo 的實際測試檔案／函式、狀態。本文件是 Work-2 §12／Work-3 §0 要求的 `ACCEPTANCE_TESTS.md` 交付物，於 WBS-B12（`docs/decisions/ADR-0024-b12-acceptance-hardening.md`）產出，作為 B0–B11 全部完成後回 Projects 驗收的依據。

**執行方式**：`make check`（`ruff check . && ruff format --check . && mypy src`）＋ `pytest -m "not integration and not migration"`（含 `temporal` 標記測試，可能因環境無 Temporal test server 而 skip，見下方 TEST-WF-01 備註）＋ `pytest -m integration`（需 `DATABASE_URL`）＋ `pytest -m migration` 並 `alembic upgrade head && alembic downgrade base && alembic upgrade head`。

---

| 測項編號 | 測試內容 | 依據 | 對應測試 | 狀態 |
|---|---|---|---|---|
| TEST-DATA-01 | K01–K06 各實體之欄位命名、型別與 DATA_MODEL.md 完全一致，無同義異名欄位 | Work-2 §2 | `tests/test_schema_contract.py::test_contract_columns_present`（含 `research_report`／`audit_log` 等 §2.9-style 補充表） | ✅ PASS |
| TEST-DATA-02 | 缺失之 `occurred_at`／`published_at`／`market_known_at` 等時間欄位保持 NULL，未被虛假精度填補 | CF-21；GP-07 | `tests/test_schema_contract.py::test_observed_time_missing_stays_null`；`tests/integration/test_acceptance_evidence_traceability.py`（`source_credibility_tier` 缺失時保持 `None`，同一精神） | ✅ PASS |
| TEST-EVENT-01 | 事件狀態機僅能依 DISCOVERED→...→PUBLISHED 順序推進，非法跳轉須被拒絕 | Work-2 §3.2 | `tests/integration/test_event_pipeline_status.py::test_sequential_advance_is_allowed`／`test_skipping_a_stage_is_rejected`／`test_going_backward_is_rejected`；E2E 全流程見 `tests/integration/test_acceptance_e2e.py` | ✅ PASS |
| TEST-EVENT-02 | K05 Event 為 Immutable：CORRECTED／SUPERSEDED 狀態變更以新 revision 寫入，不覆寫原始事件 | CF-35/36 | `tests/integration/test_relationship_event_evidence.py::test_correct_event_preserves_old_row_data`／`test_withdraw_event_creates_new_revision_same_data`／`test_list_revision_chain_order` | ✅ PASS |
| TEST-CFL-01 | CFL-07 矛盾資料（CONTRADICT Evidence）不得被系統自動核准（Auto-pass） | Work-2 §5 | `tests/integration/test_cfl_rules_db.py::test_cfl07_never_auto_passes_even_with_high_confidence`；`tests/integration/test_relationship_event_evidence.py::test_record_contradiction_raises_cfl07` | ✅ PASS |
| TEST-CFL-02 | CFL-08 未通過人工核准前，事件無法進入 PUBLISHED 狀態 | CF-33；G06 | `tests/integration/test_event_pipeline_status.py::test_external_approval_publish_blocked_without_cfl08_approved`／`test_external_approval_publish_allowed_once_cfl08_approved`；`tests/integration/test_reports_cfl_gated.py::test_approve_external_publication_moves_to_approved_and_publishes_event` | ✅ PASS |
| TEST-CFL-03 | 任一模組嘗試繞過 G01 直接寫入 `cfl_status` 須被拒絕 | Work-2 §5.2 | `tests/integration/test_ingestion_db.py::test_cfl_status_direct_write_blocked`／`test_cfl_status_write_via_guard_ok`；`tests/integration/test_research_report_db.py::test_cfl_status_direct_write_blocked` | ✅ PASS |
| TEST-RBAC-01 | 任一 Agent／使用者角色不得同時擁有 Evidence 寫入與 Approval／Publication 權限 | GP-21；G02/G05 | Agent 側：`tests/test_rbac.py::test_real_roster_is_gp21_compliant`／`test_no_agent_holds_approval_or_publication`；人類角色側：`tests/test_rbac_matrix.py::test_no_role_holds_both_evidence_write_and_approval_publish` | ✅ PASS |
| TEST-CMI-01 | M04 CMI 計算不得使用尚未達 availability time 的未來資料（No Future Data） | GP-08；CF-26 | `tests/integration/test_seco_cmi_db.py::test_record_cmi_score_rejects_future_data`；`tests/test_cmi.py`（純函式門檻測試） | ✅ PASS |
| TEST-PIT-01 | M07 市值計算使用對應時間點之 Point-in-Time Shares Outstanding，而非目前最新值 | CF-24 | `tests/integration/test_materiality_marketcap_db.py::test_pit_market_cap_uses_each_dates_own_shares_outstanding` | ✅ PASS |
| TEST-VER-01 | Seco／CMI／Materiality／Confidence 任一模型權重變更須產生新 Model Version，不得覆寫既有結果 | GP-10；G04 | `tests/integration/test_seco_cmi_db.py::test_record_and_correct_seco_score_preserves_old_row`／`test_record_and_correct_cmi_score_preserves_old_row`（`correct_*` 只改 `valid_to`，新開一列） | ✅ PASS |
| TEST-EVID-01 | Evidence 之 `evidence_type`（SUPPORT／CONTRADICT／NEUTRAL-CONTEXT）與 `source_credibility_tier`（S1–S5）皆有值且可追溯至 `content_hash` | CF-07/08/11 | `tests/integration/test_acceptance_evidence_traceability.py::test_evidence_type_tier_and_content_hash_are_all_populated_and_traceable`／`test_untiered_source_leaves_tier_none_not_guessed` | ✅ PASS |
| TEST-WF-01 | W05 重試／逾時工作流：模擬下游失敗後可正確重試且不重複寫入 | Charter §22 Auditability | 重試機制（真實 Temporal 執行）：`tests/test_acceptance_workflow_retry.py::test_workflow_retries_a_failing_activity_until_it_succeeds`；不重複寫入：`tests/integration/test_acceptance_idempotent_writes.py::test_retried_snapshot_write_does_not_duplicate` | ✅ PASS（`temporal` 標記測試在無 Temporal test server 的環境會 skip 而非 fail，見 `ADR-0019` §1；本機／CI 若能啟動則為真實執行） |
| TEST-API-01 | 第 4.2 節所列端點回應皆含 `version` 與 `cfl_status` 欄位；4xx 錯誤含統一 `error_code` 格式 | Work-2 §4 | `tests/integration/test_acceptance_api_contract.py`（全端點掃描）；個別端點：`tests/integration/test_api_endpoints.py`、`tests/integration/test_api_reports_endpoints.py` | ✅ PASS（Company 無 `version` 欄位為 Event-only 之既有事實，見 `ADR-0021` §1，非缺陷） |
| TEST-E2E-01 | 完整跑一次每日研究管線（Discover→...→Publish），Completion Report 與各測項結果一併送回 Projects 驗收 | SOP 第四節 | `tests/integration/test_acceptance_e2e.py::test_full_daily_pipeline_discover_to_publish` | ✅ PASS（A01 LLM 抽取階段無真實實作，以直接建構 Evidence 列模擬——見該測試檔案 docstring 與 `ADR-0024` §3） |

---

## 已知限制（誠實揭露，非本批新缺口）

- **A01–A06（LLM-based Agent）尚無真實實作**：`agents/roster.py` 所有具體 Agent 仍為 `NotImplementedError`（WBS-B6 決議，`ADR-0017`）。TEST-E2E-01 因此在 EXTRACTED 階段以直接建構 Evidence 列模擬 A01 產出，其餘階段（P/K/M/G/R）皆為真實程式碼串接。
- **負載測試（Load Testing）**：本專案未部署 I01–I06 基礎設施，無法進行真正的併發／吞吐量測試；B12 僅交付「異常演練」（`tests/integration/test_acceptance_exception_drill.py`：被拒絕的治理操作不留下部分寫入、session 仍可正常使用）。真正的負載測試待實際部署後另行規劃（`ADR-0024` §4）。
- **`GET /exports`**：U05 匯出格式設計本身（非任何 R 模組）維持 501，非 TEST-API-01 涵蓋範圍內的迴歸。
