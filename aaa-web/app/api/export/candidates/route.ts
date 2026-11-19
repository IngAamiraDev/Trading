import { NextResponse, type NextRequest } from "next/server";

import { getSession } from "@/lib/auth";
import { toCsv } from "@/lib/csv";
import {
  getLatestRun,
  isUuid,
  listCandidates,
} from "@/lib/db/queries";

export const dynamic = "force-dynamic";

export async function GET(request: NextRequest) {
  const session = await getSession();
  if (!session) {
    return NextResponse.json({ error: "No autorizado." }, { status: 401 });
  }

  const params = request.nextUrl.searchParams;
  const requestedRun = params.get("run");
  const run = isUuid(requestedRun)
    ? { id: requestedRun }
    : await getLatestRun();

  if (!run) {
    return NextResponse.json({ error: "Sin runs publicados." }, { status: 404 });
  }

  const minScore = params.get("minScore");
  const rows = await listCandidates(run.id, {
    mode: params.get("mode") ?? undefined,
    status: params.get("status") ?? undefined,
    sector: params.get("sector") ?? undefined,
    q: params.get("q") ?? undefined,
    minScore: minScore ? Number(minScore) : undefined,
    sort:
      (params.get("sort") as "score" | "risk" | "rr" | "ticker" | null) ??
      "score",
  });

  const csv = toCsv(
    [
      "mode",
      "ticker",
      "company",
      "sector",
      "industry",
      "status",
      "score",
      "a1",
      "a2",
      "a3",
      "setup",
      "price",
      "entry",
      "stop",
      "target",
      "rr",
      "risk_pct",
      "shares",
      "earnings",
      "last_bar",
      "selected",
      "reasons",
    ],
    rows.map((row) => [
      row.mode,
      row.ticker,
      row.company,
      row.sector,
      row.industry,
      row.status,
      row.score,
      row.a1,
      row.a2,
      row.a3,
      row.setup,
      row.price,
      row.entry,
      row.stop,
      row.target,
      row.rr,
      row.riskPct,
      row.shares,
      row.earnings,
      row.lastBar,
      row.selected,
      row.reasons.join(" | "),
    ]),
  );

  return new NextResponse(csv, {
    headers: {
      "Content-Type": "text/csv; charset=utf-8",
      "Content-Disposition": `attachment; filename="aaa-candidates-${run.id.slice(0, 8)}.csv"`,
      "Cache-Control": "no-store",
    },
  });
}
