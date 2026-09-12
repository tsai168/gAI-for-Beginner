# ADR-0022 — WBS-B10：UI 層（U01–U04，React + TypeScript + Vite 定案）

- 狀態：**ACCEPTED（B10 實作決議）**
- 日期：2026-09-12
- 核可：Research Director／Executive User（隨 B10 PR 審閱；UI 技術路線經 AskUserQuestion 當面確認 React + TypeScript + Vite）
- 來源：Work-3 §2 DAG B10 列、§4 TEST 驗收（"U04 可完整操作 CFL Queue 核准／駁回流程"）、Work-1 §3.9（U01–U05）、CLAUDE.md §5（"UI 技術堆疊…暫定 React + TypeScript + Vite，B10 前另立 ADR 再議"）、Charter GP-04（Seco ≠ Investment Recommendation）

---

## 1. UI 技術路線定案

CLAUDE.md §5 的暫定值（React + TypeScript + Vite）**予以確認**，不變更。這是本專案第一次引入 Node.js／npm 工具鏈（先前 B0–B9 全為 Python）；已與使用者當面確認採用此路線並新增對應 CI job，而非改用零建置的純 HTML/JS 或本批只交付 ADR 不寫程式碼。

**目錄位置**：程式碼放在**新的頂層 `frontend/`目錄**（與 `src/`、`infra/`、`tests/`、`docs/` 同層），而非 CLAUDE.md §2 建議樹狀圖裡的 `src/ui`——後者是給 Python package 用的（hatchling wheel 仍列 `"src/ui"`，維持原樣、不放實際程式碼），React/Vite 專案有自己的 `package.json`／建置系統，硬塞進 Python package 目錄沒有實益。CLAUDE.md §2 標題本身即為「建議」，且 UI 技術堆疊明文留待本 ADR 決定，此路徑調整不算違反該建議樹狀圖。

**測試框架**：Vitest + React Testing Library（貼近 Vite 生態、設定最少）。**Lint（ESLint）本批刻意略過**：本沙盒環境沒有 Node.js，無法本地執行 `npm install`／`tsc`／`vitest` 驗證任何一行 TypeScript——`tsc --noEmit`（型別檢查，等同 Python 側的 mypy）與 Vitest 已是能在 CI 上真正把關的兩道關卡；ESLint 設定本身也有版本／flat-config 相容性風險，在無法本地驗證的情況下新增只會提高 CI 迴圈失敗的機率，故列為待確認、非本批交付範圍。

**Package lock**：同樣因為本地無 Node.js，**未提交 `package-lock.json`**（手工偽造鎖檔案風險更高，等同說謊）；CI 用 `npm install` 而非 `npm ci`。待任何一次 CI 成功後，建議下載其產生的 lockfile 提交回 repo 以固定版本（見 §5 待確認）。

## 2. 後端配合調整（非新端點，僅擴充既有 B9 端點的查詢參數）

Work-2 §4.2 的 11 個端點清單已在 B9 全數實作；B10 發現其中兩個既有 GET 端點的查詢能力不足以支撐 U02／U04：

- `GET /companies` 新增 `q`（公司名稱子字串，忽略大小寫）與 `cfl_status`（精確比對）——供 U02 搜尋、U04 CFL Queue 使用。
- `GET /events` 新增 `cfl_status` 與 `entity_id`——同上，`entity_id` 另外供 U03 公司詳情頁抓「相關事件」。

這些都是**既有端點的查詢參數擴充**，不是新增端點，不觸及 Work-2 §4.2 凍結的端點清單本身；對應的 repository 函式（`list_companies_by_universe`、`list_events`）以關鍵字參數擴充，呼叫端全部維持相容（同 B9 自己擴充 `list_companies_by_universe` 時的作法）。

## 3. 認證：本批沒有 OIDC 登入流程

Work-1 §3.9 把 U01–U04 定義為畫面，不是身分提供者整合；真正的 OIDC 登入（授權碼＋PKCE 等）需要一套完整的前端認證流程設計，超出「畫面」範疇，本 ADR 明確列為待確認、非本批交付。誠實的替代方案：`TokenInput` 元件讓使用者貼上（由部署方 IdP 核發，經任何管道取得的）Bearer Token，存在 `localStorage`，每次 API 呼叫帶上——這樣前端打到後端時走的是 B9 **真正**的 JWT 驗證路徑（`src/api/auth.py`），不是假流程。

`API_CORS_ORIGINS`（新環境變數，逗號分隔 origin，留空＝不啟用 CORS）讓前端開發伺服器（不同 origin）能呼叫後端。

## 4. 四個畫面

- **U01 儀表板**（`pages/Dashboard.tsx`）：公司 Universe 分布（真實資料，`GET /companies`）＋ GP-04 免責聲明（`DisclaimerBanner`，每個牽涉 Seco／CMI 類指標的畫面都掛）。`GET /dashboard/seco-cmi`（R03）保證 501，本頁刻意不呼叫，直接顯示「尚未建置」，避免呼叫一個穩定失敗的端點。
- **U02 搜尋**（`pages/Search.tsx`）：只有公司名稱搜尋是真的（`GET /companies?q=`）。Event 沒有可搜尋的文字/標題欄位（Work-2 §3.1 Event Contract 沒有這種欄位），Evidence 完全沒有清單端點（§4.2）——頁面上明講這兩個缺口，不假裝有搜尋。
- **U03 公司／事件詳情頁**（`pages/CompanyDetail.tsx`、`pages/EventDetail.tsx`）：`GET /companies/{id}`、`GET /events/{id}` 真實資料，含 Evidence 數量（無內容讀取端點，只有 `evidence_ids`）與 Event 的完整 Revision Chain。兩頁都內嵌 `CflDecisionForm`，可直接對該筆資料送出 CFL 決定。
- **U04 審查主控台**（`pages/AdminReview.tsx`）：`GET /companies?cfl_status=REVIEW-REQUIRED` ＋ `GET /events?cfl_status=REVIEW-REQUIRED` 兩條真實佇列，逐筆嵌入 `CflDecisionForm` 完成核准／駁回，滿足 Work-3 TEST 要求「U04 可完整操作 CFL Queue 核准／駁回流程」。**Relationship／Evidence 的 REVIEW-REQUIRED 佇列本批看不到**——§4.2 沒有這兩者的清單端點，不在本批新增（見 §5）。

`CflDecisionForm` 是 U03／U04 共用元件，直接呼叫 `POST /cfl/{cfl_id}/decision`（B9 已實作），顯示後端回傳的 `error_code`（400/404/409/423）。

## 5. 待確認 / 後續

1. **ESLint**：本批未設定（§1）——待有 Node.js 可本地驗證的環境時補上。
2. **`package-lock.json`**：待任一次 CI 的 `npm install` 成功後，取回其鎖檔提交，把 `npm install` 換回 `npm ci`。
3. **OIDC 登入流程**：`TokenInput` 只是誠實的過渡方案；真正的登入（redirect/PKCE/refresh token）需要另立設計，非本批範圍。
4. **Relationship／Evidence 清單端點**：U04 CFL Queue 目前只涵蓋 Company／Event；若要完整涵蓋全部 `CFL_GOVERNED_TABLES`，需要對 Work-2 §4.2 提出正式 Change Request 新增 `GET /relationships`、某種 Evidence 查詢端點，而非本批單方面決定新增。
5. Work-3 之後：**B11**（R01–R06 全部報告輸出；含 Internal Auto／Material Review／External Approval 三層，R06 正式外部發布須先通過 CFL-08）——完成後，U01 的 Seco／CMI 儀表板與 `POST /publications/{id}/approve` 才能從 501 換成真實邏輯。
