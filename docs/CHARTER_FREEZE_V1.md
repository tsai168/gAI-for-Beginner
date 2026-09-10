**CPO AI**

**台灣 CPO／矽光子產業情報、公司事件、生態系卡位\
與市值重估 AI Agent System**

**PROJECT CHARTER FREEZE V1.0**

專案需求與研究治理正式凍結基準

Status: FROZEN\
Date: 2026-09-05\
Next Gate: Work-1 --- Technical Specification Baseline V1

# 0. 文件控制與 Freeze 聲明

  --------------------------------------------------------------------------
  項目                                內容
  ----------------------------------- --------------------------------------
  文件名稱                            CPO AI Project Charter Freeze V1.0

  文件性質                            專案商業需求、研究契約、資料治理與 AI
                                      自治權之正式凍結基準

  版本                                V1.0

  狀態                                FROZEN

  上游來源                            Chat 階段完成之 Project Charter 與
                                      OQ-01～OQ-30 決策

  下游文件                            Work-1 Technical Specification
                                      Baseline V1；Work-2 Contract
                                      Freeze；Work-3 Implementation
                                      Blueprint + Acceptance Criteria

  變更原則                            Work 與 Codex 不得自行修改 Frozen
                                      Decision。任何重大研究邏輯變更必須依
                                      Change Control 產生新 Charter 版本。
  --------------------------------------------------------------------------

本文件是 CPO AI 後續工程化的 Single Source of
Truth。它規範「系統要解決什麼問題、研究結果如何成立、AI
可以做什麼與不能做什麼」；不在本階段指定資料庫表格、API、程式語言實作、Repository
結構或部署細節。

# 1. Executive Summary

CPO AI
的目標不是建立一般新聞搜尋器，而是建立一套可追溯、可重現、Point-in-Time、Evidence-first
的 CPO／Silicon Photonics 研究系統，形成「技術情報 → 公司 → 產品 →
客戶／供應商 → 事件 → 生態系位置 → 籌碼／資本市場動能 →
市場重新定價」的研究鏈。

核心研究契約：Source → Evidence → Claim → Analysis → Conclusion →
Report。沒有 Evidence，不得把 AI 推論升級為 Fact；沒有
Point-in-Time，不得進入事件研究；沒有 Version，不得宣稱研究可重現；沒有
CFL，不得發布重大結論。

Phase 3 不追求無限制全自動，而採 L0～L4 Risk-based Agent
Autonomy：低風險、確定性與高重複工作高度自動化；高
Materiality、高衝突、高不確定性及外部發布保留 Human Authority。

# 2. Purpose

建立台灣 CPO／矽光子產業的長期 AI
研究基礎設施，使公司分類、供應鏈關係、重大事件、Seco、CMI、事件窗口與研究報告均可追溯至來源與
Evidence，並能在每日更新下維持時間一致性、版本一致性與治理一致性。

# 3. Business Objectives

- 建立 CPO、Silicon Photonics、Optical I/O、ELSFP、FAU、PIC、EIC、Fiber
  Array、MPO、PMF、CoWoS、SoIC、COUPE 等技術與產業知識庫。

- 建立台灣上市、上櫃與興櫃 CPO 相關公司 Universe，並區分
  Core／Adjacent／Watchlist。

- 分析公司在 CPO
  生態系中的技術、產品、客戶、供應商、合作夥伴與競爭者角色。

- 持續發現、驗證與版本化重大公司事件。

- 建立 Company--Technology--Product--Customer--Supplier--Event 關係。

- 判斷公司是否真正進入 CPO 供應鏈，避免以概念股或關鍵字取代 Evidence。

- 建立 Seco（Ecosystem Positioning Score）。

- 建立 CMI（Chip / Capital Market Momentum Indicator）。

- 建立以事件日 t 為中心之 t−N 到 t+M 日／週均價、市值、AR、CAR
  與市場重新定價研究。

- 所有重大研究結論保留 Source、Evidence、Citation、Confidence、Version
  與 Audit Trail。

- 形成可每日更新、可人工核准、可逐步自治的研究與報告流程。

# 4. Research Questions

- 哪些台灣公司真正屬於 CPO Core、Adjacent 或 Watchlist？其分類 Evidence
  為何？

- 公司位於 CPO 生態系哪一層？其技術、產品與商業化成熟度如何？

- 哪些 Customer／Supplier／Partner 關係已 Confirmed，哪些僅為 Candidate
  或匿名關係？

- 事件的 Evidence Stage 是 E0～E6 哪一階段？是否構成 Material Event？

- 公司 Seco 在特定 Point-in-Time 為何？變化由哪些 Evidence 驅動？

- CMI 是否顯示籌碼集中、法人動能與交易結構的同步變化？

- 重大事件前後是否出現顯著 AR／CAR、市值重新定價與 Seco×CMI 共振？

- 結論是否存在 CONTRADICT
  Evidence、時間污染、資料洩漏或版本不可重現問題？

# 5. Users and Use Cases

  ------------------------------------------------------------------------------
  角色                                主要用途
  ----------------------------------- ------------------------------------------
  Research Director                   研究治理、模型版本、重大結論與發布核准

  Semiconductor Analyst               技術、公司、產品、客戶與事件研究

  Quant Researcher                    CMI、Event Window、AR/CAR、Robustness Test

  Research Reviewer                   Evidence、Conflict、Confidence、CFL 審查

  Executive User                      閱讀公司、生態系、事件與市場重新定價摘要

  System Administrator                資料流程、權限、成本、稽核與營運治理
  ------------------------------------------------------------------------------

# 6. Scope

- 台灣上市、上櫃、興櫃公司之 CPO 投資研究 Universe。

- 海外公司可建立 Company Entity，並建立
  Customer／Supplier／Partner／Competitor／Technology 關係，但 V1
  不納入台灣股票事件研究 Universe。

- CPO／Silicon Photonics
  技術、產品、事件、Evidence、Citation、Relationship、Seco、CMI、MarketData
  與 ResearchReport。

- 官方／公開資料優先；架構保留未來合法授權付費資料來源。

- 日／週市場資料、法人、融資融券／借券、TDCC 等 Point-in-Time 可用資料。

# 7. Out of Scope

- V1 不以海外股票作為主要投資事件研究 Universe。

- 不以單一媒體標籤或『CPO 概念股』作為 Core 分類證據。

- 不把 LLM 推論直接當成 Fact。

- 不在 Charter V1.0 固定程式語言、資料庫 schema、API
  contract、部署拓撲與 Repository 細節。

- Seco 不等於投資建議；CMI
  不等於單純價格技術指標；研究結果不自動等於可外部發布。

# 8. Data Requirements and Preferred Sources

優先資料來源包括：TWSE、TPEx、MOPS、公司
IR、財務報告、法說會、新聞稿、客戶／供應商官方資料、國際 CPO／Silicon
Photonics
技術來源、可信產業媒體、主流財經媒體、股價成交、法人買賣、融資融券／借券與
TDCC 股權分布。

資料必須盡可能保存原始 URL、標題、Publisher、published time、retrieved
time、content hash、合法可保存之 snapshot／內容版本、parser version 與
source version。

# 9. Core Research Objects

  --------------------------------------------------------------------------
  Object                              用途
  ----------------------------------- --------------------------------------
  Company                             公司身分與投資 Universe 主體

  Technology                          技術分類與版本

  Product                             產品／模組／規格

  Person                              重要人物與聲明主體

  Event                               事件及修正鏈

  Source                              原始資訊來源

  Evidence                            支持／反證／脈絡證據

  Citation                            研究引用定位

  Relationship                        公司、技術、產品、客戶、供應商等關係

  MarketData                          價格、成交與市場資料

  InstitutionalTrading                法人交易

  Shareholding                        TDCC／持股結構

  Seco                                生態系定位分數

  CMI                                 籌碼／資本市場動能

  ValuationEventWindow                事件窗口、市值、AR/CAR

  ResearchReport                      版本化研究輸出
  --------------------------------------------------------------------------

# 10. CPO Taxonomy and Universe Governance

V1 Taxonomy 至少包含：CPO、Silicon Photonics、Optical
Engine、PIC、EIC、Laser、CW Laser、FAU、Fiber
Array、MPO、PMF、Connector、Optical Packaging、Micro Lens、Hybrid
Bonding、CoWoS、SoIC、COUPE、Switch ASIC、ELSFP、1.6T、3.2T。Taxonomy
必須可版本化與擴充。

Universe 採 Core／Adjacent／Watchlist。CPO、Optical
I/O、ELSFP、Pluggable Optics 保留獨立 taxonomy identity；CPO
為核心，Optical I/O 為核心或高度相鄰，ELSFP 為 Adjacent，Pluggable
Optics 為脈絡／比較層，不得自動視為同義詞。

# 11. Evidence, Source and Relationship Governance

## 11.1 Evidence Stage E0--E6

  -----------------------------------------------------------------------
  Stage                               定義
  ----------------------------------- -----------------------------------
  E0                                  Rumor / Mention

  E1                                  Technology Capability

  E2                                  Development / Sampling

  E3                                  Qualification / Validation

  E4                                  Design-in / Customer Adoption

  E5                                  Production / Shipment

  E6                                  Revenue Contribution
  -----------------------------------------------------------------------

『有 CPO 技術』≠『進入供應鏈』≠『量產』≠『營收貢獻』。

## 11.2 Source Tier S1--S5

  -------------------------------------------------------------------------------------------
  Tier                                定義
  ----------------------------------- -------------------------------------------------------
  S1                                  Authoritative Primary：法定／交易所／監管揭露

  S2                                  Corporate / Counterparty
                                      Primary：IR、財報、法說、新聞稿、客戶／供應商官方來源

  S3                                  Authoritative Technical /
                                      Institutional：標準、官方技術文件、學術／產業技術機構

  S4                                  Reputable Secondary：可信產業媒體、主流財經媒體

  S5                                  Unverified /
                                      Discovery-only：論壇、社群、傳聞、未驗證轉載
  -------------------------------------------------------------------------------------------

S5 可作 Discovery Lead，但原則上不得單獨支持重大正式
Claim。來源衝突不依語言排序，而依 Authority + Directness + Time +
Specificity + Independence 評估。Evidence 必須支援
SUPPORT／CONTRADICT／NEUTRAL-CONTEXT。

匿名關係可以保存，例如 Company A → supplies → Anonymous North American
CSP；Candidate Identity 與 Confirmed Relationship 必須分離，AI
不得無充分 Evidence 自行把匿名客戶映射為具名公司。

# 12. Seco --- Ecosystem Positioning Score

Seco 衡量公司在時間 t 的 CPO
生態系實際定位與商業化成熟度，不是股票買賣建議。

  -----------------------------------------------------------------------
  構面                                權重
  ----------------------------------- -----------------------------------
  S1 Technology Relevance             15%

  S2 Product Readiness                15%

  S3 Customer Validation              20%

  S4 Ecosystem Position               20%

  S5 Commercialization                20%

  S6 Strategic Defensibility          10%
  -----------------------------------------------------------------------

Seco(i,t) = 0.15S1 + 0.15S2 + 0.20S3 + 0.20S4 + 0.20S5 + 0.10S6。V1
權重為 Expert Prior；Phase 2 可統計校準，但任何新權重必須建立新 Model
Version。

尺度 0--100：0--19 Minimal/Insufficient；20--39 Emerging；40--59
Developing；60--79 Established；80--100 Strong。每個 Seco 必須伴隨
Confidence。

Seco 採 Point-in-Time / Bitemporal Versioning，區分 Effective Time 與
Knowledge Time。Correction 與 New Evidence 分離；未來 Evidence
不得回填成歷史當時已知。

# 13. CMI --- Chip / Capital Market Momentum Indicator

CMI 衡量公司層級的籌碼集中、法人動能與交易結構，而非單純價格技術指標。

  -----------------------------------------------------------------------
  構面                                V1 權重
  ----------------------------------- -----------------------------------
  C1 Foreign Institutional Momentum   20%

  C2 Domestic Institutional Momentum  20%

  C3 Margin & Short Position          20%

  C4 Ownership Concentration          20%

  C5 Trading Structure                20%
  -----------------------------------------------------------------------

CMI V1 採等權 Expert Prior；Phase 2 再以
sensitivity、regression、PCA/factor、out-of-sample validation 或 ML
calibration 驗證。任何權重變更建立新 Model Version。

TDCC 等低頻資料必須依真正 public/available time 進入 CMI；effective
period 不等於 availability time，禁止 backward filling。

# 14. Event Window, Market Repricing and Event Timing

## 14.1 Event Windows

標準窗口：短期 \[-1,+1\]、\[-3,+3\]、\[-5,+5\]；中期
\[-10,+10\]、\[-20,+20\]；並允許 configurable
\[-N,+M\]。週資料窗口另行定義，不以日資料粗略聚合替代。

## 14.2 Abnormal Return / CAR

至少支援 Market-adjusted 與 Market Model 兩種版本化
Benchmark。Market-adjusted：AR(i,t)=R(i,t)−R(m,t)。Market
Model：R(i,t)=α_i+β_iR_m,t+ε_i,t；AR 為 actual−expected。CAR\[a,b\]=Σ
AR。每個結果必須帶 Benchmark Model Version。

## 14.3 Market Cap

MarketCap(i,t)=Price(i,t)×SharesOutstanding(i,t)，必須使用 Point-in-Time
Shares Outstanding，不得以今日股本回算歷史市值。

## 14.4 Observed-Time + Event Trading Date Hierarchy

  ------------------------------------------------------------------------------------
  欄位                                規則
  ----------------------------------- ------------------------------------------------
  occurred_at                         Optional；只有來源明確提供事件實際發生時間才填

  published_at                        Preferred；來源明確提供發布時間／日期才填

  retrieved_at                        Required；CPO AI 實際取得來源之系統時間

  market_known_at                     Optional / Evidence-only；有可靠 Evidence
                                      才保存，不得由 LLM 猜測

  event_trading_date                  Event Study Required；依 Time Evidence、Trading
                                      Calendar 與 Conservative Alignment Rule 推導
  ------------------------------------------------------------------------------------

缺失時間保持 NULL；Unknown Time Must Remain Unknown。不得以 00:00
等虛假精度填補 DATE_ONLY 資料。每個 Event Study Event 保存
time_basis、time_precision、time_confidence。

Trading-session Alignment：盤前可得資訊以當日為
t；盤中公開且只有日資料時可用當日但須揭露限制；盤後或非交易日公開則原則上以下一交易日為
t；只有日期、無法判斷盤前／盤後時採 Conservative
Alignment，原則上以下一交易日為安全 t=0。

同一 Event 可連結多個 Source，每個 Source 保留自己的 published_at /
retrieved_at；Event 層以最早可靠公開 Evidence 形成研究 timing。可依 Time
Quality 分 High／Medium／Low 樣本進行 CAR Robustness Check。

# 15. Event Taxonomy and Materiality

  -----------------------------------------------------------------------
  Code                                Event Type
  ----------------------------------- -----------------------------------
  EV01                                Technology

  EV02                                Product

  EV03                                Qualification

  EV04                                Customer

  EV05                                Partnership

  EV06                                Production

  EV07                                Shipment

  EV08                                Order

  EV09                                Revenue

  EV10                                Capacity

  EV11                                Competition

  EV12                                Negative Event
  -----------------------------------------------------------------------

Event 與 Material Event 分離。Materiality Score 0--100 至少考慮 CPO
Relevance、Evidence Strength、Commercial Impact、Ecosystem
Impact、Novelty；V1 採 Expert Rule，Phase 2 可校準。只有通過 CFL-04
的事件才升級為 Material Event。

# 16. Confidence

Research Confidence 採 Evidence-based Confidence，尺度
0--1，不得直接使用 LLM 自評信心。

  -----------------------------------------------------------------------
  Code                                構面
  ----------------------------------- -----------------------------------
  CF1                                 Source Authority

  CF2                                 Evidence Directness

  CF3                                 Independent Corroboration

  CF4                                 Temporal Quality

  CF5                                 Conflict Penalty
  -----------------------------------------------------------------------

V1 採 Rule-based / Expert Prior；Phase 2 再做 calibration。

# 17. CFL Governance

  ----------------------------------------------------------------------------
  CFL                     治理對象                V1 原則
  ----------------------- ----------------------- ----------------------------
  CFL-01                  公司身分                高
                                                  Confidence、可確定驗證者可
                                                  Auto-pass

  CFL-02                  CPO 分類                Watchlist/Adjacent 可 AI
                                                  建議；首次升級 Core 需 Human
                                                  Review

  CFL-03                  來源可信度              已知官方來源可
                                                  Auto-pass；新／未知來源需
                                                  Review

  CFL-04                  重大事件                一般事件可 AI 分類；高
                                                  Materiality 需 Human Review

  CFL-05                  生態系關係              Candidate 可保存；重大具名
                                                  Customer 首次 Confirmed 需
                                                  Human Review

  CFL-06                  競爭分析                AI 可 Draft；正式重大結論需
                                                  Human Review

  CFL-07                  矛盾資料                重大 CONTRADICT Evidence
                                                  不得 Auto-pass

  CFL-08                  發布核准                正式外部重大研究結論 Human
                                                  Approval Required
  ----------------------------------------------------------------------------

CFL 採 AUTO-PASS／REVIEW-REQUIRED／BLOCKED 的 Risk-based
Automation；狀態生命週期可包含 PENDING → AUTO-PASS/REVIEW-REQUIRED →
APPROVED/REJECTED/BLOCKED → SUPERSEDED。

# 18. Publication Governance

採三層發布：Internal Auto／Material Review／External Approval。Daily
source digest、事件清單、Watchlist changes、Evidence
updates、Data-quality alert 可在基本驗證後內部自動產生；Core
升級、Confirmed Customer、Seco 大幅變動、重大 CMI Signal、顯著
CAR、正式競爭結論等需 Review；正式外部重大研究須通過 CFL-08 Human
Approval。

# 19. Hybrid Monitoring + Batch AI Parsing

CPO AI 不採 LLM 24 小時持續處理。Continuous
階段優先使用低成本、確定性機制進行來源監控、Crawler/API、Hash
comparison、Change Detection、Basic Cleaning、Deduplication 與
Staging。原則上此層不呼叫 LLM。

新增或變更資料在預定 LLM Wake-up Window、Priority Trigger
或其他核准條件下，才進入 Batch AI Parsing，執行 Entity/Event/Evidence
Extraction、Classification、Relationship/Conflict Analysis 等語意工作。

23:00、06:00 僅為候選 Wake-up Window，不屬 Charter Freeze。具體 Wake-up
Time、Snapshot Time、Batch Size、Priority Wake-up Threshold、Token
Budget / Ceiling 等均 Deferred to Operations Specification。

治理原則：Deterministic First, AI When
Needed。Hash、Rule、Parser、SQL、公式計算可完成者，原則上不得無必要使用
LLM。

# 20. Event Revision and Historical Integrity

Event 採 Immutable Event + Revision
Chain，不得直接覆寫歷史。狀態至少支援
ACTIVE／CORRECTED／SUPERSEDED／WITHDRAWN／DISPUTED。Correction、Withdrawal
與後續 New Evidence 必須建立版本關係並保留舊
Source、Evidence、時間、版本與 Reason。

被撤回的公告不代表其歷史上未曾存在；若市場曾接收 V1，Event Study
可分別研究 Announcement Effect 與 Correction/Withdrawal Effect。

# 21. Phase 3 Agent Autonomy --- L0～L4

  --------------------------------------------------------------------------------------------------------------
  Level                   定位                    權限
  ----------------------- ----------------------- --------------------------------------------------------------
  L0                      Deterministic           Crawler、API、Hash、Cleaning、Dedup、Trading Calendar、AR/CAR
                          Automation              等確定性工作可 Full Automation

  L1                      AI Extraction           可自動建立 Entity/Event/Evidence/Technology Structured
                                                  Candidate；Candidate ≠ Fact

  L2                      AI Analysis &           可做 Relationship、Conflict、Seco
                          Recommendation          input、Materiality、研究假設與 Recommendation；Recommendation
                                                  ≠ Approval

  L3                      Conditional Autonomous  僅在 Rule 明確、Confidence 足夠、無重大 Conflict、非高風險
                          Decision                State Transition 且通過 CFL 時自動決策

  L4                      Reserved Human          高風險分類／關係／衝突／模型升版／重大正式結論／外部發布保留
                          Authority               Human Authority
  --------------------------------------------------------------------------------------------------------------

任何 Low Confidence、重大 CONTRADICT Evidence、High
Materiality、Anonymous→Named Identity、Major State Transition 或
External Publication，應升級至 L4 Human Review。

Agent 不得自行修改 CFL、Source Tier、Confidence Formula、Seco/CMI
權重、Materiality Threshold、Publication Policy、Token
Budget、Production Model Version 或提升自身 Autonomy Level。

採 Evidence / Analysis / Approval / Publication 四權分離；單一 Agent
不應同時完成 Evidence、Conclusion、Approval 與 Publication。所有 L1～L3
行為必須保留 Agent、Rule、Input、Evidence、Confidence、Model
Version、Decision、Timestamp 與 Audit Trail。

# 22. Non-functional Requirements

- Traceability：每個重大 Claim 可回溯 Source、Evidence 與 Citation。

- Reproducibility：結果攜帶 Model Version、Input Version、Calculation
  Time。

- Point-in-Time Integrity：禁止 future knowledge / look-ahead bias。

- Auditability：來源、解析、決策、修正與發布保留稽核鏈。

- Versionability：Taxonomy、Evidence Rule、Seco、CMI、Benchmark、CFL 與
  Report 可版本化。

- Cost Governance：Deterministic First；LLM 採 Batch / Priority Queue
  與後續 Token Budget。

- Human Governance：高風險狀態轉換與正式外部發布保留 Human Authority。

- Extensibility：支援新技術、新公司、新來源、新模型與新 Event
  Type，但不得破壞既有版本可重現性。

# 23. Success Metrics

- 重大研究結論具可追溯 Evidence/Citation 的覆蓋率。

- Core／Confirmed Relationship 的人工審核一致性與錯誤率。

- Event deduplication、entity resolution、event classification 的品質。

- Point-in-Time／Time Evidence 完整率與資料洩漏事件數。

- Seco／CMI／AR-CAR 結果的版本可重現率。

- 重大 CONTRADICT Evidence 的發現與升級率。

- Daily Snapshot 的準時率、資料新鮮度與 Batch AI 成本。

- 人工審核工作量相對於有效研究產出的改善。

- 外部發布前 CFL-08 合規率。

# 24. Major Risks

- 媒體／市場概念標籤造成 CPO 公司誤分類。

- 匿名客戶被 AI 過度推論為具名公司。

- 來源時間缺失導致 Event Day 錯置與 look-ahead bias。

- TDCC 等低頻資料被錯誤回填。

- 後續 Evidence 偷偷改寫歷史研究狀態。

- LLM hallucination 被誤當 Evidence 或 Confidence。

- 來源授權、版權、robots/terms 或付費資料使用限制。

- LLM 全天候處理造成 Token 成本失控。

- AI 自行改變模型、治理門檻或發布政策造成治理漂移。

- 研究指標被錯誤解讀為投資建議。

# 25. Assumptions

- V1 以公開／官方來源優先，並遵守合法使用與授權限制。

- 台灣上市、上櫃、興櫃為主要投資研究 Universe。

- 研究時間以市場可合理取得之 Point-in-Time
  資訊為基本原則；無法取得精確時間時採保守規則。

- Expert Prior 可作 V1 起點，但必須明確標示且允許 Phase 2 統計校準。

- Human Review 是治理設計的一部分，不視為系統失敗。

- Operations Specification 將決定具體排程、成本與批次參數。

# 26. MVP / Phase 2 / Phase 3

## 26.1 MVP

MVP 的成功標準不是建立最多 Agent，而是證明至少一家公司可完整走通 Source
→ Evidence → Claim/Relationship → Event → Seco → CFL →
Report，且可重現、可稽核。

## 26.2 Phase 2

加入完整 CMI、Event Study Engine、公司／事件比較、Seco×CMI
交互分析、回測、統計檢定、Confidence/Materiality/模型權重校準與
Robustness Test。

## 26.3 Phase 3

形成 Governed Autonomous Research Intelligence：Discover → Retrieve →
Normalize → Extract → Verify → Build Evidence → Update Knowledge Graph →
Detect Event → Calculate Seco/CMI → Event Study → Conflict Check → CFL →
Human Approval（必要時）→ Publish → Monitor；自治權依 L0～L4 Risk-based
Model 控制。

# 27. Frozen Decisions Register --- CF-01～CF-46

  ------------------------------------------------------------------------------------------------
  Freeze ID               來源                    正式決策摘要
  ----------------------- ----------------------- ------------------------------------------------
  CF-01                   OQ-01                   Universe = Core / Adjacent / Watchlist

  CF-02                   OQ-02                   CPO、Optical I/O、ELSFP、Pluggable Optics
                                                  保留獨立 taxonomy identity

  CF-03                   OQ-03                   台灣 Universe = 上市 + 上櫃 + 興櫃

  CF-04                   OQ-04                   海外公司建立 Entity/Relationship，但 V1
                                                  不納入台股投資 Universe

  CF-05                   OQ-05                   Supply-chain Evidence Maturity = E0--E6

  CF-06                   OQ-06                   允許匿名關係；Candidate Identity ≠ Confirmed
                                                  Relationship

  CF-07                   OQ-17                   Source Credibility = S1--S5

  CF-08                   OQ-24                   來源保存可稽核版本與 hash/snapshot metadata

  CF-09                   OQ-25                   MVP Public / Official First；保留 licensed
                                                  source 架構

  CF-10                   OQ-26                   來源衝突依 Authority + Directness + Time +
                                                  Specificity + Independence

  CF-11                   OQ-29                   Evidence 支援 SUPPORT / CONTRADICT /
                                                  NEUTRAL-CONTEXT

  CF-12                   OQ-07                   Seco V1 六構面

  CF-13                   OQ-07                   Seco V1 權重 15/15/20/20/20/10，Expert Prior

  CF-14                   OQ-08                   Seco scale = 0--100

  CF-15                   OQ-08                   Seco 必須伴隨 Confidence

  CF-16                   OQ-27                   Seco 採 Point-in-Time / Bitemporal Versioning

  CF-17                   OQ-27                   Correction 與 New Evidence 分離，歷史版本保留

  CF-18                   OQ-09                   CMI V1 = C1--C5 五構面

  CF-19                   OQ-10                   CMI V1 等權 Expert Prior；Phase 2 統計校準

  CF-20                   OQ-11                   Event Window 採多窗口 + configurable \[-N,+M\]

  CF-21                   OQ-12                   Observed-Time + Event Trading Date
                                                  Hierarchy；缺失時間不得猜測

  CF-21A                  OQ-12                   Event Study 保存 time_basis / time_precision /
                                                  time_confidence

  CF-22                   OQ-13                   Trading-session Alignment + Conservative
                                                  Alignment

  CF-23                   OQ-14                   AR/CAR 採版本化 Benchmark，至少
                                                  Market-adjusted + Market Model

  CF-24                   OQ-15                   Market Cap 使用 Point-in-Time Shares Outstanding

  CF-25                   OQ-23                   歷史起點採 Dataset-specific Earliest Reliable
                                                  Date

  CF-26                   OQ-09/23                TDCC/低頻資料依實際 availability time 進入
                                                  CMI，禁止 backward filling

  CF-27                   OQ-16                   Event 採 EV01--EV12 Taxonomy + Materiality Score
                                                  0--100

  CF-28                   OQ-16                   Event ≠ Material Event；CFL-04 控制升級

  CF-29                   OQ-18                   Confidence = CF1--CF5 Evidence-based，0--1

  CF-30                   OQ-18                   Confidence V1 Rule-based / Expert Prior；Phase 2
                                                  calibration

  CF-31                   OQ-19                   CFL = AUTO-PASS / REVIEW-REQUIRED / BLOCKED

  CF-32                   OQ-20                   Hybrid Human-AI Governance，高風險狀態需人工介入

  CF-33                   OQ-21                   Publication = Internal Auto / Material Review /
                                                  External Approval

  CF-34R                  OQ-22                   Hybrid Monitoring + Batch AI
                                                  Parsing；具體時間/成本參數 Deferred

  CF-35                   OQ-28                   Event = Immutable + Revision Chain

  CF-36                   OQ-28                   Event status =
                                                  ACTIVE/CORRECTED/SUPERSEDED/WITHDRAWN/DISPUTED

  CF-37                   OQ-30                   Phase 3 採 L0--L4 Risk-based Agent Autonomy

  CF-38                   OQ-30                   L0 Deterministic Automation 可 Full Automation

  CF-39                   OQ-30                   L1 AI Extraction 可建立 Candidate；Candidate ≠
                                                  Fact

  CF-40                   OQ-30                   L2 AI Analysis 可 Recommendation；Recommendation
                                                  ≠ Approval

  CF-41                   OQ-30                   L3 僅低風險、規則明確、Confidence 足夠時
                                                  Conditional Autonomous Decision

  CF-42                   OQ-30                   L4 = Reserved Human Authority

  CF-43                   OQ-30                   Core 升級、重大具名關係、Conflict、高
                                                  Materiality、Model Promotion、重大外部發布需
                                                  Human Approval

  CF-44                   OQ-30                   Agent 不得自行修改 Governance / Production Model
                                                  / Autonomy

  CF-45                   OQ-30                   L1--L3 AI 行為必須保留完整 Audit Trail

  CF-46                   OQ-30                   Evidence / Analysis / Approval / Publication
                                                  四權分離
  ------------------------------------------------------------------------------------------------

# 28. Governance Principles Register --- GP-01～GP-21

  -----------------------------------------------------------------------
  GP                                  治理原則
  ----------------------------------- -----------------------------------
  GP-01                               CPO Label ≠ CPO Evidence

  GP-02                               Absence of Evidence ≠ Evidence of
                                      Absence

  GP-03                               Inference ≠ Evidence

  GP-04                               Seco ≠ Investment Recommendation

  GP-05                               Evidence Stage ≠ Seco

  GP-06                               Future Knowledge Must Not Rewrite
                                      Historical Knowledge

  GP-07                               Unknown Time Must Remain
                                      Unknown；研究 Event Date 依可靠
                                      Time Evidence 推導

  GP-08                               No Future Data in CMI

  GP-09                               Effective Period ≠ Availability
                                      Time

  GP-10                               Model Version Must Travel With
                                      Result

  GP-11                               LLM Confidence ≠ Research
                                      Confidence

  GP-12                               Materiality ≠ Truth

  GP-13                               AI May Recommend; Governance
                                      Decides

  GP-14                               Publication Is a Separate State
                                      Transition

  GP-15                               History Is Immutable;
                                      Interpretation Is Versioned

  GP-16                               Deterministic First, AI When Needed

  GP-17                               Candidate ≠ Fact

  GP-18                               Recommendation ≠ Approval

  GP-19                               Autonomy Decreases as Risk
                                      Increases

  GP-20                               Agents Cannot Govern Themselves

  GP-21                               Evidence, Analysis, Approval and
                                      Publication Must Be Separable
  -----------------------------------------------------------------------

# 29. Deferred Decisions

下列項目不是未完成需求，而是刻意延後至更適合的下游規格階段決定。Work
必須保留 Deferred 狀態，不得將候選值誤視為 Frozen。

  -----------------------------------------------------------------------
  Deferred Item                       預定決策階段
  ----------------------------------- -----------------------------------
  LLM Wake-up Window（23:00、06:00    Operations Specification
  僅候選）                            

  Daily Snapshot 產生時間             Operations Specification

  Batch Size / Queue Policy           Operations Specification

  Priority Wake-up Trigger /          Operations Specification
  Threshold                           

  Token Budget / Daily Ceiling / Cost Operations Specification
  Alert                               

  資料集實際完整歷史起點              Data Availability Audit / Technical
                                      Specification

  Confidence 精確權重／校準方式       Phase 2 Model Calibration

  Materiality 精確權重／threshold     Phase 2 Model Calibration
  校準                                

  Seco / CMI 統計校準後新權重         Phase 2；需新 Model Version
  -----------------------------------------------------------------------

# 30. Explicit Non-Assumptions

- 不得假設所有 Source 都有 occurred_at、published_at 或
  market_known_at。

- 不得假設 retrieved_at 等於市場首次知道時間。

- 不得假設新聞提及等於供應鏈 Confirmed。

- 不得假設匿名客戶可由 AI 自動具名。

- 不得假設 S1 Source 的所有 Claim 都必然正確；仍需
  Directness、Time、Specificity 與 Conflict 檢查。

- 不得假設 Event 高 Materiality 就等於高 Truth Confidence。

- 不得假設 Seco、CMI、AR/CAR 直接構成投資建議。

- 不得假設 Phase 3 代表 AI 可自行核准或外部發布。

- 不得假設 23:00／06:00 已成為正式排程。

- 不得假設 Work 或 Codex 有權重寫 Frozen Charter。

# 31. Change Control

任何影響 Universe、Taxonomy、Evidence Stage、Source Tier、Relationship
Confirmation、Seco、CMI、Event Timing、Event
Window、Confidence、CFL、Publication Policy 或 Agent Autonomy
的重大變更，必須提交 Change
Request，說明原因、影響、向後相容性、資料重算需求與驗收方式。

小幅且不改變研究契約的調整可升版為
V1.1；改變核心研究邏輯、模型定義或治理邊界者應升版為 V2.0。不得覆寫 V1.0
歷史文件。

# 32. Work-1 Handoff Contract

Work-1 的任務是把本 Charter 工程化為 Technical Specification Baseline
V1，而不是重新定義研究需求。Work-1 必須逐項對應
CF、GP、Scope、Objects、CFL、Point-in-Time、Versioning、Auditability 與
Deferred Items，並產生可供 Work-2 Contract Freeze 的技術基線。

Work-1 可以提出 Technical Question / Risk / Alternative，但不得靜默修改
Frozen Decision。若技術限制迫使研究契約變更，必須回到 Charter Change
Control。

建議後續管線：Chat Charter Freeze V1.0 → Work-1 Technical Specification
Baseline V1 → Work-2 Contract Freeze → Work-3 Implementation Blueprint +
Acceptance Criteria → AGENTS.md → Codex Phase 1
Repository/Contracts/Skeleton/Tests → Codex Phase 2 Module
Implementation/Integration/Verification。

# 33. Final Freeze Statement

截至 V1.0，OQ-01～OQ-30 已完成決策或明確 Deferred。CF-01～CF-46（含
CF-21A 與修正版 CF-34R）以及 GP-01～GP-21 構成 CPO AI
的正式研究與治理基準。

本 Charter Freeze 的最高原則為：Evidence-first、Point-in-Time、No Future
Data、Versioned Research、Risk-based Autonomy、Human Authority for
High-risk Decisions，以及 Deterministic First / AI When Needed。

**批准本文件後，下一個正式 Gate 為 Work-1 --- Technical Specification
Baseline V1。**
