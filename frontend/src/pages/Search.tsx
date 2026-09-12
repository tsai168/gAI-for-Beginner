import { useState } from "react";
import type { FormEvent } from "react";
import { Link } from "react-router-dom";
import { ApiClientError, type CompanyOut, listCompanies } from "../api/client";

/** U02 — Search & Exploration (Work-1 §3.9: "跨 Company/Event/Evidence 搜尋").
 * Only Company name search is real: GET /companies supports `q` (WBS-B10).
 * Event has no text/title field in the Event Contract (Work-2 §3.1) to
 * search against, and there is no Evidence list endpoint at all
 * (Work-2 §4.2) — both are documented gaps (ADR-0022 §5), not silently
 * dropped. */
export function Search() {
  const [query, setQuery] = useState("");
  const [companies, setCompanies] = useState<CompanyOut[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [searched, setSearched] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    try {
      const results = await listCompanies({ q: query });
      setCompanies(results);
      setSearched(true);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "搜尋失敗");
    }
  }

  return (
    <div>
      <h1>搜尋與探索</h1>
      <form onSubmit={handleSubmit}>
        <label htmlFor="search-query">公司名稱關鍵字</label>{" "}
        <input
          id="search-query"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />{" "}
        <button type="submit">搜尋</button>
      </form>
      {error && <p role="alert">{error}</p>}
      {searched && (
        <section>
          <h2>公司（{companies.length}）</h2>
          <ul>
            {companies.map((c) => (
              <li key={c.company_id}>
                <Link to={`/companies/${c.company_id}`}>{c.company_name}</Link>
              </li>
            ))}
          </ul>
        </section>
      )}
      <p>
        事件與 Evidence 搜尋目前 API
        未提供：Event 無文字/標題欄位可比對，Evidence 無獨立查詢端點（Work-2
        §4.2）。有事件相關需求請至各公司詳情頁查看關聯事件列表。
      </p>
    </div>
  );
}
