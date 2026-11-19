import { formatPrice } from "@/lib/format";

type Level = {
  label: string;
  value: number | null;
  tone: "stop" | "entry" | "target";
};

export function PriceLadder({
  entry,
  stop,
  target,
  riskPct,
  rr,
}: {
  entry: number | null;
  stop: number | null;
  target: number | null;
  riskPct: number | null;
  rr: number | null;
}) {
  const levels: Level[] = [
    { label: "Objetivo", value: target, tone: "target" },
    { label: "Entrada", value: entry, tone: "entry" },
    { label: "Stop", value: stop, tone: "stop" },
  ];

  const values = levels
    .map((level) => level.value)
    .filter((value): value is number => value !== null);

  if (values.length < 2) {
    return (
      <p className="border border-dashed border-line px-4 py-8 text-sm text-muted">
        Sin niveles suficientes para dibujar la escalera.
      </p>
    );
  }

  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = Math.max(max - min, 0.01);
  const paddedMin = min - span * 0.14;
  const paddedMax = max + span * 0.14;
  const range = paddedMax - paddedMin;

  const position = (value: number) =>
    Math.max(2, Math.min(98, ((value - paddedMin) / range) * 100));

  const toneClass = {
    stop: "border-down bg-down text-down",
    entry: "border-copper bg-copper text-copper",
    target: "border-up bg-up text-up",
  };

  return (
    <div className="grid grid-cols-[1fr_auto] gap-6">
      <div>
        <div className="relative ml-2 h-64 border-l border-line">
          {levels.map((level) => {
            if (level.value === null) return null;
            const tone = toneClass[level.tone];
            return (
              <div
                key={level.label}
                className="absolute left-0 flex w-full items-center"
                style={{ bottom: `${position(level.value)}%` }}
              >
                <span
                  className={`-ml-[5px] h-2.5 w-2.5 rounded-full border ${tone}`}
                  aria-hidden="true"
                />
                <span className="ml-3 h-px flex-1 bg-line" aria-hidden="true" />
                <span className="tabular ml-3 font-mono text-sm text-paper">
                  {formatPrice(level.value)}
                </span>
                <span className="ml-3 w-16 text-right text-[11px] text-muted">
                  {level.label}
                </span>
              </div>
            );
          })}
        </div>
        <div className="mt-2 flex justify-between font-mono text-[10px] text-muted">
          <span>{formatPrice(paddedMin)}</span>
          <span>{formatPrice(paddedMax)}</span>
        </div>
      </div>

      <dl className="flex flex-col justify-between border-l border-line pl-5 text-sm">
        <div>
          <dt className="text-[11px] text-muted">R/R</dt>
          <dd className="tabular mt-0.5 font-mono text-2xl text-paper">
            {rr === null ? "—" : rr.toFixed(1)}
          </dd>
        </div>
        <div>
          <dt className="text-[11px] text-muted">Riesgo hasta stop</dt>
          <dd className="tabular mt-0.5 font-mono text-lg text-down">
            {riskPct === null ? "—" : `${riskPct.toFixed(2)}%`}
          </dd>
        </div>
        <div>
          <dt className="text-[11px] text-muted">Distancia al objetivo</dt>
          <dd className="tabular mt-0.5 font-mono text-lg text-up">
            {entry !== null && target !== null && entry > 0
              ? `${(((target - entry) / entry) * 100).toFixed(2)}%`
              : "—"}
          </dd>
        </div>
      </dl>
    </div>
  );
}
