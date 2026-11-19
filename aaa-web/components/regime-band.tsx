import type { RegimeIndex, ScanRun } from "@/lib/db/schema";
import {
  formatNumber,
  formatPrice,
  regimeLabel,
  trendLabel,
  trendTone,
  REGIME_DESCRIPTIONS,
  TREND_DESCRIPTIONS,
} from "@/lib/format";
import { marketTrend } from "@/lib/market";

function AboveMark({ value }: { value: boolean | null }) {
  if (value === null) {
    return <span className="text-muted">—</span>;
  }
  return (
    <span className={value ? "text-up" : "text-down"}>{value ? "sí" : "no"}</span>
  );
}

export function RegimeBand({
  run,
  indices,
}: {
  run: ScanRun;
  indices: RegimeIndex[];
}) {
  const vix = run.vix;
  const trend = marketTrend(run.trend, indices);
  const vixWidth = vix === null ? 0 : Math.min(100, Math.max(0, (vix / 50) * 100));
  const vixHot = vix !== null && vix >= 25;

  return (
    <section className="reveal border border-line bg-panel">
      <div className="grid gap-px bg-line lg:grid-cols-[1.05fr_1.35fr_0.9fr]">
        <div className="bg-panel p-6 sm:p-7">
          <p className="font-mono text-[11px] tracking-[0.14em] text-muted">
            01 · Mercado
          </p>
          <div className="mt-4 flex flex-wrap items-baseline gap-x-4 gap-y-2">
            <h2
              className={`font-display text-6xl leading-none tracking-tight ${trendTone(trend)}`}
            >
              {trendLabel(trend)}
            </h2>
            <span className="font-mono text-xs text-muted">
              {formatNumber(run.vix, 2)} VIX
            </span>
          </div>
          <p className="mt-4 max-w-sm text-sm leading-relaxed text-muted">
            {TREND_DESCRIPTIONS[trend] ?? TREND_DESCRIPTIONS["sin datos"]}
          </p>

          <div className="mt-4 flex flex-wrap items-center gap-2 border-t border-line pt-3">
            <span
              className={`border px-2 py-0.5 font-mono text-[11px] ${
                run.regime === "risk_on"
                  ? "border-up/50 bg-up/10 text-up"
                  : run.regime === "risk_off"
                    ? "border-down/50 bg-down/10 text-down"
                    : "border-warn/50 bg-warn/10 text-warn"
              }`}
            >
              {regimeLabel(run.regime)}
            </span>
            <span className="text-xs leading-relaxed text-muted">
              {REGIME_DESCRIPTIONS[run.regime] ??
                "Lectura de contexto sin datos suficientes."}
            </span>
          </div>

          <div className="mt-6">
            <div className="flex items-center justify-between font-mono text-[11px] text-muted">
              <span>VIX</span>
              <span className={vixHot ? "text-down" : "text-up"}>
                límite 25
              </span>
            </div>
            <div className="relative mt-2 h-2 bg-line">
              <div
                className={`h-full ${vixHot ? "bg-down" : "bg-up"}`}
                style={{ width: `${vixWidth}%` }}
              />
              <span
                className="absolute -top-1 bottom-[-4px] w-px bg-paper/70"
                style={{ left: "50%" }}
                aria-hidden="true"
              />
            </div>
            <div className="mt-1 flex justify-between font-mono text-[10px] text-muted">
              <span>0</span>
              <span>25</span>
              <span>50</span>
            </div>
          </div>
        </div>

        <div className="bg-panel p-6 sm:p-7">
          <p className="font-mono text-[11px] tracking-[0.14em] text-muted">
            Índices de referencia
          </p>
          <table className="mt-4 w-full text-sm">
            <thead className="text-left text-xs text-muted">
              <tr className="border-b border-line">
                <th scope="col" className="pb-2 font-medium">Símbolo</th>
                <th scope="col" className="pb-2 text-right font-medium">Cierre</th>
                <th scope="col" className="pb-2 text-right font-medium">SMA50</th>
                <th scope="col" className="pb-2 text-right font-medium">SMA200</th>
                <th scope="col" className="pb-2 text-right font-medium">&gt; 50</th>
                <th scope="col" className="pb-2 text-right font-medium">&gt; 200</th>
              </tr>
            </thead>
            <tbody>
              {indices.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-4 text-sm text-muted">
                    Sin datos de índices en este run.
                  </td>
                </tr>
              ) : (
                indices.map((index) => (
                  <tr key={index.id} className="border-b border-line/60 last:border-b-0">
                    <td className="py-2.5 font-mono text-paper">{index.symbol}</td>
                    {index.error ? (
                      <td colSpan={5} className="py-2.5 text-right text-xs text-down">
                        {index.error}
                      </td>
                    ) : (
                      <>
                        <td className="tabular py-2.5 text-right font-mono text-paper">
                          {formatPrice(index.close)}
                        </td>
                        <td className="tabular py-2.5 text-right font-mono text-muted">
                          {formatPrice(index.smaFast)}
                        </td>
                        <td className="tabular py-2.5 text-right font-mono text-muted">
                          {formatPrice(index.smaSlow)}
                        </td>
                        <td className="py-2.5 text-right">
                          <AboveMark value={index.aboveFast} />
                        </td>
                        <td className="py-2.5 text-right">
                          <AboveMark value={index.aboveSlow} />
                        </td>
                      </>
                    )}
                  </tr>
                ))
              )}
            </tbody>
          </table>
          <p className="mt-4 text-xs leading-relaxed text-muted">
            Riesgo abierto: la lectura del régimen manda sobre cualquier gráfico
            individual.
          </p>
        </div>

        <div className="bg-panel p-6 sm:p-7">
          <p className="font-mono text-[11px] tracking-[0.14em] text-muted">
            02 · Sector · RS 1m vs SPY
          </p>
          {run.leaders.length === 0 ? (
            <p className="mt-4 text-sm text-muted">Sin ranking de sectores.</p>
          ) : (
            <ol className="mt-4 space-y-0">
              {run.leaders.map((leader, index) => (
                <li
                  key={leader}
                  className="flex items-baseline gap-3 border-b border-line/60 py-2.5 last:border-b-0"
                >
                  <span className="font-mono text-[11px] text-copper">
                    {String(index + 1).padStart(2, "0")}
                  </span>
                  <span className="text-sm text-paper">{leader}</span>
                </li>
              ))}
            </ol>
          )}
          <p className="mt-5 border-t border-line pt-3 text-xs leading-relaxed text-muted">
            Primero el mercado, después el sector y por último la acción contra
            su propio sector. Si un nivel falla, no hay setup.
          </p>
        </div>
      </div>
    </section>
  );
}
