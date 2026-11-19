import type { RegimeIndex } from "@/lib/db/schema";

export type MarketTrend = "alcista" | "lateral" | "bajista" | "sin datos";

/**
 * Dirección del mercado a partir de la estructura de los índices.
 * Usa `run.trend` cuando el run lo trae y, si no, lo deriva de los índices
 * guardados (runs antiguos). Misma regla que `Regime.trend` del motor.
 */
export function marketTrend(
  trend: string | null | undefined,
  indices: RegimeIndex[],
): MarketTrend {
  if (trend === "alcista" || trend === "lateral" || trend === "bajista") {
    return trend;
  }
  const valid = indices.filter((index) => !index.error);
  if (valid.length === 0) {
    return "sin datos";
  }
  const allAboveFast = valid.every((index) => index.aboveFast === true);
  const allAboveSlow = valid.every((index) => index.aboveSlow === true);
  if (allAboveFast && allAboveSlow) {
    return "alcista";
  }
  if (valid.every((index) => index.aboveSlow === false)) {
    return "bajista";
  }
  return "lateral";
}
