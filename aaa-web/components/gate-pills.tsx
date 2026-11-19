type GateValue = boolean | null | undefined;

const LABELS: Record<string, string> = {
  A1: "Mercado y sector",
  A2: "Acción vs SPY y sector",
  A3: "Entrada y riesgo",
};

export function GatePills({
  gates,
}: {
  gates: { A1?: GateValue; A2?: GateValue; A3?: GateValue };
}) {
  return (
    <span className="inline-flex items-center gap-1">
      {(["A1", "A2", "A3"] as const).map((gate) => {
        const value = gates[gate];
        const tone =
          value === true
            ? "border-copper bg-copper text-canvas"
            : value === false
              ? "border-down/50 bg-down/10 text-down"
              : "border-dashed border-line bg-transparent text-muted/60";
        const reading =
          value === true ? "pasa" : value === false ? "no pasa" : "sin dato";
        return (
          <span
            key={gate}
            title={`${gate} ${LABELS[gate]}: ${reading}`}
            aria-label={`${gate} ${LABELS[gate]}: ${reading}`}
            className={`inline-flex h-6 w-8 items-center justify-center border font-mono text-[10px] leading-none ${tone}`}
          >
            {gate}
          </span>
        );
      })}
    </span>
  );
}
