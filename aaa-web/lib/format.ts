export const MODE_LABELS: Record<string, string> = {
  swing: "Swing",
  invest: "Inversión",
  day: "Day",
};

export const REGIME_LABELS: Record<string, string> = {
  risk_on: "Risk-on",
  neutral: "Neutral",
  risk_off: "Risk-off",
};

export const TREND_LABELS: Record<string, string> = {
  alcista: "Alcista",
  lateral: "Lateral",
  bajista: "Bajista",
  "sin datos": "Sin datos",
};

export const TREND_DESCRIPTIONS: Record<string, string> = {
  alcista: "Los índices están por encima de sus medias de 50 y 200 sesiones.",
  lateral: "Estructura mixta: unos índices aguantan y otros han perdido soporte.",
  bajista: "Los índices han perdido sus medias largas; el mercado no acompaña.",
  "sin datos": "No hay índices suficientes para leer la dirección del mercado.",
};

export const SECTOR_STATE_LABELS: Record<string, string> = {
  fuerte: "Fuerte",
  lateral: "Lateral",
  débil: "Débil",
};

export const REGIME_DESCRIPTIONS: Record<string, string> = {
  risk_on: "Se permiten setups AAA con tamaño completo.",
  neutral: "Solo setups A+ y media posición.",
  risk_off: "No se abren nuevos largos; solo vigilancia.",
};

const ACTIONABLE = new Set(["AAA listo", "Core", "Listo"]);
const WATCH = new Set(["Vigilancia", "Watch"]);

export function isActionable(status: string) {
  return ACTIONABLE.has(status);
}

export function isWatch(status: string) {
  return WATCH.has(status);
}

export function isRejected(status: string) {
  return !isActionable(status) && !isWatch(status);
}

export function modeLabel(mode: string) {
  return MODE_LABELS[mode] ?? mode;
}

export function regimeLabel(regime: string) {
  return REGIME_LABELS[regime] ?? regime;
}

export function formatNumber(value: unknown, digits = 2) {
  const number = toNumber(value);
  if (number === null) return "—";
  return new Intl.NumberFormat("en-US", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(number);
}

export function formatPrice(value: unknown) {
  return formatNumber(value, 2);
}

export function formatScore(value: unknown) {
  return formatNumber(value, 1);
}

export function formatPercent(value: unknown, digits = 2, withSign = false) {
  const number = toNumber(value);
  if (number === null) return "—";
  const formatted = formatNumber(number, digits);
  if (withSign && number > 0) return `+${formatted}%`;
  return `${formatted}%`;
}

export function formatPoints(value: unknown, digits = 1, withSign = true) {
  const number = toNumber(value);
  if (number === null) return "—";
  const formatted = formatNumber(number, digits);
  if (withSign && number > 0) return `+${formatted} pp`;
  return `${formatted} pp`;
}

export function formatMoney(value: unknown, digits = 0) {
  const number = toNumber(value);
  if (number === null) return "—";
  return `$${new Intl.NumberFormat("en-US", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(number)}`;
}

export function formatCompactMoney(value: unknown) {
  const number = toNumber(value);
  if (number === null) return "—";
  const units = [
    { limit: 1e12, suffix: "T" },
    { limit: 1e9, suffix: "B" },
    { limit: 1e6, suffix: "M" },
    { limit: 1e3, suffix: "K" },
  ];
  for (const unit of units) {
    if (Math.abs(number) >= unit.limit) {
      return `$${formatNumber(number / unit.limit, 1)}${unit.suffix}`;
    }
  }
  return `$${formatNumber(number, 0)}`;
}

export function formatDate(value: Date | string | null | undefined) {
  if (!value) return "—";
  const dateOnly =
    typeof value === "string" && /^\d{4}-\d{2}-\d{2}([T ].*)?$/.test(value);
  const date = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat("es-ES", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    timeZone: dateOnly ? "UTC" : "America/New_York",
  }).format(date);
}

export function formatTime(value: Date | string | null | undefined) {
  if (!value) return "—";
  const date = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat("es-ES", {
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "America/New_York",
  }).format(date);
}

export function formatDateTime(value: Date | string | null | undefined) {
  if (!value) return "—";
  const date = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat("es-ES", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "America/New_York",
  }).format(date);
}

export function isStale(value: Date | string, hours = 36) {
  const date = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(date.getTime())) return true;
  return Date.now() - date.getTime() > hours * 60 * 60 * 1000;
}

export function toNumber(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string" && value.trim() !== "") {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}

export function statusTone(status: string) {
  if (isActionable(status)) {
    return "border-copper/60 bg-copper/10 text-copper";
  }
  if (isWatch(status)) {
    return "border-warn/50 bg-warn/10 text-warn";
  }
  return "border-down/40 bg-down/10 text-down";
}

export function regimeTone(regime: string) {
  if (regime === "risk_on") return "text-up";
  if (regime === "risk_off") return "text-down";
  return "text-warn";
}

export function trendLabel(trend: string | null | undefined) {
  return TREND_LABELS[trend ?? ""] ?? trend ?? "Sin datos";
}

export function trendTone(trend: string | null | undefined) {
  if (trend === "alcista") return "text-up";
  if (trend === "bajista") return "text-down";
  if (trend === "lateral") return "text-warn";
  return "text-muted";
}

export function sectorStateLabel(state: string | null | undefined) {
  return SECTOR_STATE_LABELS[state ?? ""] ?? state ?? "Sin dato";
}

export function numberTone(value: number | null | undefined) {
  if (value === null || value === undefined) return "text-muted";
  if (value > 0) return "text-up";
  if (value < 0) return "text-down";
  return "text-muted";
}

export function metricNumber(
  metrics: Record<string, unknown> | null | undefined,
  key: string,
) {
  return toNumber(metrics?.[key]);
}

export function metricString(
  metrics: Record<string, unknown> | null | undefined,
  key: string,
) {
  const value = metrics?.[key];
  return typeof value === "string" ? value : null;
}

export function blockValues(metrics: Record<string, unknown> | null | undefined) {
  const blocks = metrics?.["bloques"];
  if (!blocks || typeof blocks !== "object" || Array.isArray(blocks)) {
    return [] as Array<{ name: string; value: number }>;
  }
  return Object.entries(blocks as Record<string, unknown>)
    .map(([name, value]) => ({ name, value: toNumber(value) }))
    .filter((item): item is { name: string; value: number } => item.value !== null);
}
