import { formatScore } from "@/lib/format";

export function ScoreBar({ value }: { value: number }) {
  const clamped = Math.max(0, Math.min(100, value));
  const tone =
    clamped >= 70 ? "bg-copper" : clamped >= 55 ? "bg-warn" : "bg-down";

  return (
    <span className="inline-flex items-center gap-2">
      <span className="tabular w-10 text-right font-mono text-sm text-paper">
        {formatScore(clamped)}
      </span>
      <span className="h-1.5 w-12 bg-line" aria-hidden="true">
        <span
          className={`block h-full ${tone}`}
          style={{ width: `${clamped}%` }}
        />
      </span>
    </span>
  );
}
