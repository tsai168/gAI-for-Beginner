import { useEffect, useState } from "react";
import { ApiClientError, type CompanyOut, listCompanies } from "../api/client";
import { DisclaimerBanner } from "../components/DisclaimerBanner";

/** U01 — Research Dashboard (Work-1 §3.9). GET /dashboard/seco-cmi (R03)
 * always 501s right now (WBS-B11 not built) — deliberately not called
 * here to avoid a network round trip to a known stub; the Universe
 * overview below uses the real GET /companies instead. */
export function Dashboard() {
  const [companies, setCompanies] = useState<CompanyOut[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listCompanies()
      .then(setCompanies)
      .catch((err: unknown) => {
        setError(err instanceof ApiClientError ? err.message : "載入失敗");
      });
  }, []);

  const universeCounts = (companies ?? []).reduce<Record<string, number>>((acc, c) => {
    acc[c.universe] = (acc[c.universe] ?? 0) + 1;
    return acc;
  }, {});

  return (
    <div>
      <h1>研究儀表板</h1>
      <DisclaimerBanner />
      {error && <p role="alert">{error}</p>}
      {companies === null && !error && <p>載入中…</p>}
      {companies !== null && (
        <section>
          <h2>公司 Universe 總覽</h2>
          <ul>
            {Object.entries(universeCounts).map(([universe, count]) => (
              <li key={universe}>
                {universe}：{count}
              </li>
            ))}
          </ul>
        </section>
      )}
      <section>
        <h2>Seco／CMI 儀表板</h2>
        <p>R03（Seco／CMI 聚合報表）尚未建置（WBS-B11）。</p>
      </section>
    </div>
  );
}
