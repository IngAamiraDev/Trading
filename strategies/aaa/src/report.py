"""Generacion de reportes Markdown, CSV y watchlist de TradingView."""

from __future__ import annotations

import csv
import json
import math
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Any

from .config import REPORTS_DIR, ensure_dir
from .models import Candidate, Regime, ScanResult


def _n(value: Any, digits: int = 2, suffix: str = "") -> str:
    if value is None:
        return "-"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    return f"{number:,.{digits}f}{suffix}"


def _date(value: str | None) -> str:
    if not value:
        return "n/d"
    return str(value)[:10]


def _table(headers: list[str], rows: list[list[Any]]) -> str:
    clean_headers = [str(h) for h in headers]
    lines = [
        "| " + " | ".join(clean_headers) + " |",
        "|" + "|".join(["---"] * len(clean_headers)) + "|",
    ]
    for row in rows:
        cells = [str(cell).replace("|", "/").replace("\n", " ") for cell in row]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def _block(metrics: dict[str, Any]) -> str:
    blocks = metrics.get("bloques", {}) if isinstance(metrics, dict) else {}
    if not blocks:
        return "-"
    return " / ".join(f"{name[:3]} {value:g}" for name, value in blocks.items())


def _json_safe(value: Any) -> Any:
    """Convierte el resultado del motor en JSON estricto."""
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return value
    if isinstance(value, bool) or isinstance(value, (str, int)) or value is None:
        return value
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    return None if math.isnan(number) or math.isinf(number) else number


def _regime_section(regime: Regime, config: dict[str, Any]) -> list[str]:
    label_map = {
        "risk_on": "Risk-on (se permiten setups AAA)",
        "neutral": "Neutral (solo A+ y media posición)",
        "risk_off": "Risk-off (no abrir nuevos largos)",
    }
    lines = ["## 1. Régimen de mercado", ""]
    lines.append(f"**Tendencia:** {regime.trend.capitalize()}")
    lines.append("")
    lines.append(f"**Lectura:** {label_map.get(regime.label, regime.label)}")
    lines.append("")
    rows = []
    for symbol, data in regime.indices.items():
        if "error" in data:
            rows.append([symbol, "sin datos", "-", "-", "-", "-"])
            continue
        rows.append(
            [
                symbol,
                _n(data.get("close")),
                _n(data.get("sma_fast")),
                _n(data.get("sma_slow")),
                "si" if data.get("above_fast") else "no",
                "si" if data.get("above_slow") else "no",
            ]
        )
    if rows:
        lines.append(_table(["Índice", "Cierre", "SMA50", "SMA200", "> SMA50", "> SMA200"], rows))
        lines.append("")
    lines.append(f"**VIX:** {_n(regime.vix, 2)} (límite {config.get('regime', {}).get('vix_max', 25)})")
    if regime.leaders:
        lines.append("")
        lines.append("**Sectores líderes (RS 1m vs SPY):** " + ", ".join(regime.leaders))
    if regime.notes:
        lines.append("")
        for note in regime.notes:
            lines.append(f"- {note}")
    lines.append("")
    return lines


def _risk_section(budget: dict[str, Any], results: dict[str, ScanResult]) -> list[str]:
    lines = ["## 2. Presupuesto de riesgo", ""]
    selected = [
        candidate
        for result in results.values()
        for candidate in result.candidates
        if candidate.selected
    ]
    open_risk = sum(
        float(candidate.metrics.get("effective_risk_pct", 0.0)) for candidate in selected
    )
    if not budget.get("capital"):
        lines.append(
            "Capital no definido: los tamaños quedan pendientes. "
            "Ejecuta con `--capital` o define `account.capital` en la config."
        )
    else:
        lines.append(f"- Capital de referencia: **${_n(budget['capital'], 0)}**")
        lines.append(
            f"- Riesgo por operación: **{budget['risk_per_trade_pct']}%** "
            f"(${_n(budget['risk_per_trade_usd'], 2)})"
        )
        lines.append(
            f"- Riesgo abierto máximo: **{budget['max_open_risk_pct']}%** "
            f"(${_n(budget['max_open_risk_usd'], 2)})"
        )
        lines.append(
            f"- Operaciones simultáneas por riesgo: **{budget['max_positions_by_risk']}**"
        )
    lines.append(f"- Máximo por sector: **{budget['max_positions_per_sector']}**")
    caps = budget.get("max_positions_per_mode", {})
    if caps:
        lines.append(
            "- Máximo por modo: "
            + ", ".join(f"{mode} {cap}" for mode, cap in caps.items())
        )
    lines.append(
        f"- Seleccionadas en este plan: **{len(selected)}** "
        f"({open_risk:.2f}% de riesgo abierto)"
    )
    lines.append("")
    return lines


def _swing_section(result: ScanResult) -> list[str]:
    lines = ["## 3. Watchlist swing (2-15 días)", ""]
    if not result.candidates:
        lines.append("Sin candidatos: el escaneo no devolvió datos o todos fueron descartados.")
        lines.append("")
        return lines
    rows = []
    for candidate in sorted(result.candidates, key=lambda c: c.score, reverse=True)[:15]:
        rows.append(
            [
                candidate.ticker,
                candidate.sector,
                _n(candidate.score, 1),
                candidate.status,
                candidate.setup,
                _n(candidate.entry),
                _n(candidate.stop),
                _n(candidate.target),
                _n(candidate.rr, 1),
                _n(candidate.risk_pct, 1, "%"),
                candidate.shares if candidate.shares is not None else "-",
                _date(candidate.earnings),
                _block(candidate.metrics),
            ]
        )
    lines.append(
        _table(
            [
                "Ticker",
                "Sector",
                "Score",
                "Estado",
                "Setup",
                "Entrada",
                "Stop",
                "Objetivo",
                "R/R",
                "Riesgo",
                "Acciones",
                "Earnings",
                "Bloques",
            ],
            rows,
        )
    )
    lines.append("")
    lines.append("**Motivos de los accionables:**")
    lines.append("")
    actionable = [c for c in result.candidates if c.is_actionable]
    if not actionable:
        lines.append("- Ninguno cumple las tres puertas con el umbral actual.")
    for candidate in actionable[:8]:
        lines.append(
            f"- **{candidate.ticker}** ({candidate.score:.1f}): "
            + "; ".join(candidate.reasons)
        )
    lines.append("")
    return lines


def _invest_section(result: ScanResult) -> list[str]:
    lines = ["## 4. Watchlist inversión (3-12 meses)", ""]
    if not result.candidates:
        lines.append("Sin candidatos de inversión en este escaneo.")
        lines.append("")
        return lines
    rows = []
    for candidate in sorted(result.candidates, key=lambda c: c.score, reverse=True)[:15]:
        metrics = candidate.metrics
        rows.append(
            [
                candidate.ticker,
                candidate.sector,
                _n(candidate.score, 1),
                candidate.status,
                _n(metrics.get("roe"), 1, "%"),
                _n(metrics.get("eps_qoq"), 1, "%"),
                _n(metrics.get("sales_qoq"), 1, "%"),
                _n(metrics.get("peg"), 2),
                _n(candidate.entry),
                _n(candidate.stop),
                _n(metrics.get("dist_high"), 1, "%"),
                _block(metrics),
            ]
        )
    lines.append(
        _table(
            [
                "Ticker",
                "Sector",
                "Score",
                "Estado",
                "ROE",
                "EPS Q/Q",
                "Ventas Q/Q",
                "PEG",
                "Entrada",
                "Stop",
                "A máx 52s",
                "Bloques",
            ],
            rows,
        )
    )
    lines.append("")
    return lines


def _day_section(result: ScanResult) -> list[str]:
    lines = ["## 5. Plan day (misma sesión, solo research/paper)", ""]
    if not result.candidates:
        lines.append("Sin candidatos intradía en este escaneo.")
        lines.append("")
        return lines
    rows = []
    for candidate in sorted(result.candidates, key=lambda c: c.score, reverse=True)[:10]:
        metrics = candidate.metrics
        gap_text = _n(metrics.get("gap_pct"), 2, "%")
        if metrics.get("gap_anomaly"):
            gap_text += " (anómalo)"
        rows.append(
            [
                candidate.ticker,
                _n(candidate.score, 1),
                candidate.status,
                candidate.setup,
                gap_text,
                _n(metrics.get("rel_vol"), 2),
                _n(candidate.entry),
                _n(candidate.stop),
                _n(candidate.target),
                _n(candidate.rr, 1),
                _n(candidate.risk_pct, 2, "%"),
                _block(metrics),
            ]
        )
    lines.append(
        _table(
            [
                "Ticker",
                "Score",
                "Estado",
                "Setup",
                "Gap",
                "RelVol",
                "Entrada",
                "Stop",
                "Objetivo",
                "R/R",
                "Riesgo",
                "Bloques",
            ],
            rows,
        )
    )
    lines.append("")
    lines.append(
        "Cierre obligatorio antes de 15:55 ET. yfinance puede estar retrasado: "
        "no usar para ejecución automática."
    )
    lines.append("")
    return lines


def _rejected_section(results: dict[str, ScanResult]) -> list[str]:
    lines = ["## 6. Descartados relevantes", ""]
    rejected: list[Candidate] = []
    for result in results.values():
        rejected.extend(
            [c for c in result.candidates if c.status in {"Descartado", "Reject"}]
        )
    rejected.sort(key=lambda c: c.score, reverse=True)
    if not rejected:
        lines.append("Ninguno.")
        lines.append("")
        return lines
    rows = []
    for candidate in rejected[:15]:
        rows.append(
            [
                candidate.ticker,
                candidate.mode,
                _n(candidate.score, 1),
                "; ".join(candidate.reasons[-3:]),
            ]
        )
    lines.append(_table(["Ticker", "Modo", "Score", "Motivo principal"], rows))
    lines.append("")
    return lines


def _quality_section(results: dict[str, ScanResult], notes: list[str]) -> list[str]:
    lines = ["## 7. Calidad de datos", ""]
    for mode, result in results.items():
        lines.append(
            f"- **{mode}:** {len(result.candidates)} candidatos, "
            f"{len(result.actionable)} accionables, {len(result.watchlist)} en vigilancia."
        )
        for note in result.notes:
            lines.append(f"  - {note}")
        for error in result.errors:
            lines.append(f"  - Error: {error}")
    for note in notes:
        lines.append(f"- {note}")
    lines.append(
        "- Datos: Finviz (screeners/fundamentales) + yfinance (OHLCV). "
        "Pueden estar retrasados o incompletos."
    )
    lines.append("- Este reporte no es asesoría financiera ni una orden de compra.")
    lines.append("")
    return lines


def build_plan(
    results: dict[str, ScanResult],
    regime: Regime,
    config: dict[str, Any],
    budget: dict[str, Any],
    generated_at: datetime | None = None,
    notes: list[str] | None = None,
) -> str:
    stamp = generated_at or datetime.now()
    lines = [
        f"# Plan AAA - {stamp.strftime('%Y-%m-%d')}",
        "",
        f"> Generado {stamp.strftime('%Y-%m-%d %H:%M')} | "
        "Aproximación configurable a los tres pilares CDI | "
        "Solo señales, no ejecuta órdenes.",
        "",
    ]
    lines.extend(_regime_section(regime, config))
    lines.extend(_risk_section(budget, results))
    lines.extend(_swing_section(results.get("swing", ScanResult(mode="swing"))))
    lines.extend(_invest_section(results.get("invest", ScanResult(mode="invest"))))
    lines.extend(_day_section(results.get("day", ScanResult(mode="day"))))
    lines.extend(_rejected_section(results))
    lines.extend(_quality_section(results, notes or []))
    return "\n".join(lines).rstrip() + "\n"


def build_payload(
    results: dict[str, ScanResult],
    regime: Regime,
    config: dict[str, Any],
    budget: dict[str, Any],
    generated_at: datetime | None = None,
    run_id: str | None = None,
    source: str = "cli",
) -> dict[str, Any]:
    """Construye el JSON estable que consume la web."""
    stamp = generated_at or datetime.now()
    identifier = run_id or str(uuid.uuid4())

    candidates_payload: list[dict[str, Any]] = []
    for mode in ("swing", "invest", "day"):
        result = results.get(mode)
        if not result:
            continue
        for candidate in sorted(result.candidates, key=lambda c: c.score, reverse=True):
            candidates_payload.append(candidate.to_payload())

    indices = {}
    for symbol, data in regime.indices.items():
        indices[symbol] = {
            "close": data.get("close"),
            "sma_fast": data.get("sma_fast"),
            "sma_slow": data.get("sma_slow"),
            "above_fast": data.get("above_fast"),
            "above_slow": data.get("above_slow"),
            "last_bar": data.get("last_bar"),
            "error": data.get("error"),
        }

    errors = [error for result in results.values() for error in result.errors]
    notes = [note for result in results.values() for note in result.notes]

    payload = {
        "run_id": identifier,
        "generated_at": stamp.isoformat(),
        "trading_date": stamp.strftime("%Y-%m-%d"),
        "source": source,
        "capital": budget.get("capital"),
        "regime": {
            "label": regime.label,
            "trend": regime.trend,
            "vix": regime.vix,
            "indices": indices,
            "leaders": list(regime.leaders),
            "notes": list(regime.notes),
        },
        "modes": {
            mode: {
                "candidates": len(result.candidates),
                "actionable": len(result.actionable),
                "watchlist": len(result.watchlist),
                "errors": list(result.errors),
                "notes": list(result.notes),
            }
            for mode, result in results.items()
        },
        "errors": errors,
        "notes": notes,
        "candidates": candidates_payload,
    }
    return _json_safe(payload)


def write_reports(
    results: dict[str, ScanResult],
    regime: Regime,
    config: dict[str, Any],
    budget: dict[str, Any],
    output_dir: str | Path | None = None,
    generated_at: datetime | None = None,
    notes: list[str] | None = None,
    run_id: str | None = None,
    source: str = "cli",
) -> dict[str, Path]:
    stamp = generated_at or datetime.now()
    identifier = run_id or str(uuid.uuid4())
    directory = Path(output_dir) if output_dir else REPORTS_DIR / stamp.strftime("%Y-%m-%d")
    ensure_dir(directory)

    plan_path = directory / "plan.md"
    plan_path.write_text(
        build_plan(results, regime, config, budget, stamp, notes), encoding="utf-8"
    )

    payload = build_payload(
        results,
        regime,
        config,
        budget,
        generated_at=stamp,
        run_id=identifier,
        source=source,
    )

    rows: list[dict[str, Any]] = []
    for mode in ("swing", "invest", "day"):
        result = results.get(mode)
        if not result:
            continue
        for candidate in sorted(result.candidates, key=lambda c: c.score, reverse=True):
            rows.append(candidate.to_row())

    csv_path = directory / "candidates.csv"
    if rows:
        with csv_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

    json_path = directory / "candidates.json"
    json_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    watchlist = sorted(
        {
            candidate.ticker
            for result in results.values()
            for candidate in result.candidates
            if candidate.is_actionable or candidate.status in {"Vigilancia", "Watch"}
        }
    )
    watchlist_path = directory / "watchlist_tradingview.txt"
    watchlist_path.write_text("\n".join(watchlist) + ("\n" if watchlist else ""), encoding="utf-8")

    summary = {
        "run_id": identifier,
        "generated_at": stamp.isoformat(),
        "trading_date": payload["trading_date"],
        "regime": regime.label,
        "trend": regime.trend,
        "vix": regime.vix,
        "capital": budget.get("capital"),
        "modes": payload["modes"],
        "errors": payload["errors"],
        "notes": payload["notes"],
    }
    summary_path = directory / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    return {
        "directory": directory,
        "plan": plan_path,
        "csv": csv_path,
        "json": json_path,
        "watchlist": watchlist_path,
        "summary": summary_path,
    }
