CPO AI

台灣 CPO／矽光子產業情報、公司事件、生態系卡位與市值重估 AI Agent System

**WORK-3 --- IMPLEMENTATION BLUEPRINT**

Dependency DAG／WBS／Acceptance Criteria／技術選型決議／CLAUDE.md

Status: DRAFT（待 Research Director／Executive User 驗收）

Upstream: CPO AI Work-2 Contract Freeze V1.0；Work-1 Technical
Specification Baseline V1；Project Charter Freeze V1.0（FROZEN）

版本：V1.1（2026-09-10；V1.0 基線同日，見 git 歷史）　　Next Gate: Claude
Code-1 --- Repository Foundation

> V1.1 變更：新增 §5.3 語言與工具鏈補充，同步 CLAUDE.md §5／§7；依
> `docs/decisions/ADR-0001-toolchain.md`。不涉及 Charter 凍結面或 Work-2
> 契約欄位（Charter §7／§31「小幅調整」）。

**0. 文件控制**

  --------------------------------------------------------------------
  **項目**         **內容**
  ---------------- ---------------------------------------------------
  文件名稱         CPO AI Work-3 Implementation Blueprint + Acceptance
                   Criteria V1.0

  文件性質         把 Work-2 已凍結之 Data／Event／API／CFL／Agent
                   Contract 轉譯為可交棒 Claude Code
                   的工程工作包；不產出程式碼、不建立 repository
                   skeleton

  版本             V1.0（Draft for Implementation Blueprint）

  狀態             DRAFT --- 待 Research Director／Executive User
                   驗收後方可進入 Claude Code-1

  上游來源         CPO AI Work-2 Contract Freeze
                   V1.0（2026-09-10）；Work-1 Technical Specification
                   Baseline V1；Project Charter Freeze
                   V1.0（FROZEN，2026-09-05）

  隨附文件         CLAUDE.md（另立檔案，供 Claude Code 開啟 repository
                   時讀取）

  下游動作         Claude Code-1：建骨架、Schema、共用契約（只建
                   Foundation，不准一次寫完整系統）

  變更原則         本文件不得靜默修改 Charter Frozen
                   Decision（CF-01～46、GP-01～21）或 Work-2
                   已凍結之契約欄位；如需變更須回到 Charter §31 Change
                   Control。
  --------------------------------------------------------------------

**1. 目的與範圍**

本文件為 SOP 治理階段④（Projects-3 / Work-3）之產出。依 Work-2 §12
Handoff Contract 要求，須完成：Dependency DAG 與施工順序、WBS
工作包定義、ACCEPTANCE_TESTS.md、I04／I05 技術選型決議（TQ-02），以及
CLAUDE.md。

**範圍內：**

- 第 2 節：Dependency DAG 與十三批施工順序（對應 SOP 步驟 11
  之通用順序，展開為 CPO AI 實際模組）

- 第 3 節：WBS 工作包定義（每批次 1--3
  個高度相關模組，含輸入、輸出、驗收關卡）

- 第 4 節：Acceptance Tests 大綱（ACCEPTANCE_TESTS.md 內容）

- 第 5
  節：I04（工作流程引擎）／I05（向量／語意儲存）技術選型決議（TQ-02）

- 第 6 節：CLAUDE.md 定位與重點摘要（完整內容見隨附 CLAUDE.md 檔案）

**範圍外：**

- 實際程式碼與 repository 骨架（留待 Claude Code-1）

- Wake-up Window、Batch 參數、Token Budget 等 Deferred Items（延續
  Work-1 §8／Work-2 §9，本文件不解除該延遲決策）

*【治理提醒】本文件是「規格→工程」之間最後一份治理文件。完成本文件並經驗收後，Claude
Code 才可開始撰寫程式碼；且第一個 Claude Code
任務仍是「只讀規格、列出矛盾與缺口」，不是直接實作（SOP 步驟 10）。*

**2. Dependency DAG 與施工順序**

依 SOP 步驟 11 建議之通用順序（Shared Contracts → 資料庫 → Source
Registry → Ingestion → 知識庫 → 分析引擎 → Agent → 工作流程引擎 → API →
UI → Reporting → Governance → Tests），展開為 CPO AI
十層模組之實際施工批次如下。每一批完成後須執行單元／整合／migration
測試與 lint／型別檢查，通過後才可 commit 並進入下一批。

  -------------------------------------------------------------------------------------------------------------------------------------------------
  **批次**   **階段**           **涵蓋模組**                                                                             **依賴前置批次**
  ---------- ------------------ ---------------------------------------------------------------------------------------- --------------------------
  B0         Shared Contracts   Work-2                                                                                   無（治理文件，非程式碼）
                                全部契約文件（DATA_MODEL／EVENT_CONTRACT／CFL_CONTRACT／API_SPEC／AGENT_SPEC）＋本文件   
                                CLAUDE.md                                                                                

  B1         資料庫             I01 關聯式資料庫、I02 物件／快照儲存（K01--K06 schema migration）                        B0

  B2         Source Registry    D01--D08 來源登錄、P03 快照／版本控制器                                                  B1

  B3         Ingestion          P01 擷取器、P02 去重器、P04 時間標準化、P05 可信度評分器、P06 交易日對齊器               B2

  B4         知識庫             K01 公司、K02 技術／Taxonomy、K03 產品、K04 關係、K05 事件、K06 證據；G04 版本註冊中心   B3

  B5         分析引擎           M01 Evidence Stage、M02 Confidence、M03 Seco、M04 CMI、M05 Materiality、M06              B4
                                事件窗口／AR-CAR、M07 PIT 市值、M08 穩健性檢核                                           

  B6         Agent              A01 抽取、A02 分類、A03 關係／矛盾、A04 Seco/CMI 分析、A05 比較分析、A06 審查、A07       B5
                                協調、A08 人工介接閘道；G02 自治權控制器、G05 RBAC                                       

  B7         工作流程引擎       W01--W06（排程、佇列、Fan-out/Fan-in、每日管線、重試、Batch Parsing）；I04 部署          B6

  B8         治理               G01 CFL 規則引擎、G03 稽核日誌、G06 發布狀態機、G07 Change Control、G08 合規監控         B7

  B9         API                U05 匯出／API 層；第 4 節端點清單全數實作                                                B8

  B10        UI                 U01 儀表板、U02 搜尋、U03 詳情頁、U04 人工審查主控台                                     B9

  B11        Reporting          R01--R06 全部報告輸出                                                                    B10

  B12        Tests／Hardening   跨模組整合測試、E2E 每日管線測試、CFL 全流程測試、負載與異常演練                         B0--B11 全部完成
  -------------------------------------------------------------------------------------------------------------------------------------------------

*【常見錯誤提醒】不建議從漂亮的
Dashboard（U01）開始施工，也不要一次同時開工超過 1--3
個高度相關模組（SOP 步驟 11）；I04 技術選型須先於 B7 前定案，見第 5
節。*

**3. WBS 工作包定義（Work Breakdown Structure）**

每個 WBS 工作包對應第 2
節之批次，展開為「輸入（依賴之規格章節）／產出／驗收關卡」三欄，供
Claude Code 逐批領取任務。

  --------------------------------------------------------------------------------------------------------------------------------
  **WBS**   **輸入（規格依據）**      **產出**                                          **驗收關卡（進入下一批前）**
  --------- ------------------------- ------------------------------------------------- ------------------------------------------
  WBS-B1    Work-2 §2                 K01--K06 資料表 migration、通用稽核欄位、G04      Migration 測試通過；欄位命名與
            DATA_MODEL.md（K01--K06   版本註冊表                                        DATA_MODEL.md 逐一比對無落差
            欄位）                                                                      

  WBS-B2    Work-1 §3.1               來源登錄資料表、P03 快照／hash／版本控制器        任一來源可回溯至 content_hash 與
            D01--D08；Work-2 §2.7 K06                                                   snapshot_ref
            source_id                                                                   

  WBS-B3    Work-2 §2.1               P01--P06 擷取管線，輸出符合 Event Contract        缺失時間欄位保持
            通用時間欄位；§3 Event    欄位之標準化資料                                  NULL（非猜測值）；交易日對齊規則測試通過
            Contract                                                                    

  WBS-B4    Work-2 §2.2--2.7 K01--K06 知識庫 CRUD／查詢層，含                           K05 Event 修正鏈測試：CORRECTED 不覆寫
            Schema                    Bitemporal（valid_from/valid_to）與 Event         ACTIVE 舊版本
                                      Revision Chain 實作                               

  WBS-B5    Work-1 §3.4               Seco／CMI／Materiality／Confidence／AR-CAR／PIT   M04 CMI 無 backward filling（GP-08）；M07
            M01--M08；CF-05/12-30     市值計算模組                                      使用 PIT Shares Outstanding（CF-24）

  WBS-B6    Work-1 §5 Autonomy        A01--A08 Agent 實作、G02 自治權控制器、G05 RBAC   四權分離測試：任一 Agent 角色不得同時具
            L0--L4；Work-2 §6                                                           Evidence 與 Approval/Publication
            AGENT_SPEC.md                                                               權（GP-21）

  WBS-B7    SOP 步驟 12；第 5 節 I04  W01--W06 工作流程、Fan-out/Fan-in 編排            重試／逾時／Fan-in 匯流整合測試通過
            決議                                                                        

  WBS-B8    Work-2 §5 CFL_CONTRACT.md G01 CFL 狀態機、G03 稽核日誌、G06                 CFL-07 矛盾資料不得 Auto-pass；CFL-08
                                      發布狀態機、G07/G08                               未核准不得進入 PUBLISHED

  WBS-B9    Work-2 §4 API_SPEC.yaml   U05／API 層，第 4.2 節端點全數實作                所有寫入 cfl_status 之端點皆經
                                                                                        G01；錯誤碼格式符合 4.3 節規範

  WBS-B10   Work-1 §3.9 U01--U05      儀表板、搜尋、詳情頁、Admin 審查主控台            U04 可完整操作 CFL Queue 核准／駁回流程

  WBS-B11   Work-1 §3.7 R01--R06      全部報告輸出（含 Internal Auto／Material          R06 正式外部發布須先通過 CFL-08
                                      Review／External Approval 三層）                  

  WBS-B12   第 4 節 Acceptance Tests  跨模組整合與 E2E 測試套件                         第 4 節全部測項通過，回 Projects 進行
            全表                                                                        Acceptance（SOP 第四節）
  --------------------------------------------------------------------------------------------------------------------------------

**4. Acceptance Tests 大綱（ACCEPTANCE_TESTS.md）**

下列測項為每批交付與最終 Projects 驗收時之必要檢核，逐項對應
Work-1／Work-2 之 CF／GP 與契約章節，作為 ACCEPTANCE_TESTS.md 之骨架。

  ---------------------------------------------------------------------------------------------
  **測項編號**    **測試內容**                                                 **依據**
  --------------- ------------------------------------------------------------ ----------------
  TEST-DATA-01    K01--K06 各實體之欄位命名、型別與 DATA_MODEL.md              Work-2 §2
                  完全一致，無同義異名欄位                                     

  TEST-DATA-02    缺失之 occurred_at／published_at／market_known_at            CF-21；GP-07
                  等時間欄位保持 NULL，未被虛假精度填補                        

  TEST-EVENT-01   事件狀態機僅能依 DISCOVERED→...→PUBLISHED                    Work-2 §3.2
                  順序推進，非法跳轉須被拒絕                                   

  TEST-EVENT-02   K05 Event 為 Immutable：CORRECTED／SUPERSEDED 狀態變更以新   CF-35/36
                  revision 寫入，不覆寫原始事件                                

  TEST-CFL-01     CFL-07 矛盾資料（CONTRADICT                                  Work-2 §5
                  Evidence）不得被系統自動核准（Auto-pass）                    

  TEST-CFL-02     CFL-08 未通過人工核准前，事件無法進入 PUBLISHED 狀態         CF-33；G06

  TEST-CFL-03     任一模組嘗試繞過 G01 直接寫入 cfl_status 須被拒絕            Work-2 §5.2

  TEST-RBAC-01    任一 Agent／使用者角色不得同時擁有 Evidence 寫入與           GP-21；G02/G05
                  Approval／Publication 權限                                   

  TEST-CMI-01     M04 CMI 計算不得使用尚未達 availability time 的未來資料（No  GP-08；CF-26
                  Future Data）                                                

  TEST-PIT-01     M07 市值計算使用對應時間點之 Point-in-Time Shares            CF-24
                  Outstanding，而非目前最新值                                  

  TEST-VER-01     Seco／CMI／Materiality／Confidence 任一模型權重變更須產生新  GP-10；G04
                  Model Version，不得覆寫既有結果                              

  TEST-EVID-01    Evidence 之                                                  CF-07/08/11
                  evidence_type（SUPPORT／CONTRADICT／NEUTRAL-CONTEXT）與      
                  source_credibility_tier（S1--S5）皆有值且可追溯至            
                  content_hash                                                 

  TEST-WF-01      W05 重試／逾時工作流：模擬下游失敗後可正確重試且不重複寫入   Charter §22
                                                                               Auditability

  TEST-API-01     第 4.2 節所列端點回應皆含 version 與 cfl_status 欄位；4xx    Work-2 §4
                  錯誤含統一 error_code 格式                                   

  TEST-E2E-01     完整跑一次每日研究管線（Discover→...→Publish），Completion   SOP 第四節
                  Report 與各測項結果一併送回 Projects 驗收                    
  ---------------------------------------------------------------------------------------------

**5. I04／I05 技術選型決議（TQ-02）**

Work-1 §9 TQ-02 指出 2026-08-28
參考文件建議之工作流程引擎與向量儲存屬技術參考而非 Frozen Decision，須於
Work-3 正式選型。以下為建議決議，仍待團隊技術能力與成本最終確認後生效。

**5.1 I04：工作流程引擎**

  -------------------------------------------------------------------------------------------------------------------
  **方案**                      **優點**                                    **疑慮／成本**
  ----------------------------- ------------------------------------------- -----------------------------------------
  Temporal（自架或 Temporal     原生支援                                    學習曲線較高；自架需額外維運人力
  Cloud）                       Fan-out／Fan-in、長時間執行、重試與版本化   
                                Workflow，與 W01--W06 需求高度吻合          

  Apache Airflow                團隊熟悉度可能較高、生態成熟                偏批次排程設計，長時間人工核准等待（CFL
                                                                            Review）與動態 Fan-out 支援較弱

  AWS Step                      免自架維運，與雲端資源整合快                廠商綁定；複雜分支邏輯之維護成本較高
  Functions（或等效雲端服務）                                               
  -------------------------------------------------------------------------------------------------------------------

**【決議】I04 建議採用 Temporal 作為工作流程引擎，理由：W03
Fan-out／Fan-in、W05 重試／逾時、W06 Batch AI Parsing
三者皆需要原生的長時間執行與版本化工作流支援，Temporal
最貼合此需求；若團隊評估自架維運成本過高，可改用 Temporal Cloud
託管版本，介面與程式碼不需變更。此決議待技術團隊於 Claude Code-1
開工前最終確認。**

**5.2 I05：向量／語意儲存**

  ----------------------------------------------------------------------------------------------------------------------------------------------
  **方案**                                       **優點**                                             **疑慮／成本**
  ---------------------------------------------- ---------------------------------------------------- ------------------------------------------
  pgvector（PostgreSQL 擴充套件）                與 I01                                               極大規模語意檢索時效能不如專用向量資料庫
                                                 關聯式資料庫共用同一套維運，降低基礎設施複雜度，V1   
                                                 資料量下效能足夠                                     

  Pinecone／Weaviate／Milvus（專用向量資料庫）   檢索效能與擴充性佳                                   新增一套需維運的基礎設施，V1
                                                                                                      階段成本效益不明顯
  ----------------------------------------------------------------------------------------------------------------------------------------------

**【決議】I05 建議 V1 採用 pgvector，供 P02 去重與 K04
關係／實體語意相似度比對使用；待資料量與查詢量成長至專用向量資料庫效益明確時，再評估遷移（不影響上層
Data／Event Contract）。**

*以上兩項決議回應 Work-1 TQ-02，不構成 Charter Frozen Decision
之變更，僅為 Work-3 階段之工程實作選型。*

**5.3 語言與工具鏈補充（V1.1，2026-09-10）**

CLAUDE.md §5／§7 之「待補充」工具鏈欄位已於 Claude Code-1 開工前定案，權威記錄見
`docs/decisions/ADR-0001-toolchain.md`（經 Research
Director／Executive User 核可）。摘要：

- 語言 Python 3.12；DB PostgreSQL 16 + pgvector；Migration Alembic
- 工作流程 SDK `temporalio`（Python）；API FastAPI + Pydantic v2
- 科學計算 numpy／pandas／statsmodels／scipy
- LLM 供應商 Claude（Anthropic），`anthropic` Python SDK；model
  id／token budget 以設定值注入（Deferred，不寫死）
- 型別 Mypy（src strict）；低風險預設 uv、Ruff（team 可替換）
- UI（B10）暫定 React + TypeScript + Vite，另立 ADR 再議
- 測試指令：見 ADR-0001 §4 與 CLAUDE.md §7

本補充不觸及 Charter 凍結面與 Work-2 契約欄位，依 Charter §7／§31
屬「小幅調整」，CLAUDE.md 與本文件同步升 V1.1，不開新 Charter 版本。

**6. CLAUDE.md 定位與重點摘要**

CLAUDE.md 是 Claude Code 開啟 repository
時主動讀取的工作邊界文件，完整內容另立檔案（CLAUDE.md）隨附提供，需與
Work-1／Work-2 規格文件一併放入 /docs 目錄。其重點摘要如下：

- 允許操作：依規格實作模組、撰寫並執行測試、建立可回溯之 migration

- 明確禁止：修改已凍結契約文件、刪除既有 migration、跳過測試、繞過 G01
  CFL 狀態機、違反四權分離（GP-21）、CMI 使用未來資料（GP-08）、覆寫既有
  Model Version（GP-10）

- 分批施工規則：一次僅實作第 2 節所定義之 1 個批次（1--3
  個高度相關模組），完成後才進入下一批

- 何時必須停下詢問人類：規格文件間出現矛盾、CFL 判定為
  REVIEW-REQUIRED／BLOCKED、任何觸及 Frozen Decision（CF/GP）變更之情形

*【檔案位置提醒】完整版 CLAUDE.md 請見隨附檔案，於 Claude Code-1
開工前，需與本文件、Work-1、Work-2 一併放入 repository 之 /docs
目錄（SOP 步驟 9）。*

**7. Work-3 驗收標準（Acceptance Criteria）**

- Dependency DAG（第 2 節）涵蓋 Work-1 十層模組全數，批次順序符合 SOP
  步驟 11 通用原則

- WBS 工作包（第 3 節）每批次皆有明確輸入、產出與驗收關卡，且批次規模為
  1--3 個高度相關模組

- Acceptance Tests（第 4 節）逐一對應 Work-1／Work-2 之 CF／GP
  與契約章節，涵蓋 Data／Event／CFL／RBAC／API 各面向

- I04／I05 技術選型決議（第 5 節）已提出並說明理由，不構成 Frozen
  Decision 變更

- CLAUDE.md（隨附檔案）已涵蓋允許／禁止操作、分批施工規則與人工介入時機

- 本文件與隨附 CLAUDE.md 未產出任何 business code 或 repository 骨架

- 經 Research Director／Executive User 依本標準審閱通過後，方可進入
  Claude Code-1

**8. Claude Code-1 Handoff（下一步）**

依 SOP 步驟 9、10，Claude Code-1 之首要任務並非直接實作，而是：

- 先將 /docs
  全部規格文件（Charter、Work-1、Work-2、本文件、CLAUDE.md）放入
  repository，不進行任何程式碼撰寫

- 第一個任務指令：讀取 /docs
  全部規格，不修改任何檔案；列出模組依賴圖、實作順序、規格矛盾、缺少的
  environment variables、外部 API 與 database migration；確認後再開始
  implementation

- 確認無矛盾後，依第 2 節批次順序，從 WBS-B1（資料庫／Shared Contracts
  落地）開始，只建立 Foundation，不准一次寫完整系統

*本文件為 Work-3 草稿，待驗收通過後方可進入 Claude Code-1 --- Repository
Foundation。*
