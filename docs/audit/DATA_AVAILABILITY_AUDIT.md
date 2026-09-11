# DATA_AVAILABILITY_AUDIT — 資料來源可用性審計（B2 前置）

- 狀態：**WORKSHEET（待填）** — 每個資料集的 `earliest_reliable_date` 等欄位在**第一次實際抓取**時由執行者確認並回填；在確認前 `data_source.earliest_reliable_date` 一律 `NULL`。
- 依據：Charter CF-25（Dataset-specific Earliest Reliable Date，Charter §29 Deferred）、`docs/decisions/ADR-0005-batch-allocation.md` G4-4。
- 用途：B2（Source Registry）seed `data_source` 之依據；B3（Ingestion）擷取窗下限；M04 CMI／M06 事件研究之歷史起點。
- **原則**：本檔的「提示」欄僅為粗略公開常識，**不是決定值**；未經確認不得寫入程式碼或當作 Frozen 參數（CLAUDE.md §4）。

---

## 欄位定義（每個資料集一列）

| 欄位 | 說明 |
|---|---|
| `source_code` | D01–D08 |
| `dataset` | 具體資料集／報表名稱 |
| `access` | 存取方式（OpenAPI／CSV 下載／網頁擷取／檔案） |
| `auth` | 認證方式（無／API key／登入／IP 白名單）— **未定義者列 待確認** |
| `cadence` | 更新頻率（日／週／不定期） |
| `earliest_reliable_date` | **待確認**（提示僅供起點估計） |
| `known_gaps` | 已知缺漏／欄位變更／格式轉換點 — 待確認 |
| `rate_limit` | 抓取頻率限制 / robots / T&C — 待確認 |
| `license` | 授權與可保存範圍（snapshot 是否可留存）— 待確認 |
| `confirmed_by` / `confirmed_on` | 確認人 / 日期 — 待填 |

---

## D01 — 交易所／主管機關官方揭露（S1）

| dataset | access | auth | cadence | earliest_reliable_date（提示） | 待確認項 |
|---|---|---|---|---|---|
| TWSE 個股日成交（STOCK_DAY 等） | OpenAPI / CSV | 待確認（一般為無） | 日 | 待確認（提示：約 2004+，機器可讀） | gaps／rate_limit／license |
| TWSE 三大法人買賣超（個股，T86） | OpenAPI / CSV | 待確認 | 日 | 待確認（提示：約 2012-05） | 同上 |
| TWSE 融資融券／借券（MI_MARGN 等） | OpenAPI / CSV | 待確認 | 日 | 待確認（提示：約 2001+） | 同上 |
| TPEx 上櫃／興櫃日成交、法人、信用 | OpenAPI / CSV | 待確認 | 日 | 待確認（提示：上櫃約 2007+；興櫃較稀疏） | 同上 |
| MOPS 重大訊息公告 | 網頁 / 檔案 | 待確認 | 不定期 | 待確認（提示：約 2002+） | 抓取合法性、robots、去重鍵 |
| MOPS 財務報表（XBRL／IFRS） | 檔案 | 待確認 | 季 | 待確認（提示：IFRS 約 2013+；本地 GAAP 更早） | 欄位對映、版本 |

## D02 — 公司／交易對手第一手（S2）

| dataset | access | auth | earliest | 待確認項 |
|---|---|---|---|---|
| 公司 IR 網站、新聞稿 | 網頁擷取 | 待確認（多為無） | 待確認（逐公司） | robots／T&C、snapshot 保存範圍、逐公司覆蓋 |
| 法說會簡報／逐字（MOPS 法說會專區、公司網站） | 檔案 / 網頁 | 待確認 | 待確認（提示：MOPS 法說會約 2010+） | 覆蓋率、語言、格式 |
| 客戶／供應商官方揭露 | 網頁 / 檔案 | 待確認 | 待確認 | 匿名關係處理（CF-06）、跨語言 |

## D03 — 技術／機構權威（S3）

| dataset | access | auth | earliest | 待確認項 |
|---|---|---|---|---|
| 國際 CPO／Silicon Photonics 標準、白皮書、技術文件 | 網頁 / PDF | 待確認 | 待確認（無時間序，屬版本化文件） | 授權、可保存性、versioning |
| 學術／產業技術機構出版 | 網頁 / PDF | 待確認 | 待確認 | 同上 |

## D04 — 可信媒體（S4）

| dataset | access | auth | earliest | 待確認項 |
|---|---|---|---|---|
| 產業／財經媒體報導 | 網頁 / RSS | **待確認（部分付費牆）** | 待確認 | 授權、robots、S4 不得單獨支持重大 Claim（Charter §11.2） |

## D05 — 市場資料（彙整層）

> D05 之原始來源即 D01 之 TWSE／TPEx 系列；本列標示「M04 CMI／M06 事件研究實際使用之最早日期」，取 D01 各子集合之交集。

| 面向 | earliest（提示） | 待確認 |
|---|---|---|
| 價格／成交量 | 待確認（提示：約 2004+） | 復權處理、股本變動 |
| 三大法人動能（CMI C1/C2） | 待確認（提示：約 2012-05） | 個股 T86 起始 |
| 融資融券／借券（CMI C3） | 待確認（提示：約 2001+） | 借券資料起始較晚，待確認 |
| PIT Shares Outstanding（CF-24） | 待確認 | 股本異動事件來源（MOPS）對映 |

## D06 — TDCC 集保股權分布

| dataset | access | auth | cadence | earliest（提示） | 待確認 |
|---|---|---|---|---|---|
| 集保戶股權分散表（含千張大戶級距） | CSV 下載 / OpenData | **待確認** | 週 | 待確認（提示：約 2004+；OpenData 版常見自 2016） | **`available_at` 對映**（發布時間 ≠ 資料週別，CF-26／GP-09）、級距定義變更、robots |

## D07 — Taxonomy／生態系參考庫

| dataset | access | earliest | 待確認 |
|---|---|---|---|
| CPO Taxonomy 版本、Universe 分類參考 | 內部策展（`model_version` model_kind=taxonomy） | N/A（版本化，非時間序） | 初版 taxonomy 內容與版本號、審核人 |

## D08 — 授權付費來源

**V1 停用**（Work-1 TQ-05、CLAUDE.md §9）。`data_source` seed 標 `is_enabled = false`。不做可用性審計，不填任何值。

---

## 產出與後續

1. 本檔每列之「待確認」在第一次抓取 spike 時回填，並記 `confirmed_by`／`confirmed_on`。
2. 回填後：更新 B2 `data_source` seed 之 `earliest_reliable_date`、`auth_method`、`license_note`（以 migration 新增 `UPDATE`，不改既有 migration）。
3. `available_at` 對映規則（D06、部分 D05）另立 `docs/decisions/ADR-00xx-availability-mapping.md`，作為 B3 P04 實作依據（CF-26／GP-09）。
4. 在全部 D01–D06 的 `earliest_reliable_date` 確認前，M04／M06 之歷史回溯範圍以「已確認來源之交集」為準，並於報告揭露。
