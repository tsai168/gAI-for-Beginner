# ADR-0026 — A01 抽取代理：最小可行版本（LLM 整合首次落地）

- 狀態：**ACCEPTED（產品範圍決策，隨本 ADR PR 由 Executive User 逐項確認）**
- 日期：2026-09-14
- 核可：Research Director／Executive User（模型選擇／Authority 來源／未知公司處理／處理單位四項，逐一於對話中確認）
- 來源：Work-2 AGENT_SPEC §6（A01，L1，"建立 Entity／Event／Evidence／Technology Candidate；Candidate ≠ Fact"）、`agents/base.py`／`models/evidence_stage.py` 既有 docstring（"no prompts, output schemas, or per-source extraction rules"／"needs semantic judgment — L1，A01"）、Charter §11.1（E0–E6）、§16（CF1–CF5）、CF-10（Authority/Directness/Time/Specificity/Independence）

---

## 0. 為什麼這是產品決策，不是純技術缺口

與 B12 之後的三項技術缺口（I03／索引稽核／ESLint）不同，`agents/base.py` 原始 docstring 明確寫著 A01 的 `_perform` "is deferred: Charter/Work-1 through 3 specify no prompts, output schemas, or per-source extraction rules. **That is product design work**"。逐一查證後（見 §1），資料模型本身（`EV01–EV12`、`E0–E6`、`SUPPORT/CONTRADICT/NEUTRAL-CONTEXT`）其實都已在 Charter 凍結，真正缺的只是「怎麼把原始文字轉成這些分類值」——但「怎麼轉」牽涉到範圍/取捨決策，依 CLAUDE.md §10 仍需人類拍板，故本 ADR 記錄的每一項範圍選擇，都是先提案、經 Executive User 逐項確認後才動工，而非工程自行決定。

## 1. 範圍勘查：資料模型其實已經凍結

- `EventTaxonomyCode`（EV01–EV12）：Charter 有明確標籤（Technology／Product／Qualification／Customer／Partnership／Production／Shipment／Order／Revenue／Capacity／Competition／Negative Event）。
- `EvidenceStage`（E0–E6）：Charter §11.1 明確定義（Rumor/Mention → ... → Revenue Contribution）。
- `EvidenceType`（SUPPORT/CONTRADICT/NEUTRAL-CONTEXT）：Charter CF-11。
- CF-10 五構面（Authority/Directness/Independence/Temporal Quality/Specificity）：Charter 有名稱，但**無語意判斷演算法**——`models/evidence_stage.py`／`models/confidence.py` 的既有 docstring 都明確點名這是 A01 的工作。
- 稽核既有 repository 函式（`create_evidence`／`create_event`／`record_contradiction`）確認：CF1 Authority（`evidence.authority`）目前**沒有任何 production 程式碼寫入**——P05（`ingestion/credibility.py`）只算 `source_credibility_tier`（S1–S5），完全沒碰 CF1–CF5 四個 0–1 欄位；這正是 A01 缺的那一塊。

## 2. 決策一：模型選擇

`LLM_MODEL_ID` 為 Work-1 §8／CLAUDE.md §4 明確列出的 Deferred Item，不得寫死。預設值經 Executive User 確認為 **`claude-sonnet-5`**，以環境變數注入（`.env.example`／`AnthropicExtractionClient`），未設定時退回此預設——與 `REDIS_URL` 等既有 opt-in 慣例一致。`LLM_MAX_OUTPUT_TOKENS`／`LLM_DAILY_TOKEN_BUDGET` 仍完全 Deferred，未定案，程式碼讀取環境變數、給一個工程合理預設（`max_tokens=4096`），不代表已定案的預算數字。

**測試策略**：Executive User 確認目前無可用 `ANTHROPIC_API_KEY`，故本批採「先 mock 開發」——單元／整合測試皆對 `LLMClient` Protocol 注入假實作，不需要真的呼叫 API；`tests/integration/test_extraction_llm.py` 對真實 API 送測，`ANTHROPIC_API_KEY` 未設定時 skip 不 fail（同 `test_cache_redis.py`／`ADR-0019` §1 既有慣例）。CI `integration` job 已接上 `secrets.ANTHROPIC_API_KEY`（目前為空）——之後在 GitHub repo 設定加上這把 key，此測試會自動從 skip 變成真的執行，不需要再改程式碼。

## 3. 決策二：CF1 Source Authority 用固定映射表，不讓 LLM 猜

`evidence.authority` 由 `source_credibility_tier`（P05 已確定性算好的 S1–S5）透過固定映射表算出（`authority_from_source_tier()`，`src/agents/extraction.py`）：

| Tier | Authority |
|---|---|
| S1 | 1.0 |
| S2 | 0.8 |
| S3 | 0.6 |
| S4 | 0.4 |
| S5 | 0.2 |

理由（Executive User 確認）：同一來源的可信度不該因為每次抽取的文字不同而忽高忽低。這組數字是實作預設（比照 `ADR-0013` §3 CF1–CF4 權重的態度），非 Frozen Decision，可調整。

## 4. 決策三：未知公司——不自動建立，回傳待人工複核清單

文字提到不在既有追蹤清單（`list_companies_by_universe(session)`，涵蓋 Core/Adjacent/Watchlist 全部，非僅 Watchlist 一層）中的公司時，**不自動建立 `Company` row**（GP-07：不得無充分依據自行具名）。這類 Evidence 仍會建立（內容本身可能仍有價值），但 `entity_ref`／`entity_ref_type` 留 `None`；同時回傳一份 `UnknownCompanyMention`（`raw_name`／`evidence_id`／`rationale`）供呼叫端交給人工複核。

**刻意的 v1 簡化**：沒有為此新增一張「待審佇列」資料表——回傳值只是一個記憶體內的 list，由呼叫端（未來的排程/報告層）決定怎麼呈現給人工。若之後實際使用量顯示需要持久化佇列，屬後續增量，非本 ADR 範圍；本 ADR 只保證「不會憑空生出錯的公司，也不會把提及默默丟掉」。

## 5. 決策四：處理單位——一份 Snapshot 對多筆 Evidence

`extract_evidence_from_snapshot()` 一次呼叫、一次 LLM request，可產出 0～N 筆 Evidence（Executive User 確認：貼近真實情境——一份公告常同時提到好幾件事）。回傳 `(list[Evidence], list[UnknownCompanyMention])`。

## 6. 明確排除：Event 建立／比對不在本批範圍

`event_taxonomy_code` 分類、判斷一段文字對應既有 Event 還是該開新 Event，需要時間維度的去重邏輯（同一事件的多份報導不該變成多個 Event），這是比「單筆 Evidence 分類」更難的獨立問題，本批**不處理**。A01 v1 只產生 Company-linked 的 Evidence（`entity_ref_type="company"`），不建立或連結任何 Event。這與既有 E2E 測試（`test_acceptance_e2e.py`）目前的簡化寫法一致——該測試裡 Event 本來就是在 A01 階段之前，由假想的 W01/W02 先建好的。

## 7. 實作

- `src/agents/extraction.py`（新）：`LLMClient` Protocol + `AnthropicExtractionClient`（`anthropic.Anthropic().messages.parse()`，Pydantic `output_format` 結構化輸出，直接複用既有 `EvidenceType`/`EvidenceStage` StrEnum，不重複定義）、`authority_from_source_tier()`、`extract_evidence_from_snapshot()`、`ExtractionRequest`/`ExtractionOutcome`（`ExtractionAgent.run()` 的 payload/回傳型別）。
- `src/agents/roster.py`：`ExtractionAgent._perform` 從 `NotImplementedError` 改為呼叫 `extract_evidence_from_snapshot`。CONTRADICT 類型的 Evidence 額外呼叫既有 `record_contradiction`（CFL-07），不繞過 G01（CLAUDE.md §4）。
- `pyproject.toml`：`anthropic` 下限由 `>=0.34` 提升為 `>=1.0`（`messages.parse()` 結構化輸出僅 1.x 提供，已於本機驗證 `anthropic==1.5.0` 確實具備此方法）。
- `.env.example`：`LLM_MODEL_ID` 註解更新為「留空即用 claude-sonnet-5 預設」。
- CI `integration` job：新增 `secrets.ANTHROPIC_API_KEY`（目前為空，skip-not-fail）。

## 8. 驗證

本地驗證（新鮮 venv，無 `DATABASE_URL`／`ANTHROPIC_API_KEY`）：`ruff check .`／`ruff format --check .`／`mypy src`（64 檔案）全通過；`pytest`：354 passed（含 `tests/test_extraction.py` 三個純函式單元測試——`authority_from_source_tier` 的已知/未知 tier／`None` 三種情形）。

**尚未在本沙盒驗證、留待 CI 或真實環境**：
- `tests/integration/test_extraction.py`（6 個測試，真實 Postgres + 假 `LLMClient`）：`entity_ref` 正確連結／未知公司不自動建立且正確回傳待審清單／CONTRADICT 正確觸發 CFL-07／空清單不建任何 Evidence／prompt 正確包含公司清單與原文／`ExtractionAgent().run()` 完整走過 G02 authorize 閘門——本機無 Postgres，全部 skip，非通過。
- `tests/integration/test_extraction_llm.py`：真實呼叫 Claude API 的結構驗證（型別／範圍，不驗證語意正確性）——本機無 `ANTHROPIC_API_KEY`，skip，非通過。
- `AnthropicExtractionClient`／`messages.parse(output_format=...)` 的實際請求／回應格式，完全依據官方 Claude API 技能文件撰寫，**從未實際打過一次 API**——與 ESLint 先前的處境相同：寫了但沒有本地執行過，需要 CI（一旦補上 `ANTHROPIC_API_KEY` secret）或人工在有 key 的環境跑一次才能真正確認。

## 9. 後續（非本批範圍）

1. 待有 `ANTHROPIC_API_KEY` 後：加為 GitHub repo secret，確認 `test_extraction_llm.py` 真的通過；同時建議先用真實資料樣本人工檢視幾筆抽取結果的品質，再考慮擴大使用範圍。
2. Event 建立／比對（§6 排除項）——需要獨立設計時間維度去重邏輯，是否／何時展開待 Executive User 決定。
3. 未知公司待審清單的持久化（§4 提到的簡化）——若實際使用顯示需要，屬後續增量。
4. A02–A08（分類／關係矛盾／Seco-CMI-重大性分析／比較／審查／協調／人工介接）——本 ADR 只解 A01，其餘 Agent 仍是 `NotImplementedError` 樁，何時展開待 Executive User 排序。
5. `LLM_MAX_OUTPUT_TOKENS`／`LLM_DAILY_TOKEN_BUDGET` 仍是未定案的 Deferred Item，目前只有工程預設（4096 tokens），非正式預算決策。
