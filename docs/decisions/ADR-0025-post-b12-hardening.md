# ADR-0025 — B12 收尾後補強：I03 快取、索引／約束稽核、ESLint 補件

- 狀態：**ACCEPTED（技術缺口補件，非新決策；三項皆屬 Charter §7／§31「小幅且不改變研究契約的調整」)**
- 日期：2026-09-13
- 核可：Research Director／Executive User（明確指示三項為「純技術缺口,決策已經定案」）
- 來源：`ADR-0005` §I03 批次歸屬（"B5：Seco/CMI 儀表板讀取需要時才加"）、`ADR-0007`／`ADR-0014` 型別基準、`ADR-0022` §1／§5（ESLint／package-lock 環境限制）

---

## 1. 範圍與三項任務的共同前提

Work-3 §2 DAG 的 B0–B12 已於 `ADR-0024` 全數完成並驗收。本 ADR 記錄 B12 之後、Executive User 明確標示「決策已定案、屬純技術缺口」的三項補強工作，逐項各自獨立，互不相依：

1. **I03 快取層實作**——`ADR-0005` 已排入 B5，技術選型（Redis／其他）當時保留待定；今指定為「低風險預設」層級，由 Claude Code 補上具體實作。
2. **索引／約束稽核**——`ADR-0007`／`ADR-0014` 已定型別基準，本項是依既有 schema 系統性補齊唯一約束／索引／FK ON DELETE 政策的工程細節，非新決策。
3. **ESLint／`package-lock.json`**——`ADR-0022` §1／§5 已記錄為純環境限制（沙盒無 Node.js），非決策問題。

## 2. I03 快取層

### 2.1 技術選型：Redis，opt-in-or-degrade

採 `CacheBackend` Protocol + 兩個實作：`InMemoryCache`（預設，零基礎設施，per-process）／`RedisCache`（`REDIS_URL` 設定時啟用，多 worker 共用）。與 `API_CORS_ORIGINS`、`OIDC_ISSUER` 同一慣例——未設定即退回安全預設，不強制依賴外部服務。`redis`（redis-py）加入 `pyproject.toml` 硬依賴（非 lazy-import：既然已固定為專案依賴，`PLC0415` 規則要求 top-level import，沒有保留「optional」的理由）。

### 2.2 快取範圍：僅 R03 儀表板讀取

Work-1 §3.10 明確點名「高頻讀取（Dashboard／Seco/CMI）加速」是 I03 存在的理由；本專案其餘讀取路徑（單筆治理查詢、報告產生）都不是高頻讀取，不需要快取，故只包住 `reports/dashboard.py` 的 `get_seco_cmi_dashboard`／`get_company_scores` 兩個函式，未擴大範圍。

### 2.3 失效策略：TTL-only（60 秒），非 invalidate-on-write

Work-1 的十層模組依賴方向固定為 D/P/K/M/A/W/R/G/U/I，R（Reporting）在 M（Models，Seco/CMI 計算）之上。若採 invalidate-on-write，M03/M04 寫入分數時必須呼叫 R03 使快取失效，等於讓下層模組依賴上層模組，違反既定分層方向。改採 TTL-only：60 秒短視窗把 staleness 上限鎖住且可預期，是明確記錄的取捨，不是疏漏——`src/reports/cache.py`／`dashboard.py` 檔頭皆有此說明。

### 2.4 驗證

- 單元測試 `tests/test_cache.py`：`InMemoryCache` 的 get/set/TTL 過期邊界（用可注入的 fake clock，非真實 sleep）／`get_cache_backend()` 預設行為。
- 整合測試 `tests/integration/test_cache_redis.py`：對真實 Redis 跑（`REDIS_URL` 未設定或連不上時 skip，非 fail，同 `ADR-0019` §1 對 Temporal 測試的既定作法）。
- 整合測試 `tests/integration/test_reports_dashboard_cache.py`：對真實 Postgres + `InMemoryCache`，直接證明「TTL 內即使 DB 已變更仍回舊值、TTL 到期後才刷新」——這是本任務最關鍵的驗證，證明快取真的接上 R03，不是只寫了一個沒人呼叫的模組。
- `mypy src/reports/cache.py`（及全專案 63 檔案）在裝有真實 `redis` 套件的 venv 下通過，`RedisCache` 對 `_RedisLike` Protocol 的結構化型別檢查無誤。
- 基礎設施：`infra/docker-compose.yml` 新增 `redis` service；CI `integration` job 新增 `redis` service container + `REDIS_URL` 環境變數，讓 `RedisCache` 分支在 CI 也被真實跑到（而非只有本機预设的 `InMemoryCache` 被覆蓋）；`.env.example` 的既有佔位改名 `CACHE_URL`→`REDIS_URL`（原註解「產品待 B5 定」已不合時宜，一併更新為指向本 ADR）。

### 2.5 CI 第一次跑，真的抓到兩個問題——記錄下來，不是船過水無痕

推上 CI（`#114`）後 `integration` job 真的紅了 2 個測試，兩個都循實際錯誤訊息追根因，而非憑印象亂猜：

1. `test_dashboard_serves_stale_data_within_ttl_then_refreshes` 丟 `MultipleResultsFound`：測試為了模擬「DB 換了新分數」，對同一間公司呼叫了兩次 `record_seco_score`——但這個函式只負責新增,不負責讓舊列退場;正確作法是`correct_seco_score`(GP-10/CF-17既有機制,`test_seco_cmi_db.py`已經這樣用過),測試沒照做,不是`cache.py`的錯。已修正。
2. `test_reports_internal_auto.py::test_dashboard_lists_companies_with_a_current_score`(B11既有測試,跟本次新增檔案無關)因為`get_seco_cmi_dashboard`的清單快取用單一固定 key,而 CI `integration` job 現在真的接了共用 Redis(本 ADR §2.4 剛加的),同一個 60 秒 TTL 視窗內任何沒自帶`cache=`的呼叫都共用同一份快取——`db_session`的逐測試 rollback 保護不到這種活在 DB 交易之外的資源。修正方式:`tests/conftest.py`加一個 autouse fixture,每個測試開始前清掉這個固定 key(每間公司自己的 cache key 因為 company_id 每次都是新 UUID,不會撞,不用清)。

兩者都只能在 CI 才會現形——本沙盒沒有 Postgres/Redis,`pytest -m integration`在本機是整批 skip,不是真的跑過再過關。修正後重推(`cff45c9`),CI `#115` 四個 job 全綠,`integration (db)`(36s)本身也通過。

## 3. 索引／約束稽核

### 3.1 方法：逐一比對，非臆測

逐一比對每個 `list_*`／`get_*` repository 函式實際使用的 `.where()` 過濾欄位，對照 ORM 既有 `Index(...)` 宣告，找出**真正**的缺口，而非猜測性地到處加索引。

### 3.2 找到的缺口（`src/knowledge/db/models.py`）

- 每個受 CFL 治理的表（`CFL_GOVERNED_TABLES`：Company／Relationship／Event／Evidence／ResearchReport）都缺 `cfl_status` 索引（G04 CFL Queue 查詢的主要過濾欄位）——全部補上。
- `Company.universe`／`Company.company_name`、`Event.pipeline_status`／`Event.entity_id`——對應既有查詢函式的過濾／關聯欄位，先前批次遺漏。
- 新增 `_range_check()` helper（`models.py`，用 SQLAlchemy `naming_convention` 產生 `ck_<table>_<column>_range` 命名），為 Company／Relationship／Event／Evidence／SecoScore／CmiScore／ResearchReport 的 confidence（0–1）與各分數欄位（0–100，Seco 六構面＋總分、CMI 五構面＋總分、Event materiality_score）補上 DB 層級 CHECK 約束——先前批次僅在應用層驗證，DB 層沒有最後一道防線。

### 3.3 FK ON DELETE 政策：稽核後確認無缺口

逐一檢視全部 FK：CASCADE（owned children，如 `company_id` 於 product/market_data/institutional_trading/shareholding/seco_score/cmi_score）、RESTRICT（設定／不可變參照，如 `model_version_id`、`technology_id`、`data_source_code`、`source_id`）、SET NULL（軟參照，如 `person.affiliation_company_id`、`evidence.event_ref`）——三類皆已在先前批次一致套用，**本次稽核結論為無缺口，不需變更**。誠實記錄「稽核過、沒問題」，優於為了交差而製造不必要的變更。

### 3.4 Migration 0008 的冪等設計

先渲染 `alembic upgrade head --sql`（改 `models.py` 之後）確認：`Base.metadata.create_all()` 永遠讀取當下的 live model 狀態，所以全新資料庫直接由 migration 0001–0007 的 `CREATE TABLE` 就會帶有新索引／約束，**migration 0008 對全新資料庫是安全的 no-op**；但對「已部署、只跑過 0001–0007」的既有資料庫，0008 是真正需要的增量升級。這是 `ADR-0013` §0（B8 CI 事故建立的 live-metadata 政策）的直接延伸：索引用 `CREATE INDEX IF NOT EXISTS`，CHECK 約束因 Postgres 無原生 `ADD CONSTRAINT IF NOT EXISTS`，改用 `DO $$ BEGIN ... EXCEPTION WHEN duplicate_object THEN NULL; END $$;` 包裝，兩者皆已驗證 upgrade／downgrade 兩個方向的 SQL 都能乾淨渲染。

### 3.5 驗證

`tests/integration/test_index_constraint_audit.py`：對真實 Postgres，直接下 `UPDATE ... SET confidence = 1.5` 之類的越界值，驗證 DB 層真的擋下（`DBAPIError` 訊息含約束名）；正常值可正常寫入；並對 7 組 table/index 查 `pg_indexes` 系統目錄確認索引確實存在。

## 4. ESLint——已寫且已由 CI 真實驗證通過；`package-lock.json` 環境限制仍在

本次 session 再次確認：本地開發沙盒無 Node.js／npm（`which node npm` 無輸出），與 B10 批次（`ADR-0022` §1）完全相同的限制。但這**不等於「無法驗證」**——CI runner 本身就有真正的 Node.js 20，所以把驗證責任交給 CI 是誠實可行的路徑，不是迴避。

- 撰寫 `frontend/eslint.config.js`（ESLint 9 flat config，`typescript-eslint` + `eslint-plugin-react-hooks` + `eslint-plugin-react-refresh`，比照 Vite React-TS 官方模板慣例，設定與 `tsconfig.json` 的 strict／ES2020／react-jsx 一致）；`frontend/package.json` 新增對應 `devDependencies` 與 `"lint": "eslint ."` script；CI 的 `frontend` job 新增 `npm run lint` 步驟（排在 type-check 之前）。
- **CI `#114`／`#115` 的 `frontend (type + test + build)` job 皆為 Success**（`npm install` 成功解析新的 ESLint 相關套件、`npm run lint` 本身乾淨通過、`type-check`／`test`／`build` 也都沒受影響）——這組設定已經是**經過真實 Node.js 環境驗證過的**，不再是「未驗證」狀態，本節先前版本的措辭已過時。
- **`package-lock.json` 依然無法在本地產生**：鎖檔案的正確內容只能來自真實 `npm install` 的解析結果，手工偽造等同說謊（`ADR-0022` §1 已有此原則）；CI 的 `frontend` job 繼續使用 `npm install`（非 `npm ci`）。既然 CI `#115` 的 `npm install` 已經成功解析出一組完整、可行的版本組合，建議下載該次 run 的 lockfile 提交回 repo，才能把 `npm install` 換回 `npm ci`——這是 `ADR-0022` §5 既有待辦的延伸，現在有了一個具體可行動的 CI run 可以取用。

## 5. 驗收

本地驗證（新鮮 venv，無 `DATABASE_URL`／`REDIS_URL`）：`ruff check .`／`ruff format --check .`／`mypy src`（全部通過，模組數隨新檔案增加）／`pytest`（單元測試全過；`integration`／`migration` 標記測試因無 Postgres/Redis 而 skip，非 fail）／`alembic upgrade head --sql` 與 `alembic downgrade --sql head:base` 兩個方向皆能乾淨渲染。

CI 驗收（真正決定性的一關，因為本地缺 Postgres/Redis/Node.js）：`#114`（`e4f1b1d`）首次推上時 `integration (db)` 兩個測試失敗（§2.5 已詳述根因與修法），修正後 `#115`（`cff45c9`）**四個 job 全綠**——`frontend (type + test + build)` 35s、`lint + type + unit` 22s、`alembic round-trip` 29s、`integration (db)` 36s。ESLint 與 I03/Redis 的 `RedisCache` 分支都是在這次才第一次被真實環境驗證，不是本機臆測。

## 6. 後續（非本批範圍）

1. 下載 CI `#115`（`cff45c9`）`npm install` 產生的 `package-lock.json` 提交回 repo，並把 `frontend` job 的 `npm install` 換回 `npm ci`（`ADR-0022` §5 既有待辦，現已有可行動的具體 run）。
2. I03 快取的 60 秒 TTL 為初始預設值，若儀表板實際流量顯示過短／過長，可調整（設定值形式，非寫死契約）。
3. `ADR-0024` §7 列出的其餘後續項目（A01–A06 LLM 整合、I01–I06 部署基礎設施等）維持原狀，不受本 ADR 影響。
