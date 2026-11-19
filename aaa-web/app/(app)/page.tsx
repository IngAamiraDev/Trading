import Link from "next/link";

import { CandidateTable, CandidateTableLegend } from "@/components/candidate-table";
import { DataQuality } from "@/components/data-quality";
import { DataUnavailable } from "@/components/data-unavailable";
import { EmptyState } from "@/components/empty-state";
import { RegimeBand } from "@/components/regime-band";
import { RiskStrip } from "@/components/risk-strip";
import { SectionHeader } from "@/components/section-header";
import { getLatestRun, getRunBundle } from "@/lib/db/queries";
import {
  formatDate,
  formatDateTime,
  isActionable,
  isRejected,
  isStale,
  isWatch,
} from "@/lib/format";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  try {
    const latest = await getLatestRun();
    if (!latest) {
      return (
        <EmptyState
          title="Todavía no hay ningún plan"
          description="Ejecuta el motor AAA y publica el resultado con scripts/aaa_web_sync/sync.py. En cuanto llegue el primer run, esta pantalla mostrará el régimen y los candidatos."
        >
          <code className="block max-w-2xl overflow-x-auto border border-line bg-panel px-4 py-3 font-mono text-xs text-copper">
            /tmp/opencode/trading-venv/bin/python strategies/aaa/main.py plan
            --capital 10000
          </code>
        </EmptyState>
      );
    }

    const bundle = await getRunBundle(latest.id);
    if (!bundle) {
      return (
        <EmptyState
          title="El run no tiene datos"
          description="La ejecución existe pero no se encontraron candidatos ni índices asociados."
        />
      );
    }

    const { run, indices, candidates } = bundle;
    const actionable = candidates.filter((row) => isActionable(row.status));
    const watch = candidates.filter((row) => isWatch(row.status));
    const rejected = candidates
      .filter((row) => isRejected(row.status))
      .slice(0, 8);
    const stale = isStale(run.generatedAt);

    return (
      <div className="space-y-8">
        <header className="reveal flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="font-mono text-[11px] tracking-[0.16em] text-copper">
              Plan de sesión
            </p>
            <h1 className="mt-2 font-display text-5xl leading-none tracking-tight text-paper sm:text-6xl">
              Hoy · {formatDate(run.tradingDate)}
            </h1>
            <p className="mt-3 text-sm text-muted">
              Última ejecución {formatDateTime(run.generatedAt)} ET ·{" "}
              {candidates.length} candidatos en {Object.keys(run.modes ?? {}).length}{" "}
              modos.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Link
              href="/candidatos"
              className="border border-line bg-panel px-3 py-2 text-sm text-paper transition-colors hover:border-copper hover:text-copper"
            >
              Ver candidatos
            </Link>
            <a
              href={`/api/export/watchlist?run=${run.id}`}
              className="border border-line bg-panel px-3 py-2 text-sm text-paper transition-colors hover:border-copper hover:text-copper"
            >
              Watchlist TradingView
            </a>
          </div>
        </header>

        {stale ? (
          <p className="border-l-2 border-warn bg-warn/10 px-4 py-3 text-sm text-warn">
            Este run tiene más de 36 horas. Antes de operar, ejecuta el plan de
            la sesión actual.
          </p>
        ) : null}

        <RegimeBand run={run} indices={indices} />
        <RiskStrip run={run} rows={candidates} />

        <section className="reveal reveal-late">
          <SectionHeader
            title="Accionables"
            description="Cumplen las tres puertas y el umbral de score del modo. Solo señales: la ejecución es humana."
            meta={<span>{actionable.length} de {candidates.length}</span>}
          />
          {actionable.length === 0 ? (
            <div className="border border-line bg-panel px-5 py-6">
              <p className="text-sm text-paper">
                Ninguno cumple las tres puertas en este run.
              </p>
              <p className="mt-1 text-sm text-muted">
                {rejected.length > 0
                  ? "Los descartados quedan abajo con su motivo. No se fuerza una entrada."
                  : "El escaneo no devolvió candidatos."}
              </p>
            </div>
          ) : (
            <CandidateTable rows={actionable} runId={run.id} variant="compact" />
          )}
          <CandidateTableLegend />
        </section>

        <section className="reveal reveal-later">
          <SectionHeader
            title="Vigilancia"
            description="Puertas incompletas o score por debajo del umbral. Se observan, no se compran."
            meta={<span>{watch.length} candidatos</span>}
          />
          <CandidateTable
            rows={watch}
            runId={run.id}
            variant="compact"
            emptyMessage="Sin candidatos en vigilancia."
          />
        </section>

        <section>
          <SectionHeader
            title="Descartados relevantes"
            description="Los de mayor score entre los que fallan alguna puerta dura. Sirven para entender el embudo, no para operar."
            meta={<span>top {rejected.length}</span>}
          />
          <CandidateTable
            rows={rejected}
            runId={run.id}
            variant="compact"
            emptyMessage="Sin descartes que mostrar."
          />
        </section>

        <DataQuality run={run} />
      </div>
    );
  } catch (error) {
    return <DataUnavailable error={error} />;
  }
}
