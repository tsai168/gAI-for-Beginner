# ADR-0004 — CFL-04 分工、G01 建置時序、傳輸機制、API 認證/RBAC（盤點報告 §6 Group 3）

- 狀態：**ACCEPTED**
- 日期：2026-09-10
- 核可：Research Director／Executive User（本專案人工授權）
- 來源：`docs/audit/CPO_AI_ReadOnly_Audit_Report.md` §3.3、D-1、X-3、G-7
- 影響檔案：`docs/WORK2_CONTRACT_FREEZE_V1.md` §4.4 → V1.3；`docs/WORK3_IMPLEMENTATION_BLUEPRINT_V1.md` §2 DAG（B1／B8 列）→ V1.2
- 治理定性：模組職責釐清、施工時序調整、既有「待補齊」佔位補實。不新增 Charter Frozen Decision，不改研究邏輯（Charter §7／§31「小幅調整」）。

---

## 決策 1 — CFL-04：M05 與 A04 分工

| 模組 | 職責 | Autonomy |
|---|---|---|
| **M05**（Materiality 評分器） | 依 Charter §15 Expert Rule 計算 `materiality_score`（0–100）；**產生 CFL-04 候選**（經 G01 介面提交，`cfl_status=PENDING`） | L0–L1（確定性／規則） |
| **A04**（Seco/CMI/重大性分析代理） | 讀 M05 分數 + Evidence 脈絡 → 產出 **Recommendation**（是否 Material 之建議、理由敘述、給審查者的旗標）。**不得寫 `materiality_score`、不得核准** | L2 |
| **G01** | 依 CFL-04 規則判定 AUTO-PASS／REVIEW-REQUIRED；高 Materiality → U04 人工 | — |

流程：`M05 算分 + raise candidate → A04 給 Recommendation → G01 判定 → (高 Materiality) U04 人工複核`。
四權分離：M05／A04 屬 Analysis，無 Approval／Publication 權（GP-21）。

## 決策 2 — G01 建置時序（D-1）

問題：G01 規則引擎排在 B8，但送 CFL 候選的模組在 B2／B3／B5／B6。

**裁定：G01 分兩段交付。**

| 批次 | G01 交付內容 |
|---|---|
| **B1** | **G01 介面樁**：`cfl_status` 欄位與 enum（`PENDING/AUTO-PASS/REVIEW-REQUIRED/APPROVED/REJECTED/BLOCKED/SUPERSEDED`）、CFL 狀態機常數、`cfl` service 介面（`submit_candidate(entity_ref, cfl_id, payload)` / `query_status(...)`）。預設實作：insert 時 `PENDING`、DB 層約束禁止其他模組直寫 `cfl_status`、**無 auto-pass**。 |
| **B8** | **完整規則引擎**：各 CFL-01～08 之 AUTO-PASS／REVIEW-REQUIRED 判定邏輯、outbox 至 U04 審查佇列。替換 B1 樁，**不動呼叫端簽章**。 |

效果：B2–B6 從第一天起就呼叫 `cfl` 介面；CLAUDE.md §4「不得繞過 G01」自 B1 起即由 DB 約束強制。

## 決策 3 — 模組間傳輸機制（X-3）

W04 每日研究管線（`DISCOVERED→…→PUBLISHED`）以 **Temporal**（I04，ADR-0001）之 workflow／activity／signal 作編排與模組間傳遞：

- 事件以 `event` 表（EVENT_CONTRACT 欄位）落地，採 **outbox pattern**；Temporal activity 讀寫該表。
- Work-2 §3.3 之 `cpoai.<layer>.<event_type>` 命名 → 對映為 Temporal signal／task-queue 名 + `event.correlation_id`／`causation_id` 串因果鏈。
- **V1 不引入獨立 message broker**（Kafka／NATS 等）。待吞吐量證明有需要時再評估（比照 ADR-0003 之 pgvector→專用向量庫策略），不影響上層 Data／Event Contract。

## 決策 4 — API 認證與 RBAC（G-7；取代 Work-2 §4.4 「待補齊」）

**認證**：OAuth2／OIDC bearer（JWT）。外部 IdP 簽發；API 驗證 JWT（issuer／audience／簽章／到期），claims 對映 Charter §5 六角色。設定經環境變數：`OIDC_ISSUER`、`OIDC_AUDIENCE`、`OIDC_JWKS_URL`。無自建帳密（Charter 禁止建立帳號類操作之精神）。

**RBAC 矩陣**（角色 × 功能群組）：

| 角色 | 讀 | Evidence／實體寫 | 模型執行 | 審查佇列 | 核准／發布 | Ops／設定 |
|---|---|---|---|---|---|---|
| Research Director | ✓ | – | – | ✓ | **✓** | – |
| Semiconductor Analyst | ✓ | **✓** | – | – | – | – |
| Quant Researcher | ✓ | – | ✓ | – | – | – |
| Research Reviewer | ✓ | – | – | ✓ | – | – |
| Executive User | ✓（僅摘要／發布層內容） | – | – | – | – | – |
| System Administrator | ✓ | – | – | – | – | ✓ |

- 無角色同時具「Evidence／實體寫」與「核准／發布」→ 符合 GP-21／CF-46。
- Agent 帳號（A01–A08）依同一原則由 G05 設定：A01（Evidence 寫，無核准）；A02–A06（Analysis，無核准／發布）；A07（L0 編排，無研究權）；A08（僅路由至人工佇列，無核准權）。
- **端點 → 功能群組**之逐條對照留待 **WBS-B9** 依本矩陣展開；不得新增跨權組合。

---

## 待確認（B9／部署階段定）

1. 具體 IdP 產品與 `OIDC_*` 值（Operations／部署）。
2. 「模型執行」端點是否需再細分（Quant Researcher 可跑哪些 M 模組、可否觸發 model promotion → 應為否，promotion 屬 Research Director）。
3. Executive User「摘要」範圍之精確界定（哪些 report_type／publication_tier 可見）。
4. Temporal task-queue 命名規範全表（B7 展開）。

## 後續

- Group 4：event topic 明細目錄（C-7）、K04 多型參照實作（ADR-0003 待確認 #5）、TQ-03 Kappa、TQ-04 γ、Deferred Items 清點。
