# ADR-0016 — WBS-B5d：M06 事件窗口／AR-CAR + M08 穩健性檢核（B5 收尾）

- 狀態：**ACCEPTED（B5d 實作決議）**
- 日期：2026-09-12
- 核可：Research Director／Executive User（隨 B5d PR 審閱）
- 來源：Work-3 WBS-B5（M06／M08）、Charter §14.1（Event Window，CF-20）、§14.2（AR/CAR，CF-23）、§14.3（CF-24，銜接 M07）、§14.4（Time Quality Robustness Check）、GP-06
- 影響：`knowledge/db/models.py`（+`ValuationEventWindow`）、`knowledge/db/base.py`（+`BenchmarkModel` enum）、migration `0005`、`src/ingestion/trading_calendar.py`（新增 `previous_trading_day`／`trading_days_around`，P06 既有模組的相容擴充）、`src/models/event_window.py`、`src/models/robustness.py`。

---

## 1. 範圍（B5 最後一批）

M06、M08。完成後 M01–M08 全數到位。

## 2. `valuation_event_window` Schema（沿用 ADR-0003，本 ADR 落地並明確化型別）

ADR-0003 原列「`ar`、`car`」兩欄但未定型別。本 ADR 明確化：

| 欄位 | 型別 | 說明 |
|---|---|---|
| `valuation_event_window_id` | uuid PK | |
| `event_id` | uuid FK→`event` | |
| `window_pre`／`window_post` | int | `[-N,+M]` 之 N／M（Charter §14.1） |
| `benchmark_model` | enum（`MARKET_ADJUSTED`／`MARKET_MODEL`） | Charter §14.2，非原生 enum（ADR-0007 §2 一致做法） |
| `ar_series` | jsonb（float 陣列，依 `trading_days_around` 順序） | 逐日 AR，非單一純量——ADR-0003 之 `ar` 欄本 ADR 明確為陣列 |
| `car` | numeric | `Σ ar_series`（Charter §14.2） |
| `market_cap` | numeric，nullable | t=0 之 PIT 市值（M07，CF-24），缺值時 `NULL`（不猜） |
| `model_version_id` | uuid FK→`model_version`，**NOT NULL** | GP-10：Benchmark Model Version 必須隨結果 |
| `created_at`／`updated_at` | timestamptz | |

無 `valid_from`／`valid_to`——事件窗口結果依 `event_id`＋`benchmark_model`＋`model_version_id` 識別一次性計算，修正時之「不覆寫」由 **新增一列**（新 `model_version_id`）保證（GP-10），不需 Bitemporal 開闔機制。

## 3. M06 — 事件窗口／AR-CAR 引擎

### 3.1 視窗建構（沿用並擴充 P06）

`trading_calendar.trading_days_around(calendar, *, center, pre, post) -> list[date]`：以事件對齊後之 `event_trading_date`（P06 產出，t=0 保證為交易日）為中心，取 `pre` 個交易日在前、`post` 個在後（Charter §14.1 標準窗口 `[-1,+1]/[-3,+3]/[-5,+5]/[-10,+10]/[-20,+20]` 與任意 `[-N,+M]` 皆可表示為 `(pre=N, post=M)`）。週資料窗口（Charter §14.1「週資料窗口另行定義」）**不在本 ADR**，留待後續。

### 3.2 AR／CAR 計算

- `market_adjusted_ar(r_i, r_m) -> float`：`R(i,t) − R(m,t)`（Charter §14.2 逐字）。
- `estimate_market_model(r_i_est, r_m_est) -> MarketModelParams(alpha, beta)`：以**估計窗**（事件窗口以外的歷史報酬序列，呼叫端提供，本模組不自動選取估計窗——避免與事件窗口重疊之判斷屬呼叫端責任）之簡單 OLS（`beta = cov(r_i,r_m)/var(r_m)`、`alpha = mean(r_i) − beta·mean(r_m)`）估計。
- `market_model_ar(r_i, r_m, *, alpha, beta) -> float`：`R(i,t) − (α + β·R(m,t))`（Charter §14.2 逐字：AR = actual − expected）。
- `compute_car(ar_series) -> float`：`Σ AR`（Charter §14.2 逐字）。

兩種 Benchmark **皆須支援**（CF-23「至少 Market-adjusted + Market Model」），呼叫端指定 `benchmark_model` 並提供對應計算所需輸入。

### 3.3 寫入（`record_valuation_event_window`）

`record_valuation_event_window(session, *, event_id, window_pre, window_post, benchmark_model, ar_series, model_version_id, market_cap=None) -> ValuationEventWindow`：`car = compute_car(ar_series)` 自動計算，寫入一列。`market_cap` 建議由呼叫端先呼叫 M07 `compute_market_cap_for_date(event_trading_date)` 取得後傳入（本模組不重複造輪子）。

## 4. M08 — 穩健性／時間品質檢核器（Charter §14.4）

### 4.1 Time Quality 分桶（銜接 P04 `time_confidence`）

Charter 只說「可依 Time Quality 分 High／Medium／Low 樣本」，未給門檻——本 ADR 依 **P04（`ADR-0010` §2）既有 `time_confidence` 數值表**對齊分桶，門檻取自 P04 confidence 表的天然分界：

| 分桶 | `time_confidence` 條件 | 對應 P04 basis/precision |
|---|---|---|
| HIGH | `>= 0.85` | OCCURRED（DATETIME 或 DATE_ONLY） |
| MEDIUM | `>= 0.55` | PUBLISHED（DATETIME 或 DATE_ONLY） |
| LOW | 其餘（含 `None`） | RETRIEVED 保底 |

`classify_time_quality(time_confidence: float | None) -> Literal["HIGH","MEDIUM","LOW"]`。

### 4.2 Robustness Summary（實作慣例，非 Charter 逐字公式）

Charter 未規定具體統計檢定——V1 給**描述性統計 + 方向一致性**檢查：`robustness_summary(car_by_quality: Mapping[str, Sequence[float]]) -> RobustnessResult`：每桶 `mean`／`std`／`n`；`sign_consistent`：HIGH 與 MEDIUM 兩桶（皆有樣本時）平均 CAR 正負號是否相同。**正式統計檢定（如 t-test／bootstrap）留待 Phase 2**（比照 Charter 對 Seco／CMI／Confidence 之 V1→Phase 2 校準模式）。

## 5. 驗收

- M06：`market_adjusted_ar`／`market_model_ar`／`compute_car` 精確公式；`estimate_market_model` 對已知線性關係資料回歸出正確 α／β；`trading_days_around` 視窗正確；DB 寫入 `car` 自動加總、`model_version_id` 必填。
- M08：`classify_time_quality` 三桶邊界；`robustness_summary` 描述統計正確、`sign_consistent` 正反例。
- 公式／分類為單元測試；DB 寫入為 integration 測試。

## 6. B5 收尾

M01–M08 全數完成（B5a～B5d）。下一批：Work-3 WBS-B6（Agent 層，A01–A08；G02 自治權控制器、G05 RBAC）。
