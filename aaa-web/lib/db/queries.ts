import { and, asc, desc, eq, gte, ilike, or, type SQL } from "drizzle-orm";

import { db } from "@/lib/db";
import {
  candidates,
  regimeIndices,
  scanRuns,
  type CandidateRow,
  type RegimeIndex,
  type ScanRun,
} from "@/lib/db/schema";

export type CandidateFilters = {
  mode?: string;
  status?: string;
  sector?: string;
  q?: string;
  minScore?: number;
  sort?: "score" | "risk" | "rr" | "ticker";
};

export type RunBundle = {
  run: ScanRun;
  indices: RegimeIndex[];
  candidates: CandidateRow[];
};

export type TickerHistoryRow = {
  runId: string;
  generatedAt: Date;
  tradingDate: string;
  mode: string;
  status: string;
  score: number;
  entry: number | null;
  stop: number | null;
  rr: number | null;
  selected: boolean;
};

const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export function isUuid(value: string | undefined | null): value is string {
  return Boolean(value && UUID_PATTERN.test(value));
}

export async function getLatestRun(): Promise<ScanRun | null> {
  const rows = await db
    .select()
    .from(scanRuns)
    .orderBy(desc(scanRuns.generatedAt), desc(scanRuns.createdAt))
    .limit(1);
  return rows[0] ?? null;
}

export async function getRun(runId: string): Promise<ScanRun | null> {
  if (!isUuid(runId)) {
    return null;
  }
  const rows = await db.select().from(scanRuns).where(eq(scanRuns.id, runId)).limit(1);
  return rows[0] ?? null;
}

export async function getRunBundle(runId?: string): Promise<RunBundle | null> {
  const run = runId ? await getRun(runId) : await getLatestRun();
  if (!run) {
    return null;
  }

  const [indices, rows] = await Promise.all([
    db
      .select()
      .from(regimeIndices)
      .where(eq(regimeIndices.runId, run.id))
      .orderBy(asc(regimeIndices.symbol)),
    db
      .select()
      .from(candidates)
      .where(eq(candidates.runId, run.id))
      .orderBy(desc(candidates.score), asc(candidates.ticker)),
  ]);

  return { run, indices, candidates: rows };
}

export async function listCandidates(
  runId: string,
  filters: CandidateFilters = {},
): Promise<CandidateRow[]> {
  const conditions: SQL[] = [eq(candidates.runId, runId)];

  if (filters.mode) {
    conditions.push(eq(candidates.mode, filters.mode));
  }
  if (filters.status) {
    conditions.push(eq(candidates.status, filters.status));
  }
  if (filters.sector) {
    conditions.push(eq(candidates.sector, filters.sector));
  }
  if (filters.minScore !== undefined && Number.isFinite(filters.minScore)) {
    conditions.push(gte(candidates.score, filters.minScore));
  }
  if (filters.q?.trim()) {
    const term = `%${filters.q.trim()}%`;
    const search = or(
      ilike(candidates.ticker, term),
      ilike(candidates.company, term),
    );
    if (search) {
      conditions.push(search);
    }
  }

  const order =
    filters.sort === "risk"
      ? asc(candidates.riskPct)
      : filters.sort === "rr"
        ? desc(candidates.rr)
        : filters.sort === "ticker"
          ? asc(candidates.ticker)
          : desc(candidates.score);

  return db
    .select()
    .from(candidates)
    .where(and(...conditions))
    .orderBy(order, asc(candidates.ticker));
}

export async function getTickerCandidates(
  runId: string,
  ticker: string,
): Promise<CandidateRow[]> {
  return db
    .select()
    .from(candidates)
    .where(
      and(
        eq(candidates.runId, runId),
        eq(candidates.ticker, ticker.trim().toUpperCase()),
      ),
    )
    .orderBy(asc(candidates.mode));
}

export async function getRegimeIndices(runId: string): Promise<RegimeIndex[]> {
  if (!isUuid(runId)) {
    return [];
  }
  return db
    .select()
    .from(regimeIndices)
    .where(eq(regimeIndices.runId, runId))
    .orderBy(asc(regimeIndices.symbol));
}

export async function getTickerHistory(
  ticker: string,
  limit = 12,
): Promise<TickerHistoryRow[]> {
  const normalized = ticker.trim().toUpperCase();
  const rows = await db
    .select({
      runId: scanRuns.id,
      generatedAt: scanRuns.generatedAt,
      tradingDate: scanRuns.tradingDate,
      mode: candidates.mode,
      status: candidates.status,
      score: candidates.score,
      entry: candidates.entry,
      stop: candidates.stop,
      rr: candidates.rr,
      selected: candidates.selected,
    })
    .from(candidates)
    .innerJoin(scanRuns, eq(candidates.runId, scanRuns.id))
    .where(eq(candidates.ticker, normalized))
    .orderBy(desc(scanRuns.generatedAt), asc(candidates.mode))
    .limit(limit);
  return rows;
}

export async function getRunCandidates(runId: string): Promise<CandidateRow[]> {
  return db
    .select()
    .from(candidates)
    .where(eq(candidates.runId, runId))
    .orderBy(desc(candidates.score), asc(candidates.ticker));
}
