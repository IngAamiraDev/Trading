"""Descarga de datos de mercado y fundamentales con cache simple."""

from __future__ import annotations

import json
import math
import re
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd
import yfinance as yf

from .config import CACHE_DIR

_PRICE_CACHE: dict[tuple, pd.DataFrame | None] = {}
_FUNDAMENTAL_CACHE: dict[str, tuple[datetime, dict[str, Any]]] = {}
_CACHE_FILE = CACHE_DIR / "fundamentals.json"


# ---------------------------------------------------------------------------
# Series de precios (yfinance)
# ---------------------------------------------------------------------------


def _normalize_frame(df: pd.DataFrame | None) -> pd.DataFrame | None:
    if df is None or len(df) == 0:
        return None
    if isinstance(df.columns, pd.MultiIndex):
        # yfinance devuelve (campo, ticker) para un solo simbolo.
        df = df.copy()
        df.columns = df.columns.get_level_values(0)
    df = df[~df.index.duplicated(keep="last")]
    required = {"Open", "High", "Low", "Close", "Volume"}
    if not required.issubset(df.columns):
        return None
    return df.sort_index()


def download(
    ticker: str,
    period: str = "2y",
    interval: str = "1d",
    prepost: bool = False,
    retries: int = 2,
) -> pd.DataFrame | None:
    """Descarga OHLCV y normaliza el DataFrame. Devuelve None si falla."""
    key = (ticker.upper(), period, interval, prepost)
    if key in _PRICE_CACHE:
        return _PRICE_CACHE[key]

    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            frame = yf.download(
                ticker,
                period=period,
                interval=interval,
                auto_adjust=True,
                progress=False,
                prepost=prepost,
                threads=False,
                timeout=15,
            )
            frame = _normalize_frame(frame)
            if frame is not None and len(frame) > 0:
                _PRICE_CACHE[key] = frame
                return frame
        except Exception as exc:  # pragma: no cover - red
            last_error = exc
        time.sleep(0.4 * (attempt + 1))

    if last_error is not None:
        _PRICE_CACHE[key] = None
    return None


def download_many(
    tickers: list[str],
    period: str = "1y",
    interval: str = "1d",
    pause: float = 0.05,
) -> dict[str, pd.DataFrame | None]:
    data: dict[str, pd.DataFrame | None] = {}
    for ticker in tickers:
        data[ticker] = download(ticker, period=period, interval=interval)
        if pause:
            time.sleep(pause)
    return data


# ---------------------------------------------------------------------------
# Fundamentales (finvizfinance)
# ---------------------------------------------------------------------------


def _load_disk_cache() -> None:
    if not _CACHE_FILE.exists():
        return
    try:
        payload = json.loads(_CACHE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return
    for ticker, entry in payload.items():
        try:
            stamp = datetime.fromisoformat(entry["timestamp"])
            _FUNDAMENTAL_CACHE[ticker] = (stamp, entry["data"])
        except (KeyError, TypeError, ValueError):
            continue


def _save_disk_cache() -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        ticker: {"timestamp": stamp.isoformat(), "data": data}
        for ticker, (stamp, data) in _FUNDAMENTAL_CACHE.items()
    }
    try:
        _CACHE_FILE.write_text(json.dumps(payload), encoding="utf-8")
    except OSError:  # pragma: no cover - disco
        pass


def fetch_fundamentals(
    ticker: str, ttl_minutes: int = 360, use_cache: bool = True
) -> dict[str, Any]:
    """Devuelve fundamentales normalizados de Finviz. {} si no hay datos."""
    ticker = ticker.upper()
    if use_cache:
        if not _FUNDAMENTAL_CACHE:
            _load_disk_cache()
        cached = _FUNDAMENTAL_CACHE.get(ticker)
        if cached:
            stamp, data = cached
            if datetime.now() - stamp < timedelta(minutes=ttl_minutes):
                return data

    raw: dict[str, Any] = {}
    try:
        from finvizfinance.quote import finvizfinance

        raw = finvizfinance(ticker).ticker_fundament() or {}
    except Exception:  # pragma: no cover - red / rate limit
        raw = {}

    data = normalize_fundamentals(raw)
    if data:
        _FUNDAMENTAL_CACHE[ticker] = (datetime.now(), data)
        _save_disk_cache()
    return data


def _parse_number(text: Any) -> float | None:
    if text is None:
        return None
    if isinstance(text, (int, float)):
        value = float(text)
        return None if math.isnan(value) else value
    match = re.search(r"-?\d+(?:[.,]\d+)?", str(text).replace(",", ""))
    if not match:
        return None
    try:
        return float(match.group(0))
    except ValueError:
        return None


def _parse_pct(text: Any) -> float | None:
    value = _parse_number(text)
    return value


def _parse_money(text: Any) -> float | None:
    """Convierte '5090.19B' o '850M' a dolares."""
    if text is None:
        return None
    raw = str(text).strip().upper().replace(",", "")
    match = re.search(r"(-?\d+(?:\.\d+)?)\s*([KMBT])?", raw)
    if not match:
        return None
    value = float(match.group(1))
    suffix = match.group(2)
    factors = {"K": 1e3, "M": 1e6, "B": 1e9, "T": 1e12}
    return value * factors.get(suffix, 1.0)


def _parse_earnings(text: Any, today: date | None = None) -> tuple[str | None, int | None]:
    """Devuelve (fecha ISO, días hasta earnings). None si no se puede parsear."""
    if text is None:
        return None, None
    raw = str(text).strip()
    if not raw:
        return None, None
    today = today or date.today()

    # Formatos ISO o "Nov 02 AMC".
    cleaned = re.sub(r"\b(AMC|BMO|TAS|TNS|After Market Close|Before Market Open)\b", "", raw, flags=re.I).strip()
    for fmt in ("%Y-%m-%d", "%b %d %Y", "%b %d", "%B %d %Y", "%B %d"):
        try:
            parsed = datetime.strptime(cleaned, fmt).date()
        except ValueError:
            continue
        if "%Y" not in fmt:
            parsed = parsed.replace(year=today.year)
            # Finviz muestra la proxima fecha; si quedo muy atras, es del ano siguiente.
            if parsed < today - timedelta(days=7):
                parsed = parsed.replace(year=today.year + 1)
        return parsed.isoformat(), (parsed - today).days
    return None, None


def normalize_fundamentals(raw: dict[str, Any]) -> dict[str, Any]:
    if not raw:
        return {}
    earnings_iso, earnings_days = _parse_earnings(raw.get("Earnings"))
    return {
        "company": raw.get("Company", ""),
        "sector": raw.get("Sector", ""),
        "industry": raw.get("Industry", ""),
        "market_cap": _parse_money(raw.get("Market Cap")),
        "eps_qoq": _parse_pct(raw.get("EPS Q/Q")),
        "sales_qoq": _parse_pct(raw.get("Sales Q/Q")),
        "eps_yoy": _parse_pct(raw.get("EPS Y/Y TTM")),
        "sales_yoy": _parse_pct(raw.get("Sales Y/Y TTM")),
        "roe": _parse_pct(raw.get("ROE")),
        "roic": _parse_pct(raw.get("ROIC")),
        "net_margin": _parse_pct(raw.get("Profit Margin")),
        "debt_equity": _parse_pct(raw.get("Debt/Eq")),
        "pe": _parse_pct(raw.get("P/E")),
        "peg": _parse_pct(raw.get("PEG")),
        "pfcf": _parse_pct(raw.get("P/FCF")),
        "ev_ebitda": _parse_pct(raw.get("EV/EBITDA")),
        "high_52w": _parse_number(raw.get("52W High")),
        "atr": _parse_pct(raw.get("ATR (14)")),
        "rel_volume": _parse_pct(raw.get("Rel Volume")),
        "avg_volume": _parse_money(raw.get("Avg Volume")),
        "sma20": _parse_number(raw.get("SMA20")),
        "sma50": _parse_number(raw.get("SMA50")),
        "sma200": _parse_number(raw.get("SMA200")),
        "perf_month": _parse_pct(raw.get("Perf Month")),
        "perf_quarter": _parse_pct(raw.get("Perf Quarter")),
        "perf_ytd": _parse_pct(raw.get("Perf YTD")),
        "earnings": earnings_iso,
        "earnings_days": earnings_days,
        "earnings_raw": raw.get("Earnings"),
        "raw_keys": sorted(raw.keys()),
    }


def quote_snapshot(ticker: str) -> dict[str, Any]:
    """Precio y metadatos rapidos usando yfinance (fallback de Finviz)."""
    frame = download(ticker, period="5d")
    fundamentals = fetch_fundamentals(ticker)
    if frame is None:
        return fundamentals
    snapshot = dict(fundamentals)
    snapshot.setdefault("sector", "")
    snapshot.setdefault("industry", "")
    snapshot["company"] = snapshot.get("company") or ""
    return snapshot
