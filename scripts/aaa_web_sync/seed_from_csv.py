#!/usr/bin/env python3
"""Genera un candidates.json aproximado desde un reporte antiguo.

El motor ya escribe candidates.json de forma nativa. Este script existe solo
para sembrar la web con reportes históricos que únicamente tienen CSV y plan.md.
No sustituye al motor: no recalcula ninguna señal.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import uuid
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
REPORTS_DIR = REPO_ROOT / "reports"

BLOCK_PREFIXES = {
    "ali": "alineación",
    "for": "fortaleza",
    "ent": "entrada",
    "cal": "calidad",
    "cre": "crecimiento",
    "val": "valoración",
    "ten": "tendencia",
}

SECTION_MODES = {
    "## 3.": "swing",
    "## 4.": "invest",
    "## 5.": "day",
}


def latest_report_dir() -> Path:
    candidates = sorted(
        (path for path in REPORTS_DIR.iterdir() if path.is_dir()),
        key=lambda path: path.name,
    )
    if not candidates:
        raise SystemExit("No hay reportes en reports/.")
    return candidates[-1]


def parse_number(value: str | None) -> float | None:
    if value is None:
        return None
    text = str(value).strip().replace(",", "")
    if not text or text in {"-", "n/d"}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse_bool(value: str | None) -> bool | None:
    if value is None:
        return None
    text = str(value).strip().lower()
    if text in {"true", "1", "si", "sí", "yes"}:
        return True
    if text in {"false", "0", "no"}:
        return False
    return None


def parse_indices(plan_text: str) -> dict[str, dict[str, Any]]:
    indices: dict[str, dict[str, Any]] = {}
    pattern = re.compile(
        r"^\|\s*([A-Z0-9.^]+)\s*\|\s*([\d.,]+)\s*\|\s*([\d.,]+)\s*\|\s*([\d.,]+)\s*\|\s*(si|no)\s*\|\s*(si|no)\s*\|",
        re.IGNORECASE,
    )
    for line in plan_text.splitlines():
        match = pattern.match(line)
        if not match:
            continue
        symbol, close, fast, slow, above_fast, above_slow = match.groups()
        indices[symbol] = {
            "close": parse_number(close),
            "sma_fast": parse_number(fast),
            "sma_slow": parse_number(slow),
            "above_fast": above_fast.lower() == "si",
            "above_slow": above_slow.lower() == "si",
            "last_bar": None,
            "error": None,
        }
    return indices


def parse_leaders(plan_text: str) -> list[str]:
    match = re.search(
        r"\*\*Sectores líderes[^*]*:\*\*\s*(.+)", plan_text, re.IGNORECASE
    )
    if not match:
        return []
    return [item.strip() for item in match.group(1).split(",") if item.strip()]


def derive_trend(indices: dict[str, dict[str, Any]]) -> str:
    """Misma regla que Regime.trend del motor: estructura de los índices."""
    valid = [data for data in indices.values() if not data.get("error")]
    if not valid:
        return "sin datos"
    all_above_fast = all(bool(data.get("above_fast")) for data in valid)
    all_above_slow = all(bool(data.get("above_slow")) for data in valid)
    if all_above_fast and all_above_slow:
        return "alcista"
    if not any(bool(data.get("above_slow")) for data in valid):
        return "bajista"
    return "lateral"


def parse_blocks(plan_text: str) -> dict[tuple[str, str], dict[str, float]]:
    blocks: dict[tuple[str, str], dict[str, float]] = {}
    mode: str | None = None
    for line in plan_text.splitlines():
        if line.startswith("## "):
            mode = next(
                (value for prefix, value in SECTION_MODES.items() if line.startswith(prefix)),
                None,
            )
            continue
        if not mode or not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 3:
            continue
        ticker = cells[0].upper()
        if not re.fullmatch(r"[A-Z0-9.\-]{1,10}", ticker):
            continue
        raw_blocks = cells[-1]
        parsed: dict[str, float] = {}
        for name, value in re.findall(r"(ali|for|ent|cal|cre|val|ten)\s+(\d+(?:\.\d+)?)", raw_blocks):
            parsed[BLOCK_PREFIXES[name]] = float(value)
        if parsed:
            blocks[(mode, ticker)] = parsed
    return blocks


def build_payload(report_dir: Path) -> dict[str, Any]:
    summary_path = report_dir / "summary.json"
    csv_path = report_dir / "candidates.csv"
    plan_path = report_dir / "plan.md"

    if not summary_path.exists() or not csv_path.exists():
        raise SystemExit(f"Faltan summary.json o candidates.csv en {report_dir}")

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    plan_text = plan_path.read_text(encoding="utf-8") if plan_path.exists() else ""
    blocks = parse_blocks(plan_text)
    indices = parse_indices(plan_text)
    leaders = parse_leaders(plan_text)

    generated_at = summary.get("generated_at") or f"{report_dir.name}T00:00:00"
    trading_date = summary.get("trading_date") or report_dir.name
    run_id = summary.get("run_id") or str(
        uuid.uuid5(uuid.NAMESPACE_URL, f"aaa-seed:{trading_date}:{generated_at}")
    )

    candidates: list[dict[str, Any]] = []
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            ticker = (row.get("ticker") or "").upper()
            mode = row.get("mode") or "swing"
            reasons = [
                reason.strip()
                for reason in (row.get("reasons") or "").split(" | ")
                if reason.strip()
            ]
            candidates.append(
                {
                    "mode": mode,
                    "ticker": ticker,
                    "company": row.get("company") or "",
                    "sector": row.get("sector") or "",
                    "industry": row.get("industry") or "",
                    "status": row.get("status") or "Descartado",
                    "score": parse_number(row.get("score")) or 0.0,
                    "gates": {
                        "A1": parse_bool(row.get("a1")),
                        "A2": parse_bool(row.get("a2")),
                        "A3": parse_bool(row.get("a3")),
                    },
                    "setup": row.get("setup") or "",
                    "price": parse_number(row.get("price")),
                    "entry": parse_number(row.get("entry")),
                    "stop": parse_number(row.get("stop")),
                    "target": parse_number(row.get("target")),
                    "rr": parse_number(row.get("rr")),
                    "risk_pct": parse_number(row.get("risk_pct")),
                    "shares": int(value) if (value := parse_number(row.get("shares"))) else None,
                    "earnings": (row.get("earnings") or "").strip() or None,
                    "last_bar": (row.get("last_bar") or "").strip() or None,
                    "selected": False,
                    "source": row.get("source") or "legacy-csv",
                    "reasons": reasons,
                    "metrics": {"bloques": blocks.get((mode, ticker), {})},
                }
            )

    modes_summary = summary.get("modes") or {}
    errors = [error for item in modes_summary.values() for error in item.get("errors", [])]
    notes = [note for item in modes_summary.values() for note in item.get("notes", [])]

    return {
        "run_id": run_id,
        "generated_at": generated_at,
        "trading_date": trading_date,
        "source": "legacy-csv",
        "capital": summary.get("capital"),
        "regime": {
            "label": summary.get("regime") or "neutral",
            "trend": summary.get("trend") or derive_trend(indices),
            "vix": summary.get("vix"),
            "indices": indices,
            "leaders": leaders,
            "notes": [],
        },
        "modes": modes_summary,
        "errors": errors,
        "notes": notes,
        "candidates": candidates,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Genera candidates.json desde CSV.")
    parser.add_argument("--report-dir", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)

    report_dir = args.report_dir or latest_report_dir()
    payload = build_payload(report_dir)
    output = args.output or (report_dir / "candidates.json")

    if output.exists() and not args.force:
        raise SystemExit(f"{output} ya existe. Usa --force para sobrescribir.")

    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"Escrito {output} | run {payload['run_id']} | "
        f"{len(payload['candidates'])} candidatos | {len(payload['regime']['indices'])} índices"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
