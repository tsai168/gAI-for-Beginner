# ADR-0018 — WBS-B7a：W01 Wake-up Window + W02 Priority Trigger Queue + W06 Batch AI Gate

- 狀態：**ACCEPTED（B7a 實作決議）**
- 日期：2026-09-12
- 核可：Research Director／Executive User（隨 B7a PR 審閱）
- 來源：Work-3 WBS-B7（W01／W02／W06 部分）、Charter §19（Hybrid Monitoring + Batch AI Parsing）、§29（Deferred Items）、GP-16（Deterministic First）；`ADR-0009`（P02 dedup）、`ADR-0015`（M05 materiality）
- 影響：新增 `src/workflows/wakeup.py`（W01）、`priority_queue.py`（W02）、`batch_gate.py`（W06）。無新表、無 migration。

---

## 1. 範圍與批次拆分

Work-3 WBS-B7 = W01–W06 + I04 部署，八項。依 CLAUDE.md §8 拆為：

- **B7a（本 ADR）**：W01、W02、W06 —— 三者皆是**確定性（L0）決策／佇列邏輯**，不需要 Temporal runtime 就能完整撰寫與測試。
- **B7b（後續 ADR）**：W03（Fan-out/Fan-in）、W04（每日管線）、W05（重試/逾時）+ I04 實際部署 —— 這三個**需要真正的 Temporal workflow/activity 語法與（至少）time-skipping test server** 才能有意義地驗證。在動手之前，需先確認：(a) `temporalio` 套件在 CI 的 `uv sync` 下能正確安裝、(b) `mypy`／`ruff` 對 Temporal 的裝飾器語法相容、(c) CI 是否要新增一個跑 `temporalio.testing.WorkflowEnvironment` 的 job（需要對外網路下載 test server 執行檔，需先確認 GitHub Actions runner 允許）。**避免在無法本機驗證的情況下連續推測試失敗的 commit**（比照先前 base.py／migration 事故之教訓）。

## 2. W01 — Wake-up Window（Charter §19／§29 Deferred 掛勾點）

`WakeupWindow(start: time, end: time)`（`end < start` 視為跨午夜）；`is_within_wakeup_window(now, windows) -> bool`。**本模組不提供任何預設時間**——23:00／06:00 僅為 Charter 候選值、非 Frozen（Charter §29），呼叫端必須從設定／環境變數注入實際窗口，CLAUDE.md §4 明文禁止把 Deferred 參數寫死。

## 3. W02 — Priority Trigger Queue（Charter §19）

`Priority`（`LOW`／`NORMAL`／`HIGH`，L0 確定性排序，非研究判斷）。

`classify_priority(*, materiality_score, dedup_verdict)`：
- `dedup_verdict != NEW`（P02 已判定為重複內容）→ `LOW`（無需優先處理，甚至無需處理）。
- `materiality_score >= 70`（**實作預設門檻，非 Charter 凍結值**，可調整）→ `HIGH`，重大事件優先進 Batch AI Parsing。
- 其餘 → `NORMAL`。

`PriorityTriggerQueue`：以 `heapq` 實作之優先佇列（`HIGH` 先出，同優先序依先進先出，`itertools.count()` 序號打破平手，避免比較 payload）。

## 4. W06 — Batch AI Parsing 閘門（Charter §19，GP-16 Deterministic First）

`evaluate_batch_gate(*, dedup_verdict, within_wakeup_window, priority) -> BatchGateDecision(should_call_llm, reason)`——**唯一** 決定「是否呼叫 LLM」的入口，彙整 P02（去重）、W01（時窗）、W02（優先序）三者：

| 條件 | 結果 |
|---|---|
| `dedup_verdict != NEW` | 不呼叫（確定性去重已足夠，GP-16） |
| `priority == HIGH` | 呼叫（重大事件優先，繞過時窗——Charter §19 Priority Trigger 精神） |
| 不在時窗內（且非 HIGH） | 不呼叫 |
| 其餘（新內容、在時窗內） | 呼叫 |

## 5. 驗收

- W01：跨午夜／不跨午夜視窗、邊界值（含端點）、多視窗聯集、`None` 視窗清單一律 `False`。
- W02：三種 Priority 分類正確、`PriorityTriggerQueue` 先進先出＋優先序、`HIGH` 一律先於 `NORMAL`/`LOW` 出列。
- W06：四種決策路徑之真值表全覆蓋，`reason` 訊息可讀。
- 全為純 Python 單元測試，不需 DB／Temporal。

## 6. 後續

B7b：W03／W04／W05＋I04 部署（見 §1 之前置確認事項）。
