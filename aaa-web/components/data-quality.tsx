import type { ScanRun } from "@/lib/db/schema";
import { formatDateTime } from "@/lib/format";

export function DataQuality({ run }: { run: ScanRun }) {
  const errors = Array.from(new Set(run.errors ?? []));
  const notes = Array.from(new Set(run.notes ?? []));
  const hasIssues = errors.length > 0 || notes.length > 0;

  return (
    <section className="border border-line bg-panel p-5">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="font-display text-2xl tracking-tight text-paper">
          Calidad de datos
        </h2>
        <p className="font-mono text-[11px] text-muted">
          {formatDateTime(run.generatedAt)} ET
        </p>
      </div>

      <div className="mt-4 grid gap-4 md:grid-cols-3">
        {["swing", "invest", "day"].map((mode) => {
          const summary = (run.modes?.[mode] ?? {}) as Record<string, unknown>;
          return (
            <div key={mode} className="border-t border-line pt-3">
              <p className="font-mono text-[11px] text-copper">{mode}</p>
              <p className="mt-1 text-sm text-paper">
                {Number(summary.candidates ?? 0)} candidatos ·{" "}
                {Number(summary.actionable ?? 0)} accionables ·{" "}
                {Number(summary.watchlist ?? 0)} en vigilancia
              </p>
            </div>
          );
        })}
      </div>

      {hasIssues ? (
        <ul className="mt-5 space-y-1.5 text-sm">
          {errors.map((error) => (
            <li key={`error-${error}`} className="border-l-2 border-down pl-3 text-down">
              {error}
            </li>
          ))}
          {notes.map((note) => (
            <li key={`note-${note}`} className="border-l-2 border-warn pl-3 text-muted">
              {note}
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-5 text-sm text-muted">
          Sin incidencias registradas en esta ejecución.
        </p>
      )}

      <p className="mt-5 border-t border-line pt-3 text-xs leading-relaxed text-muted">
        Finviz y yfinance pueden llegar con retraso o incompletos. Un dato
        ausente se muestra como «—», nunca se rellena a mano. Este panel no es
        asesoría financiera ni una orden de compra.
      </p>
    </section>
  );
}
