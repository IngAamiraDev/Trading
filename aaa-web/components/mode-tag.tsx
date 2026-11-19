import { modeLabel } from "@/lib/format";

const TONES: Record<string, string> = {
  swing: "text-copper",
  invest: "text-up",
  day: "text-warn",
};

export function ModeTag({ mode }: { mode: string }) {
  return (
    <span
      className={`font-mono text-[11px] tracking-wide ${TONES[mode] ?? "text-muted"}`}
    >
      {modeLabel(mode)}
    </span>
  );
}
