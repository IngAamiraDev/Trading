import {
  formatCompactMoney,
  formatNumber,
  formatPercent,
  formatPoints,
  formatPrice,
  metricNumber,
  metricString,
  sectorStateLabel,
} from "@/lib/format";

type Metric = { label: string; value: string };

function boolText(value: unknown) {
  if (value === true) return "Sí";
  if (value === false) return "No";
  return null;
}

export function MetricGrid({
  mode,
  metrics,
}: {
  mode: string;
  metrics: Record<string, unknown>;
}) {
  const entries: Metric[] = [];

  const addNumber = (
    label: string,
    key: string,
    formatter: (value: number) => string = (value) =>
      formatNumber(value, 2),
  ) => {
    const value = metricNumber(metrics, key);
    if (value !== null) entries.push({ label, value: formatter(value) });
  };

  const addBool = (label: string, key: string) => {
    const text = boolText(metrics[key]);
    if (text !== null) entries.push({ label, value: text });
  };

  const addString = (
    label: string,
    key: string,
    formatter: (value: string) => string = (value) => value,
  ) => {
    const value = metricString(metrics, key);
    if (value) entries.push({ label, value: formatter(value) });
  };

  if (mode === "invest") {
    addNumber("ROE", "roe", (value) => formatPercent(value, 1));
    addNumber("Margen neto", "net_margin", (value) => formatPercent(value, 1));
    addNumber("EPS Q/Q", "eps_qoq", (value) => formatPercent(value, 1, true));
    addNumber("Ventas Q/Q", "sales_qoq", (value) => formatPercent(value, 1, true));
    addNumber("EPS Y/Y", "eps_yoy", (value) => formatPercent(value, 1, true));
    addNumber("Ventas Y/Y", "sales_yoy", (value) => formatPercent(value, 1, true));
    addNumber("Deuda/Equity", "debt_equity", (value) => formatNumber(value, 2));
    addNumber("PEG", "peg", (value) => formatNumber(value, 2));
    addNumber("P/FCF", "pfcf", (value) => formatNumber(value, 1));
    addNumber("EV/EBITDA", "ev_ebitda", (value) => formatNumber(value, 1));
    addNumber("RS 3m vs SPY", "rs63", (value) => formatPoints(value));
    addNumber("RS 1m vs sector", "rs_sector21", (value) => formatPoints(value));
    addNumber("RS 3m vs sector", "rs_sector63", (value) => formatPoints(value));
    addString("ETF del sector", "sector_etf");
    addString("Estado del sector", "sector_state", sectorStateLabel);
    addNumber("Dist. máximo 52s", "dist_high", (value) => formatPercent(value, 1));
    addNumber("Market cap", "market_cap", (value) => formatCompactMoney(value));
  } else if (mode === "day") {
    addNumber("Gap de apertura", "gap_pct", (value) => formatPercent(value, 2, true));
    addBool("Gap anómalo", "gap_anomaly");
    addNumber("Volumen relativo", "rel_vol", (value) => formatNumber(value, 2));
    addNumber("VWAP", "vwap", (value) => formatPrice(value));
    addNumber("Máximo premarket", "pre_high", (value) => formatPrice(value));
    addNumber("Mínimo premarket", "pre_low", (value) => formatPrice(value));
    addNumber("Máximo del día", "day_high", (value) => formatPrice(value));
    addNumber("Mínimo del día", "day_low", (value) => formatPrice(value));
    addNumber("ATR", "atr", (value) => formatPrice(value));
    addNumber("Cambio hoy", "change_today", (value) =>
      formatPercent(value, 2, true),
    );
    addString("ETF del sector", "sector_etf");
    addString("Estado del sector", "sector_state", sectorStateLabel);
    addNumber("RS sector 1m vs SPY", "sector_rs21", (value) => formatPoints(value));
    addNumber("RS 1m vs sector", "rs_sector21", (value) => formatPoints(value));
  } else {
    addNumber("RS 1m vs SPY", "rs21", (value) => formatPoints(value));
    addNumber("RS 3m vs SPY", "rs63", (value) => formatPoints(value));
    addString("ETF del sector", "sector_etf");
    addString("Estado del sector", "sector_state", sectorStateLabel);
    addNumber("RS sector 1m vs SPY", "sector_rs21", (value) => formatPoints(value));
    addNumber("RS 1m vs sector", "rs_sector21", (value) => formatPoints(value));
    addNumber("RS 3m vs sector", "rs_sector63", (value) => formatPoints(value));
    addNumber("Dist. máximo 52s", "dist_high", (value) => formatPercent(value, 1));
    addNumber("Volumen relativo", "rel_vol", (value) => formatNumber(value, 2));
    addNumber("ATR %", "atr_pct", (value) => formatPercent(value, 1));
    addNumber("RSI 14", "rsi", (value) => formatNumber(value, 1));
    addNumber("Pivote 20d", "pivot20", (value) => formatPrice(value));
    addNumber("Mínimo 10d", "low10", (value) => formatPrice(value));
    addNumber("Market cap", "market_cap", (value) => formatCompactMoney(value));
    addBool("Extendido", "extended");
  }

  if (entries.length === 0) {
    return (
      <p className="text-sm text-muted">
        Este run no incluye métricas adicionales para el modo.
      </p>
    );
  }

  return (
    <dl className="grid grid-cols-2 gap-px border border-line bg-line sm:grid-cols-3">
      {entries.map((entry) => (
        <div key={entry.label} className="bg-panel px-3 py-2.5">
          <dt className="text-[11px] leading-tight text-muted">{entry.label}</dt>
          <dd className="tabular mt-1 font-mono text-sm text-paper">
            {entry.value}
          </dd>
        </div>
      ))}
    </dl>
  );
}
