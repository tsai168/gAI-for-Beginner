# CFL_MAPPING_LEGACY_0828 — 舊版 CFL 對照表停用聲明

> **狀態：DEPRECATED / 停用（不作為任何治理判斷依據）**
> 建立日期：2026-09-10
> 依據：`/docs/WORK1_TECH_SPEC_BASELINE_V1.md` §2 Reconciliation Note、§9 TQ-01；`/docs/WORK2_CONTRACT_FREEZE_V1.md` §5.3；`/docs/CHARTER_FREEZE_V1.md` §17、§32。

## 1. 本目錄檔案

| 檔案 | 說明 |
|---|---|
| `20260828-Ecosystem-Positioning-AI-Agent-Architecture-Design.docx` | 《Claude 生態系卡位 AI 代理系統完整架構設計文件》（2026-08-28）。原始檔名：`20260828-Claude-生態系卡位AI代理系統_完整架構設計文件.docx`。Charter Freeze 之前產出的技術參考文件，**非 Frozen**。 |
| `20260829-Ecosystem-Positioning-AI-Agent-Architecture-Design.docx` | 2026-08-29 版。原始檔名：`20260829-Claude-生態系卡位AI代理系統_完整架構設計文件.docx`。經 MD5 比對與 2026-08-28 版**位元組完全相同**（`734f4f7d0157fd86c525dd84a3a45681`），僅日期／檔名不同，無內容差異。 |

## 2. 停用範圍

`2026-08-28` 文件**附錄 A** 自行定義了一套 `CFL-01～08` 對照表，將該來源文件中的「排他／降級／門檻／防洩漏」規則編號為 CFL。該套編號與定義**與 Charter §17 正式凍結之 CFL-01～08 同號但不同義**，即日起**停用**，不得作為本 repository 任何契約、程式碼或治理判斷之依據。

依 Charter §32 Work-1 Handoff Contract「不得靜默修改 Frozen Decision」，已於 Work-1 §2 明確以 Charter §17 為唯一有效版本（見 Work-1 §9 TQ-01）。

## 3. 唯一權威版本（取代 legacy CFL 對照表）

`CFL-01～08` 的唯一有效定義來源，依優先順序：

1. `/docs/CHARTER_FREEZE_V1.md` §17 — CFL 治理對象與 V1 原則（FROZEN）
2. `/docs/WORK1_TECH_SPEC_BASELINE_V1.md` §4 — CFL 技術落地點（候選產生模組／判斷審查模組）
3. `/docs/WORK2_CONTRACT_FREEZE_V1.md` §5 — CFL_CONTRACT（欄位級規格與狀態機）

Charter §17 之 CFL-01～08 治理對象為：

| CFL | 治理對象 |
|---|---|
| CFL-01 | 公司身分 |
| CFL-02 | CPO 分類 |
| CFL-03 | 來源可信度 |
| CFL-04 | 重大事件 |
| CFL-05 | 生態系關係 |
| CFL-06 | 競爭分析 |
| CFL-07 | 矛盾資料 |
| CFL-08 | 發布核准 |

CFL 狀態機（Work-2 §5.2，由 G01 統一實作，禁止繞過）：
`PENDING → AUTO-PASS／REVIEW-REQUIRED → APPROVED／REJECTED／BLOCKED → SUPERSEDED`

## 4. 文件其餘內容之處理

`2026-08-28` 文件其餘內容（依 Work-1 §2 所述包含：約 43 個模組、`X1–X43` 規則引擎、Seco／CMI／事件窗口重估／γ 迴歸等）為 Work-1 十層模組架構之**技術參考輸入**，其設計精神被 Work-1 借用，但：

- 其模組編號體系（43 模組、`X1–X43`）**不等同**且**不取代** Work-1 §3 十層架構（`D/P/K/M/A/W/R/G/U/I`）與 `D01–D08 / P01–P06 / K01–K06 / M01–M08 / A01–A08 / W01–W06 / R01–R06 / G01–G08 / U01–U05 / I01–I06`。
- γ 共振交互作用迴歸與穩健性檢定屬 Charter §26.2 Phase 2 範圍（Work-1 §9 TQ-04），非 MVP。
- Kappa 一致性稽核器為 Work-1 §9 TQ-03 提出之選配 QA 模組，是否納入 V1 **尚待 Research Director 決定**。

## 5. 待確認（本聲明未涵蓋、需人工核對）

1. `2026-08-28` 文件附錄 A 之 CFL-01～08 **逐條規則內容**（哪些排他／降級／門檻／防洩漏規則）未於本聲明列舉；如需逐條對照哪些 legacy 規則作廢、哪些已被 Charter §17／Work-2 §5 以其他形式吸收，須實際開啟 `docs/legacy/` 之 `.docx` 由人工核對。
2. Work-1 §9 TQ-03（Kappa 一致性稽核器）納入與否。
3. `X1–X43` 規則引擎與現行 M 層（M01–M08）之對應關係（Work-1 §9 TQ-04 僅預留 M06／M08 下游擴充點）。

---
*本檔案依 Work-1 §2／Work-2 §5.3 之封存建議建立。任何變更 CFL 定義之提案須回到 Charter §31 Change Control。*
