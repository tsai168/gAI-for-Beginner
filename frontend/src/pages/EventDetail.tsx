import { useCallback, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { ApiClientError, type EventDetailOut, getEvent } from "../api/client";
import { CflDecisionForm } from "../components/CflDecisionForm";

/** U03 — Event detail page: pipeline/CFL status plus the full Revision
 * Chain (K05, CF-35/36). */
export function EventDetail() {
  const { eventId } = useParams<{ eventId: string }>();
  const [event, setEvent] = useState<EventDetailOut | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    if (!eventId) return;
    getEvent(eventId)
      .then(setEvent)
      .catch((err: unknown) => setError(err instanceof ApiClientError ? err.message : "載入失敗"));
  }, [eventId]);

  useEffect(() => {
    load();
  }, [load]);

  if (error) return <p role="alert">{error}</p>;
  if (!event) return <p>載入中…</p>;

  return (
    <div>
      <h1>事件 {event.event_id}</h1>
      <dl>
        <dt>Pipeline 狀態</dt>
        <dd>{event.pipeline_status}</dd>
        <dt>CFL 狀態</dt>
        <dd>{event.cfl_status}</dd>
        <dt>Version</dt>
        <dd>{event.version}</dd>
        <dt>Confidence</dt>
        <dd>{event.confidence ?? "—"}</dd>
      </dl>
      <section>
        <h2>Revision Chain</h2>
        <ol>
          {event.revision_chain.map((id) => (
            <li key={id}>{id}</li>
          ))}
        </ol>
      </section>
      <CflDecisionForm
        table="event"
        rowId={event.event_id}
        currentCflStatus={event.cfl_status}
        onDecided={load}
      />
    </div>
  );
}
