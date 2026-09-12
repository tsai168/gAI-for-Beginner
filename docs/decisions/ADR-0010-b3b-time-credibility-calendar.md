# ADR-0010 — WBS-B3b：P04 時間標準化 + P05 可信度評分 + P06 交易日對齊

- 狀態：**ACCEPTED（B3b 實作決議）**
- 日期：2026-09-12
- 核可：Research Director／Executive User（隨 B3b PR 審閱）
- 來源：Work-3 WBS-B3、Charter §14.4、CF-21／CF-21A／CF-22、CF-07、GP-07；`ADR-0004`（CFL 候選/G01 樁模式）
- 影響：`src/ingestion/time_normalize.py`（P04）、`src/ingestion/trading_calendar.py`（P06）、`src/ingestion/credibility.py`（P05）。無新資料表、無 migration。

---

## 1. 範圍（B3 後半：P04／P05／P06）

延續 B3a（P01／P02）。三者皆 L0 確定性計算，不呼叫 LLM（Charter §19 Deterministic First）。

## 2. P04 — Observed-Time 標準化

輸入：`RawTimeInput(value: datetime | None, has_time_of_day: bool)`——由擷取／解析層明確告知該欄位是否只有日期（避免 P04 自行猜測精度）。

輸出 `ObservedTime`：`occurred_at／published_at／retrieved_at／market_known_at／time_basis／time_precision／time_confidence`，對應 `ObservedTimeMixin`。

**優先序（實作慣例，非 Charter 條文，可調整）**：`time_basis` 取 `occurred_at`（若有）→ `published_at`（次選）→ `retrieved_at`（保底，Required 必有值）。`market_known_at` 依 Charter §14.4「Optional／Evidence-only」保留獨立欄位，**不**參與 `time_basis` 排序。

**`time_confidence`（實作慣例，非 Charter 條文，V1 Expert Prior，可調整，比照 Charter 對 Seco／CMI／Confidence 之「V1 Expert Prior、Phase 2 校準」原則）**：

| basis／precision | confidence |
|---|---|
| OCCURRED + DATETIME | 1.00 |
| OCCURRED + DATE_ONLY | 0.85 |
| PUBLISHED + DATETIME | 0.70 |
| PUBLISHED + DATE_ONLY | 0.55 |
| RETRIEVED（保底，無 occurred／published） | 0.20 |

**硬性規則**：任何欄位缺失一律 `None`，**不**以 00:00 等虛假精度填補 DATE_ONLY 資料（Charter §14.4、GP-07）。

## 3. P06 — 交易日對齊器（Charter §14.4 逐字實作）

`TradingCalendar` 為 Protocol（`is_trading_day`／`next_trading_day`）；**具體官方交易日曆（TWSE／TPEx 假日表）Deferred**，比照 P01 具體 adapter（ADR-0009）——待 `DATA_AVAILABILITY_AUDIT`／D07 提供真實資料。本 ADR 只交付對齊演算法 + 測試用 `SetTradingCalendar`。

`align_event_trading_date()` 規則（逐字對應 Charter §14.4）：

| 情境 | 對齊結果 |
|---|---|
| 有精確時間，早於開盤（`market_open`，預設 09:00） | `t = 當日`，`basis=PRE_MARKET` |
| 有精確時間，盤中（09:00–13:30，預設收盤） | `t = 當日`，`basis=INTRADAY`，附精度受限之 `caveat` |
| 有精確時間，晚於收盤 | `t = 下一交易日`，`basis=AFTER_HOURS` |
| 有精確時間，但當日非交易日 | `t = 下一交易日`，`basis=NON_TRADING_DAY` |
| **只有日期**，無法判斷盤前／盤後 | **Conservative Alignment**：`t = 下一交易日`（不論該日期本身是否為交易日），`basis=CONSERVATIVE` |
| 完全無時間證據 | 回傳 `None`（GP-07：Unknown Time Must Remain Unknown，不得推測） |

`market_open`／`market_close` 預設 09:00／13:30（台股一般交易時段），可由呼叫端覆寫。

## 4. P05 — 來源可信度評分器（CF-07；CFL-03 候選產生模組）

- `resolve_source_tier(session, source_id) -> SourceTier | None`：`source.data_source_code → data_source.source_tier` 查表。D05／D06／D07 無固定 tier，回傳 `None`（非錯誤）。
- `score_evidence_credibility(session, evidence, *, cfl_service=default_cfl_service)`：寫入 `evidence.source_credibility_tier`，並經 G01 介面 `submit_candidate(..., cfl_id=CflId.CFL_03)` 提交候選（沿用 ADR-0004 CFL-04 模式：**P05 算分並 raise，G01 判定**；B1 樁下一律 `PENDING`，B8 補 AUTO-PASS／REVIEW-REQUIRED 規則）。
- `UnknownSourceTierError`：`source.data_source_code` 指向不存在的 `data_source` 列時拋出。因 `source.data_source_code` 有 FK 約束（ADR-0008），此路徑在正常資料下不可觸發，屬防禦性程式碼（保留供未來若移除該 FK 時使用）。

## 5. 測試策略

- **單元**（純 Python，`pytest -m "not integration and not migration"`）：P04（優先序／precision／confidence／缺值保持 None）、P06（五種對齊情境、`SetTradingCalendar`）。
- **整合**（`pytest -m integration`）：P05（真實 `data_source`／`source`／`evidence` 資料，驗證 tier 查表與 CFL-03 candidate 提交）。

## 6. 待確認 / 後續

1. `time_basis`／`time_precision`／`time_confidence` 之優先序與信心公式為**實作慣例**，非 Charter 條文；若 Research Director 要求不同排序或公式，屬「小幅調整」（Charter §7／§31），改本 ADR 即可，不需 Charter CR。
2. 真實交易日曆資料來源與載入方式 → 待 `DATA_AVAILABILITY_AUDIT` 完成、D07 taxonomy／calendar 參考庫建立後另立 ADR。
3. CF-10 之 `authority／directness／time／specificity／independence` 五項評分（Evidence 衝突判準，不同於本 ADR 之 source tier）**不在 B3b 範圍**——留待涉及矛盾分析的批次（A03／A06，B6）。
