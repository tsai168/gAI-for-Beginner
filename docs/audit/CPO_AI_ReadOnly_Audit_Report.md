# CPO AI — Claude Code-1 唯讀盤點報告

**盤點範圍**：`CLAUDE.md`、`docs/Charter_Freeze_V1.md`、`docs/Work1_Technical_Specification_Baseline_V1.md`、`docs/Work2_Contract_Freeze_V1.md`、`docs/Work3_Implementation_Blueprint_V1.md`（皆已完整讀取，逐段核對）
**性質**：唯讀盤點，未修改／新增／刪除任何檔案，未撰寫任何程式碼
**盤點日期**：2026-09-10

> 附註（環境事實，非規格內容）：`docs/` 下四份規格文件在磁碟上實際型別為 **Microsoft Word 2007+（.docx）**，僅副檔名為 `.md`（`file` 指令確認）。內容本身可正常解析，不影響本次盤點結論，但若 Claude Code 或其他工具日後以純文字／Markdown 剖析器直接開啟這些檔案，會讀到二進位亂碼而非文字。建議日後統一副檔名與實際格式（例如另存為真正的 `.md` 純文字，或都掛 `.docx`），此處先列為待確認，不擅自轉檔或修改。

---

## 1. 模組依賴圖：Work-3 DAG 與 Work-1／Work-2 一致性檢查

### 1.1 十層模組總表覆蓋率

逐一比對 Work-3 §2 的 B0–B12 十三批施工順序，是否覆蓋 Work-1 §3 十層架構定義的全部模組編號：

| 層 | Work-1 定義編號 | Work-3 DAG 中出現的批次 | 覆蓋狀態 |
|---|---|---|---|
| D（資料來源層） | D01–D08 | B2 Source Registry | 完整 |
| P（擷取處理層） | P01–P06 | P03→B2；P01/P02/P04/P05/P06→B3 | 完整（P03 提前於 B2） |
| K（知識庫層） | K01–K06 | B4；schema migration 於 B1 | 完整 |
| M（計算／模型層） | M01–M08 | B5 | 完整 |
| A（AI Agent 協作層） | A01–A08 | B6 | 完整 |
| W（工作流程層） | W01–W06 | B7 | 完整 |
| R（報告／輸出層） | R01–R06 | B11 | 完整 |
| G（治理層） | G01–G08 | G04→B4；G02/G05→B6；G01/G03/G06/G07/G08→B8 | 完整，但分散於三個批次 |
| U（UI／API 層） | U01–U05 | U05→B9；U01–U04→B10 | 完整 |
| I（基礎設施層） | I01–I06 | **I01/I02→B1；I04→B7** | **不完整，見 1.2** |

### 1.2 發現的落差：I03／I05／I06 未被分配到任何 WBS 批次

Work-1 §3.10 定義了 I01–I06 六個基礎設施模組，但 Work-3 §2 Dependency DAG 表格中，**只有 I01、I02（B1）與 I04（B7）被明確指派到批次**，以下三者全文搜尋未出現於 Work-3 §2／§3 任何批次或 WBS 工作包中：

- **I03（快取層）**：Work-1 定義其用途為「高頻讀取（Dashboard／Seco/CMI）加速」，理應與 B5（分析引擎）或 B10（U01 儀表板）有依賴關係，但無對應批次。
- **I05（向量／語意儲存）**：Work-1 定義其用途為「供 P02（去重）、K04（關係）使用」，且 Work-3 §5.2 已做出「V1 採用 pgvector」的技術選型決議——但**決議本身未被回寫進 §2 DAG 或 §3 WBS**。若 I05 是 PostgreSQL 擴充套件（pgvector），邏輯上應隨 I01 一併在 B1 建置（extension 啟用需要 migration），但表格中未提及。
- **I06（容器化部署與 CI/CD）**：Work-1 備註為「分批施工、測試自動化」，性質橫跨所有批次，但同樣沒有任何批次明確涵蓋其建置工作。

**結論**：Work-1 的十層架構與 Work-3 的施工批次在 I 層存在明確缺口，不是命名不一致，而是**遺漏指派**。建議在授權 WBS-B1 前先補上 I03／I05／I06 的批次歸屬，否則 pgvector extension 何時啟用、快取層何時導入、CI/CD 何時建置都無施工依據。

### 1.3 依賴關係本身的一致性

- B0→B12 的批次間依賴（B1 依賴 B0、B2 依賴 B1……B12 依賴 B0–B11 全部）與 Work-2 §12 Handoff Contract 所述施工順序（Shared Contracts → 資料庫 → Source Registry → Ingestion → 知識庫 → 分析引擎 → Agent → 工作流程引擎 → API → UI → Reporting → Governance → Tests）**逐項相符**，且與 CLAUDE.md §8「分批施工規則」所述順序文字完全一致，未發現矛盾。
- 唯一需留意：Work-3 §2 把「治理」排在 B8（工作流程引擎 B7 之後、API B9 之前），但 CLAUDE.md §8 文字順序寫的是「...→ Agent → 工作流程引擎 → API → UI → Reporting → **Governance** → Tests」，把 Governance 排在 Reporting 之後、Tests 之前——**這與 Work-3 §2 實際表格順序（治理在 B8，早於 API/UI/Reporting）不一致**。CLAUDE.md 文字敘述的順序與 Work-3 正式 DAG 表格的順序不同，屬於下游文件（CLAUDE.md）與其依據文件（Work-3）之間的敘述性矛盾，建議澄清何者為準（G01 CFL 引擎理論上必須早於 API/UI 才能讓寫入 cfl_status 的端點受管，Work-3 表格順序在邏輯上更合理，但兩份文件文字不一致，需人工確認）。

---

## 2. 實作順序確認（Work-3 §3 WBS 工作包，逐批重述供核對）

| WBS | 涵蓋模組（依 §2） | 輸入 | 產出 | 驗收關卡 |
|---|---|---|---|---|
| B0 | Shared Contracts | Work-2 全部契約文件 + Work-3 本文件 + CLAUDE.md | （無程式碼，治理文件落地 `/docs`） | 文件齊備，不涉及測試 |
| WBS-B1 | I01 關聯式資料庫、I02 物件／快照儲存 | Work-2 §2 DATA_MODEL.md（K01–K06 欄位） | K01–K06 資料表 migration、通用稽核欄位、G04 版本註冊表 | Migration 測試通過；欄位命名與 DATA_MODEL.md 逐一比對無落差 |
| WBS-B2 | D01–D08 來源登錄、P03 快照／版本控制器 | Work-1 §3.1；Work-2 §2.7 K06 source_id | 來源登錄資料表、P03 快照／hash／版本控制器 | 任一來源可回溯至 content_hash 與 snapshot_ref |
| WBS-B3 | P01 擷取器、P02 去重器、P04 時間標準化、P05 可信度評分器、P06 交易日對齊器 | Work-2 §2.1 通用時間欄位；§3 Event Contract | P01–P06 擷取管線，輸出符合 Event Contract 欄位之標準化資料 | 缺失時間欄位保持 NULL；交易日對齊規則測試通過 |
| WBS-B4 | K01–K06、G04 版本註冊中心 | Work-2 §2.2–2.7 K01–K06 Schema | 知識庫 CRUD／查詢層，含 Bitemporal 與 Event Revision Chain | K05 Event 修正鏈測試：CORRECTED 不覆寫 ACTIVE 舊版本 |
| WBS-B5 | M01–M08 | Work-1 §3.4；CF-05/12-30 | Seco／CMI／Materiality／Confidence／AR-CAR／PIT 市值計算模組 | M04 CMI 無 backward filling（GP-08）；M07 使用 PIT Shares Outstanding（CF-24） |
| WBS-B6 | A01–A08、G02、G05 | Work-1 §5 Autonomy L0–L4；Work-2 §6 AGENT_SPEC.md | A01–A08 Agent 實作、G02 自治權控制器、G05 RBAC | 四權分離測試：任一 Agent 角色不得同時具 Evidence 與 Approval/Publication 權（GP-21） |
| WBS-B7 | W01–W06、I04 | SOP 步驟 12；Work-3 §5 I04 決議 | W01–W06 工作流程、Fan-out/Fan-in 編排 | 重試／逾時／Fan-in 匯流整合測試通過 |
| WBS-B8 | G01、G03、G06、G07、G08 | Work-2 §5 CFL_CONTRACT.md | G01 CFL 狀態機、G03 稽核日誌、G06 發布狀態機、G07/G08 | CFL-07 矛盾資料不得 Auto-pass；CFL-08 未核准不得進入 PUBLISHED |
| WBS-B9 | U05、第 4 節端點清單 | Work-2 §4 API_SPEC.yaml | U05／API 層，端點全數實作 | 所有寫入 cfl_status 之端點皆經 G01；錯誤碼格式符合 4.3 節規範 |
| WBS-B10 | U01–U04 | Work-1 §3.9 | 儀表板、搜尋、詳情頁、Admin 審查主控台 | U04 可完整操作 CFL Queue 核准／駁回流程 |
| WBS-B11 | R01–R06 | Work-1 §3.7 | 全部報告輸出（三層發布） | R06 正式外部發布須先通過 CFL-08 |
| WBS-B12 | 跨模組整合測試 | Work-3 §4 Acceptance Tests 全表 | E2E 每日管線測試、CFL 全流程測試 | 第 4 節全部測項通過，回 Projects 進行 Acceptance |

以上為我理解之施工順序，與 Work-3 §2／§3 原文逐項核對一致（I03／I05／I06 缺口見第 1.2 節，未反映於本表，因原文未指派）。

---

## 3. 規格矛盾與缺口

### 3.1 Event 共用欄位範圍：Work-2 內部自相矛盾（重要）

- Work-2 **§3.1 EVENT_CONTRACT.md「通用事件欄位（固定，跨模組共用）」**明確列出 14 個欄位：
  `event_id / project_id / entity_id / source_id / occurred_at / published_at / retrieved_at / status / version / correlation_id / causation_id / confidence / evidence_ids / cfl_status / created_at`
  ——**只包含 3 個時間欄位**：occurred_at、published_at、retrieved_at。
- 但 Work-2 **§2.6 K05 事件實體**寫的是「（時間欄位）沿用 2.1 通用時間欄位規範」，而 §2.1 的「通用稽核與時間欄位規範」定義了 **6 項**：occurred_at、published_at、retrieved_at、market_known_at、event_trading_date，以及 time_basis／time_precision／time_confidence。
- 也就是說，**K05 Event 實體的時間欄位範圍（§2.6→§2.1，6 項）與 EVENT_CONTRACT 固定共用欄位表（§3.1，3 項）不一致**：market_known_at、event_trading_date、time_basis/precision/confidence 這幾個 Charter CF-21／CF-21A 明確要求的欄位，究竟屬不屬於「Event 共用固定欄位」，Work-2 文件本身給出兩種答案。
- 此矛盾會直接影響 WBS-B1／B3／B4：K05 資料表 migration 該建幾個時間欄位？P04 時間標準化模組輸出是否包含 market_known_at／event_trading_date／time_basis 等？Work-3 §4 的 TEST-DATA-02（檢查 occurred_at／published_at／market_known_at 保持 NULL）已經預設 market_known_at 是 Event/相關實體的標準欄位，等於間接採用了 §2.1 的 6 項版本，但 §3.1 固定表未列，**此為需要人工裁決的矛盾，不應自行選擇其中一版本**。
- 同樣受影響：CLAUDE.md §6「事件欄位固定為」直接照抄 Work-2 §3.1 的 14 欄位版本（3 項時間欄位），與 Work-3 TEST-DATA-02、Charter §14.4（明確定義 5 項 Observed-Time 欄位：occurred_at/published_at/retrieved_at/market_known_at/event_trading_date）不一致。

### 3.2 CFL-01～08 候選產生模組與 Agent Spec 權責的模糊地帶

- Work-1 §4 與 Work-2 §5 的 CFL 落地表**彼此完全一致**（逐格比對無差異），兩份文件之間沒有矛盾。
- 但與 Agent Spec（Work-2 §6 A01–A08）對照時，有一處命名易生混淆：**A03 被命名為「關係與矛盾分析代理」**（Relationship *and Conflict* Analysis Agent），字面上暗示 A03 負責矛盾（矛盾資料）分析；但 **CFL-07（矛盾資料）的候選產生模組是 A06（審查代理 Critic），不是 A03**。規格中並未明文區分「A03 的『矛盾分析』」與「A06 觸發 CFL-07 的『矛盾偵測』」是否為同一件事、不同範疇（例如 A03 處理關係圖譜層級的邏輯衝突，A06 處理 Evidence 層級的 CONTRADICT 證據），此區分未見任何文件明確定義，屬於待確認事項。
- 另外，CFL-04（重大事件）與 CFL-03（來源可信度）的候選產生模組分別是 **M05、P05**（計算／擷取層模組），而非 A0x Agent；這與其餘五項 CFL（皆由 A02/A03/A05/A06 或 R06 產生候選）不同型態。規格未說明為何部分 CFL 的候選來自計算層、部分來自 Agent 層的設計原則是否一致，建議在 Work-3 施工前明確此分工邏輯是否為刻意設計（可能是合理設計，但目前四份文件都沒有明文解釋）。

### 3.3 Deferred Items 被下游文件當作已定案的疑慮

- 逐項檢查 Charter §29／Work-1 §8／Work-2 §9 列出的 Deferred Items（Wake-up Window、Daily Snapshot 時間、Batch Size／Queue Policy、Priority Threshold、Token Budget、資料集歷史起點、Confidence／Materiality 校準、Seco／CMI 校準）在 Work-3 全文中的引用方式，**未發現有任何 Deferred 值被寫死或誤當 Frozen 參數**——Work-3 全文未提及 23:00／06:00 等候選時間，皆正確維持掛勾點敘述。此項無矛盾。
- 但發現一個相關但不同性質的問題：**I04（Temporal）／I05（pgvector）技術選型本身不是 Charter Deferred Item（屬 Work-1 TQ-02，明訂由 Work-3 正式決議），Work-3 §5 已完成決議，這點沒有疑慮**。疑慮在於**用詞的確定性層級不一致**：
  - Work-3 §5.1 原文：「此決議**待技術團隊於 Claude Code-1 開工前最終確認**」；
  - Work-3 §5.2 原文：「**建議** V1 採用 pgvector」；
  - 但 **CLAUDE.md §5** 卻直接寫成「I04 工作流程引擎：Temporal（或 Temporal Cloud）— 依 Work-3 §5.1 決議」「I05 向量／語意儲存：pgvector（PostgreSQL 擴充）— 依 Work-3 §5.2 決議」，**用詞上呈現為已拍板的既定事實，未反映 Work-3 自己標註的「待最終確認」保留語氣**。
  - 這不是把 Charter Deferred Item 誤當 Frozen，而是把 **Work-3 標示為「建議決議、待確認」的技術選型，在 CLAUDE.md 被引用為確定值**，建議在授權 WBS-B7（工作流程引擎批次，依賴 I04）之前，由團隊正式書面確認 I04／I05 選型是否真的定案，避免施工到一半才變更工作流程引擎。

### 3.4 K06 Evidence 衝突評分維度與 M02 Confidence 維度的相似但不同命名

- Charter CF-10／Work-2 §2.7 K06：來源衝突判準為 **authority／directness／time／specificity／independence** 五項評分（用於 SUPPORT/CONTRADICT/NEUTRAL-CONTEXT 判斷）。
- Charter CF-29／Work-2 §2.1／M02：Confidence 引擎的 **CF1–CF5** 五構面為 Source Authority、Evidence Directness、Independent Corroboration、Temporal Quality、Conflict Penalty。
- 兩組五維度在概念上高度重疊（Authority、Directness、Time/Temporal、Independence/Corroboration 皆對應），但**規格未明確說明 K06 的五項評分是否就是 M02 CF1–CF5 的底層輸入，或是完全獨立計算的兩套分數**。若為同一份底層數值卻在兩處用不同欄位名稱各自儲存，會有資料重複與不同步風險；若為獨立計算，需要文件說明計算邏輯差異。此為待確認事項，不應自行假設兩者關係。

### 3.5 Work-2 §4.4「待 Work-3 補齊」的 API 權限對照表，Work-3 並未完成

- Work-2 §4.4 原文明確寫：「【待 Work-3 補齊】角色權限對照表需依 Charter §5 六類使用者角色與 G05 RBAC 設計展開為完整清單，此屬 Work-3／CLAUDE.md 之工作範圍」。
- 但通篇檢視 Work-3 全文（含隨附 CLAUDE.md），**未見任何「六類使用者角色 × API 端點」的完整權限對照表**。Work-3 §3 WBS-B9 僅有「所有寫入 cfl_status 之端點皆經 G01」作為驗收關卡，未涵蓋角色層級的讀寫權限矩陣；CLAUDE.md 也沒有此對照表。
- 這是一個**明確承諾但尚未交付**的缺口，屬於 Work-2→Work-3 Handoff Contract 未完全履行的項目，建議在 WBS-B9（API 層，依賴 B8 治理層完成）施工前補齊，否則 G05 RBAC 與四權分離（GP-21）的端點層級落地會缺乏依據。

### 3.6 其他核對結果（未發現矛盾之處，供交叉確認）

- CF-01～CF-46（含 CF-21A、CF-34R）於 Work-1 §10 追溯矩陣逐項有對應模組，經抽查未發現遺漏。
- GP-01～GP-21 於 Work-1 §11 追溯矩陣逐項有對應治理機制，經抽查未發現遺漏。
- CLAUDE.md §6 事件欄位命名規則與 Work-2 §3.1（除 3.1 節 6 項的矛盾外）在欄位「拼寫」層級一致，無同義異名（如 `name`/`code` 混用）情形。
- D08 停用狀態在 Charter §8、Work-1 §3.1／TQ-05、CLAUDE.md §9 三處描述一致，無矛盾。
- CFL 狀態機（PENDING → AUTO-PASS/REVIEW-REQUIRED → APPROVED/REJECTED/BLOCKED → SUPERSEDED）在 Charter §17、Work-1 §4、Work-2 §5.2 三處文字完全一致。

---

## 4. 缺少的 Environment Variables

以下依 I01–I06 基礎設施模組、D01–D08 外部來源與 Work-3 §5 技術選型，列出**可預見**需要的環境變數類別。規格中完全沒有給出實際變數名稱、連線字串格式或金鑰介面，故以下僅為「類別」清單，非規格定義值——**全部項目在目前四份文件中均為「介面與數值未定義」，須團隊於 Claude Code-1 開工前於 CLAUDE.md §5／§7 補充**（CLAUDE.md 原文已自陳此節「待團隊於 Claude Code-1 開工時補充確認」）。

| 類別 | 對應模組 | 目前規格狀態 |
|---|---|---|
| 資料庫連線字串（PostgreSQL，含 pgvector extension） | I01、I05 | 未定義：連線字串格式、host/port/dbname、是否需 SSL 均未提及；I05 是否與 I01 共用同一連線亦未明確聲明（僅 Work-3 §5.2 說「與 I01 關聯式資料庫共用同一套維運」，屬維運層敘述而非連線介面定義） |
| 物件／快照儲存（I02） | P03 snapshot 存放 | 未定義：儲存後端完全未指名（S3？本機磁碟？其他物件儲存？），因此無從列出對應金鑰／endpoint 變數名 |
| 快取層連線（I03） | Dashboard／Seco/CMI 加速 | 未定義：連線目標完全未指名（是否為 Redis 或其他），且如第 1.2 節所述 I03 尚未被分配到任何 WBS 批次 |
| 工作流程引擎連線（I04 Temporal） | W01–W06 | 部分決議、細節未定：Work-3 §5.1 僅決議「採用 Temporal（或 Temporal Cloud）」，未定義 host/namespace/TLS 憑證／API Key 等連線介面，且此決議本身待最終確認（見 3.3） |
| LLM／Batch AI Parsing 供應商與金鑰 | W06、A01–A06（L1/L2） | **完全未定義**：四份文件從未指名要使用哪一家 LLM 供應商或模型（OpenAI／Anthropic／其他），Charter §19、Work-1 W06 僅談「Batch AI Parsing」的治理原則（Deterministic First），沒有任何技術選型或金鑰介面敘述。這是所有環境變數缺口中最關鍵的一項，因為 A01–A08 的 L1/L2 行為都依賴它 |
| D01–D07 外部資料來源存取憑證／API Key | D01（TWSE/TPEx/MOPS）、D02（公司 IR）、D03（技術標準機構）、D04（媒體）、D05（市場資料）、D06（TDCC） | 未定義：Work-1 §3.1 僅列出來源類別與對應 Source Tier，未指名實際資料供應商、API 端點或是否需要付費／申請憑證；究竟是公開網頁爬取或正式 API 介接亦未區分 |
| D08 授權付費來源金鑰 | D08 | V1 明確停用（CF-09、TQ-05），暫不需要，但架構須保留掛勾點 |
| RBAC／使用者認證機制（JWT Secret／OAuth 設定等） | G05、U04 | 未定義：Charter §5 僅定義六類使用者角色，Work-2 §4.4 明確承認「待 Work-3 補齊」且 Work-3 未完成（見 3.5），因此認證機制本身（是否為 JWT、OAuth、SSO）與對應環境變數均無從列出 |
| Token Budget／Cost Ceiling 相關設定 | G08、W06 | Charter §29 明確列為 Deferred Item，留待 Operations Specification，目前確實不應寫死，屬於刻意保留而非缺失 |
| Wake-up Window／Batch Schedule 設定 | W01、W02 | 同上，Deferred Item，刻意保留 |

---

## 5. 外部 API 與 Database Migration 需求

### 5.1 第一批（WBS-B1／B2）需要建立的 Database Migration 清單

依 Work-2 §2 DATA_MODEL.md 與 Work-3 WBS-B1／B2 定義，第一批應建立以下資料表（**僅列出規格中明確定義的欄位／主鍵；索引設計、外鍵約束細節、欄位型別，規格全文從未提及，一律列為待確認，不自行假設**）：

**WBS-B1（K01–K06 + G04）：**

| 資料表（推定） | 主鍵 | 規格中已定義的欄位 | 索引 |
|---|---|---|---|
| K01 Company | company_id | stock_code、company_name、universe、listing_market、is_overseas、taxonomy_refs + §2.1 共用稽核欄位（confidence/cfl_status/model_version_id/valid_from-to/created_at-updated_at） | 未定義 |
| K02 Technology | technology_id | taxonomy_version_id、category、parent_technology_id、effective_from/effective_to | 未定義 |
| K03 Product | product_id | company_id、technology_id（外鍵，未明定約束）、evidence_stage、spec_summary | 未定義 |
| K04 Relationship | relationship_id | source_entity_id、target_entity_id、relationship_type、is_named、status、evidence_ids | 未定義 |
| K05 Event | event_id | revision_of_event_id（自參照）、status、event_taxonomy_code、materiality_score、cfl_status + 時間欄位（範圍有矛盾，見 3.1） | 未定義 |
| K06 Evidence | evidence_id | source_id、entity_ref／event_ref（多型參照，未定義實作方式：單表+type 欄位或多對多關聯表）、evidence_type、evidence_stage、source_credibility_tier、authority/directness/time/specificity/independence、content_hash/snapshot_ref、cfl_status | 未定義 |
| G04 Model Version Registry | 未定義（規格未給出欄位表，僅說明用途為「Taxonomy／Seco／CMI／Benchmark／Materiality／Confidence Model Version」註冊） | 未定義 | 未定義 |

**WBS-B2（Source Registry + P03）：**

| 資料表（推定） | 主鍵 | 規格中已定義的欄位 | 索引 |
|---|---|---|---|
| Source Registry（D01–D08 來源登錄） | source_id（依 K06 §2.7 提及「source_id 來源登錄，關聯 P03 快照與 hash」推定） | 規格未給出完整欄位表，僅能確認需可被 K06.source_id 參照 | 未定義 |
| P03 Snapshot／版本控制 | 未定義 | content_hash、snapshot_ref（欄位名稱由 K06 §2.7 提及）、parser_version、source_version（欄位名稱由 Charter §8／Work-1 P03 功能敘述提及，但未見於 Work-2 DATA_MODEL 正式欄位表） | 未定義 |

**待確認事項（不應自行決定）**：
- 通用稽核欄位（confidence／cfl_status／model_version_id／valid_from-to／created_at-updated_at）是否在每張表各自複製一份欄位，還是設計為共用父表／mixin？規格未說明實作方式。
- K06 的 `entity_ref／event_ref` 多型參照如何在關聯式資料庫中落地（單表 polymorphic 欄位、每型別一個外鍵欄位、或獨立關聯表）？規格只講語意不講實作。
- 除主鍵外，規格從未提及任何索引、唯一約束（例如 company_id + stock_code 是否需要 unique）、外鍵 ON DELETE 行為。
- parser_version／source_version 兩欄位名稱僅見於 Work-1 P03 功能敘述與 Charter §8，**未出現在 Work-2 §2 DATA_MODEL.md 正式欄位表中**，屬於 3.1 節之外另一個「規格提及但未正式收錄進 Contract」的欄位缺口，建議一併請人工確認是否要正式納入 K06/P03 schema。

### 5.2 需要串接的外部 API／資料來源，及認證方式未定義者

依 Work-1 §3.1 D01–D08 清單：

| 編號 | 來源類別 | 實際供應商／API | 認證方式 |
|---|---|---|---|
| D01 | TWSE、TPEx、MOPS 等法定公開資訊 | 未指名具體 API（是否用官方 OpenAPI、或爬蟲） | **未定義** |
| D02 | 公司 IR、財報、法說會、新聞稿、客戶供應商官方來源 | 未指名（來源分散、無單一 API） | **未定義** |
| D03 | 國際 CPO／矽光子標準與技術文件、學術產業機構 | 未指名 | **未定義** |
| D04 | 可信產業媒體、主流財經媒體 | 未指名 | **未定義** |
| D05 | 股價成交、法人買賣、融資融券／借券 | 未指名資料供應商 | **未定義** |
| D06 | TDCC 千張大戶等低頻持股資料 | 未指名是否為 TDCC 官方開放資料或第三方轉發 | **未定義** |
| D07 | CPO Taxonomy／Universe 分類參考庫 | 內部維護參考庫，非傳統外部 API，但未說明資料如何持續更新（人工維護？外部訂閱？） | **未定義（性質待確認）** |
| D08 | 授權付費來源 | V1 停用，不啟用 | 不適用（V1） |

**結論**：D01–D07 全部七個啟用中的來源，其實際供應商、API 端點與認證方式在四份規格文件中**全數未定義**，僅有 Source Tier（S1–S5）與用途分類。這是 WBS-B2（Source Registry）與 WBS-B3（Ingestion，P01 擷取器需要實際串接這些來源）施工前必須由人工補齊的關鍵資訊，否則 P01 無從實作。

另外，如第 4 節所述，**LLM／Batch AI Parsing 供應商**同樣未定義，雖不屬於 D01–D08 資料來源清單，但屬於外部 API 串接需求的一部分，一併列入待確認。

---

## 6. 待確認問題清單（彙整，供人工逐項回覆後方可授權 WBS-B1）

1. **【Event 欄位範圍矛盾】** Work-2 §3.1 EVENT_CONTRACT 固定共用欄位（14 項，僅 3 個時間欄位）與 §2.6/§2.1（K05 沿用通用時間欄位規範，6 項時間相關欄位）不一致，market_known_at／event_trading_date／time_basis/precision/confidence 是否應納入 Event 的固定共用欄位？以哪一版為準？
2. **【CLAUDE.md 與 Work-2 不同步】** CLAUDE.md §6 的事件欄位清單目前採用 Work-2 §3.1 的 3 項時間欄位版本，若問題 1 的答案是採用 6 項版本，CLAUDE.md 需同步更新（但依專案規則，CLAUDE.md 修改須走 Charter §31 Change Control／對應治理流程，不可逕自變更）。
3. **【I 層 WBS 缺口】** I03（快取層）、I05（向量／語意儲存）、I06（容器化部署與 CI/CD）三個基礎設施模組未被指派到任何 WBS 批次，應補在哪一批？I05 pgvector 是否應併入 WBS-B1（因為是 PostgreSQL extension，需要 migration 啟用）？
4. **【技術選型確定性】** Work-3 §5.1／§5.2 用「建議決議」「待最終確認」的措辭描述 I04 Temporal、I05 pgvector 選型，但 CLAUDE.md §5 已將其寫成確定事實。在授權 WBS-B7（依賴 I04）前，I04／I05 選型是否已經團隊正式拍板？
5. **【CLAUDE.md 施工順序文字 vs Work-3 DAG 表格】** CLAUDE.md §8 文字敘述的施工順序把「Governance」放在「Reporting」之後、「Tests」之前；但 Work-3 §2 DAG 表格把「治理」排在 B8（早於 API B9、UI B10、Reporting B11）。兩者順序不同，應以哪一份為準？
6. **【A03 與 A06 矛盾分析權責】** A03（關係與矛盾分析代理）之「矛盾分析」與 A06（審查代理 Critic，CFL-07 候選產生者）之「偵測 CONTRADICT Evidence」是否為不同範疇（關係層級 vs 證據層級）？若是，能否在 AGENT_SPEC 中明確界定二者邊界，避免實作時混淆？
7. **【K06 五維評分 vs M02 CF1–CF5】** K06 Evidence 的 authority/directness/time/specificity/independence 五項評分，與 M02 Confidence 引擎的 CF1–CF5（Source Authority/Evidence Directness/Independent Corroboration/Temporal Quality/Conflict Penalty）是否為同一組底層數值的兩種呈現，還是各自獨立計算？
8. **【Work-2→Work-3 RBAC 對照表未交付】** Work-2 §4.4 明確載明「角色權限對照表待 Work-3 補齊」，但 Work-3全文（含 CLAUDE.md）未見完整的「六類角色 × API 端點」權限矩陣。此表由誰、於何時補齊？是否須在 WBS-B9（API 層）施工前完成，或在 WBS-B6（Agent/RBAC 層）階段一併產出？
9. **【CFL 候選產生模組型態不一致】** CFL-03／CFL-04 的候選產生模組為 P05／M05（非 Agent 層），與其餘 CFL 多由 A0x Agent 產生候選的模式不同，是否為刻意設計？是否需要在 AGENT_SPEC／CFL_CONTRACT 中補充說明此分工原則？
10. **【LLM／Batch AI Parsing 供應商未定】** A01–A06（L1/L2 AI 行為）與 W06 Batch AI Parsing 所依賴的 LLM 供應商、模型版本與金鑰管理方式，四份規格文件全數未提及，應由誰、於哪個 WBS 批次前決定？
11. **【D01–D07 外部資料來源介接細節】** D01 至 D07 共七個啟用中的資料來源，其實際供應商、API 端點與認證方式全數未定義，是否已有初步技術評估？WBS-B2／B3 施工前需要哪些單位（IT／法務／採購）提供資訊？
12. **【parser_version／source_version 欄位歸屬】** 此二欄位僅見於 Work-1 P03 功能敘述與 Charter §8 文字描述，未列入 Work-2 §2 DATA_MODEL.md 正式欄位表，是否應正式收錄進 K06／P03 Schema？
13. **【共用稽核欄位實作方式】** confidence／cfl_status／model_version_id／valid_from-to／created_at-updated_at 等共用稽核欄位，在資料庫層是否要每表各自複製欄位，或設計共用父表／mixin？規格未說明。
14. **【K06 多型參照實作方式】** K06 的 entity_ref／event_ref 多型參照，資料庫層應如何落地（單一 polymorphic 欄位＋type、每型別獨立外鍵、或關聯表）？規格僅有語意層敘述。
15. **【索引設計】** WBS-B1／B2 全部資料表目前規格中完全沒有索引、唯一約束、外鍵 ON DELETE 行為的定義，是否留待實作階段由工程團隊自行設計，或需要先經過 Review？
16. **【副檔名與實際檔案格式不符】**（環境問題，非規格內容）`docs/` 下四份規格文件實際為 .docx 二進位格式但副檔名為 .md，是否需要正式轉存為純文字 Markdown，以避免後續工具誤讀？

---

*本報告依 CLAUDE.md §10「何時必須停下來詢問人類」原則產出：發現規格文件間矛盾與缺口、環境變數與外部 API 介接細節不明確，故在此停止，不進入任何實作。待以上 16 項問題逐一獲得人工回覆後，方建議授權開始 WBS-B1。*
