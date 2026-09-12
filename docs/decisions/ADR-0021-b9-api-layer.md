# ADR-0021 — WBS-B9：U05 API 層（OIDC/JWT 認證、G05 六角色 RBAC、端點、錯誤碼）

- 狀態：**ACCEPTED（B9 實作決議）**
- 日期：2026-09-12
- 核可：Research Director／Executive User（隨 B9 PR 審閱）
- 來源：Work-3 §2 DAG B9 列、Work-2 §4（API_SPEC 大綱：§4.1 設計原則／§4.2 端點清單／§4.3 錯誤碼／§4.4 認證與 RBAC）、Charter §5（六類使用者角色）；`ADR-0004`（決議 d：Work-2 §4.4 補齊 OIDC/JWT + 六角色 RBAC 矩陣，留待 B9 展開）

---

## 1. 範圍

Work-3 B9 = 「U05／API 層；第 4 節端點清單全數實作」。Work-2 §4 本身只是「大綱」（endpoint 清單＋設計原則＋錯誤碼規則＋RBAC 矩陣骨架），細節（逐端點功能群組對照、error_code 前綴、JWT 驗證實作）明文留給 B9（§4.2 表格下方："端點→功能群組之細目對照留待 WBS-B9 依本矩陣展開，不得新增跨權組合"）——以下即為該展開。

## 2. G05 擴充 — 六角色 RBAC 矩陣（`src/governance/rbac.py`）

Work-2 §4.4 矩陣逐格轉錄為 `UserRole`（Charter §5 六類角色）× `FunctionGroup`（讀／Evidence-實體寫／模型執行／審查佇列／核准-發布／Ops-設定）。與既有 A01–A08 `AgentRole`／`AgentPower` 系統**完全獨立**（人類帳號與 Agent 帳號分開治理，兩套 GP-21 檢查各自成立：`assert_gp21_roster_compliance` 管 Agent，新的 `assert_no_cross_power_role` 管人類角色）。

Executive User 的「讀（摘要）」與其他角色的「讀」不是同一件事——本 ADR 建成 `FunctionGroup.READ_SUMMARY`（弱）與 `FunctionGroup.READ`（強）兩個值，`role_satisfies`：持有 `READ` 的角色自動滿足 `READ_SUMMARY` 需求，反之不成立。§4.2 端點→功能群組對照（新規則，本 ADR 制定）：

| 端點 | 功能群組 | 理由 |
|---|---|---|
| GET /dashboard/seco-cmi | READ_SUMMARY | 儀表板聚合資料，符合 Charter §5 Executive User「摘要」定位 |
| GET /companies | READ_SUMMARY | 清單層級查詢，同上 |
| GET /companies/{id} | READ | 含 Evidence/Citation 完整明細，非摘要 |
| GET /events | READ_SUMMARY | 清單層級查詢 |
| GET /events/{id} | READ | 含 Revision Chain 完整明細 |
| GET /reports/{id} | READ | 正式研究報告產出 |
| GET /event-studies/{id} | READ | 量化明細 |
| GET /comparisons/{id} | READ | 競爭分析明細 |
| POST /publications/{id}/approve | APPROVAL_PUBLISH | CFL-08 正式外部發布核准 |
| POST /cfl/{cfl_id}/decision | REVIEW_QUEUE | CFL 人工審查／核准／駁回——注意這與 `/publications/.../approve` 刻意分屬不同功能群組：Research Reviewer 有 REVIEW_QUEUE 但沒有 APPROVAL_PUBLISH，只有 Research Director 兩者皆有——對應 Charter「正式外部發布」門檻高於一般 CFL 審查的設計 |
| GET /exports | READ | 匯出已核准內容 |

OPS_CONFIG 目前無對應端點（Work-2 §4.2 之 11 個端點皆未涵蓋 Admin/Ops 設定介面）——矩陣定義保留，端點留待日後設計，不在本批新增未經凍結文件授權的端點。

## 3. 認證（`src/api/auth.py`）

`OIDC_ISSUER`／`OIDC_AUDIENCE`／`OIDC_JWKS_URL` 純環境變數注入（CLAUDE.md §9）。函式庫選用 `pyjwt[crypto]`（新增依賴，屬 §5 「低風險預設，團隊可換」等級的實作庫選擇，非 Frozen Decision）。

`fetch_jwks`（真正對外 HTTP 呼叫）與 `decode_bearer_token`（實際簽章／iss／aud 驗證）刻意拆開：後者可接受呼叫端直接傳入 JWKS dict，因此測試（`tests/test_api_auth.py`）能用**真實**本地產生的 RSA 金鑰對＋自建 JWKS 走完整簽章驗證流程（錯誤金鑰／錯 aud／錯 iss／未知 kid／未知角色 claim 各自被正確拒絕），不需要連到真正的 IdP——與 B7b Temporal 測試「真實但走本地」的一貫作法相同。

## 4. 端點（`src/api/app.py`）

Work-2 §4.2 十一個端點全部實作，依對應模組是否已存在分兩類（同 `agents/roster.py`／`workflows/daily_pipeline.py` 一貫立場：**沒有的東西不假裝有**）：

**真實邏輯**（模組已存在）：`GET /companies`、`GET /companies/{id}`（K01，新增 `list_evidence_for_entity` 供 Evidence 明細）、`GET /events`、`GET /events/{id}`（K05，新增 `list_events` 過濾查詢）、`POST /cfl/{cfl_id}/decision`（G01，人工轉移 `cfl_status`，含 §4.3 之 400/404/409/423 判斷）。

**501 誠實佔位**（依附模組 R01–R06 尚未建置，WBS-B11）：`GET /dashboard/seco-cmi`（R03）、`GET /reports/{id}`（R02）、`GET /event-studies/{id}`（R04）、`GET /comparisons/{id}`（R05）、`POST /publications/{id}/approve`（R06——`governance.publication` 的 CFL-08 閘門邏輯已備妥，R06 一旦建置即可直接呼叫）、`GET /exports`（U05 匯出，依賴 R01–R06）。

## 5. 錯誤碼（`src/api/errors.py`）

`<MODULE>-ERR-<NNN>` 之 MODULE 採 Work-1 模組代號（`K01`／`K05`／`G01`／`G05`），非模組專屬之 API 層本身概念（認證失敗）用 `API`。409／423 專供 CFL 阻擋（§4.3：CFL-07 不得 Auto-pass、或現況已 BLOCKED）；501 專供依附 R01–R06 尚未建置之端點；`RequestValidationError`（Pydantic 驗證失敗）統一轉譯為 `API-ERR-422`，確保「所有 4xx 皆含統一 error_code」不留例外。5xx／`correlation_id`：本批端點沒有真正會製造 5xx 的邏輯路徑（DB 例外由框架預設處理），欄位保留供未來使用。

## 6. 驗收

- G05：六角色矩陣逐格核對 Work-2 §4.4；`assert_no_cross_power_role` 通過；`READ`/`READ_SUMMARY` 階層行為（`tests/test_rbac_matrix.py`）。
- 認證：真實 RSA／JWKS 簽章驗證全流程，含各種拒絕情境（`tests/test_api_auth.py`）。
- 錯誤碼：格式與各 Error 子類別之 status_code/module（`tests/test_api_errors.py`）。
- 端點：`tests/integration/test_api_endpoints.py`（FastAPI `TestClient` + `db_session` fixture 覆寫 `get_session`/`get_current_role`）涵蓋 5 個真實端點（含 404/400/409 各分支）、RBAC 403 拒絕、2 個 501 佔位端點。

## 7. 待確認 / 後續

1. `OPS_CONFIG` 尚無對應端點（見 §2）——留待 Admin/Ops 介面設計時再展開。
2. R01–R06（WBS-B11）建置後，6 個 501 端點需替換為真實邏輯；`governance.publication` 的 tier 分類與 CFL-08 閘門屆時直接可用，無需重寫。
3. Work-3 之後：**B10**（U01–U05 儀表板／搜尋／詳情頁／Admin 審查主控台；U04 需能完整操作 CFL Queue 核准／駁回流程）。
