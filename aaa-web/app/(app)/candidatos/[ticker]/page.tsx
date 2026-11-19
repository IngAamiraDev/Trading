import Link from "next/link";

import { DataUnavailable } from "@/components/data-unavailable";
import { EmptyState } from "@/components/empty-state";
import { GatePills } from "@/components/gate-pills";
import { MetricGrid } from "@/components/metric-grid";
import { ModeTag } from "@/components/mode-tag";
import { PriceLadder } from "@/components/price-ladder";
import { ScoreBlocks } from "@/components/score-blocks";
import { StatusBadge } from "@/components/status-badge";
import {
  getLatestRun,
  getRegimeIndices,
  getRun,
  getTickerCandidates,
  getTickerHistory,
  isUuid,
} from "@/lib/db/queries";
import {
  formatDate,
  formatTime,
  formatNumber,
  formatPercent,
  formatPoints,
  formatPrice,
  isActionable,
  metricNumber,
  metricString,
  modeLabel,
  numberTone,
  regimeLabel,
  sectorStateLabel,
  trendLabel,
  trendTone,
} from "@/lib/format";
import { marketTrend } from "@/lib/market";

export const dynamic = "force-dynamic";

type PageProps = {
  params: Promise<{ ticker: string }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
};

function first(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] : value;
}

export default async function CandidateDetailPage({
  params,
  searchParams,
}: PageProps) {
  try {
    const { ticker: rawTicker } = await params;
    const query = await searchParams;
    const ticker = decodeURIComponent(rawTicker).toUpperCase();

    const requestedRun = first(query.run);
    const run = isUuid(requestedRun)
      ? await getRun(requestedRun)
      : await getLatestRun();

    if (!run) {
      return (
        <EmptyState
          title="Sin runs publicados"
          description="Publica un plan para poder abrir el detalle de un candidato."
        />
      );
    }

    const rows = await getTickerCandidates(run.id, ticker);
    if (rows.length === 0) {
      return (
        <EmptyState
          title={`${ticker} no está en este run`}
          description="Puede que el ticker no pasara los filtros de Finviz o que el run sea de otra fecha. Vuelve a la lista para ver el universo evaluado."
        >
          <Link
            href={`/candidatos?run=${run.id}`}
            className="inline-block border border-line bg-panel px-4 py-2 text-sm text-paper transition-colors hover:border-copper hover:text-copper"
          >
            Volver a candidatos
          </Link>
        </EmptyState>
      );
    }

    const requestedMode = first(query.mode);
    const candidate =
      rows.find((row) => row.mode === requestedMode) ??
      rows.find((row) => row.mode === "swing") ??
      rows[0];

    const history = await getTickerHistory(ticker, 10);
    const indices = await getRegimeIndices(run.id);
    const reasons = candidate.reasons ?? [];
    const failures = reasons.filter((reason) => /^A[123]:/.test(reason));
    const otherReasons = reasons.filter((reason) => !/^A[123]:/.test(reason));
    const metrics = candidate.metrics ?? {};

    const trend = marketTrend(run.trend, indices);
    const sectorEtf = metricString(metrics, "sector_etf");
    const sectorState = metricString(metrics, "sector_state");
    const sectorRs21 = metricNumber(metrics, "sector_rs21");
    const rsSector21 = metricNumber(metrics, "rs_sector21");
    const rsSector63 = metricNumber(metrics, "rs_sector63");
    const rsSpy21 = metricNumber(metrics, "rs21");
    const rsSpy63 = metricNumber(metrics, "rs63");
    const extremeMove = metrics.extreme_move === true;

    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between gap-3">
          <Link
            href={`/candidatos?run=${run.id}`}
            className="text-sm text-muted underline-offset-4 transition-colors hover:text-paper hover:underline"
          >
            ← Candidatos
          </Link>
          <p className="font-mono text-[11px] text-muted">
            Run de {formatDate(run.tradingDate)} · {formatTime(run.generatedAt)}{" "}
            ET
          </p>
        </div>

        <header className="flex flex-wrap items-end justify-between gap-5 border-b border-line pb-5">
          <div>
            <div className="flex flex-wrap items-center gap-3">
              <ModeTag mode={candidate.mode} />
              <StatusBadge status={candidate.status} />
              {candidate.selected ? (
                <span className="border border-copper/50 bg-copper/10 px-2 py-0.5 font-mono text-[11px] text-copper">
                  Seleccionada por riesgo
                </span>
              ) : null}
            </div>
            <h1 className="mt-2 font-display text-6xl leading-none tracking-tight text-paper">
              {candidate.ticker}
            </h1>
            <p className="mt-2 max-w-2xl text-sm text-muted">
              {candidate.company || "Empresa sin nombre"} ·{" "}
              {candidate.sector || "sector sin dato"} ·{" "}
              {candidate.industry || "industria sin dato"}
            </p>
          </div>
          <div className="text-right">
            <p className="text-[11px] text-muted">Score del modo</p>
            <p className="tabular font-mono text-5xl leading-none text-copper">
              {formatNumber(candidate.score, 1)}
            </p>
          </div>
        </header>

        {rows.length > 1 ? (
          <nav aria-label="Modos" className="flex flex-wrap gap-1">
            {rows.map((row) => (
              <Link
                key={row.mode}
                href={`/candidatos/${encodeURIComponent(ticker)}?run=${run.id}&mode=${row.mode}`}
                aria-current={row.mode === candidate.mode ? "page" : undefined}
                className={`border px-3 py-1.5 text-sm transition-colors ${
                  row.mode === candidate.mode
                    ? "border-copper bg-copper/10 text-copper"
                    : "border-line text-muted hover:border-paper hover:text-paper"
                }`}
              >
                {modeLabel(row.mode)}
              </Link>
            ))}
          </nav>
        ) : null}

        <section className="reveal border border-line bg-panel">
          <div className="grid gap-px bg-line md:grid-cols-3">
            <div className="bg-panel p-5">
              <p className="font-mono text-[11px] tracking-[0.14em] text-muted">
                01 · Mercado
              </p>
              <p
                className={`mt-3 font-display text-3xl leading-none tracking-tight ${trendTone(trend)}`}
              >
                {trendLabel(trend)}
              </p>
              <p className="mt-3 text-xs leading-relaxed text-muted">
                {regimeLabel(run.regime)} · VIX {formatNumber(run.vix, 2)}
              </p>
            </div>

            <div className="bg-panel p-5">
              <p className="font-mono text-[11px] tracking-[0.14em] text-muted">
                02 · Sector
              </p>
              <p
                className={`mt-3 font-display text-3xl leading-none tracking-tight ${
                  sectorState === "fuerte"
                    ? "text-up"
                    : sectorState === "débil"
                      ? "text-down"
                      : sectorState === "lateral"
                        ? "text-warn"
                        : "text-muted"
                }`}
              >
                {sectorStateLabel(sectorState)}
              </p>
              <p className="mt-3 text-xs leading-relaxed text-muted">
                {sectorEtf ? `${sectorEtf} · ` : ""}
                RS 1m {formatPoints(sectorRs21)} vs SPY
              </p>
            </div>

            <div className="bg-panel p-5">
              <p className="font-mono text-[11px] tracking-[0.14em] text-muted">
                03 · Acción vs sector
              </p>
              <p
                className={`mt-3 font-display text-3xl leading-none tracking-tight ${numberTone(rsSector21)}`}
              >
                {rsSector21 === null ? "—" : formatPoints(rsSector21)}
              </p>
              <p className="mt-3 text-xs leading-relaxed text-muted">
                1m contra {sectorEtf ?? "el sector"} · 3m:{" "}
                {formatPoints(rsSector63)}
                <br />
                Contra SPY: {formatPoints(rsSpy21)} 1m ·{" "}
                {formatPoints(rsSpy63)} 3m
              </p>
            </div>
          </div>
          <p className="border-t border-line px-5 py-3 text-xs leading-relaxed text-muted">
            {candidate.mode === "swing"
              ? "Primero el mercado, después el sector y por último la acción contra su propio sector. Si la acción no lidera a su sector, A2 no pasa."
              : candidate.mode === "invest"
                ? "Lectura de contexto: mercado y sector. En inversión, A2 es la puerta de calidad (ROE, márgenes, crecimiento y deuda)."
                : "Lectura de contexto: mercado y sector. En intradía, A2 es gap, volumen relativo y setup sobre el VWAP."}
          </p>
          {extremeMove ? (
            <p className="border-t border-down/40 bg-down/10 px-5 py-3 text-xs leading-relaxed text-down">
              La serie diaria tiene un salto extremo (split o dato corrupto): la
              fuerza relativa no es comparable y se muestra como ausente.
            </p>
          ) : null}
        </section>

        <div className="grid gap-6 lg:grid-cols-[1.35fr_0.65fr]">
          <div className="space-y-6">
            <section className="border border-line bg-panel p-5 sm:p-6">
              <div className="flex flex-wrap items-end justify-between gap-3">
                <div>
                  <h2 className="font-display text-3xl tracking-tight text-paper">
                    Niveles de la operación
                  </h2>
                  <p className="mt-1 text-sm text-muted">
                    Setup: {candidate.setup || "sin setup identificable"}
                  </p>
                </div>
                <GatePills
                  gates={{ A1: candidate.a1, A2: candidate.a2, A3: candidate.a3 }}
                />
              </div>
              <div className="mt-6">
                <PriceLadder
                  entry={candidate.entry}
                  stop={candidate.stop}
                  target={candidate.target}
                  riskPct={candidate.riskPct}
                  rr={candidate.rr}
                />
              </div>
              <dl className="mt-6 grid grid-cols-2 gap-px border border-line bg-line sm:grid-cols-4">
                <div className="bg-panel px-3 py-2.5">
                  <dt className="text-[11px] text-muted">Precio actual</dt>
                  <dd className="tabular mt-1 font-mono text-sm text-paper">
                    {formatPrice(candidate.price)}
                  </dd>
                </div>
                <div className="bg-panel px-3 py-2.5">
                  <dt className="text-[11px] text-muted">Entrada</dt>
                  <dd className="tabular mt-1 font-mono text-sm text-paper">
                    {formatPrice(candidate.entry)}
                  </dd>
                </div>
                <div className="bg-panel px-3 py-2.5">
                  <dt className="text-[11px] text-muted">Stop</dt>
                  <dd className="tabular mt-1 font-mono text-sm text-down">
                    {formatPrice(candidate.stop)}
                  </dd>
                </div>
                <div className="bg-panel px-3 py-2.5">
                  <dt className="text-[11px] text-muted">Objetivo</dt>
                  <dd className="tabular mt-1 font-mono text-sm text-up">
                    {formatPrice(candidate.target)}
                  </dd>
                </div>
                <div className="bg-panel px-3 py-2.5">
                  <dt className="text-[11px] text-muted">Riesgo %</dt>
                  <dd className="tabular mt-1 font-mono text-sm text-paper">
                    {formatPercent(candidate.riskPct, 2)}
                  </dd>
                </div>
                <div className="bg-panel px-3 py-2.5">
                  <dt className="text-[11px] text-muted">R/R</dt>
                  <dd className="tabular mt-1 font-mono text-sm text-paper">
                    {formatNumber(candidate.rr, 1)}
                  </dd>
                </div>
                <div className="bg-panel px-3 py-2.5">
                  <dt className="text-[11px] text-muted">Acciones</dt>
                  <dd className="tabular mt-1 font-mono text-sm text-paper">
                    {candidate.shares ?? "—"}
                  </dd>
                </div>
                <div className="bg-panel px-3 py-2.5">
                  <dt className="text-[11px] text-muted">Earnings</dt>
                  <dd className="mt-1 font-mono text-sm text-paper">
                    {candidate.earnings ? formatDate(candidate.earnings) : "—"}
                  </dd>
                </div>
              </dl>
            </section>

            <section className="border border-line bg-panel p-5 sm:p-6">
              <h2 className="font-display text-3xl tracking-tight text-paper">
                Tesis y motivos
              </h2>
              <p className="mt-1 text-sm text-muted">
                Lo que el motor vio, en el orden en que lo vio. No se añade
                contexto externo.
              </p>
              {reasons.length === 0 ? (
                <p className="mt-4 text-sm text-muted">Sin motivos registrados.</p>
              ) : (
                <ul className="mt-4 space-y-2 text-sm leading-relaxed">
                  {failures.map((reason) => (
                    <li
                      key={reason}
                      className="border-l-2 border-down pl-3 text-down"
                    >
                      {reason}
                    </li>
                  ))}
                  {otherReasons.map((reason) => (
                    <li
                      key={reason}
                      className="border-l-2 border-line pl-3 text-muted"
                    >
                      {reason}
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </div>

          <div className="space-y-6">
            <section className="border border-line bg-panel p-5">
              <h2 className="font-display text-2xl tracking-tight text-paper">
                Score por bloques
              </h2>
              <p className="mt-1 text-xs leading-relaxed text-muted">
                El score ordena, no compensa una puerta fallida.
              </p>
              <div className="mt-5">
                <ScoreBlocks mode={candidate.mode} metrics={metrics} />
              </div>
            </section>

            <section className="border border-line bg-panel p-5">
              <h2 className="font-display text-2xl tracking-tight text-paper">
                Puertas duras
              </h2>
              <ul className="mt-4 space-y-3 text-sm">
                {(
                  [
                    ["A1", "Mercado y sector", candidate.a1],
                    ["A2", "Acción vs SPY y sector", candidate.a2],
                    ["A3", "Entrada y riesgo", candidate.a3],
                  ] as const
                ).map(([gate, label, value]) => (
                  <li key={gate} className="flex items-center justify-between gap-3">
                    <span className="text-muted">
                      <span className="font-mono text-[11px] text-copper">
                        {gate}
                      </span>{" "}
                      {label}
                    </span>
                    <span
                      className={
                        value === true
                          ? "font-mono text-xs text-up"
                          : value === false
                            ? "font-mono text-xs text-down"
                            : "font-mono text-xs text-muted"
                      }
                    >
                      {value === true ? "pasa" : value === false ? "no pasa" : "sin dato"}
                    </span>
                  </li>
                ))}
              </ul>
            </section>

            <section className="border border-line bg-panel p-5">
              <h2 className="font-display text-2xl tracking-tight text-paper">
                Métricas del modo
              </h2>
              <div className="mt-4">
                <MetricGrid mode={candidate.mode} metrics={metrics} />
              </div>
            </section>

            <section className="border border-line bg-panel p-5">
              <h2 className="font-display text-2xl tracking-tight text-paper">
                Trazabilidad
              </h2>
              <dl className="mt-4 space-y-2 text-sm">
                <div className="flex justify-between gap-3">
                  <dt className="text-muted">Última barra</dt>
                  <dd className="text-right font-mono text-xs text-paper">
                    {candidate.lastBar ? formatDate(candidate.lastBar) : "—"}
                  </dd>
                </div>
                <div className="flex justify-between gap-3">
                  <dt className="text-muted">Fuente</dt>
                  <dd className="text-right font-mono text-xs text-paper">
                    {candidate.source || "—"}
                  </dd>
                </div>
                <div className="flex justify-between gap-3">
                  <dt className="text-muted">Estado</dt>
                  <dd className="text-right text-xs text-paper">
                    {isActionable(candidate.status)
                      ? "Accionable"
                      : "No accionable"}
                  </dd>
                </div>
              </dl>
            </section>
          </div>
        </div>

        <section className="border border-line bg-panel p-5">
          <h2 className="font-display text-3xl tracking-tight text-paper">
            Historial del ticker
          </h2>
          <p className="mt-1 text-sm text-muted">
            Últimas apariciones en runs publicados. Sirve para ver si el setup
            mejora o se deteriora.
          </p>
          <div className="mt-4 overflow-x-auto">
            <table className="w-full min-w-[640px] text-left text-sm">
              <thead className="text-xs text-muted">
                <tr className="border-b border-line">
                  <th scope="col" className="py-2 font-medium">Run</th>
                  <th scope="col" className="py-2 font-medium">Modo</th>
                  <th scope="col" className="py-2 font-medium">Estado</th>
                  <th scope="col" className="py-2 text-right font-medium">Score</th>
                  <th scope="col" className="py-2 text-right font-medium">Entrada</th>
                  <th scope="col" className="py-2 text-right font-medium">Stop</th>
                  <th scope="col" className="py-2 text-right font-medium">R/R</th>
                </tr>
              </thead>
              <tbody>
                {history.map((row) => (
                  <tr key={`${row.runId}-${row.mode}`} className="border-b border-line/60 last:border-b-0">
                    <td className="py-2 font-mono text-xs text-muted">
                      <Link
                        href={`/candidatos/${encodeURIComponent(ticker)}?run=${row.runId}&mode=${row.mode}`}
                        className="underline-offset-4 hover:text-copper hover:underline"
                      >
                        {formatDate(row.tradingDate)}
                      </Link>
                    </td>
                    <td className="py-2">
                      <ModeTag mode={row.mode} />
                    </td>
                    <td className="py-2">
                      <StatusBadge status={row.status} />
                    </td>
                    <td className="tabular py-2 text-right font-mono text-paper">
                      {formatNumber(row.score, 1)}
                    </td>
                    <td className="tabular py-2 text-right font-mono text-muted">
                      {formatPrice(row.entry)}
                    </td>
                    <td className="tabular py-2 text-right font-mono text-muted">
                      {formatPrice(row.stop)}
                    </td>
                    <td className="tabular py-2 text-right font-mono text-muted">
                      {formatNumber(row.rr, 1)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    );
  } catch (error) {
    return <DataUnavailable error={error} />;
  }
}
