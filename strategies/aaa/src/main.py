"""CLI del motor AAA: scan, plan y review."""

from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime
from typing import Any

import pandas as pd

from .config import DEFAULT_CONFIG_PATH, load_config
from .finviz_presets import PRESETS, run_presets
from .market_data import download, fetch_fundamentals
from .models import Candidate, Regime, ScanResult
from .report import write_reports
from .risk import apply_risk, risk_budget
from .scoring import (
    compute_regime,
    evaluate_day,
    evaluate_invest,
    evaluate_swing,
    load_sector_data,
    sector_context,
)

MODES = ("swing", "invest", "day")


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Motor AAA-CDI: screening y planificación (solo señales)."
    )
    parser.add_argument(
        "command",
        choices=["scan", "plan", "review"],
        help="scan: un modo; plan: swing+inversión+day; review: un ticker",
    )
    parser.add_argument("ticker", nargs="?", help="Ticker para review")
    parser.add_argument(
        "--mode",
        choices=list(MODES),
        default=None,
        help="Modo para scan (por defecto swing)",
    )
    parser.add_argument(
        "--capital", type=float, default=None, help="Capital de referencia en USD"
    )
    parser.add_argument(
        "--limit", type=int, default=None, help="Maximo de candidatos por modo"
    )
    parser.add_argument(
        "--config", default=str(DEFAULT_CONFIG_PATH), help="Ruta del JSON de config"
    )
    parser.add_argument(
        "--output", default=None, help="Directorio de salida del reporte"
    )
    parser.add_argument(
        "--no-write", action="store_true", help="No escribir reportes en disco"
    )
    return parser.parse_args(argv)


def _meta_from_row(row: pd.Series, preset: str) -> dict[str, Any]:
    return {
        "company": row.get("Company", ""),
        "sector": row.get("Sector", ""),
        "industry": row.get("Industry", ""),
        "market_cap": row.get("Market Cap"),
        "price": row.get("Price"),
        "change": row.get("Change"),
        "volume": row.get("Volume"),
        "preset": preset or row.get("preset", "finviz"),
    }


def _scan_mode(
    mode: str,
    config: dict[str, Any],
    regime: Regime,
    limit: int,
    sector_data: dict[str, pd.DataFrame | None],
    spy: pd.DataFrame | None,
) -> ScanResult:
    result = ScanResult(mode=mode)
    scan_cfg = config.get("scan", {})
    presets = scan_cfg.get("presets", {}).get(mode, [])
    if not presets:
        result.errors.append(f"No hay presets configurados para {mode}.")
        return result

    per_preset = max(20, min(limit, 50))
    frame, errors, notes = run_presets(
        presets,
        limit=per_preset,
        sleep_sec=float(scan_cfg.get("finviz_sleep_seconds", 0.8)),
    )
    result.errors.extend(errors)
    result.notes.extend(notes)
    if frame is None or frame.empty:
        result.errors.append(f"Finviz no devolvió candidatos para {mode}.")
        return result

    frame = frame.head(limit)
    fundamentals_sleep = float(scan_cfg.get("fundamentals_sleep_seconds", 0.3))
    yfinance_sleep = float(scan_cfg.get("yfinance_sleep_seconds", 0.15))
    ttl = int(scan_cfg.get("cache_ttl_minutes", 360))

    for _, row in frame.iterrows():
        ticker = str(row["Ticker"]).upper()
        meta = _meta_from_row(row, str(row.get("preset", "")))
        try:
            fundamentals = fetch_fundamentals(ticker, ttl_minutes=ttl)
            if mode == "day":
                daily = download(ticker, period="3mo")
                intraday = download(
                    ticker, period="5d", interval="5m", prepost=True
                )
                candidate = evaluate_day(
                    ticker,
                    meta,
                    daily,
                    intraday,
                    spy,
                    fundamentals,
                    config,
                    regime,
                )
            elif mode == "invest":
                daily = download(ticker, period="2y")
                candidate = evaluate_invest(
                    ticker, meta, daily, spy, fundamentals, config, regime
                )
            else:
                daily = download(ticker, period="2y")
                sector = sector_context(meta.get("sector", ""), sector_data, spy)
                candidate = evaluate_swing(
                    ticker,
                    meta,
                    daily,
                    spy,
                    sector,
                    fundamentals,
                    config,
                    regime,
                )
            result.candidates.append(candidate)
        except Exception as exc:  # pragma: no cover - red / datos
            result.errors.append(f"{ticker}: {exc}")
        time.sleep(max(fundamentals_sleep, yfinance_sleep))

    result.candidates = apply_risk(
        result.candidates, config, config.get("account", {}).get("capital"), regime
    )
    return result


def _print_summary(results: dict[str, ScanResult], regime: Regime) -> None:
    print(f"Regimen: {regime.label} | VIX: {regime.vix}")
    if regime.leaders:
        print("Sectores líderes: " + ", ".join(regime.leaders))
    for mode, result in results.items():
        print(
            f"\n[{mode}] {len(result.candidates)} candidatos | "
            f"{len(result.actionable)} accionables | {len(result.watchlist)} en vigilancia"
        )
        ordered = sorted(result.candidates, key=lambda c: c.score, reverse=True)
        for candidate in ordered[:10]:
            print(
                f"  {candidate.ticker:6s} {candidate.score:5.1f} {candidate.status:12s} "
                f"{candidate.setup:18s} entrada {candidate.entry} stop {candidate.stop} "
                f"R/R {candidate.rr}"
            )
        if result.errors:
            print(f"  errores: {len(result.errors)}")


def _review(
    ticker: str,
    config: dict[str, Any],
    regime: Regime,
    sector_data: dict[str, pd.DataFrame | None],
    spy: pd.DataFrame | None,
    mode: str | None = None,
) -> list[Candidate]:
    ticker = ticker.upper()
    fundamentals = fetch_fundamentals(ticker)
    meta = {
        "company": fundamentals.get("company", ""),
        "sector": fundamentals.get("sector", ""),
        "industry": fundamentals.get("industry", ""),
        "market_cap": fundamentals.get("market_cap"),
        "preset": "review",
    }
    candidates: list[Candidate] = []
    modes = [mode] if mode else list(MODES)
    for current in modes:
        if current == "day":
            daily = download(ticker, period="3mo")
            intraday = download(ticker, period="5d", interval="5m", prepost=True)
            candidates.append(
                evaluate_day(
                    ticker, meta, daily, intraday, spy, fundamentals, config, regime
                )
            )
        elif current == "invest":
            daily = download(ticker, period="2y")
            candidates.append(
                evaluate_invest(ticker, meta, daily, spy, fundamentals, config, regime)
            )
        else:
            daily = download(ticker, period="2y")
            sector = sector_context(meta.get("sector", ""), sector_data, spy)
            candidates.append(
                evaluate_swing(
                    ticker, meta, daily, spy, sector, fundamentals, config, regime
                )
            )
    return candidates


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    config = load_config(args.config)
    if args.capital is not None:
        config.setdefault("account", {})["capital"] = args.capital
    capital = config.get("account", {}).get("capital")
    limit = args.limit or int(config.get("scan", {}).get("max_candidates", 60))

    print("Calculando régimen de mercado...")
    regime = compute_regime(config)
    print(f"Regimen: {regime.label} | VIX: {regime.vix}")
    spy = download("SPY", period="2y")

    results: dict[str, ScanResult] = {}
    if args.command == "review":
        if not args.ticker:
            print("Falta el ticker: main.py review NVDA", file=sys.stderr)
            return 2
        sector_data = load_sector_data()
        candidates = _review(
            args.ticker, config, regime, sector_data, spy, args.mode
        )
        for candidate in candidates:
            print(
                f"\n[{candidate.mode}] {candidate.ticker} {candidate.score:.1f} "
                f"{candidate.status}"
            )
            for reason in candidate.reasons:
                print(f"  - {reason}")
        if not args.no_write:
            results = {
                candidate.mode: ScanResult(
                    mode=candidate.mode, candidates=[candidate]
                )
                for candidate in candidates
            }
            budget = risk_budget(config, capital)
            paths = write_reports(results, regime, config, budget, args.output)
            print(f"\nReporte: {paths['plan']}")
        return 0

    modes = list(MODES) if args.command == "plan" else [args.mode or "swing"]
    sector_data = load_sector_data() if "swing" in modes else {}

    for mode in modes:
        print(f"\nEscaneando {mode}...")
        result = _scan_mode(mode, config, regime, limit, sector_data, spy)
        results[mode] = result
        print(
            f"  {len(result.candidates)} candidatos, "
            f"{len(result.actionable)} accionables, {len(result.errors)} errores"
        )

    _print_summary(results, regime)

    if not args.no_write:
        budget = risk_budget(config, capital)
        paths = write_reports(results, regime, config, budget, args.output)
        print(f"\nReporte: {paths['plan']}")
        print(f"CSV: {paths['csv']}")
        print(f"Watchlist: {paths['watchlist']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
