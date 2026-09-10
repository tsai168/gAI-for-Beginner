**CPO AI**

**台灣 CPO／矽光子產業情報、公司事件、生態系卡位與市值重估 AI Agent
System**

**WORK-1 --- TECHNICAL SPECIFICATION BASELINE V1**

Architecture Freeze：模組架構、Agent 架構、治理落地與驗收規格

Status: DRAFT FOR ARCHITECTURE FREEZE

Upstream: CPO AI Project Charter Freeze V1.0 (2026-09-05, FROZEN)

Date: 2026-09-10

Next Gate: Work-2 --- Contract Freeze

0\. 文件控制

  -------------------------------------------------------------------------------------------------------
  **項目**       **內容**
  -------------- ----------------------------------------------------------------------------------------
  文件名稱       CPO AI Work-1 Technical Specification Baseline V1

  文件性質       將 Project Charter Freeze V1.0 工程化為模組架構、Agent
                 架構、事件流程、資料模型輪廓與治理落地規格；不產出程式碼、不固定資料庫欄位細節、不固定
                 API contract

  版本           V1.0 (Draft for Architecture Freeze)

  狀態           DRAFT --- 待 Research Director／Executive User 驗收後方可進入 Work-2

  上游來源       CPO AI Project Charter Freeze V1.0（FROZEN，2026-09-05）；歷史參考：20260828 生態系卡位
                 AI 代理系統完整架構設計文件（非 Frozen，作為技術參考輸入）

  下游文件       Work-2 Contract Freeze（Data／Event／API／CFL Contract）；Work-3 Implementation
                 Blueprint + Acceptance Criteria；CLAUDE.md

  變更原則       本文件不得靜默修改 Charter 之 Frozen
                 Decision（CF-01～CF-46、GP-01～GP-21）。若技術限制迫使研究契約變更，須回到 Charter
                 Change Control（Charter §31）。
  -------------------------------------------------------------------------------------------------------

1\. 目的與範圍

本文件為 SOP「Claude 對話 → Claude Projects（深度研究）→ CLAUDE.md →
Claude Code → Test → Projects 驗收」中第②階段之產出：Architecture
Freeze／Technical Specification Baseline V1。

目的：把 Charter 所定義的「系統要解決什麼問題、研究結果如何成立、AI
可以做什麼與不能做什麼」，轉譯為「系統應如何設計」------完整模組架構、Agent
架構、事件流程、CFL 落地機制、安全治理與驗收規格。

範圍內：十層模組架構與模組編號、模組 I/O 與依賴、Core Research Object
對應之知識庫模組、CFL-01～08 技術落地點、Agent Autonomy L0～L4
對應、Point-in-Time／版本化機制之架構設計、CF/GP 逐項追溯表、Work-1
驗收標準。

範圍外（依 Charter §7 與 SOP 治理原則，留待
Work-2／Work-3）：資料庫欄位層級 schema、API contract
細節、事件契約完整欄位表、程式語言與框架選型之最終確認、Repository
結構、部署拓撲、Wake-up Window／Batch 參數等 Deferred Items（見第 9
節）。

2\. 與既有文件的關係與整合處理

本專案輸入包含三份文件：

- 《CPO AI Project Charter Freeze
  V1.0》（2026-09-05，FROZEN）------本規格之唯一權威來源（Single Source
  of Truth）。

- 《Claude AI 代理專案標準作業流程
  SOP》（2026-09-07）------定義本文件在治理管線中的定位與應包含之十層架構樣板。

- 《Claude 生態系卡位 AI
  代理系統完整架構設計文件》（2026-08-28）------Charter Freeze
  之前產出的技術參考文件，內容詳實（43 個模組、X1-X43
  規則引擎、Seco/CMI/事件窗口重估/γ迴歸），本文件大量借用其模組設計精神，但其狀態非
  Frozen，且部分定義先於 Charter，故本文件對其進行下列處理：

*重要協調聲明（Reconciliation Note）：0828 文件在附錄 A 中自行定義了一套
CFL-01～08 對照表（將來源文件中的排他／降級／門檻／防洩漏規則編號為
CFL），該定義內容與 Charter §17 正式凍結之 CFL-01～08（公司身分／CPO
分類／來源可信度／重大事件／生態系關係／競爭分析／矛盾資料／發布核准）並不相同。依
Charter §32 Work-1 Handoff Contract，Work-1 不得靜默修改 Frozen
Decision，因此本文件明確以 Charter §17 之 CFL-01～08
為唯一有效版本；0828 文件之舊版 CFL
對照表視為歷史技術參考，予以停用並建議封存為
docs/legacy/CFL_MAPPING_LEGACY_0828.md，不再作為治理依據。*

3\. 十層模組架構（Module Architecture）

依 SOP 建議之通用十層架構（D／P／K／M／A／W／R／G／U／I），對應 CPO AI
之研究契約與治理需求展開如下。各模組於本階段僅定義功能、輸入、輸出與依賴，不含資料庫欄位與程式碼。

3.1 資料來源層 D01--D08

  ------------------------------------------------------------------------------------------------------
  **編號**   **模組名稱**               **功能**                                       **對應 Source
                                                                                       Tier / Charter
                                                                                       依據**
  ---------- -------------------------- ---------------------------------------------- -----------------
  D01        交易所／主管機關官方揭露   TWSE、TPEx、MOPS 等法定公開資訊                S1；CF-07

  D02        公司／交易對手第一手來源   IR、財報、法說會、新聞稿、客戶供應商官方來源   S2；CF-07

  D03        技術／機構權威來源         國際 CPO／Silicon Photonics                    S3；CF-07
                                        標準與技術文件、學術產業機構                   

  D04        可信媒體來源               可信產業媒體、主流財經媒體                     S4；CF-07

  D05        市場資料來源               股價成交、法人買賣、融資融券／借券             Charter §8

  D06        TDCC 股權分布來源          TDCC 千張大戶等低頻持股資料                    CF-26；GP-08/09

  D07        Taxonomy／生態系參考庫     CPO Taxonomy 版本、Universe 分類參考           CF-02；Charter
                                                                                       §10

  D08        授權付費來源（保留）       V1 不啟用，僅保留架構擴充點                    Charter §8；CF-09
  ------------------------------------------------------------------------------------------------------

3.2 擷取處理層 P01--P06

  ---------------------------------------------------------------------------------------------------------------------------------------------------
  **編號**   **模組名稱**             **功能**                                                                                 **對應 Charter 依據**
  ---------- ------------------------ ---------------------------------------------------------------------------------------- ----------------------
  P01        Crawler／API 擷取器      自 D01--D06 擷取原始文件與市場資料                                                       Charter §19

  P02        去重器                   Hash-based 內容去重                                                                      Charter §19；GP-16

  P03        快照／版本控制器         保存原始 URL、標題、Publisher、content hash、snapshot、parser version、source version    CF-08

  P04        時間標準化與             occurred_at／published_at／retrieved_at／market_known_at／event_trading_date；缺失保持   CF-21、CF-21A；GP-07
             Observed-Time 階層       NULL                                                                                     

  P05        來源可信度評分器         依 S1--S5 評級來源                                                                       CF-07

  P06        交易日曆與事件日對齊器   Trading-session Alignment、Conservative Alignment Rule                                   CF-22
  ---------------------------------------------------------------------------------------------------------------------------------------------------

3.3 知識庫層 K01--K06（對應 Charter §9 Core Research Objects）

  -------------------------------------------------------------------------------------------------------------
  **編號**   **模組名稱**                             **對應 Core Research         **關鍵治理規則**
                                                      Object**                     
  ---------- ---------------------------------------- ---------------------------- ----------------------------
  K01        公司實體與 Universe 分類                 Company                      CF-01、CF-03、CF-04；GP-01

  K02        技術與 Taxonomy（版本化）                Technology                   CF-02；Charter §10

  K03        產品／模組／規格實體                     Product                      Charter §9

  K04        關係圖譜（客戶／供應商／夥伴／競爭者）   Relationship（含 Person）    CF-06；GP-01/03

  K05        事件實體與修正鏈（Immutable + Revision） Event                        CF-35、CF-36；GP-06/15

  K06        證據與引用存放                           Evidence、Source、Citation   CF-10、CF-11；GP-02/03/17
  -------------------------------------------------------------------------------------------------------------

3.4 計算／模型層 M01--M08

  -----------------------------------------------------------------------------------------------------------------
  **編號**   **模組名稱**             **功能**                                      **對應 Charter 依據**
  ---------- ------------------------ --------------------------------------------- -------------------------------
  M01        Evidence Stage 分類器    E0--E6 供應鏈成熟度判定                       CF-05；GP-05

  M02        Confidence 引擎          CF1--CF5 Evidence-based Confidence，0--1      CF-29、CF-30；GP-11

  M03        Seco 引擎                S1--S6                                        CF-12～CF-17
                                      六構面加權（15/15/20/20/20/10），Bitemporal   

  M04        CMI 引擎                 C1--C5 等權合成，禁 backward filling          CF-18、CF-19、CF-26；GP-08/09

  M05        Materiality 評分器       EV01--EV12 Event Taxonomy + Materiality       CF-27、CF-28；GP-12
                                      0--100                                        

  M06        事件窗口／AR-CAR 引擎    多窗口 \[-N,+M\]、Market-adjusted 與 Market   CF-20、CF-23
                                      Model 雙版本 Benchmark                        

  M07        Point-in-Time 市值計算器 Price × PIT Shares Outstanding                CF-24

  M08        穩健性／時間品質檢核器   High/Medium/Low 樣本 CAR Robustness Check     Charter §14.4
  -----------------------------------------------------------------------------------------------------------------

3.5 AI Agent 協作層 A01--A08

  --------------------------------------------------------------------------------------
  **編號**   **模組名稱**                **Autonomy   **功能／權責**
                                         Level**      
  ---------- --------------------------- ------------ ----------------------------------
  A01        抽取代理                    L1           建立
                                                      Entity/Event/Evidence/Technology
                                                      Candidate；Candidate ≠ Fact

  A02        實體判斷與分類代理          L1/L2        Universe／Taxonomy 分類建議

  A03        關係與矛盾分析代理          L2           Relationship／Conflict 分析與
                                                      Recommendation

  A04        Seco／CMI／重大性分析代理   L2           研究假設與
                                                      Recommendation；Recommendation ≠
                                                      Approval

  A05        比較分析代理                L2           競爭分析 Draft（CFL-06
                                                      控管，正式結論需 Human Review）

  A06        審查代理（Critic）          L2           偵測 CONTRADICT
                                                      Evidence、資料洩漏風險，觸發
                                                      CFL-07

  A07        協調代理                    L0           Fan-out／Fan-in
                                                      編排、排程、重試（Temporal
                                                      或等效引擎）

  A08        人工介接閘道代理            L3/L4 gate   將高風險決策路由至 Human
                                                      Review／Approval 佇列
  --------------------------------------------------------------------------------------

3.6 工作流程層 W01--W06

  -------------------------------------------------------------------------------------------------------------------
  **編號**   **模組名稱**                 **功能**                                                  **對應 Charter
                                                                                                    依據**
  ---------- ---------------------------- --------------------------------------------------------- -----------------
  W01        排程與 Wake-up 觸發器        候選 Wake-up Window 掛勾點（實際時間 Deferred）           CF-34R；Charter
                                                                                                    §29

  W02        Priority Trigger 佇列        重大事件優先進入 Batch AI Parsing                         Charter §19

  W03        Fan-out／Fan-in 編排器       選定 N 個對象平行處理後匯流                               SOP 步驟 12

  W04        每日研究管線工作流           Discover→Retrieve→Normalize→Extract→Verify→\...→Publish   Charter §26.3

  W05        重試／逾時／錯誤處理工作流   確保管線可重試、可追蹤                                    Charter §22
                                                                                                    Auditability

  W06        Batch AI Parsing 工作流      Deterministic First 閘門，僅核准後才呼叫 LLM              Charter
                                                                                                    §19；GP-16
  -------------------------------------------------------------------------------------------------------------------

3.7 報告／輸出層 R01--R06

  ----------------------------------------------------------------------------------
  **編號**   **模組名稱**              **發布層級**         **功能**
  ---------- ------------------------- -------------------- ------------------------
  R01        每日來源摘要／Watchlist   Internal Auto        Charter §18
             異動報告                                       

  R02        公司／事件研究報告        依 Materiality 分流  版本化 ResearchReport

  R03        Seco／CMI 儀表板資料      Internal Auto        供 U01 消費

  R04        事件研究／CAR 報告        Material Review      CF-20、CF-23

  R05        比較與競爭分析報告        Material             Draft→Human Review
                                       Review（CFL-06）     

  R06        正式外部發布包            External             Charter §18
                                       Approval（CFL-08）   
  ----------------------------------------------------------------------------------

3.8 治理層 G01--G08

  --------------------------------------------------------------------------------------------------------------------------------------
  **編號**   **模組名稱**       **功能**                                                                         **對應 Charter 依據**
  ---------- ------------------ -------------------------------------------------------------------------------- -----------------------
  G01        CFL 規則引擎       CFL-01～08                                                                       Charter §17；CF-31
                                狀態機：PENDING→AUTO-PASS/REVIEW-REQUIRED→APPROVED/REJECTED/BLOCKED→SUPERSEDED   

  G02        Agent 自治權控制器 L0--L4 執行與四權分離（Evidence/Analysis/Approval/Publication）                  CF-37～CF-46

  G03        稽核日誌與決策鏈   保存 Agent、Rule、Input、Evidence、Confidence、Model                             CF-45；Charter §22
                                Version、Decision、Timestamp                                                     

  G04        版本註冊中心       Taxonomy／Seco／CMI／Benchmark／Materiality／Confidence Model Version            GP-10；CF-13/19/23/30

  G05        RBAC 與角色管理    對應 Charter §5 六類使用者角色之權限邊界                                         Charter §5；GP-20/21

  G06        發布狀態機         Internal Auto／Material Review／External Approval 三層                           CF-33；Charter §18

  G07        Change Control     Charter §31 變更請求、版本升級（V1.1/V2.0）紀錄                                  Charter §31
             紀錄器                                                                                              

  G08        非功能合規監控器   Traceability／Reproducibility／PIT Integrity／Cost Governance 檢查               Charter §22
  --------------------------------------------------------------------------------------------------------------------------------------

3.9 UI／API 層 U01--U05

  ---------------------------------------------------------------------------
  **編號**   **模組名稱**           **功能**
  ---------- ---------------------- -----------------------------------------
  U01        研究儀表板             公司／生態系／Seco／CMI 總覽

  U02        搜尋與探索介面         跨 Company/Event/Evidence 搜尋

  U03        公司／事件詳情頁       含 Evidence、Citation、Revision 歷史呈現

  U04        人工審查／Admin 主控台 CFL Queue、Human Review、Approval
                                    操作介面

  U05        報告匯出與 API         R01--R06 之匯出格式與存取介面
  ---------------------------------------------------------------------------

3.10 基礎設施層 I01--I06

  -------------------------------------------------------------------------------------------
  **編號**   **模組名稱**      **功能**                              **備註**
  ---------- ----------------- ------------------------------------- ------------------------
  I01        關聯式資料庫      核心實體與事件溯源儲存                欄位設計留待 Work-2
                                                                     DATA_MODEL.md

  I02        物件／快照儲存    原始來源快照、content hash 存放       CF-08

  I03        快取層            高頻讀取（Dashboard／Seco/CMI）加速   

  I04        工作流程引擎      支援 Fan-out/Fan-in、重試、逾時管理   候選：Temporal
                                                                     或等效引擎，技術選型待
                                                                     Work-3 確認

  I05        向量／語意儲存    實體去重、語意相似度比對（供 P02、K04 技術選型待 Work-3 確認
                               使用）                                

  I06        容器化部署與      分批施工、測試自動化                  SOP 步驟 9--11
             CI/CD                                                   
  -------------------------------------------------------------------------------------------

4\. CFL 技術落地點（依 Charter §17，唯一有效版本）

下表說明 Charter §17 之 CFL-01～08
各自由哪些模組產生候選、由哪個模組執行 AUTO-PASS／REVIEW-REQUIRED
判斷，以及最終審查介面。

  --------------------------------------------------------------------------------------------
  **CFL**   **治理對象**   **候選產生模組**   **判斷／審查模組**   **V1 原則**
  --------- -------------- ------------------ -------------------- ---------------------------
  CFL-01    公司身分       A02                G01 + G05            高 Confidence、可驗證者
                                                                   Auto-pass

  CFL-02    CPO 分類       A02                G01 → U04（首次升    Watchlist/Adjacent AI
                                              Core 需人工）        建議；首次升 Core 需 Human
                                                                   Review

  CFL-03    來源可信度     P05                G01                  已知官方來源
                                                                   Auto-pass；新／未知來源需
                                                                   Review

  CFL-04    重大事件       M05                G01 → U04            一般事件 AI 分類；高
                                                                   Materiality 需 Human Review

  CFL-05    生態系關係     A03/K04            G01 → U04            Candidate 可保存；重大具名
                                                                   Confirmed 首次需 Human
                                                                   Review

  CFL-06    競爭分析       A05                G01 → U04            AI 可 Draft；正式重大結論需
                                                                   Human Review

  CFL-07    矛盾資料       A06/K06            G01（不得            重大 CONTRADICT Evidence
                                              Auto-pass）          不得 Auto-pass

  CFL-08    發布核准       R06                G06 → U04            正式外部重大研究結論 Human
                                                                   Approval Required
  --------------------------------------------------------------------------------------------

CFL 狀態生命週期 PENDING → AUTO-PASS/REVIEW-REQUIRED →
APPROVED/REJECTED/BLOCKED → SUPERSEDED 由 G01
統一實作為狀態機，所有模組僅能經由 G01 提交候選與查詢狀態，不得繞過。

5\. Agent Autonomy L0--L4 對應

  -----------------------------------------------------------------------------------------------------------------------------------------------------------------------
  **Level**   **定位**           **對應模組**                                                        **四權分離落實方式**
  ----------- ------------------ ------------------------------------------------------------------- --------------------------------------------------------------------
  L0          Deterministic      P01--P06、M06、M07、A07、W 全層                                     純確定性計算，不涉及 Evidence／Analysis 判斷權
              Automation                                                                             

  L1          AI Extraction      A01                                                                 僅能寫入 Candidate（K05/K06 標記 state=DRAFT/CANDIDATE），無
                                                                                                     Approval 權

  L2          AI Analysis &      A03、A04、A05                                                       僅能產出 Recommendation，不具 Approval／Publication 權（G05 RBAC
              Recommendation                                                                         強制）

  L3          Conditional        G02（規則明確＋Confidence足夠＋無重大衝突＋非高風險狀態轉換＋通過   由 G02 依規則自動決策，仍受 G03 稽核與 G01 CFL 閘門
              Autonomous         CFL）                                                               
              Decision                                                                               

  L4          Reserved Human     A08 → U04                                                           高風險分類／關係／衝突／模型升版／重大結論／外部發布，僅人工可核准
              Authority                                                                              
  -----------------------------------------------------------------------------------------------------------------------------------------------------------------------

G02 強制實作 Evidence／Analysis／Approval／Publication
四權分離（GP-21）：任一 Agent（A01--A08）之角色權限（由 G05 RBAC
定義）僅能落在其中一項功能類別，禁止單一 Agent 帳號同時具備 Evidence
寫入與 Approval／Publication 權限。

6\. Point-in-Time 與版本化機制（架構層級）

本節僅說明機制設計原則，實際欄位與資料型別由 Work-2
DATA_MODEL.md／EVENT_CONTRACT.md 定義。

- Observed-Time
  階層（P04）：occurred_at（Optional）／published_at（Preferred）／retrieved_at（Required）／market_known_at（Optional/Evidence-only）／event_trading_date（Event
  Study Required），缺失一律 NULL，不得虛假精度填補。

- Bitemporal 設計（M03 Seco、M04 CMI、K05 Event）：區分 Effective Time
  與 Knowledge Time；Correction 與 New Evidence 分離寫入，不回填歷史。

- Event Revision Chain（K05）：Immutable Event + 版本鏈，狀態
  ACTIVE／CORRECTED／SUPERSEDED／WITHDRAWN／DISPUTED，撤回不等於歷史未曾存在（可分別研究
  Announcement Effect 與 Correction Effect）。

- Model Version
  隨結果攜帶（G04）：Seco/CMI/Materiality/Confidence/Benchmark
  任一權重或公式變更，一律建立新 Model Version，不得覆寫既有版本結果。

7\. 非功能需求技術對應

  -----------------------------------------------------------------------------------
  **Charter 非功能需求**    **技術落地模組／機制**
  ------------------------- ---------------------------------------------------------
  Traceability              K06 Evidence/Citation 與 G03 Audit Log 聯合查詢

  Reproducibility           G04 Model Version + P03 Input Version + 計算時間戳

  Point-in-Time Integrity   P04、P06、M04（No Future Data）、G08 監控

  Auditability              G03 全鏈路稽核（來源、解析、決策、修正、發布）

  Versionability            G04（Taxonomy／Evidence
                            Rule／Seco／CMI／Benchmark／CFL／Report 版本化）

  Cost Governance           W06（Deterministic First 閘門）＋ G08（Token Budget
                            監控掛勾點，具體額度 Deferred）

  Human Governance          G02＋A08＋U04（高風險狀態轉換與正式外部發布保留人工權）

  Extensibility             K02（Taxonomy
                            版本化擴充）、G04（新模型版本註冊）不破壞既有可重現性
  -----------------------------------------------------------------------------------

8\. Deferred Items（延續 Charter §29，本階段不決策）

下列項目依 Charter 明示為刻意延後決策，Work-1
僅提供掛勾點（W01/W02/G08），不得將候選值誤設為 Frozen 參數：

- LLM Wake-up Window（23:00、06:00 僅為候選）→ 掛勾於 W01，具體時間留待
  Operations Specification

- Daily Snapshot 產生時間、Batch Size／Queue Policy、Priority Wake-up
  Threshold → 掛勾於 W01/W02，參數留待 Operations Specification

- Token Budget／Daily Ceiling／Cost Alert → 掛勾於 G08，額度留待
  Operations Specification

- 資料集實際完整歷史起點 → 掛勾於 P03/G04，留待 Data Availability
  Audit／Work-2 Technical Specification

- Confidence／Materiality 精確權重與校準方式 → 掛勾於 M02/M05 +
  G04，留待 Phase 2 Model Calibration

- Seco／CMI 統計校準後新權重 → 掛勾於 M03/M04 + G04，需建立新 Model
  Version，留待 Phase 2

9\. Work-1 提出之技術問題／風險／備選方案（不構成 Frozen Decision 變更）

  -------------------------------------------------------------------------------------------------------------------------------
  **編號**   **議題**                                         **說明**                           **建議處理**
  ---------- ------------------------------------------------ ---------------------------------- --------------------------------
  TQ-01      0828 舊版 CFL 對照表與 Charter §17 衝突          兩份文件皆用 CFL-01～08            採 Charter §17
                                                              編號但定義不同                     為唯一有效版本；0828
                                                                                                 版本封存為歷史參考文件，見第 2
                                                                                                 節

  TQ-02      工作流程引擎與向量儲存之技術選型（I04/I05）      0828 文件建議 Temporal             留待 Work-3 Implementation
                                                              與語意相似度模型，屬技術參考而非   Blueprint
                                                              Frozen Decision                    依團隊技術能力與成本正式選型

  TQ-03      Kappa 一致性稽核器（雙人編碼一致性檢核）         0828 文件提出但未出現於 Charter    建議保留為選配 QA
                                                              任何 CF/GP                         模組（不編入十層必要架構），待
                                                                                                 Research Director 決定是否納入
                                                                                                 V1

  TQ-04      γ 共振交互作用迴歸與穩健性檢定（回測、統計檢定） 屬 Charter §26.2 Phase 2 範圍，非  M-層預留 M06/M08
                                                              MVP                                之下游擴充點，正式實作延後至
                                                                                                 Phase 2

  TQ-05      授權付費資料來源（D08）之法遵與合約條件          Charter 僅保留架構，未定義啟用條件 建議 Work-2/Work-3
                                                                                                 前由法務／採購確認後再啟用，V1
                                                                                                 維持停用
  -------------------------------------------------------------------------------------------------------------------------------

10\. 追溯矩陣一：CF-01～CF-46 → 模組對應

  ----------------------------------------------------------------------------------------
  **Freeze   **決策摘要**                                         **對應模組**
  ID**                                                            
  ---------- ---------------------------------------------------- ------------------------
  CF-01      Universe = Core/Adjacent/Watchlist                   K01、A02、G01(CFL-02)

  CF-02      CPO/Optical I/O/ELSFP/Pluggable Optics 獨立 taxonomy K02、D07
             identity                                             

  CF-03      台灣 Universe = 上市+上櫃+興櫃                       K01

  CF-04      海外公司建 Entity/Relationship，V1 不納入台股        K01、K04
             Universe                                             

  CF-05      Supply-chain Evidence Maturity = E0--E6              M01

  CF-06      允許匿名關係；Candidate ≠ Confirmed Relationship     K04、G01(CFL-05)

  CF-07      Source Credibility = S1--S5                          P05、D01--D04

  CF-08      來源保存可稽核版本與 hash/snapshot metadata          P03、I02

  CF-09      MVP Public/Official First；保留 licensed source 架構 D01--D04、D08

  CF-10      來源衝突依                                           K06、A06
             Authority+Directness+Time+Specificity+Independence   

  CF-11      Evidence 支援 SUPPORT/CONTRADICT/NEUTRAL-CONTEXT     K06

  CF-12      Seco V1 六構面                                       M03

  CF-13      Seco V1 權重 15/15/20/20/20/10，Expert Prior         M03、G04

  CF-14      Seco scale = 0--100                                  M03

  CF-15      Seco 必須伴隨 Confidence                             M03、M02

  CF-16      Seco 採 Point-in-Time / Bitemporal Versioning        M03、G04

  CF-17      Correction 與 New Evidence 分離，歷史版本保留        K05

  CF-18      CMI V1 = C1--C5 五構面                               M04

  CF-19      CMI V1 等權 Expert Prior；Phase 2 統計校準           M04、G04

  CF-20      Event Window 採多窗口 + configurable \[-N,+M\]       M06

  CF-21      Observed-Time + Event Trading Date                   P04
             Hierarchy；缺失時間不得猜測                          

  CF-21A     Event Study 保存                                     P04、K05
             time_basis/time_precision/time_confidence            

  CF-22      Trading-session Alignment + Conservative Alignment   P06

  CF-23      AR/CAR 採版本化 Benchmark，至少                      M06、G04
             Market-adjusted+Market Model                         

  CF-24      Market Cap 使用 Point-in-Time Shares Outstanding     M07

  CF-25      歷史起點採 Dataset-specific Earliest Reliable Date   P03、G04

  CF-26      TDCC/低頻資料依 availability time 進入 CMI，禁       P04、M04、D06
             backward filling                                     

  CF-27      Event 採 EV01--EV12 Taxonomy + Materiality Score     M05
             0--100                                               

  CF-28      Event ≠ Material Event；CFL-04 控制升級              M05、G01(CFL-04)

  CF-29      Confidence = CF1--CF5 Evidence-based，0--1           M02

  CF-30      Confidence V1 Rule-based/Expert Prior；Phase 2       M02、G04
             calibration                                          

  CF-31      CFL = AUTO-PASS/REVIEW-REQUIRED/BLOCKED              G01

  CF-32      Hybrid Human-AI Governance，高風險狀態需人工介入     G01、G02、A08

  CF-33      Publication = Internal Auto/Material Review/External G06
             Approval                                             

  CF-34R     Hybrid Monitoring + Batch AI Parsing；具體參數       W01、W02、W06、G08
             Deferred                                             

  CF-35      Event = Immutable + Revision Chain                   K05

  CF-36      Event status =                                       K05
             ACTIVE/CORRECTED/SUPERSEDED/WITHDRAWN/DISPUTED       

  CF-37      Phase 3 採 L0--L4 Risk-based Agent Autonomy          G02

  CF-38      L0 Deterministic Automation 可 Full Automation       A07、P層、W層、M06/M07

  CF-39      L1 AI Extraction 可建立 Candidate；Candidate ≠ Fact  A01

  CF-40      L2 AI Analysis 可 Recommendation；Recommendation ≠   A03、A04、A05
             Approval                                             

  CF-41      L3 僅低風險、規則明確、Confidence 足夠時 Conditional G02
             Autonomous Decision                                  

  CF-42      L4 = Reserved Human Authority                        A08、G02

  CF-43      Core 升級、重大具名關係、Conflict、高                G01、U04
             Materiality、Model Promotion、重大外部發布需 Human   
             Approval                                             

  CF-44      Agent 不得自行修改 Governance/Production             G02、G04、G05、G07
             Model/Autonomy                                       

  CF-45      L1--L3 AI 行為必須保留完整 Audit Trail               G03

  CF-46      Evidence/Analysis/Approval/Publication 四權分離      G02、G05
  ----------------------------------------------------------------------------------------

11\. 追溯矩陣二：GP-01～GP-21 → 治理機制對應

  ------------------------------------------------------------------------------
  **GP**   **治理原則**                             **對應機制／模組**
  -------- ---------------------------------------- ----------------------------
  GP-01    CPO Label ≠ CPO Evidence                 A02、K02

  GP-02    Absence of Evidence ≠ Evidence of        A01、M01
           Absence                                  

  GP-03    Inference ≠ Evidence                     K06、A01

  GP-04    Seco ≠ Investment Recommendation         R系列、U01（免責標示）

  GP-05    Evidence Stage ≠ Seco                    M01 與 M03 分離

  GP-06    Future Knowledge Must Not Rewrite        K05、P04
           Historical Knowledge                     

  GP-07    Unknown Time Must Remain Unknown         P04

  GP-08    No Future Data in CMI                    M04、P04

  GP-09    Effective Period ≠ Availability Time     P04、M04

  GP-10    Model Version Must Travel With Result    G04

  GP-11    LLM Confidence ≠ Research Confidence     M02

  GP-12    Materiality ≠ Truth                      M05 與 M02 分離

  GP-13    AI May Recommend; Governance Decides     G02

  GP-14    Publication Is a Separate State          G06
           Transition                               

  GP-15    History Is Immutable; Interpretation Is  K05、G04
           Versioned                                

  GP-16    Deterministic First, AI When Needed      W06、G08

  GP-17    Candidate ≠ Fact                         A01、K06

  GP-18    Recommendation ≠ Approval                A03/A04/A05 與 G01 分離

  GP-19    Autonomy Decreases as Risk Increases     G02

  GP-20    Agents Cannot Govern Themselves          G02、G04、G05、G07

  GP-21    Evidence/Analysis/Approval/Publication   G02、G05
           Must Be Separable                        
  ------------------------------------------------------------------------------

12\. Work-1 驗收標準（Acceptance Criteria）

- CF-01～CF-46 每一項均有對應模組編號，無遺漏（見第 10 節）。

- GP-01～GP-21 每一項均有對應治理機制或模組（見第 11 節）。

- Charter §29 Deferred Items 均以「掛勾點」形式呈現，未被誤設為 Frozen
  參數（見第 8 節）。

- CFL-01～08 之技術落地與 Charter §17 定義完全一致；0828 舊版 CFL
  對照表之取代關係已明確記載（見第 2、4 節）。

- Agent Autonomy L0--L4 與 Evidence/Analysis/Approval/Publication
  四權分離已對應到具體模組與 RBAC 設計（見第 5 節）。

- 本文件未產出程式碼、資料庫欄位層級 schema 或 API contract 細節（留待
  Work-2/Work-3）。

- 已列出 Work-1 自身發現之技術問題／風險／備選方案，且未以此靜默變更任何
  Frozen Decision（見第 9 節）。

- 經 Research Director／Executive User 依本標準審閱通過後，方可進入
  Work-2 Contract Freeze。

13\. Work-2 Handoff Contract

Work-2 Contract Freeze 之任務是把本 Work-1
模組架構固定為跨模組不可任意變更的「契約」，至少須完成：

- EVENT_CONTRACT.md：固定共用事件欄位（如
  event_id/project_id/entity_id/source_id/occurred_at/published_at/retrieved_at/status/version/correlation_id/causation_id/confidence/evidence_ids/cfl_status/created_at）與狀態機（DISCOVERED→FETCHED→NORMALIZED→EXTRACTED→VERIFIED→ANALYZED→APPROVED→PUBLISHED）。

- DATA_MODEL.md：K01--K06 各 Core Research Object 之資料庫 Schema。

- CFL_CONTRACT.md：本文件第 4 節 CFL-01～08
  落地點之欄位級規格與狀態機實作細節。

- API_SPEC.yaml：U01--U05 與 R01--R06 對外介面之 OpenAPI 規格。

- AGENT_SPEC.md：A01--A08 角色、RBAC 權限與 G05 對應細節。

*Work-2 完成前，不建議 Claude Code 大量撰寫 business code（SOP 步驟
6）。*

**本文件為 Work-1 草稿，待驗收通過後方可進入 Work-2 Contract Freeze。**
