import Link from "next/link";

import { CandidateTable, CandidateTableLegend } from "@/components/candidate-table";
import { DataUnavailable } from "@/components/data-unavailable";
import { EmptyState } from "@/components/empty-state";
import { SectionHeader } from "@/components/section-header";
import {
  getLatestRun,
  getRunBundle,
  isUuid,
  listCandidates,
} from "@/lib/db/queries";
import {
  formatDate,
  formatDateTime,
  isActionable,
  isWatch,
  modeLabel,
} from "@/lib/format";

export const dynamic = "force-dynamic";

type SearchParams = Record<string, string | string[] | undefined>;

function first(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] : value;
}

export default async function CandidatesPage({
  searchParams,
}: {
  searchParams: Promise<SearchParams>;
}) {
  try {
    const params = await searchParams;
    const requestedRun = first(params.run);
    const run = isUuid(requestedRun)
      ? (await getRunBundle(requestedRun))?.run ?? null
      : await getLatestRun();

    if (!run) {
      return (
        <EmptyState
          title="Sin runs publicados"
          description="Publica el primer plan con scripts/aaa_web_sync/sync.py para poder filtrar candidatos."
        />
      );
    }

    const bundle = await getRunBundle(run.id);
    if (!bundle) {
      return (
        <EmptyState
          title="Run sin candidatos"
          description="La ejecución no contiene filas. Revisa el resumen de errores en el plan."
        />
      );
    }

    const filters = {
      mode: first(params.mode),
      status: first(params.status),
      sector: first(params.sector),
      q: first(params.q),
      minScore: first(params.minScore)
        ? Number(first(params.minScore))
        : undefined,
      sort:
        (first(params.sort) as "score" | "risk" | "rr" | "ticker" | undefined) ??
        "score",
    };

    const rows = await listCandidates(run.id, filters);
    const sectors = Array.from(
      new Set(bundle.candidates.map((row) => row.sector).filter(Boolean)),
    ).sort((a, b) => a.localeCompare(b));
    const statuses = Array.from(
      new Set(bundle.candidates.map((row) => row.status)),
    ).sort((a, b) => a.localeCompare(b));

    const actionable = rows.filter((row) => isActionable(row.status)).length;
    const watch = rows.filter((row) => isWatch(row.status)).length;

    const exportParams = new URLSearchParams({ run: run.id });
    for (const [key, value] of Object.entries(filters)) {
      if (value !== undefined && value !== "") {
        exportParams.set(key, String(value));
      }
    }

    return (
      <div className="space-y-6">
        <header className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="font-mono text-[11px] tracking-[0.16em] text-copper">
              Universo evaluado
            </p>
            <h1 className="mt-2 font-display text-5xl leading-none tracking-tight text-paper">
              Candidatos
            </h1>
            <p className="mt-3 text-sm text-muted">
              Run de {formatDate(run.tradingDate)} ·{" "}
              {formatDateTime(run.generatedAt)} ET · {bundle.candidates.length}{" "}
              filas.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <a
              href={`/api/export/candidates?${exportParams.toString()}`}
              className="border border-line bg-panel px-3 py-2 text-sm text-paper transition-colors hover:border-copper hover:text-copper"
            >
              Exportar CSV
            </a>
            <Link
              href={`/api/export/watchlist?run=${run.id}`}
              className="border border-line bg-panel px-3 py-2 text-sm text-paper transition-colors hover:border-copper hover:text-copper"
            >
              Watchlist TradingView
            </Link>
          </div>
        </header>

        <form
          method="get"
          className="grid gap-3 border border-line bg-panel p-4 sm:grid-cols-2 lg:grid-cols-6"
        >
          <input type="hidden" name="run" value={run.id} />

          <label className="flex flex-col gap-1 text-xs text-muted lg:col-span-2">
            Buscar
            <input
              name="q"
              defaultValue={filters.q ?? ""}
              placeholder="Ticker o empresa"
              className="h-9 border border-line bg-canvas px-2.5 text-sm text-paper outline-none focus:border-copper"
            />
          </label>

          <label className="flex flex-col gap-1 text-xs text-muted">
            Modo
            <select
              name="mode"
              defaultValue={filters.mode ?? ""}
              className="h-9 border border-line bg-canvas px-2 text-sm text-paper outline-none focus:border-copper"
            >
              <option value="">Todos</option>
              <option value="swing">Swing</option>
              <option value="invest">Inversión</option>
              <option value="day">Day</option>
            </select>
          </label>

          <label className="flex flex-col gap-1 text-xs text-muted">
            Estado
            <select
              name="status"
              defaultValue={filters.status ?? ""}
              className="h-9 border border-line bg-canvas px-2 text-sm text-paper outline-none focus:border-copper"
            >
              <option value="">Todos</option>
              {statuses.map((status) => (
                <option key={status} value={status}>
                  {status}
                </option>
              ))}
            </select>
          </label>

          <label className="flex flex-col gap-1 text-xs text-muted">
            Sector
            <select
              name="sector"
              defaultValue={filters.sector ?? ""}
              className="h-9 border border-line bg-canvas px-2 text-sm text-paper outline-none focus:border-copper"
            >
              <option value="">Todos</option>
              {sectors.map((sector) => (
                <option key={sector} value={sector}>
                  {sector}
                </option>
              ))}
            </select>
          </label>

          <label className="flex flex-col gap-1 text-xs text-muted">
            Score mínimo
            <input
              name="minScore"
              type="number"
              min={0}
              max={100}
              step={1}
              defaultValue={filters.minScore ?? ""}
              className="h-9 border border-line bg-canvas px-2 font-mono text-sm text-paper outline-none focus:border-copper"
            />
          </label>

          <label className="flex flex-col gap-1 text-xs text-muted">
            Orden
            <select
              name="sort"
              defaultValue={filters.sort}
              className="h-9 border border-line bg-canvas px-2 text-sm text-paper outline-none focus:border-copper"
            >
              <option value="score">Score</option>
              <option value="rr">R/R</option>
              <option value="risk">Riesgo</option>
              <option value="ticker">Ticker</option>
            </select>
          </label>

          <div className="flex items-end gap-2 sm:col-span-2 lg:col-span-6">
            <button
              type="submit"
              className="h-9 border border-copper bg-copper px-4 text-sm font-medium text-canvas transition-colors hover:border-paper hover:bg-paper"
            >
              Aplicar filtros
            </button>
            <Link
              href={`/candidatos?run=${run.id}`}
              className="h-9 border border-line px-4 text-sm leading-8 text-muted transition-colors hover:border-copper hover:text-copper"
            >
              Limpiar
            </Link>
          </div>
        </form>

        <section>
          <SectionHeader
            title={`${rows.length} resultados`}
            description={`${actionable} accionables y ${watch} en vigilancia en este corte.`}
            meta={<span>Orden: {filters.sort}</span>}
          />
          <CandidateTable
            rows={rows}
            runId={run.id}
            emptyMessage="Ningún candidato coincide con estos filtros. Prueba a limpiar la búsqueda o bajar el score mínimo."
          />
          <CandidateTableLegend />
        </section>

        <p className="text-xs text-muted">
          Modos disponibles:{" "}
          {["swing", "invest", "day"].map((mode) => modeLabel(mode)).join(" · ")}.
        </p>
      </div>
    );
  } catch (error) {
    return <DataUnavailable error={error} />;
  }
}
