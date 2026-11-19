import type { CandidateRow, ScanRun } from "@/lib/db/schema";
import { formatMoney, isActionable, isWatch } from "@/lib/format";

export function RiskStrip({
  run,
  rows,
}: {
  run: ScanRun;
  rows: CandidateRow[];
}) {
  const actionable = rows.filter((row) => isActionable(row.status)).length;
  const watch = rows.filter((row) => isWatch(row.status)).length;
  const selected = rows.filter((row) => row.selected).length;

  const stats = [
    { label: "Capital de referencia", value: formatMoney(run.capital) },
    { label: "Riesgo por operación", value: "0.5%" },
    { label: "Riesgo abierto máximo", value: "2.0%" },
    { label: "Accionables", value: String(actionable) },
    { label: "En vigilancia", value: String(watch) },
    { label: "Seleccionadas", value: String(selected) },
  ];

  return (
    <section className="reveal reveal-late grid grid-cols-2 gap-px border border-line bg-line sm:grid-cols-3 lg:grid-cols-6">
      {stats.map((stat) => (
        <div key={stat.label} className="bg-panel px-4 py-4">
          <p className="text-[11px] leading-tight text-muted">{stat.label}</p>
          <p className="tabular mt-1.5 font-mono text-xl text-paper">
            {stat.value}
          </p>
        </div>
      ))}
    </section>
  );
}
