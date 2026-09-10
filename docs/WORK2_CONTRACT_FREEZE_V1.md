CPO AI

台灣 CPO／矽光子產業情報、公司事件、生態系卡位與市值重估 AI Agent System

**WORK-2 --- CONTRACT FREEZE**

Data／Event／API／CFL／Agent Contract --- Technical Specification

Status: TECHNICAL SPECIFICATION COMPLETE（待 Research
Director／Executive User 驗收）

Upstream: CPO AI Work-1 Technical Specification Baseline
V1（2026-09-10）；Project Charter Freeze V1.0（2026-09-05, FROZEN）

版本：V1.4（2026-09-10；V1.0 基線同日，見 git 歷史）　　Next Gate: Work-3
--- Implementation Blueprint

> **V1.1 變更（`docs/decisions/ADR-0002-naming.md`，RD／EU 核可）**：欄位消歧，不改語意／enum、不觸及 Charter 凍結面。
> (1) §2.6 K05 `status` → `lifecycle_status`。(2) §3.1 事件欄位 `status` → `pipeline_status`。(3) §2.3 K02 `effective_from／effective_to` → `valid_from／valid_to`。
>
> **V1.2 變更（`docs/decisions/ADR-0003-schema-gaps.md`，RD／EU 核可）**：補契約缺口，皆為新增、不改既有欄位語意（Change Request 依 §2.8／Charter §31）。
> (4) §2.1 新增 `available_at`（低頻資料可取得時間，CF-26／GP-09）。
> (5) §2.6 K05 新增 `revision_seq`。
> (6) 新增 §2.9：market_data／institutional_trading／shareholding／person／seco_score／cmi_score／valuation_event_window／research_report 八張表（逐欄型別待 B1／B5 依 ADR-0003 訂定）。
>
> **V1.3 變更（`docs/decisions/ADR-0004-cfl-order-rbac.md`，RD／EU 核可）**：
> (7) §4.4 補齊認證（OIDC/JWT）與 RBAC 六角色矩陣（原「待 Work-3 補齊」佔位取代）。
>
> **V1.4 變更（`docs/decisions/ADR-0006-confirmations.md`，RD／EU 核可）**：
> (8) §3.3 註明事件型別目錄產出於 WBS-B7（`docs/EVENT_CATALOGUE.md`），傳輸層 = Temporal + `event` 表 outbox。

**0. 文件控制**

  ---------------------------------------------------------------------
  **項目**         **內容**
  ---------------- ----------------------------------------------------
  文件名稱         CPO AI Work-2 Contract Freeze --- Technical
                   Specification V1.0

  文件性質         將 Work-1 Technical Specification Baseline V1
                   之十層模組架構，凍結為跨模組不可任意變更的
                   Data／Event／API／CFL／Agent 契約；不產出 business
                   code，不做技術選型最終確認

  版本             V1.4（V1.1 消歧 / V1.2 缺口 / V1.3 §4.4 認證 / V1.4 §3.3 事件目錄；V1.0 基線見 git）

  狀態             DRAFT --- 待 Research Director／Executive User
                   驗收後方可進入 Work-3

  上游來源         CPO AI Work-1 Technical Specification Baseline
                   V1（2026-09-10）；CPO AI Project Charter Freeze
                   V1.0（FROZEN，2026-09-05）

  下游文件         Work-3 Implementation Blueprint + Acceptance
                   Criteria；CLAUDE.md

  變更原則         本文件不得靜默修改 Charter 之 Frozen
                   Decision（CF-01～CF-46、GP-01～GP-21），亦不得修改
                   Work-1 已定義之模組編號與依賴。若需變更，須回到
                   Charter Change Control（Charter §31）。
  ---------------------------------------------------------------------

**1. 目的與範圍**

本文件為 SOP 治理階段③（Projects-2 / Work-2）之產出，目的是把 Work-1
定義的十層模組架構（D/P/K/M/A/W/R/G/U/I）與 CFL-01～08
落地點，固定為跨模組不可任意變更的「契約」，使 Claude Code 在 Work-3
開始大量撰寫 business code 之前，各模組已有共同語言可以互接。

**範圍內：**

- DATA_MODEL.md：K01--K06 核心研究物件之資料庫 Schema（第 2 節）

- EVENT_CONTRACT.md：共用事件欄位與狀態機（第 3 節）

- API_SPEC.yaml 大綱：U01--U05、R01--R06 對外介面（第 4 節）

- CFL_CONTRACT.md：CFL-01～08 欄位級規格與狀態機實作細節（第 5 節）

- AGENT_SPEC.md：A01--A08 角色、RBAC 權限與四權分離對應（第 6 節）

**範圍外（留待 Work-3）：**

- I04／I05 工作流程引擎與向量儲存之最終技術選型（TQ-02）

- Wake-up Window、Batch Size、Token Budget 等 Operations 參數（延續
  Charter §29 Deferred Items，見第 9 節）

- Repository 結構、部署拓撲、CI/CD 細節

*【延續聲明】Work-1 §2 之協調聲明（Reconciliation
Note）於本文件延續有效：CFL-01～08 唯一權威版本為 Charter §17／Work-1
§4；2026-08-28 舊版 CFL 對照表視為歷史參考，不作為本契約依據（對應
TQ-01）。*

**2. Data Contract --- DATA_MODEL.md（K01--K06 核心研究物件 Schema）**

**2.1 通用稽核與時間欄位規範**

依 Charter CF-21／P04 Observed-Time
階層，所有具時間屬性之實體共用下列時間欄位，缺失一律保持
NULL，不得虛假精度填補：

  -----------------------------------------------------------------------------------------------
  **欄位**                                      **說明**                          **依據**
  --------------------------------------------- --------------------------------- ---------------
  occurred_at                                   事件實際發生時間（Optional）      CF-21

  published_at                                  來源發布時間（Preferred）         CF-21

  retrieved_at                                  系統擷取時間（Required）          CF-21

  market_known_at                               市場得知時間（Optional／僅        CF-21
                                                Evidence 使用）                   

  available_at                                  資料在市場／公開實際可取得之時間；   CF-26；
                                                低頻資料（TDCC 等）必填，供 M04     GP-09
                                                CMI 判斷 No-Future-Data；與         （V1.2）
                                                market_known_at 不同               

  event_trading_date                            事件研究交易日（Event Study       CF-21
                                                必填）                            

  time_basis／time_precision／time_confidence   時間依據、精度與信心註記          CF-21A
  -----------------------------------------------------------------------------------------------

此外，所有實體共用以下稽核／治理欄位：

  -------------------------------------------------------------------------------------------------------
  **欄位**                 **說明**
  ------------------------ ------------------------------------------------------------------------------
  confidence               CF1--CF5 Evidence-based Confidence，範圍 0--1（M02，CF-29/30）

  cfl_status               對應 CFL-01～08 狀態機（見第 5
                           節）：PENDING/AUTO-PASS/REVIEW-REQUIRED/APPROVED/REJECTED/BLOCKED/SUPERSEDED

  model_version_id         所用計算模型版本，隨結果攜帶，不得覆寫既有版本結果（G04，GP-10）

  valid_from／valid_to     Bitemporal 設計中的 Effective Time（區別於 Knowledge Time／created_at）

  created_at／updated_at   系統寫入稽核時間
  -------------------------------------------------------------------------------------------------------

**2.2 K01 公司實體（Company）**

  ------------------------------------------------------------------------------
  **欄位**                   **說明**                            **依據**
  -------------------------- ----------------------------------- ---------------
  company_id                 系統唯一鍵（主鍵）                  ---

  stock_code／company_name   股票代碼／公司名稱                  ---

  universe                   Core／Adjacent／Watchlist           CF-01；CFL-02

  listing_market             上市／上櫃／興櫃                    CF-03

  is_overseas                是否為海外公司（V1 不納入台股       CF-04
                             Universe，僅建                      
                             Entity/Relationship）               

  taxonomy_refs              關聯 K02 Taxonomy（版本化）         CF-02
  ------------------------------------------------------------------------------

**2.3 K02 技術／Taxonomy（Technology，版本化）**

  --------------------------------------------------------------------------------
  **欄位**                       **說明**                               **依據**
  ------------------------------ -------------------------------------- ----------
  technology_id                  系統唯一鍵                             ---

  taxonomy_version_id            關聯 G04 版本註冊中心                  GP-10

  category                       CPO／Optical I/O／ELSFP／Pluggable     CF-02
                                 Optics（各自獨立 taxonomy identity）   

  parent_technology_id           上層分類（供樹狀結構）                 Charter
                                                                        §10

  valid_from／valid_to           分類版本有效區間（統一 2.1 通用命名，   GP-10
                                 V1.1）                                 
  --------------------------------------------------------------------------------

**2.4 K03 產品／模組／規格實體（Product）**

  ------------------------------------------------------------------------------
  **欄位**                    **說明**                              **依據**
  --------------------------- ------------------------------------- ------------
  product_id                  系統唯一鍵                            ---

  company_id／technology_id   所屬公司與對應技術分類                Charter §9

  evidence_stage              供應鏈成熟度 E0--E6                   CF-05；M01

  spec_summary                規格摘要（衍生欄位，不作識別鍵）      ---
  ------------------------------------------------------------------------------

**2.5 K04 關係圖譜（Relationship，含 Person）**

  ----------------------------------------------------------------------------------------
  **欄位**                             **說明**                            **依據**
  ------------------------------------ ----------------------------------- ---------------
  relationship_id                      系統唯一鍵                          ---

  source_entity_id／target_entity_id   關係兩端實體（可為                  CF-06
                                       Company／Person）                   

  relationship_type                    客戶／供應商／夥伴／競爭者          Charter §9

  is_named                             是否具名（允許匿名關係存在）        CF-06

  status                               CANDIDATE／CONFIRMED（Candidate ≠   GP-17；CFL-05
                                       Confirmed）                         

  evidence_ids                         佐證證據 ID 清單                    K06
  ----------------------------------------------------------------------------------------

**2.6 K05 事件實體與修正鏈（Event，Immutable + Revision）**

  ------------------------------------------------------------------------------------------------------------------
  **欄位**               **說明**                                                                       **依據**
  ---------------------- ------------------------------------------------------------------------------ ------------
  event_id               系統唯一鍵，Immutable                                                          CF-35

  revision_of_event_id   指向被修正之原事件（Revision Chain，自我參照）                                 CF-35

  revision_seq           修正鏈序號（整數，同一 event_id 鏈內遞增，起始 1；V1.2 新增）                  CF-35

  lifecycle_status       ACTIVE／CORRECTED／SUPERSEDED／WITHDRAWN／DISPUTED（撤回不等於歷史未曾存在；V1.1 由 `status` 更名，enum 不變）   CF-36

  event_taxonomy_code    EV01--EV12                                                                     CF-27；M05

  materiality_score      0--100（Event ≠ Material Event，CFL-04 控制升級）                              CF-27/28

  （時間欄位）           沿用 2.1 通用時間欄位規範                                                      CF-21／P04

  cfl_status             對應 CFL-04 審查狀態                                                           CFL-04
  ------------------------------------------------------------------------------------------------------------------

**2.7 K06 證據與引用存放（Evidence／Source／Citation）**

  ------------------------------------------------------------------------------------------------------------------------
  **欄位**                                                 **說明**                                       **依據**
  -------------------------------------------------------- ---------------------------------------------- ----------------
  evidence_id                                              系統唯一鍵                                     ---

  source_id                                                來源登錄（關聯 P03 快照與 hash）               CF-08

  entity_ref／event_ref                                    多型參照（Company／Relationship／Event 等）    K06

  evidence_type                                            SUPPORT／CONTRADICT／NEUTRAL-CONTEXT           CF-11

  evidence_stage                                           E0--E6                                         CF-05

  source_credibility_tier                                  S1--S5                                         CF-07

  authority／directness／time／specificity／independence   來源衝突判準之五項評分                         CF-10

  content_hash／snapshot_ref                               原始內容雜湊與快照位置（不可竄改稽核）         CF-08

  cfl_status                                               對應                                           CFL-03；CFL-07
                                                           CFL-03（來源可信度）／CFL-07（矛盾資料，不得   
                                                           Auto-pass）                                    
  ------------------------------------------------------------------------------------------------------------------------

**2.8 版本控管規則**

任一 Schema 欄位新增、型別變更或主鍵變更，皆須提出 Change
Request（Charter §31），經 Projects 驗收後升版為
V1.1／V1.2......，不得直接覆寫本文件或既有資料。K02／M03／M04／M05／M02／CFL
等模型或分類權重變更，一律經 G04 建立新 Model
Version，不得回填覆寫既有結果（GP-10）。

**2.9 補充實體 Schema（V1.2，依 `docs/decisions/ADR-0003-schema-gaps.md`）**

Charter §9 列 16 個 Core Research Object，§2.2–2.7 僅涵蓋 K01–K06。以下
7 個物件於 V1.2 補齊為契約實體；逐欄型別留待 Claude Code-1 於 WBS-B1／B5
依 ADR-0003 訂定（本表僅固定表名、關鍵欄位與依據，型別標「待確認」）。
K01–K06 編號與 Work-1 §3.3 不變。

原始資料實體（D 層來源，B1／B2／B3 建置）：

  ----------------------------------------------------------------------------------------
  **表名**                **關鍵欄位（型別待確認）**                         **來源／依據**
  ----------------------- -------------------------------------------------- -------------
  market_data             market_data_id(PK)、company_id(FK)、trade_date、   D05；CF-24
                          close_price、volume、**shares_outstanding**（PIT，  
                          隨 valid_from/valid_to）、通用時間／稽核欄位       

  institutional_trading   institutional_trading_id(PK)、company_id(FK)、     D05
                          trade_date、investor_type、net_buy_sell、          
                          available_at、通用時間／稽核欄位                  

  shareholding            shareholding_id(PK)、company_id(FK)、as_of_date、  D06 TDCC；
                          bucket、holders、shares、pct、**available_at**（必  CF-26；
                          填）、通用時間／稽核欄位                          GP-08/09

  person                  person_id(PK)、full_name、role_title、             Charter §9；
                          affiliation_company_id(FK, nullable)、通用時間／   CF-06
                          稽核欄位；K04 關係兩端可指向 company 或 person    
  ----------------------------------------------------------------------------------------

模型輸出／報告實體（B5／B11 建置，皆 Bitemporal、隨 model_version_id）：

  ----------------------------------------------------------------------------------------
  **表名**                  **關鍵欄位（型別待確認）**                       **模組／依據**
  ------------------------- ----------------------------------------------- --------------
  seco_score                seco_score_id(PK)、company_id(FK)、as_of、       M03；
                            score(0–100)、tech_relevance、product_readiness、CF-12～17
                            customer_validation、ecosystem_position、        
                            commercialization、strategic_defensibility、     
                            confidence、valid_from/valid_to、model_version_id

  cmi_score                 cmi_score_id(PK)、company_id(FK)、as_of、         M04；
                            score、foreign_inst_momentum、                   CF-18/19；
                            domestic_inst_momentum、margin_short、           GP-08
                            ownership_concentration、trading_structure、      
                            valid_from/valid_to、model_version_id            

  valuation_event_window    valuation_event_window_id(PK)、event_id(FK)、    M06；
                            window(\[-N,+M\])、benchmark_model、ar、car、     CF-20/23/24
                            market_cap、model_version_id                     

  research_report           research_report_id(PK)、report_type、subject_ref、R02；
                            version、publication_tier、cfl_status、           CF-33；
                            content_ref、model_version_id、通用稽核欄位      Charter §18
  ----------------------------------------------------------------------------------------

Seco／Confidence 構面欄位命名依 ADR-0002（具名，不用 S1..S6／CF1..CF5）。

**3. Event Contract --- EVENT_CONTRACT.md**

**3.1 通用事件欄位（固定，跨模組共用）**

**event_id / project_id / entity_id / source_id / occurred_at /
published_at / retrieved_at / pipeline_status / version / correlation_id /
causation_id / confidence / evidence_ids / cfl_status / created_at**

> V1.1：`status` → `pipeline_status`（事件處理管線狀態，見 3.2）。K05
> 實體另有 `lifecycle_status`（見 2.6）；兩者為不同欄位，勿混用。

  --------------------------------------------------------------------------------------------
  **欄位**                                  **說明**
  ----------------------------------------- --------------------------------------------------
  event_id                                  事件唯一識別碼

  project_id                                所屬專案（CPO AI）

  entity_id                                 關聯之核心研究物件（Company／Event／Relationship
                                            等）

  source_id                                 資料來源（關聯 K06／P03）

  occurred_at／published_at／retrieved_at   Observed-Time 階層（見 2.1）

  pipeline_status                           事件處理管線狀態，見 3.2（V1.1
                                            由 `status` 更名）

  version                                   事件／資料版本號

  correlation_id                            同一業務流程之關聯識別碼

  causation_id                              觸發本事件之上一事件 ID（因果鏈追蹤）

  confidence                                CF1--CF5 可信度分數

  evidence_ids                              佐證證據 ID 清單（K06）

  cfl_status                                對應 CFL-01～08 審查狀態

  created_at                                事件寫入時間
  --------------------------------------------------------------------------------------------

**3.2 事件狀態機（`pipeline_status`，對應 W04 每日研究管線工作流）**

**DISCOVERED → FETCHED → NORMALIZED → EXTRACTED → VERIFIED → ANALYZED →
APPROVED → PUBLISHED**

  -----------------------------------------------------------------------------------------
  **狀態**       **對應模組**                  **說明**
  -------------- ----------------------------- --------------------------------------------
  DISCOVERED     W01／W02                      候選來源被發現／進入 Priority Trigger 佇列

  FETCHED        P01                           已擷取原始資料

  NORMALIZED     P02／P03／P04／P06            去重、快照版本控制、時間標準化、交易日對齊

  EXTRACTED      A01（L1）                     AI 抽取代理建立 Candidate，Candidate ≠ Fact

  VERIFIED       P05／A06                      來源可信度評分、矛盾與洩漏風險審查

  ANALYZED       M01--M08／A02--A05（L1/L2）   分類、Seco／CMI／Materiality 計算與分析建議

  APPROVED       G01（CFL-01～08）             通過對應 CFL 規則之人工或自動核准

  PUBLISHED      G06／R01--R06                 依 Internal Auto／Material Review／External
                                               Approval 三層發布
  -----------------------------------------------------------------------------------------

**3.3 事件與模組觸發對應（Topic 命名模板）**

建議命名規則：cpoai.\<layer\>.\<event_type\>，例如
cpoai.ingestion.source_fetched、cpoai.knowledge.event_revised、cpoai.governance.cfl_decision。

*V1.3（ADR-0006）：完整事件型別目錄留待 **WBS-B7** 開工時產出
`docs/EVENT_CATALOGUE.md`（逐一列 `cpoai.<layer>.<event_type>`）；B3–B6
先用最小集，B7 補全。傳輸層＝Temporal workflow/activity/signal + `event`
表 outbox（ADR-0004），`<layer>` 用資料夾名（ingestion／knowledge／
models／agents／workflows／reports／governance／api／ui）。*

**4. API Contract --- API_SPEC.yaml 大綱**

**4.1 設計原則**

- 所有欄位命名與 Data Contract（第 2 節）、Event Contract（第 3
  節）一致，不得另創別名

- 任一 API 端點對應之角色權限須符合 G05 RBAC 與 GP-21
  四權分離：Evidence／Analysis／Approval／Publication
  四種功能不得由同一角色帳號跨權操作

- 涉及 cfl_status 變更之寫入端點，一律經 G01 CFL 規則引擎，不得繞過

**4.2 端點清單（依 U01--U05、R01--R06 展開）**

  -----------------------------------------------------------------------------------
  **方法／路徑**                 **說明**                              **對應模組**
  ------------------------------ ------------------------------------- --------------
  GET /dashboard/seco-cmi        Seco／CMI 儀表板資料                  R03／U01

  GET /companies                 公司／Universe 清單查詢               K01／U02

  GET /companies/{company_id}    公司詳情（含                          K01／U03
                                 Evidence／Citation／Revision 歷史）   

  GET /events                    事件流查詢（可依                      K05／U02
                                 status／materiality／correlation_id   
                                 篩選）                                

  GET /events/{event_id}         事件詳情與修正鏈                      K05／U03

  GET /reports/{report_id}       公司／事件研究報告（依 Materiality    R02
                                 分流）                                

  GET /event-studies/{event_id}  事件窗口／CAR 報告                    R04

  GET                            比較與競爭分析報告（CFL-06 管控）     R05
  /comparisons/{comparison_id}                                         

  POST                           正式外部發布核准（CFL-08）            R06／G06
  /publications/{id}/approve                                           

  POST /cfl/{cfl_id}/decision    CFL 人工審查／核准／駁回              G01／U04

  GET /exports                   報告匯出（R01--R06 匯出格式）         U05
  -----------------------------------------------------------------------------------

**4.3 狀態碼與錯誤碼規範**

  --------------------------------------------------------------------
  **類別**         **規則**
  ---------------- ---------------------------------------------------
  成功             2xx，回應內容須包含對應資源之 version 與 cfl_status
                   欄位

  用戶端錯誤       4xx，錯誤內容須含統一
                   error_code（格式：\<MODULE\>-ERR-\<NNN\>）

  伺服器錯誤       5xx，須記錄 correlation_id 供追蹤與重試判斷（W05）

  CFL 阻擋         409／423，用於 CFL-07 矛盾資料不得 Auto-pass
                   或狀態被 BLOCKED 之情形
  --------------------------------------------------------------------

**4.4 認證與權限（V1.3，依 `docs/decisions/ADR-0004-cfl-order-rbac.md`）**

**認證**：OAuth2／OIDC bearer（JWT），由外部 IdP 簽發；API 驗證 JWT 後將
claims 對映至 Charter §5 六類角色。`OIDC_ISSUER`／`OIDC_AUDIENCE`／
`OIDC_JWKS_URL` 一律經環境變數注入（CLAUDE.md §9）。

**RBAC 矩陣**（角色 × 端點功能群組；強制 GP-21 四權分離）：

  ------------------------------------------------------------------------------------------------
  **角色**                讀   Evidence／實體寫   模型執行   審查佇列   核准／發布   Ops／設定
  ----------------------- ---- ----------------- ---------- ---------- ------------ -------------
  Research Director        ✓    –                 –          ✓          ✓            –

  Semiconductor Analyst    ✓    ✓                 –          –          –            –

  Quant Researcher         ✓    –                 ✓          –          –            –

  Research Reviewer        ✓    –                 –          ✓          –            –

  Executive User           ✓（摘要）  –           –          –          –            –

  System Administrator     ✓    –                 –          –          –            ✓
  ------------------------------------------------------------------------------------------------

無任一角色同時具「Evidence／實體寫」與「核准／發布」→ 符合 GP-21／CF-46。
端點→功能群組之細目對照留待 WBS-B9 依本矩陣展開，不得新增跨權組合。
Agent 帳號（A01–A08）之權限由 G05 依同一矩陣精神設定（Work-1 §5、第 6 節）。

**5. CFL Contract --- CFL_CONTRACT.md（Charter §17 為唯一有效版本）**

下表為 CFL-01～08 之候選產生模組、判斷／審查模組與 V1 核准原則，逐項對應
Charter §17 正式凍結定義，與 2026-08-28 舊版 CFL 對照表（已停用，見第 1
節延續聲明）無關。

  --------------------------------------------------------------------------------------------
  **CFL**   **治理對象**   **候選產生模組**   **判斷／審查模組**   **V1 原則**
  --------- -------------- ------------------ -------------------- ---------------------------
  CFL-01    公司身分       A02                G01 + G05            高 Confidence、可驗證者
                                                                   Auto-pass

  CFL-02    CPO 分類       A02                G01 → U04            首次升 Core 需 Human Review

  CFL-03    來源可信度     P05                G01                  已知官方來源
                                                                   Auto-pass；新／未知來源需
                                                                   Review

  CFL-04    重大事件       M05                G01 → U04            一般事件 AI 分類；高
                                                                   Materiality 需 Human Review

  CFL-05    生態系關係     A03／K04           G01 → U04            Candidate 可保存；重大具名
                                                                   Confirmed 首次需 Human
                                                                   Review

  CFL-06    競爭分析       A05                G01 → U04            AI 可 Draft；正式重大結論需
                                                                   Human Review

  CFL-07    矛盾資料       A06／K06           G01（不得            重大 CONTRADICT Evidence
                                              Auto-pass）          不得 Auto-pass

  CFL-08    發布核准       R06                G06 → U04            正式外部重大研究結論 Human
                                                                   Approval Required
  --------------------------------------------------------------------------------------------

**5.2 CFL 狀態機（G01 統一實作，禁止繞過）**

**PENDING → AUTO-PASS／REVIEW-REQUIRED → APPROVED／REJECTED／BLOCKED →
SUPERSEDED**

所有模組僅能經由 G01 提交候選與查詢狀態，不得繞過此狀態機直接寫入
cfl_status。

**5.3 舊版對照表停用聲明**

2026-08-28《生態系卡位 AI 代理系統完整架構設計文件》附錄 A 之 CFL-01～08
對照表（排他／降級／門檻／防洩漏規則編號）與 Charter §17 定義不同，依
Charter §32 Work-1 Handoff Contract，已於 Work-1 明確停用，建議封存為
docs/legacy/CFL_MAPPING_LEGACY_0828.md，不再作為本契約或任何治理判斷之依據（對應
TQ-01）。

**6. Agent Spec --- AGENT_SPEC.md（A01--A08 角色與 RBAC）**

  -----------------------------------------------------------------------------------------
  **編號**   **角色**                    **Autonomy   **功能／權責**
                                         Level**      
  ---------- --------------------------- ------------ -------------------------------------
  A01        抽取代理                    L1           建立
                                                      Entity／Event／Evidence／Technology
                                                      Candidate；Candidate ≠ Fact

  A02        實體判斷與分類代理          L1／L2       Universe／Taxonomy 分類建議

  A03        關係與矛盾分析代理          L2           Relationship／Conflict 分析與
                                                      Recommendation

  A04        Seco／CMI／重大性分析代理   L2           研究假設與
                                                      Recommendation；Recommendation ≠
                                                      Approval

  A05        比較分析代理                L2           競爭分析 Draft（CFL-06
                                                      控管，正式結論需 Human Review）

  A06        審查代理（Critic）          L2           偵測 CONTRADICT
                                                      Evidence、資料洩漏風險，觸發 CFL-07

  A07        協調代理                    L0           Fan-out／Fan-in 編排、排程、重試

  A08        人工介接閘道代理            L3／L4 gate  將高風險決策路由至 Human
                                                      Review／Approval 佇列
  -----------------------------------------------------------------------------------------

**6.2 Agent Autonomy L0--L4 對應**

  --------------------------------------------------------------------------------------------------------
  **Level**   **定位**                **四權分離落實方式**
  ----------- ----------------------- --------------------------------------------------------------------
  L0          Deterministic           純確定性計算，不涉及 Evidence／Analysis 判斷權
              Automation              

  L1          AI Extraction           僅能寫入 Candidate（state=DRAFT/CANDIDATE），無 Approval 權

  L2          AI Analysis &           僅能產出 Recommendation，不具 Approval／Publication 權（G05 RBAC
              Recommendation          強制）

  L3          Conditional Autonomous  由 G02 依規則自動決策，仍受 G03 稽核與 G01 CFL 閘門
              Decision                

  L4          Reserved Human          高風險分類／關係／衝突／模型升版／重大結論／外部發布，僅人工可核准
              Authority               
  --------------------------------------------------------------------------------------------------------

**6.3 四權分離規則（GP-21，強制）**

G02 強制實作 Evidence／Analysis／Approval／Publication 四權分離：任一
Agent（A01--A08）之角色權限（由 G05 RBAC
定義）僅能落在其中一項功能類別，禁止單一 Agent 帳號同時具備 Evidence
寫入與 Approval／Publication 權限，此規則同時適用於第 4 節 API
權限設計。

**7. 契約凍結範圍確認清單**

  -------------------------------------------------------------------------------------------------
  **項目**                 **本文件涵蓋章節**                                        **狀態**
  ------------------------ --------------------------------------------------------- --------------
  Module ID                延續 Work-1                                               已凍結（沿用
                           十層模組編號（D/P/K/M/A/W/R/G/U/I），本文件未新增或變更   Work-1）

  Input／Output Schema     第 3 節 Event Contract、第 4 節 API 端點                  完成

  Database Schema          第 2 節 K01--K06 Schema                                   完成

  Event Schema             第 3 節                                                   完成

  Status／Error Code       第 3.2 節、第 4.3 節、第 5.2 節（CFL 狀態機）             完成

  Version／Evidence／CFL   第 2.1／2.8 節、第 5 節                                   完成
  Contract                                                                           
  -------------------------------------------------------------------------------------------------

**8. 追溯性聲明**

Work-1 §10、§11 已建立 CF-01～CF-46 與 GP-01～GP-21
之完整模組追溯矩陣，本文件之契約設計延續該矩陣，不重複列出全表；其中與
Data／Event／CFL／API／Agent 契約直接相關者摘列如下，供驗收比對：

  ------------------------------------------------------------------------------------------
  **CF／GP**          **內容摘要**                                     **本文件對應章節**
  ------------------- ------------------------------------------------ ---------------------
  CF-07/08/09/10/11   來源可信度、快照版本、Evidence 衝突判準與類型    2.7 K06

  CF-21/21A/22        Observed-Time 階層、Event Study                  2.1、2.6
                      時間欄位、交易日對齊                             

  CF-24/26            Point-in-Time 市值、禁 backward filling          2.1、2.2

  CF-27/28            Event Taxonomy 與 Materiality Score              2.6

  CF-35/36            Event Immutable + Revision Chain                 2.6

  CF-31/32/33         CFL 狀態機、Hybrid Governance、發布三層          5.2、4.2

  CF-37～CF-46        Agent Autonomy L0--L4 與四權分離                 6.2、6.3

  GP-06/07/08/09/15   歷史不可改寫、未知時間保持未知、CMI              2.1、2.6
                      禁未來資料、Bitemporal 版本化                    

  GP-17/18/20/21      Candidate≠Fact、Recommendation≠Approval、Agent   5、6.3
                      不得自我治理、四權分離                           
  ------------------------------------------------------------------------------------------

**9. Deferred Items 延續聲明**

下列項目延續 Work-1 §8（源於 Charter
§29），本文件僅維持掛勾點，不在本階段決策，亦不得誤設為 Frozen 參數：

- W01／W02：Wake-up Window、Daily Snapshot 時間、Batch Size／Queue
  Policy、Priority Threshold

- G08：Token Budget／Daily Ceiling／Cost Alert 額度

- P03／G04：資料集實際完整歷史起點

- M02／M05＋G04：Confidence／Materiality 精確權重與校準方式（Phase 2）

- M03／M04＋G04：Seco／CMI 統計校準後新權重（Phase 2）

- I04／I05：工作流程引擎與向量儲存最終技術選型（TQ-02，留待 Work-3）

**10. 版本與變更管理**

本文件為 Contract V1.0。任何後續調整（新增欄位、調整狀態機、新增 CFL
規則）皆須提出 Change Request，依 Charter §31 經 Claude Projects
重新驗收後升版為
V1.1、V1.2......，不得直接覆寫本文件內容或略過版本紀錄。

**11. Work-2 驗收標準（Acceptance Criteria）**

- K01--K06 之 Data Contract 欄位定義完整，且與 Work-1 CF/GP
  對應一致，無同義異名情形

- Event Contract 欄位與狀態機已固定，並對應至 W04 每日研究管線各階段

- CFL-01～08 之技術落地與 Charter §17 定義完全一致；0828
  舊版對照表停用聲明已明確記載

- API 端點清單已對應
  U01--U05、R01--R06，且四權分離（GP-21）已落實於權限設計原則

- Agent Autonomy L0--L4 與 A01--A08 角色權責已對應完成，RBAC
  四權分離規則明確

- 本文件未產出程式碼，Deferred Items（第 9 節）未被誤設為 Frozen 參數

- 經 Research Director／Executive User 依本標準審閱通過後，方可進入
  Work-3 Implementation Blueprint

**12. Work-3 Handoff Contract**

Work-3 之任務是把本文件固定之契約轉譯為可交棒 Claude Code
的工程工作包，至少須完成：

- IMPLEMENTATION_PLAN.md：依 Dependency DAG 排定 Shared Contracts →
  資料庫 → Source Registry → Ingestion → 知識庫 → 分析引擎 → Agent →
  工作流程引擎 → API → UI → Reporting → Governance → Tests 之施工順序

- ACCEPTANCE_TESTS.md：對應第 11 節驗收標準之可執行測試案例

- I04／I05 技術選型決議（TQ-02）

- CLAUDE.md：定義 Claude Code 的工作邊界與規則

**Work-3 完成前，不建議 Claude Code 大量撰寫 business code（SOP 步驟
6／Work-1 §13）。**

*本文件為 Work-2 草稿，待驗收通過後方可進入 Work-3 Implementation
Blueprint。*
