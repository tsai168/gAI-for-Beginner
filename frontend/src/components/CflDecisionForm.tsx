import { useState } from "react";
import type { FormEvent } from "react";
import { ApiClientError, decideCfl } from "../api/client";

const CFL_IDS = ["CFL-01", "CFL-02", "CFL-03", "CFL-04", "CFL-05", "CFL-06", "CFL-07", "CFL-08"];
// Human-settable outcomes only — AUTO-PASS/PENDING are G01-engine-only
// (Work-2 §5.2; src/governance/cfl.py's RuleBasedCflService).
const TARGETS = ["APPROVED", "REJECTED", "BLOCKED"];

interface Props {
  table: string;
  rowId: string;
  currentCflStatus: string;
  onDecided?: (cflStatus: string) => void;
}

/** POST /cfl/{cfl_id}/decision (U04 / G01) — shared by the Admin Review
 * console and each detail page's own review action. */
export function CflDecisionForm({ table, rowId, currentCflStatus, onDecided }: Props) {
  const [cflId, setCflId] = useState(CFL_IDS[0]);
  const [target, setTarget] = useState(TARGETS[0]);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setPending(true);
    try {
      const result = await decideCfl(cflId, { table, row_id: rowId, target });
      onDecided?.(result.cfl_status);
    } catch (err) {
      setError(err instanceof ApiClientError ? `${err.errorCode}：${err.message}` : "操作失敗");
    } finally {
      setPending(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} aria-label="cfl-decision-form">
      <p>目前 CFL 狀態：{currentCflStatus}</p>
      <label htmlFor={`cfl-id-${rowId}`}>CFL 規則</label>{" "}
      <select
        id={`cfl-id-${rowId}`}
        value={cflId}
        onChange={(event) => setCflId(event.target.value)}
      >
        {CFL_IDS.map((id) => (
          <option key={id} value={id}>
            {id}
          </option>
        ))}
      </select>{" "}
      <label htmlFor={`cfl-target-${rowId}`}>決定</label>{" "}
      <select
        id={`cfl-target-${rowId}`}
        value={target}
        onChange={(event) => setTarget(event.target.value)}
      >
        {TARGETS.map((t) => (
          <option key={t} value={t}>
            {t}
          </option>
        ))}
      </select>{" "}
      <button type="submit" disabled={pending}>
        送出
      </button>
      {error && <p role="alert">{error}</p>}
    </form>
  );
}
