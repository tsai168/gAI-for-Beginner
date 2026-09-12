# ADR-0020 — WBS-B8：治理層完整版（G01 規則引擎／G03 稽核日誌／G06 發布狀態機／G07／G08）

- 狀態：**ACCEPTED（B8 實作決議）**
- 日期：2026-09-12
- 核可：Research Director／Executive User（隨 B8 PR 審閱）
- 來源：Work-3 §2 DAG B8 列、§4 TEST-CFL-01/02/03、Charter §17（CFL）／§18（Publication）／§22（NFR）／§31（Change Control）；Work-2 §5 CFL_CONTRACT；`ADR-0003`（G-1 schema 缺口先例）、`ADR-0004`（CFL 分工／B1 樁→B8 引擎）、`ADR-0005`（G8 Material Review 旗標）

---

## 1. 範圍

Work-3 B8 = 「G01 CFL 規則引擎（各 CFL 之 AUTO-PASS/REVIEW-REQUIRED 邏輯、outbox 至 U04；替換 B1 介面樁，不動呼叫端）、G03 稽核日誌、G06 發布狀態機、G07 Change Control、G08 合規監控」。五個子模組性質差異大，逐一說明；共同原則：**不動既有呼叫端**（`company.py`/`relationship.py`/`evidence.py`/`credibility.py`/`materiality.py` 皆完全不改），只替換／新增其背後的實作。

## 2. G01 — CFL 規則引擎（`src/governance/cfl.py`）

`DefaultCflService`（B1 樁，永遠回 PENDING）→ `RuleBasedCflService`（真正判斷），`default_cfl_service` 這個既有呼叫端 import 的名稱不變。規則對應 Charter §17 V1 原則，逐一鍵於既有欄位（呼叫端完全不用多傳參數）：

| CFL | 判斷依據 | 理由 |
|---|---|---|
| CFL-01 公司身分 | `company.confidence >= 0.85` **且** `stock_code` 非空 → Auto-pass；否則 Review | 「高 Confidence、可驗證」＝已有信心分數且能對到交易所股票代號；目前無呼叫端（A02 尚未實作候選產生），規則備妥待接 |
| CFL-02 CPO 分類 | 永遠 Review | `company.set_universe` 本身只在「首次升 Core」才會呼叫 G01（呼叫端已篩選），故 G01 收到即代表命中 Charter「首次升 Core 需 Human Review」 |
| CFL-03 來源可信度 | `evidence.source_credibility_tier` 非空（已知 D01–D08 官方來源）→ Auto-pass；否則 Review | 直接對應 P05 已寫入的欄位 |
| CFL-04 重大事件 | `event.materiality_score >= 70` → Review；否則 Auto-pass | 「一般事件 AI 分類；高 Materiality 需 Review」；`70`為 V1 Expert-Rule 預設，**非 Frozen**，可調整 |
| CFL-05 生態系關係 | 永遠 Review | 同 CFL-02：`confirm_relationship` 只在「首次具名 Confirmed」才呼叫 G01 |
| CFL-06 競爭分析 | 永遠 Review（保守預設） | R05 比較分析輸出 schema 尚未建置，無法判斷 Draft vs 正式重大結論；目前也無呼叫端 |
| CFL-07／CFL-08 | 永遠 Review（`NO_AUTO_PASS` 不變） | Charter 明文禁止 Auto-pass |

`_HIGH_CONFIDENCE_THRESHOLD`（0.85）／`_HIGH_MATERIALITY_THRESHOLD`（70.0）為模組常數，非寫死於呼叫端、可獨立調整，性質同 M02/M05 既有權重（非 Frozen Decision）。

`submit_candidate` 新增**冪等**語意：若該列 `cfl_status` 已非 PENDING（已經決議過，或人工已手動轉移），直接回傳現況，不重新判斷——避免「資料事後變更 → 重跑候選 → 已核准的閘門被悄悄改判」（治理漂移風險，Charter §24 已列risk）。要改變已決議的 CFL 狀態，一律走 `set_status`（人工／U04）明確轉移。

「outbox 至 U04」：U04（B10，尚未開工）目前沒有實作，故本批**不**新建 outbox 佇列表；`REVIEW-REQUIRED` 的列本身即可用 `SELECT ... WHERE cfl_status = 'REVIEW-REQUIRED'` 查詢，U04 開工時再決定是否需要專用佇列/通知機制。

## 3. G03 — 稽核日誌（`src/governance/audit.py` + `audit_log` 表）

Work-1 §3.8：G03 需保存「Agent、Rule、Input、Evidence、Confidence、Model」，但此表不在 Work-2 §2／§2.9 任何一張凍結 schema 內——與 `ADR-0003` 當時補 K01–K06 缺口性質相同，本 ADR 沿用同一套治理程序補齊：新表**不改**既有欄位語意，純新增。

`audit_log`：`audit_log_id / agent_id / rule_ref / table_name / row_id / decision / evidence_ids / confidence / model_version_id / correlation_id / created_at`。Append-only（migration 0006 沿用 migration 0002 既有的 `cpoai_append_only()` trigger function，不重新定義）——治理決策紀錄本身不可竄改（CF-08/GP-15 同一精神）。

寫入點：`RuleBasedCflService.set_status`（所有 `cfl_status` 寫入的唯一入口，見 §2）。`agent_id`／`Evidence`（`evidence_ids`）目前多數呼叫端還沒有這些資訊可傳（`agent_id` 全部為 `None`），欄位保留給未來 A01–A08／U04 真正串接時使用，不是現在就能填滿的資料。

## 4. G06 — 發布狀態機（`src/governance/publication.py` + K05 `advance_pipeline_status`）

Charter §18 三層發布（Internal Auto／Material Review／External Approval）與其列名的內容種類（`PublicationContentKind`）逐字轉錄；`classify_publication_tier` 只是查表，不做任何推論。`assert_publication_allowed`：Internal Auto 免閘門；Material Review／External Approval 都要求對應 CFL 已 `APPROVED`（呼叫端自行決定要傳哪個 CFL 的現況——G06 不重複 Work-2 §5 CFL_CONTRACT 的「哪個 CFL 管哪種內容」對照表）。

`research_report`（R02，B11 才建；`ADR-0003` G-1 已標記 `content_ref` 儲存位置 "OPEN — B11 前定"）尚不存在，故 G06 本批**不**接上一個真正的 Report 實體；而是接上 Work-2 §3.2 EVENT_CONTRACT 明文列出的 `APPROVED → PUBLISHED`（對應模組 G06/R01–R06）這一步——K05 新增 `advance_pipeline_status`，同時補齊 TEST-EVENT-01 一直未被實作的一般性檢查（`pipeline_status` 只能依 `DISCOVERED→...→PUBLISHED` 逐格前進，不得跳格／倒退），並在 `PUBLISHED` 這一步接上 G06 閘門（TEST-CFL-02）。`publication_tier` 預設 `INTERNAL_AUTO`（對應 Charter §18 例子「事件清單」），R06 開工後可傳入真正分類的 tier。

## 5. G07 — Change Control（`src/governance/change_control.py`）

Work-2 沒有為「Change Request」定義資料庫 schema——本專案實務上一直用 `docs/decisions/ADR-*.md` 兼任 CR 記錄（`ADR-0003` 自己就寫明「本 ADR 兼任 CR 記錄」）。本模組**不**另建一套平行資料庫，只是把 Charter §31 要求的 CR 五要素（原因／影響／向後相容性／資料重算需求／驗收方式）與版本升級規則（V1.x／V2.0）給一個可驗證的型別（`ChangeRequest`/`validate_change_request`/`classify_version_bump`），供未來工具（例如 U04 admin 檢視）使用。

## 6. G08 — 非功能合規監控（`src/governance/compliance.py`）

Work-1 §3.8／Charter §22：Traceability／Reproducibility／PIT Integrity／Cost Governance。**這是監控（掃描已算好的資料找違規），不是攔截（M04 `assert_no_future_data`／`cpoai_cfl_guard` trigger 那種即時擋）**——兩者角色不同，不重複實作既有 guard。`is_material_score_change`（比例門檁 20%，非 Frozen）對應 `ADR-0005` §後續「Seco/CMI 大幅變動走 G08 Material Review 旗標（非新 CFL）」，餵給 G06 的 `PublicationTier.MATERIAL_REVIEW`。`CostBudget`（Token Budget／Daily Ceiling／Cost Alert）延續 Work-2 §9 Deferred Item：所有欄位預設 `None`＝未設定＝不限制，**不寫死任何數字**。

## 7. 驗收

- G01：CFL-01（confidence+stock_code 各種組合）、CFL-03/04（既有呼叫端測試更新其預期值：PENDING→實際判斷結果）、CFL-07（永遠 Review）、submit_candidate 冪等性、每次決策必留 audit_log（`tests/integration/test_cfl_rules_db.py` + 既有整合測試更新）。
- G03：寫入／查詢、append-only trigger 拒絕 UPDATE（`tests/integration/test_audit_log.py`）。
- G06：Charter §18 全部內容種類對照表、Internal Auto 免閘門、Material/External 需 APPROVED 才放行（`tests/test_publication.py`）；K05 `advance_pipeline_status`：合法逐格前進／跳格拒絕／倒退拒絕／PUBLISHED 前 CFL-08 未過擋下／過了才放行（`tests/integration/test_event_pipeline_status.py`）。
- G07：CR 五要素缺一即拒絕、V1.x/V2.0 分類（`tests/test_change_control.py`）。
- G08：四類檢查＋Material 變動門檁＋Cost Budget 未設定不擋（`tests/test_compliance.py`）。

本地驗證：新鮮 venv，`ruff check .`／`ruff format --check .`／`mypy src`（strict，49 檔案）／`pytest`（313 unit passed；56 integration/migration skipped，本機無 `DATABASE_URL`）；`alembic upgrade head --sql` 與 `downgrade --sql head:base` 皆完整渲染至 `0006_audit_log`。

## 8. 待確認 / 後續

1. CFL-01／CFL-06 目前無真正呼叫端（A02／R05 尚未實作）——規則已備妥，等對應模組開工時直接接上，不需再動 G01。
2. U04（B10）開工時，需決定 REVIEW-REQUIRED 佇列是否需要專用 outbox 表，或直接查詢 `cfl_status = 'REVIEW-REQUIRED'` 已足夠。
3. `research_report`（R02，B11）建置時，`advance_pipeline_status` 的 `publication_tier`/`cfl_08_status` 預設值（目前皆為 Internal Auto／None）需由 R06 依實際內容分類傳入真值。
4. Work-3 之後：**B9**（U05／API 層，第 4.2 節端點全數實作；所有寫入 `cfl_status` 之端點皆經 G01；錯誤碼格式符合 4.3 節規範）。
