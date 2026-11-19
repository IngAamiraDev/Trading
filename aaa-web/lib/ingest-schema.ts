import { z } from "zod";

const nullableNumber = z.number().finite().nullable().optional();

const regimeIndexSchema = z.object({
  close: nullableNumber,
  sma_fast: nullableNumber,
  sma_slow: nullableNumber,
  above_fast: z.boolean().nullable().optional(),
  above_slow: z.boolean().nullable().optional(),
  last_bar: z.string().nullable().optional(),
  error: z.string().nullable().optional(),
});

export const candidateSchema = z.object({
  mode: z.enum(["swing", "invest", "day"]),
  ticker: z
    .string()
    .min(1)
    .max(16)
    .transform((value) => value.trim().toUpperCase()),
  company: z.string().default(""),
  sector: z.string().default(""),
  industry: z.string().default(""),
  status: z.string().min(1),
  score: z.number().finite(),
  gates: z
    .object({
      A1: z.boolean().nullable().optional(),
      A2: z.boolean().nullable().optional(),
      A3: z.boolean().nullable().optional(),
    })
    .default({}),
  setup: z.string().default(""),
  price: nullableNumber,
  entry: nullableNumber,
  stop: nullableNumber,
  target: nullableNumber,
  rr: nullableNumber,
  risk_pct: nullableNumber,
  shares: z.number().int().nullable().optional(),
  earnings: z.string().nullable().optional(),
  last_bar: z.string().nullable().optional(),
  selected: z.boolean().default(false),
  source: z.string().default(""),
  reasons: z.array(z.string()).default([]),
  metrics: z.record(z.string(), z.unknown()).default({}),
});

export const ingestSchema = z.object({
  run_id: z.string().uuid(),
  generated_at: z.string().min(1),
  trading_date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
  source: z.string().default("cli"),
  capital: nullableNumber,
  regime: z.object({
    label: z.enum(["risk_on", "neutral", "risk_off"]),
    trend: z.enum(["alcista", "lateral", "bajista", "sin datos"]).optional(),
    vix: nullableNumber,
    indices: z.record(z.string(), regimeIndexSchema).default({}),
    leaders: z.array(z.string()).default([]),
    notes: z.array(z.string()).default([]),
  }),
  modes: z.record(z.string(), z.unknown()).default({}),
  errors: z.array(z.string()).default([]),
  notes: z.array(z.string()).default([]),
  candidates: z.array(candidateSchema).default([]),
});

export type IngestPayload = z.infer<typeof ingestSchema>;
export type IngestCandidate = z.infer<typeof candidateSchema>;
