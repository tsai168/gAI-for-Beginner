import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  ApiClientError,
  type CompanyOut,
  type EventOut,
  listCompanies,
  listEvents,
} from "../api/client";
import { CflDecisionForm } from "../components/CflDecisionForm";

/** U04 — Admin Review console (Work-1 §3.9: "CFL Queue、Human Review、
 * Approval 操作介面"). Lists Company/Event rows sitting at
 * REVIEW-REQUIRED and lets a reviewer act on each via G01's
 * POST /cfl/{cfl_id}/decision.
 *
 * Relationship/Evidence have no list endpoint (Work-2 §4.2 only defines
 * GET /companies and GET /events) — their REVIEW-REQUIRED rows aren't
 * visible here yet (ADR-0022 §5, flagged for a future CR rather than
 * inventing new endpoints outside the frozen contract). */
export function AdminReview() {
  const [companies, setCompanies] = useState<CompanyOut[]>([]);
  const [events, setEvents] = useState<EventOut[]>([]);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const [companyResults, eventResults] = await Promise.all([
        listCompanies({ cfl_status: "REVIEW-REQUIRED" }),
        listEvents({ cfl_status: "REVIEW-REQUIRED" }),
      ]);
      setCompanies(companyResults);
      setEvents(eventResults);
      setError(null);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "載入失敗");
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return (
    <div>
      <h1>人工審查主控台</h1>
      <p>
        僅列出 Company／Event 之 REVIEW-REQUIRED 佇列——Relationship／Evidence
        目前無對應清單端點。
      </p>
      {error && <p role="alert">{error}</p>}
      <section>
        <h2>公司（{companies.length}）</h2>
        {companies.map((c) => (
          <article key={c.company_id}>
            <h3>
              <Link to={`/companies/${c.company_id}`}>{c.company_name}</Link>
            </h3>
            <CflDecisionForm
              table="company"
              rowId={c.company_id}
              currentCflStatus={c.cfl_status}
              onDecided={refresh}
            />
          </article>
        ))}
      </section>
      <section>
        <h2>事件（{events.length}）</h2>
        {events.map((ev) => (
          <article key={ev.event_id}>
            <h3>
              <Link to={`/events/${ev.event_id}`}>{ev.event_id}</Link>
            </h3>
            <CflDecisionForm
              table="event"
              rowId={ev.event_id}
              currentCflStatus={ev.cfl_status}
              onDecided={refresh}
            />
          </article>
        ))}
      </section>
    </div>
  );
}
