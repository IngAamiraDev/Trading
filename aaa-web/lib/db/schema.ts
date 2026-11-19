import {
  boolean,
  date,
  doublePrecision,
  index,
  integer,
  jsonb,
  pgTable,
  text,
  timestamp,
  uniqueIndex,
  uuid,
} from "drizzle-orm/pg-core";

export const scanRuns = pgTable(
  "scan_runs",
  {
    id: uuid("id").primaryKey(),
    generatedAt: timestamp("generated_at", { withTimezone: true }).notNull(),
    tradingDate: date("trading_date").notNull(),
    regime: text("regime").notNull(),
    trend: text("trend"),
    vix: doublePrecision("vix"),
    capital: doublePrecision("capital"),
    source: text("source").notNull().default("cli"),
    leaders: jsonb("leaders").$type<string[]>().notNull().default([]),
    errors: jsonb("errors").$type<string[]>().notNull().default([]),
    notes: jsonb("notes").$type<string[]>().notNull().default([]),
    modes: jsonb("modes").$type<Record<string, unknown>>().notNull().default({}),
    createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
  },
  (table) => [index("scan_runs_generated_at_idx").on(table.generatedAt)],
);

export const regimeIndices = pgTable(
  "regime_indices",
  {
    id: uuid("id").primaryKey().defaultRandom(),
    runId: uuid("run_id")
      .notNull()
      .references(() => scanRuns.id, { onDelete: "cascade" }),
    symbol: text("symbol").notNull(),
    close: doublePrecision("close"),
    smaFast: doublePrecision("sma_fast"),
    smaSlow: doublePrecision("sma_slow"),
    aboveFast: boolean("above_fast"),
    aboveSlow: boolean("above_slow"),
    lastBar: text("last_bar"),
    error: text("error"),
  },
  (table) => [
    uniqueIndex("regime_indices_run_symbol_idx").on(table.runId, table.symbol),
  ],
);

export const candidates = pgTable(
  "candidates",
  {
    id: uuid("id").primaryKey().defaultRandom(),
    runId: uuid("run_id")
      .notNull()
      .references(() => scanRuns.id, { onDelete: "cascade" }),
    mode: text("mode").notNull(),
    ticker: text("ticker").notNull(),
    company: text("company").notNull().default(""),
    sector: text("sector").notNull().default(""),
    industry: text("industry").notNull().default(""),
    status: text("status").notNull(),
    score: doublePrecision("score").notNull().default(0),
    a1: boolean("a1"),
    a2: boolean("a2"),
    a3: boolean("a3"),
    setup: text("setup").notNull().default(""),
    price: doublePrecision("price"),
    entry: doublePrecision("entry"),
    stop: doublePrecision("stop"),
    target: doublePrecision("target"),
    rr: doublePrecision("rr"),
    riskPct: doublePrecision("risk_pct"),
    shares: integer("shares"),
    earnings: text("earnings"),
    lastBar: text("last_bar"),
    selected: boolean("selected").notNull().default(false),
    source: text("source").notNull().default(""),
    reasons: jsonb("reasons").$type<string[]>().notNull().default([]),
    metrics: jsonb("metrics").$type<Record<string, unknown>>().notNull().default({}),
  },
  (table) => [
    uniqueIndex("candidates_run_mode_ticker_idx").on(
      table.runId,
      table.mode,
      table.ticker,
    ),
    index("candidates_ticker_idx").on(table.ticker),
    index("candidates_status_idx").on(table.status),
    index("candidates_score_idx").on(table.score),
  ],
);

export type ScanRun = typeof scanRuns.$inferSelect;
export type RegimeIndex = typeof regimeIndices.$inferSelect;
export type CandidateRow = typeof candidates.$inferSelect;
export type NewCandidate = typeof candidates.$inferInsert;
