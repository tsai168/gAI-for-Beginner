# ADR-0014 — WBS-B5b：M03 Seco 引擎 + M04 CMI 引擎（含 §2.9 輸出表）

- 狀態：**ACCEPTED（B5b 實作決議）**
- 日期：2026-09-12
- 核可：Research Director／Executive User（隨 B5b PR 審閱）
- 來源：Work-3 WBS-B5（M03／M04；驗收關卡「M04 CMI 無 backward filling（GP-08）」）、Charter §12（Seco，CF-12～17）、§13（CMI，CF-18／19）、GP-08／GP-09／GP-10；`ADR-0003`（§2.9 表結構）、`ADR-0011`（K02 bitemporal open/close 模式沿用）
- 影響：`knowledge/db/models.py`（+`SecoScore`／`CmiScore`）、migration `0004`、`src/models/seco.py`、`src/models/cmi.py`。

---

## 1. 範圍

B5（8 模組）第二批：M03、M04。建 `seco_score`／`cmi_score`（ADR-0003 已定欄位，本 ADR 落地）。純新表，不改既有表欄位，不觸發 `ADR-0013` §0 之風險。

## 2. M03 — Seco 引擎（Charter §12，權重為 Frozen Decision CF-13）

`compute_seco(*, tech_relevance, product_readiness, customer_validation, ecosystem_position, commercialization, strategic_defensibility) -> float`：**逐字**採用 Charter 凍結權重 `0.15/0.15/0.20/0.20/0.20/0.10`；六個輸入須落在 `[0,100]`（Charter §12 尺度），否則 `ValueError`。

`seco_band(score) -> str`：Charter §12 五段（`0–19 Minimal/Insufficient`；`20–39 Emerging`；`40–59 Developing`；`60–79 Established`；`80–100 Strong`）。

**Bitemporal 讀寫**（沿用 `ADR-0011` §3 K02 的 open／close 模式）：
- `record_seco_score(session, *, company_id, as_of, dims, confidence, model_version_id, valid_from) -> SecoScore`：`confidence` **必填**（CF-15「Seco 必須伴隨 Confidence」），`valid_to=NULL`（目前有效版本）。
- `correct_seco_score(session, old, *, dims, confidence, model_version_id, valid_from)`：先 `close`（`old.valid_to = valid_from`，其餘欄位不動）再 `record` 新列——**不覆寫**（CF-17／GP-10：新權重／新分數必須是新 Model Version 之新列）。

## 3. M04 — CMI 引擎（Charter §13，V1 等權 CF-19）

`compute_cmi(*, foreign_inst_momentum, domestic_inst_momentum, margin_short, ownership_concentration, trading_structure) -> float`：五構面等權 20%；輸入須 `[0,100]`。

**GP-08／GP-09 No-Future-Data 強制關卡（本批驗收核心）**：`assert_no_future_data(as_of, availabilities)`——每個構面須附其**資料可取得時間**（`available_at`，接 B1 `market_data`／`institutional_trading`／`shareholding` 之同名欄位）；任一構面 `available_at is None` 或 `available_at > as_of` 一律 `FutureDataError`（拒絕計算，不是拒絕寫入——**計算階段就擋，不給任何機會 backward fill**）。`compute_cmi_guarded(*, as_of, dims, availabilities)` = 先檢查再算分，唯一對外建議入口。

**CMI 不強制 `confidence`**（Charter 只對 Seco 明文要求 CF-15，CMI 無對應條文；ADR-0003 之 `cmi_score` 欄位表本就未列 `confidence`）。其餘（bitemporal open/close、`model_version_id` 必填）與 M03 對稱：`record_cmi_score`／`correct_cmi_score`。

## 4. `seco_score`／`cmi_score` Schema（沿用 ADR-0003，本 ADR 落地）

兩表皆：`*_score_id`(PK)／`company_id`(FK)／`as_of`／`score`／各自構面欄位／`valid_from`／`valid_to`／`model_version_id`(**NOT NULL**，FK→`model_version`)／`created_at`／`updated_at`。`seco_score` 額外 `confidence`(NOT NULL)；`cmi_score` 不含 `confidence`。索引 `(company_id, as_of)`。

## 5. 驗收

- M03：`compute_seco` 精確權重、越界拋錯、`seco_band` 五段邊界；bitemporal open/close 不覆寫舊列。
- M04：`compute_cmi` 等權；**`assert_no_future_data`／`compute_cmi_guarded` 對「缺 available_at」與「available_at 晚於 as_of」兩種情境皆拒絕**（此為 WBS-B5 驗收關卡逐字對應）。
- 純公式與 guard 為單元測試；DB 讀寫（record／correct）為 integration 測試。

## 6. 待確認 / 後續

1. 六個 Seco 構面分數（`tech_relevance` 等）、五個 CMI 構面分數之**輸入來源**（誰算出 0–100 的原始構面值）不在 M03／M04 範圍——那需要對 K01–K06／`market_data` 等原始資料做更細的特徵工程，屬 A04（B6）或後續模組；M03／M04 只做「已知構面分數 → 加權組合＋治理」。
2. B5c：M05 Materiality、M07 PIT 市值。B5d：M06 事件窗口／AR-CAR、M08 穩健性檢核。
