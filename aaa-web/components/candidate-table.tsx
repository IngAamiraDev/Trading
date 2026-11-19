import Link from "next/link";

import type { CandidateRow } from "@/lib/db/schema";
import {
  formatNumber,
  formatPercent,
  formatPrice,
  modeLabel,
} from "@/lib/format";

import { GatePills } from "./gate-pills";
import { ModeTag } from "./mode-tag";
import { ScoreBar } from "./score-bar";
import { StatusBadge } from "./status-badge";

type CandidateTableProps = {
  rows: CandidateRow[];
  runId: string;
  variant?: "full" | "compact";
  emptyMessage?: string;
};

function DetailLink({
  row,
  runId,
  className,
  children,
}: {
  row: CandidateRow;
  runId: string;
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <Link
      href={`/candidatos/${encodeURIComponent(row.ticker)}?run=${runId}&mode=${row.mode}`}
      className={className}
    >
      {children}
    </Link>
  );
}

function MobileCards({
  rows,
  runId,
}: {
  rows: CandidateRow[];
  runId: string;
}) {
  return (
    <ul className="divide-y divide-line border border-line bg-panel md:hidden">
      {rows.map((row) => (
        <li key={`${row.runId}-${row.mode}-${row.ticker}`}>
          <DetailLink
            row={row}
            runId={runId}
            className="block px-4 py-3.5 transition-colors active:bg-raised/70"
          >
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <p className="font-mono text-base font-medium text-paper">
                  {row.ticker}
                  <span className="ml-2 align-middle">
                    <ModeTag mode={row.mode} />
                  </span>
                </p>
                <p className="mt-0.5 truncate text-xs text-muted">
                  {row.company || "—"}
                </p>
              </div>
              <StatusBadge status={row.status} />
            </div>

            <div className="mt-3 flex items-center justify-between gap-3">
              <ScoreBar value={row.score} />
              <GatePills gates={{ A1: row.a1, A2: row.a2, A3: row.a3 }} />
            </div>

            <dl className="mt-3 grid grid-cols-4 gap-px border border-line bg-line text-center">
              {[
                ["Entrada", formatPrice(row.entry), "text-paper"],
                ["Stop", formatPrice(row.stop), "text-down"],
                ["Objetivo", formatPrice(row.target), "text-up"],
                ["R/R", formatNumber(row.rr, 1), "text-paper"],
              ].map(([label, value, tone]) => (
                <div key={label} className="bg-canvas px-2 py-1.5">
                  <dt className="text-[10px] leading-tight text-muted">{label}</dt>
                  <dd className={`tabular mt-0.5 font-mono text-xs ${tone}`}>
                    {value}
                  </dd>
                </div>
              ))}
            </dl>
          </DetailLink>
        </li>
      ))}
    </ul>
  );
}

export function CandidateTable({
  rows,
  runId,
  variant = "full",
  emptyMessage = "Sin candidatos en este corte.",
}: CandidateTableProps) {
  if (rows.length === 0) {
    return (
      <p className="border border-dashed border-line px-4 py-8 text-sm text-muted">
        {emptyMessage}
      </p>
    );
  }

  const compact = variant === "compact";

  return (
    <>
      <MobileCards rows={rows} runId={runId} />

      <div className="hidden overflow-x-auto border border-line md:block">
        <table className="w-full min-w-[720px] text-left text-sm">
          <thead className="sticky top-0 z-10 bg-panel text-xs font-medium text-muted">
            <tr className="border-b border-line">
              <th scope="col" className="px-3 py-2.5">Ticker</th>
              <th scope="col" className="px-3 py-2.5">Modo</th>
              <th scope="col" className="px-3 py-2.5">Score</th>
              <th scope="col" className="px-3 py-2.5">Estado</th>
              {compact ? null : (
                <th scope="col" className="hidden px-3 py-2.5 2xl:table-cell">
                  Setup
                </th>
              )}
              <th scope="col" className="px-3 py-2.5 text-right">Entrada</th>
              <th scope="col" className="px-3 py-2.5 text-right">Stop</th>
              {compact ? null : (
                <th scope="col" className="px-3 py-2.5 text-right">Objetivo</th>
              )}
              <th scope="col" className="px-3 py-2.5 text-right">R/R</th>
              {compact ? null : (
                <th scope="col" className="hidden px-3 py-2.5 text-right 2xl:table-cell">
                  Riesgo
                </th>
              )}
              <th scope="col" className="px-3 py-2.5">Puertas</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr
                key={`${row.runId}-${row.mode}-${row.ticker}`}
                className="border-b border-line/70 transition-colors last:border-b-0 hover:bg-raised/60"
              >
                <td className="px-3 py-2.5">
                  <DetailLink
                    row={row}
                    runId={runId}
                    className="font-mono text-sm font-medium text-paper underline-offset-4 hover:text-copper hover:underline"
                  >
                    {row.ticker}
                  </DetailLink>
                  <span className="mt-0.5 block max-w-44 truncate text-xs text-muted">
                    {row.company || "—"}
                  </span>
                </td>
                <td className="whitespace-nowrap px-3 py-2.5">
                  <ModeTag mode={row.mode} />
                </td>
                <td className="px-3 py-2.5">
                  <ScoreBar value={row.score} />
                </td>
                <td className="px-3 py-2.5">
                  <StatusBadge status={row.status} />
                </td>
                {compact ? null : (
                  <td className="hidden px-3 py-2.5 text-muted 2xl:table-cell">
                    {row.setup || "—"}
                  </td>
                )}
                <td className="tabular whitespace-nowrap px-3 py-2.5 text-right font-mono text-paper">
                  {formatPrice(row.entry)}
                </td>
                <td className="tabular whitespace-nowrap px-3 py-2.5 text-right font-mono text-down">
                  {formatPrice(row.stop)}
                </td>
                {compact ? null : (
                  <td className="tabular whitespace-nowrap px-3 py-2.5 text-right font-mono text-up">
                    {formatPrice(row.target)}
                  </td>
                )}
                <td className="tabular whitespace-nowrap px-3 py-2.5 text-right font-mono text-paper">
                  {formatNumber(row.rr, 1)}
                </td>
                {compact ? null : (
                  <td className="tabular hidden whitespace-nowrap px-3 py-2.5 text-right font-mono text-muted 2xl:table-cell">
                    {formatPercent(row.riskPct, 1)}
                  </td>
                )}
                <td className="px-3 py-2.5">
                  <GatePills gates={{ A1: row.a1, A2: row.a2, A3: row.a3 }} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}

export function CandidateTableLegend() {
  return (
    <p className="mt-2 text-xs text-muted">
      Puertas: A1 mercado y sector alineados, A2 la acción lidera a SPY y a su
      propio sector, A3 entrada y riesgo. Cobre = pasa, rojo = no pasa,
      discontinuo = sin dato. Modos:{" "}
      {["swing", "invest", "day"].map((mode) => modeLabel(mode)).join(", ")}.
    </p>
  );
}
