# ADR-0015 — WBS-B5c：M05 Materiality 評分器 + M07 PIT 市值計算器

- 狀態：**ACCEPTED（B5c 實作決議）**
- 日期：2026-09-12
- 核可：Research Director／Executive User（隨 B5c PR 審閱）
- 來源：Work-3 WBS-B5（M05／M07）、Charter §15（CF-27/28）、§14.3（CF-24）、GP-12；`ADR-0004`（CFL-04 分工：M05 算分/raise、A04 建議、G01 判定）
- 影響：`src/models/materiality.py`、`src/models/market_cap.py`。無新表、無 migration（沿用 B1 `event.materiality_score`、`market_data.close_price/shares_outstanding`）。

---

## 1. 範圍

B5（8 模組）第三批：M05、M07。

## 2. M05 — Materiality 評分器（Charter §15）

Charter 給了考量因子（CPO Relevance／Evidence Strength／Commercial Impact／Ecosystem Impact／Novelty）但**未凍結權重**（「V1 採 Expert Rule」，跟 M02 Confidence 同款不完整）。

**本 ADR 權重（實作慣例，非 Frozen Decision，可調整）**：

| 因子 | 權重 |
|---|---|
| CPO Relevance | 0.25 |
| Evidence Strength | 0.25 |
| Commercial Impact | 0.20 |
| Ecosystem Impact | 0.20 |
| Novelty | 0.10 |

`compute_materiality(factors: MaterialityFactors) -> float`：五因子（皆 `[0,100]`）加權和，結果 `[0,100]`。

`score_event_materiality(session, event, factors, *, cfl_service=default_cfl_service) -> CflStatus`：寫入 `event.materiality_score`，經 G01 提交 **CFL-04** 候選（沿用 `ADR-0004` 決策 1 之模式：M05 算分並 raise，A04（B6）給 Recommendation，G01 判定；B1 樁下一律 `PENDING`）。

**GP-12（Materiality ≠ Truth）**：本模組只產生分數，**不**因高分而自動變更 `lifecycle_status`／`cfl_status` 以外的任何欄位；「Event ≠ Material Event」由既有 `cfl_status` 狀態機（CFL-04 通過與否）區分，本 ADR 不另建欄位。

## 3. M07 — Point-in-Time 市值計算器（Charter §14.3，CF-24）

`MarketCap(i,t) = Price(i,t) × SharesOutstanding(i,t)`，**必須用該筆 `market_data` 列自己的 `shares_outstanding`**，不得以「目前最新股本」回算歷史市值。

**架構性防呆**（非僅文件警告）：`compute_market_cap_for_date(session, *, company_id, trade_date)` 只讀取 **該 `company_id`＋`trade_date`（`valid_to IS NULL` 現行版）那一筆 `market_data` 列**的 `close_price`／`shares_outstanding` 一起計算——`shares_outstanding` 永遠跟該筆歷史列的日期綁在一起，結構上不可能誤用「最新股本」。任一欄位缺值回傳 `None`（不得猜測）。

## 4. 驗收

- M05：`compute_materiality` 加權正確、越界拋錯；`score_event_materiality` 寫入分數並提交 CFL-04（`PENDING`，B1 樁）。
- M07：`compute_market_cap` 純函式；`compute_market_cap_for_date` 對**兩個不同交易日、不同股本**的歷史列分別算出正確市值（證明不會用錯股本，CF-24 核心驗收）；缺值回 `None`。
- M05 為 DB-backed（integration，需寫 `event`）；M07 純公式為單元測試，`_for_date` 查詢為 integration 測試。

## 5. 後續

B5d（B5 最後一批）：M06 事件窗口／AR-CAR、M08 穩健性檢核。
