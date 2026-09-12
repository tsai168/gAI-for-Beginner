import { useCallback, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import {
  ApiClientError,
  type CompanyDetailOut,
  type EventOut,
  getCompany,
  listEvents,
} from "../api/client";
import { CflDecisionForm } from "../components/CflDecisionForm";

/** U03 — Company detail page (Work-1 §3.9: "含 Evidence、Citation、Revision
 * 歷史呈現"). Evidence is shown as a count only — there is no Evidence
 * content-read endpoint yet (Work-2 §4.2), only `evidence_ids` nested in
 * the Company detail response. */
export function CompanyDetail() {
  const { companyId } = useParams<{ companyId: string }>();
  const [company, setCompany] = useState<CompanyDetailOut | null>(null);
  const [events, setEvents] = useState<EventOut[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    if (!companyId) return;
    getCompany(companyId)
      .then(setCompany)
      .catch((err: unknown) => setError(err instanceof ApiClientError ? err.message : "載入失敗"));
    listEvents({ entity_id: companyId })
      .then(setEvents)
      .catch(() => {
        // supplementary data — a failure here shouldn't blank the whole page
      });
  }, [companyId]);

  useEffect(() => {
    load();
  }, [load]);

  if (error) return <p role="alert">{error}</p>;
  if (!company) return <p>載入中…</p>;

  return (
    <div>
      <h1>{company.company_name}</h1>
      <dl>
        <dt>Universe</dt>
        <dd>{company.universe}</dd>
        <dt>股票代號</dt>
        <dd>{company.stock_code ?? "—"}</dd>
        <dt>CFL 狀態</dt>
        <dd>{company.cfl_status}</dd>
        <dt>Confidence</dt>
        <dd>{company.confidence ?? "—"}</dd>
        <dt>Evidence 數量</dt>
        <dd>{company.evidence_ids.length}</dd>
      </dl>
      <section>
        <h2>相關事件</h2>
        {events.length === 0 && <p>無相關事件。</p>}
        <ul>
          {events.map((ev) => (
            <li key={ev.event_id}>
              {ev.event_id}（{ev.pipeline_status}）
            </li>
          ))}
        </ul>
      </section>
      <CflDecisionForm
        table="company"
        rowId={company.company_id}
        currentCflStatus={company.cfl_status}
        onDecided={load}
      />
    </div>
  );
}
