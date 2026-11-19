import { timingSafeEqual } from "node:crypto";

import { eq } from "drizzle-orm";
import { NextResponse, type NextRequest } from "next/server";

import { db } from "@/lib/db";
import {
  candidates,
  regimeIndices,
  scanRuns,
  type NewCandidate,
} from "@/lib/db/schema";
import { ingestSchema } from "@/lib/ingest-schema";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

function authorized(request: NextRequest) {
  const expected = process.env.AAA_INGEST_TOKEN;
  const header = request.headers.get("authorization") ?? "";
  const token = header.startsWith("Bearer ") ? header.slice(7).trim() : "";
  if (!expected || !token) {
    return false;
  }
  const provided = Buffer.from(token);
  const wanted = Buffer.from(expected);
  return (
    provided.length === wanted.length && timingSafeEqual(provided, wanted)
  );
}

export async function POST(request: NextRequest) {
  if (!authorized(request)) {
    return NextResponse.json({ error: "No autorizado." }, { status: 401 });
  }

  const raw = await request.json().catch(() => null);
  const parsed = ingestSchema.safeParse(raw);
  if (!parsed.success) {
    return NextResponse.json(
      { error: "Payload inválido.", issues: parsed.error.issues },
      { status: 400 },
    );
  }

  const payload = parsed.data;
  const generatedAt = new Date(payload.generated_at);
  if (Number.isNaN(generatedAt.getTime())) {
    return NextResponse.json(
      { error: "generated_at no es una fecha válida." },
      { status: 400 },
    );
  }

  const seen = new Set<string>();
  const candidateRows: NewCandidate[] = [];
  for (const candidate of payload.candidates) {
    const key = `${candidate.mode}:${candidate.ticker}`;
    if (seen.has(key)) {
      continue;
    }
    seen.add(key);
    candidateRows.push({
      runId: payload.run_id,
      mode: candidate.mode,
      ticker: candidate.ticker,
      company: candidate.company,
      sector: candidate.sector,
      industry: candidate.industry,
      status: candidate.status,
      score: candidate.score,
      a1: candidate.gates.A1 ?? null,
      a2: candidate.gates.A2 ?? null,
      a3: candidate.gates.A3 ?? null,
      setup: candidate.setup,
      price: candidate.price ?? null,
      entry: candidate.entry ?? null,
      stop: candidate.stop ?? null,
      target: candidate.target ?? null,
      rr: candidate.rr ?? null,
      riskPct: candidate.risk_pct ?? null,
      shares: candidate.shares ?? null,
      earnings: candidate.earnings ?? null,
      lastBar: candidate.last_bar ?? null,
      selected: candidate.selected,
      source: candidate.source,
      reasons: candidate.reasons,
      metrics: candidate.metrics,
    });
  }

  const indexRows = Object.entries(payload.regime.indices).map(
    ([symbol, data]) => ({
      runId: payload.run_id,
      symbol,
      close: data.close ?? null,
      smaFast: data.sma_fast ?? null,
      smaSlow: data.sma_slow ?? null,
      aboveFast: data.above_fast ?? null,
      aboveSlow: data.above_slow ?? null,
      lastBar: data.last_bar ?? null,
      error: data.error ?? null,
    }),
  );

  try {
    await db.transaction(async (tx) => {
      await tx
        .insert(scanRuns)
        .values({
          id: payload.run_id,
          generatedAt,
          tradingDate: payload.trading_date,
          regime: payload.regime.label,
          trend: payload.regime.trend ?? null,
          vix: payload.regime.vix ?? null,
          capital: payload.capital ?? null,
          source: payload.source,
          leaders: payload.regime.leaders,
          errors: payload.errors,
          notes: payload.notes,
          modes: payload.modes,
        })
        .onConflictDoUpdate({
          target: scanRuns.id,
          set: {
            generatedAt,
            tradingDate: payload.trading_date,
            regime: payload.regime.label,
            trend: payload.regime.trend ?? null,
            vix: payload.regime.vix ?? null,
            capital: payload.capital ?? null,
            source: payload.source,
            leaders: payload.regime.leaders,
            errors: payload.errors,
            notes: payload.notes,
            modes: payload.modes,
          },
        });

      await tx.delete(candidates).where(eq(candidates.runId, payload.run_id));
      await tx
        .delete(regimeIndices)
        .where(eq(regimeIndices.runId, payload.run_id));

      if (indexRows.length > 0) {
        await tx.insert(regimeIndices).values(indexRows);
      }
      if (candidateRows.length > 0) {
        await tx.insert(candidates).values(candidateRows);
      }
    });
  } catch (error) {
    console.error("[ingest] no se pudo guardar el run", error);
    return NextResponse.json(
      {
        error: "No se pudo guardar el run.",
        detail:
          process.env.NODE_ENV === "production"
            ? undefined
            : error instanceof Error
              ? error.message
              : String(error),
      },
      { status: 500 },
    );
  }

  return NextResponse.json({
    ok: true,
    run_id: payload.run_id,
    trading_date: payload.trading_date,
    candidates: candidateRows.length,
    indices: indexRows.length,
  });
}
