import { blockValues, formatNumber } from "@/lib/format";

const MAX_BY_MODE: Record<string, Record<string, number>> = {
  swing: { alineación: 35, fortaleza: 40, entrada: 25 },
  day: { alineación: 25, fortaleza: 45, entrada: 30 },
  invest: { calidad: 40, crecimiento: 25, valoracion: 20, tendencia: 15 },
};

const ORDER_BY_MODE: Record<string, string[]> = {
  swing: ["alineación", "fortaleza", "entrada"],
  day: ["alineación", "fortaleza", "entrada"],
  invest: ["calidad", "crecimiento", "valoracion", "tendencia"],
};

export function ScoreBlocks({
  mode,
  metrics,
}: {
  mode: string;
  metrics: Record<string, unknown>;
}) {
  const blocks = blockValues(metrics);
  if (blocks.length === 0) {
    return (
      <p className="text-sm text-muted">
        Este run no incluye desglose de bloques.
      </p>
    );
  }

  const order = ORDER_BY_MODE[mode] ?? [];
  blocks.sort((a, b) => {
    const ia = order.indexOf(a.name);
    const ib = order.indexOf(b.name);
    return (ia === -1 ? 99 : ia) - (ib === -1 ? 99 : ib);
  });

  const maxima = MAX_BY_MODE[mode] ?? {};

  return (
    <div className="space-y-4">
      {blocks.map((block) => {
        const max = maxima[block.name] ?? 100;
        const pct = Math.max(0, Math.min(100, (block.value / max) * 100));
        return (
          <div key={block.name}>
            <div className="flex items-baseline justify-between text-xs">
              <span className="capitalize text-paper">{block.name}</span>
              <span className="tabular font-mono text-muted">
                {formatNumber(block.value, 1)} / {max}
              </span>
            </div>
            <div className="mt-1.5 h-1.5 bg-line" aria-hidden="true">
              <div className="h-full bg-copper" style={{ width: `${pct}%` }} />
            </div>
          </div>
        );
      })}
    </div>
  );
}
