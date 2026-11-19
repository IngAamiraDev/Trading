import { NextResponse, type NextRequest } from "next/server";

import { getSession } from "@/lib/auth";
import {
  getLatestRun,
  getRunCandidates,
  isUuid,
} from "@/lib/db/queries";
import { isActionable, isWatch } from "@/lib/format";

export const dynamic = "force-dynamic";

export async function GET(request: NextRequest) {
  const session = await getSession();
  if (!session) {
    return NextResponse.json({ error: "No autorizado." }, { status: 401 });
  }

  const requestedRun = request.nextUrl.searchParams.get("run");
  const run = isUuid(requestedRun)
    ? { id: requestedRun }
    : await getLatestRun();

  if (!run) {
    return NextResponse.json({ error: "Sin runs publicados." }, { status: 404 });
  }

  const rows = await getRunCandidates(run.id);
  const tickers = Array.from(
    new Set(
      rows
        .filter((row) => isActionable(row.status) || isWatch(row.status))
        .map((row) => row.ticker),
    ),
  ).sort();

  return new NextResponse(`${tickers.join("\n")}\n`, {
    headers: {
      "Content-Type": "text/plain; charset=utf-8",
      "Content-Disposition": `attachment; filename="aaa-watchlist-${run.id.slice(0, 8)}.txt"`,
      "Cache-Control": "no-store",
    },
  });
}
