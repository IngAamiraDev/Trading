"""Regimen de mercado, features y evaluacion AAA por modo."""

from __future__ import annotations

import math
from datetime import date, time
from typing import Any

import pandas as pd

from .indicators import (
    atr,
    avg_volume,
    last_timestamp,
    last_value,
    pct_change,
    pct_from_high,
    relative_strength,
    rsi,
    slope_pct,
    sma,
    volume_ratio,
)
from .market_data import download, download_many
from .models import Candidate, Regime

SECTOR_ETFS = {
    "Technology": "XLK",
    "Communication Services": "XLC",
    "Healthcare": "XLV",
    "Financial": "XLF",
    "Consumer Cyclical": "XLY",
    "Consumer Defensive": "XLP",
    "Energy": "XLE",
    "Basic Materials": "XLB",
    "Industrials": "XLI",
    "Utilities": "XLU",
    "Real Estate": "XLRE",
}


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------


def _f(value: Any) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(number) or math.isinf(number):
        return None
    return number


def _clamp(value: float, maximum: float) -> float:
    return round(min(max(value, 0.0), maximum), 1)


def _gt(value: float | None, threshold: float) -> bool:
    return value is not None and value > threshold


def _fmt(value: float | None, digits: int = 1, suffix: str = "") -> str:
    if value is None:
        return "n/d"
    return f"{value:.{digits}f}{suffix}"


# ---------------------------------------------------------------------------
# Regimen
# ---------------------------------------------------------------------------


def compute_regime(config: dict[str, Any]) -> Regime:
    regime_cfg = config.get("regime", {})
    fast = int(regime_cfg.get("sma_fast", 50))
    slow = int(regime_cfg.get("sma_slow", 200))
    vix_max = float(regime_cfg.get("vix_max", 25.0))
    symbols = regime_cfg.get("index_symbols", ["SPY", "QQQ"])

    details: dict[str, dict[str, Any]] = {}
    notes: list[str] = []
    for symbol in symbols:
        frame = download(symbol, period="1y")
        if frame is None or len(frame) < slow:
            details[symbol] = {"error": "sin datos suficientes"}
            notes.append(f"{symbol}: sin datos suficientes para SMA{slow}.")
            continue
        close = last_value(frame["Close"])
        fast_ma = sma(frame["Close"], fast)
        slow_ma = sma(frame["Close"], slow)
        details[symbol] = {
            "close": close,
            "sma_fast": fast_ma,
            "sma_slow": slow_ma,
            "above_fast": close is not None and fast_ma is not None and close > fast_ma,
            "above_slow": close is not None and slow_ma is not None and close > slow_ma,
            "last_bar": last_timestamp(frame),
        }

    vix_frame = download(regime_cfg.get("vix_symbol", "^VIX"), period="3mo")
    vix = last_value(vix_frame["Close"]) if vix_frame is not None else None
    if vix is None:
        notes.append("VIX no disponible; el régimen se decide solo con índices.")

    valid = [d for d in details.values() if "error" not in d]
    if not valid:
        label = "neutral"
        notes.append("Sin datos de índices: régimen neutral por precaución.")
    else:
        below_fast = any(not d["above_fast"] for d in valid)
        all_slow = all(d["above_slow"] for d in valid)
        if below_fast or (vix is not None and vix >= vix_max):
            label = "risk_off"
        elif all_slow:
            label = "risk_on"
        else:
            label = "neutral"

    leaders: list[str] = []
    spy = download(symbols[0], period="6mo") if symbols else None
    if spy is not None:
        spy_close = spy["Close"]
        momentum: list[tuple[str, float]] = []
        for sector, etf in SECTOR_ETFS.items():
            frame = download(etf, period="6mo")
            if frame is None:
                continue
            change = pct_change(frame["Close"], 21)
            bench = pct_change(spy_close, 21)
            if change is not None and bench is not None:
                momentum.append((sector, change - bench))
        momentum.sort(key=lambda item: item[1], reverse=True)
        leaders = [f"{name} ({value:+.1f} pp)" for name, value in momentum[:4]]

    return Regime(label=label, vix=vix, indices=details, leaders=leaders, notes=notes)


def load_sector_data(period: str = "9mo") -> dict[str, pd.DataFrame | None]:
    return download_many(list(SECTOR_ETFS.values()), period=period, pause=0.03)


def sector_context(
    sector: str,
    sector_data: dict[str, pd.DataFrame | None],
    spy: pd.DataFrame | None,
) -> dict[str, Any]:
    etf = SECTOR_ETFS.get(sector)
    context: dict[str, Any] = {
        "etf": etf,
        "aligned": None,
        "rs21": None,
        "state": None,
        "note": "",
        "frame": None,
    }
    if not etf:
        context["note"] = "sector sin ETF mapeado"
        return context
    frame = sector_data.get(etf)
    if frame is None or len(frame) < 60:
        context["note"] = f"sin datos de {etf}"
        return context
    close = last_value(frame["Close"])
    fast = sma(frame["Close"], 50)
    slow = sma(frame["Close"], 200) if len(frame) >= 200 else None
    context["close"] = close
    context["sma50"] = fast
    context["sma200"] = slow
    context["aligned"] = bool(
        close is not None
        and fast is not None
        and close > fast
        and (slow is None or close > slow)
    )
    if context["aligned"]:
        context["state"] = "fuerte"
    elif close is not None and fast is not None and close < fast:
        context["state"] = "débil"
    elif close is not None and fast is not None:
        context["state"] = "lateral"
    if spy is not None:
        context["rs21"] = relative_strength(frame["Close"], spy["Close"], 21)
    context["frame"] = frame
    return context


MAX_DAILY_MOVE_PCT = 100.0


def _has_extreme_move(close: pd.Series, periods: int = 21) -> bool:
    """True si la serie dio un salto extremo en un dia (split o dato corrupto).

    Un salto asi hace que la fuerza relativa no sea comparable: mejor no
    informar el numero que informar uno falso.
    """
    if close is None or len(close) < periods + 1:
        return False
    window = close.iloc[-(periods + 1) :]
    moves = window.pct_change().dropna()
    if moves.empty:
        return False
    return bool(moves.abs().max() * 100.0 > MAX_DAILY_MOVE_PCT)


def sector_relative_strength(
    daily: pd.DataFrame | None, sector: dict[str, Any]
) -> tuple[float | None, float | None]:
    """Fuerza relativa de la accion contra el ETF de su sector (1m y 3m).

    Devuelve (None, None) si el run no trae el frame del sector o si la serie
    diaria de la accion tiene un salto extremo (split o dato corrupto), en cuyo
    caso la comparacion no es fiable.
    """
    frame = sector.get("frame")
    if (
        daily is None
        or not isinstance(frame, pd.DataFrame)
        or "Close" not in frame
        or "Close" not in daily
    ):
        return None, None
    if _has_extreme_move(daily["Close"]):
        return None, None
    sector_close = frame["Close"].reindex(daily.index).ffill()
    return (
        relative_strength(daily["Close"], sector_close, 21),
        relative_strength(daily["Close"], sector_close, 63),
    )


# ---------------------------------------------------------------------------
# Features diarios
# ---------------------------------------------------------------------------


def _daily_features(
    daily: pd.DataFrame, spy: pd.DataFrame | None, config: dict[str, Any]
) -> dict[str, Any] | None:
    if daily is None or len(daily) < 60:
        return None
    close_series = daily["Close"]
    close = last_value(close_series)
    if close is None:
        return None

    sma20 = sma(close_series, 20)
    sma50 = sma(close_series, 50)
    sma200 = sma(close_series, 200)
    atr14 = atr(daily, 14)
    rsi14 = rsi(close_series, 14)
    high52 = _f(daily["High"].tail(252).max())
    low52 = _f(daily["Low"].tail(252).min())

    sma200_series = close_series.rolling(200).mean() if len(close_series) >= 200 else None
    sma200_slope = slope_pct(sma200_series, 20) if sma200_series is not None else None

    rs21 = rs63 = None
    extreme_move = _has_extreme_move(close_series)
    if spy is not None and "Close" in spy and not extreme_move:
        aligned_spy = spy["Close"].reindex(close_series.index).ffill()
        rs21 = relative_strength(close_series, aligned_spy, 21)
        rs63 = relative_strength(close_series, aligned_spy, 63)

    pivot = _f(daily["High"].iloc[-21:-1].max()) if len(daily) >= 21 else None
    low10 = _f(daily["Low"].tail(10).min()) if len(daily) >= 10 else None
    rel_vol_yf = volume_ratio(daily, 50)

    return {
        "close": close,
        "sma20": sma20,
        "sma50": sma50,
        "sma200": sma200,
        "sma200_slope": sma200_slope,
        "atr14": atr14,
        "atr_pct": (atr14 / close * 100.0) if atr14 and close else None,
        "rsi14": rsi14,
        "high52": high52,
        "low52": low52,
        "dist_high": pct_from_high(close, high52),
        "rs21": rs21,
        "rs63": rs63,
        "extreme_move": extreme_move,
        "pivot20": pivot,
        "low10": low10,
        "avg_volume50": avg_volume(daily, 50),
        "rel_vol_yf": rel_vol_yf,
        "last_bar": last_timestamp(daily),
        "bars": len(daily),
    }


def _detect_swing_setup(features: dict[str, Any]) -> tuple[str, bool]:
    close = features["close"]
    pivot = features["pivot20"]
    sma20 = features["sma20"]
    sma50 = features["sma50"]
    extended = False
    if pivot and close >= pivot * 0.995:
        extended = close > pivot * 1.05
        return "breakout", extended
    if sma20 and sma50 and close > sma20 and close > sma50 and close <= sma20 * 1.03:
        return "pullback", False
    return "none", False


def _earnings_ok(
    fundamentals: dict[str, Any], blackout_days: int
) -> tuple[bool, str]:
    days = fundamentals.get("earnings_days")
    if days is None:
        return True, "earnings desconocido"
    if 0 <= days <= blackout_days:
        return False, f"earnings en {days} días"
    if days < 0:
        return True, f"earnings hace {abs(days)} días"
    return True, f"earnings en {days} días"


# ---------------------------------------------------------------------------
# Swing
# ---------------------------------------------------------------------------


def evaluate_swing(
    ticker: str,
    meta: dict[str, Any],
    daily: pd.DataFrame | None,
    spy: pd.DataFrame | None,
    sector: dict[str, Any],
    fundamentals: dict[str, Any],
    config: dict[str, Any],
    regime: Regime,
) -> Candidate:
    cfg = config.get("swing", {})
    universe = config.get("universe", {})
    candidate = Candidate(
        ticker=ticker,
        mode="swing",
        company=str(meta.get("company") or fundamentals.get("company") or ""),
        sector=str(meta.get("sector") or fundamentals.get("sector") or ""),
        industry=str(meta.get("industry") or fundamentals.get("industry") or ""),
        source=str(meta.get("preset", "finviz")),
    )
    features = _daily_features(daily, spy, config)
    if features is None:
        candidate.status = "Descartado"
        candidate.reasons.append("sin datos diarios suficientes")
        return candidate

    close = features["close"]
    sma20, sma50, sma200 = features["sma20"], features["sma50"], features["sma200"]
    candidate.price = close
    candidate.last_bar = features["last_bar"]

    setup, extended = _detect_swing_setup(features)
    candidate.setup = setup

    pivot = features["pivot20"] or close
    entry = close
    if setup == "breakout" and not extended:
        entry = max(close, pivot * 1.001)
    entry = round(entry, 2)
    candidate.entry = entry

    atr14 = features["atr14"] or 0.0
    atr_mult = float(cfg.get("atr_multiple", 1.5))
    stop_atr = entry - atr_mult * atr14
    low10 = features["low10"]
    stop = max(low10, stop_atr) if low10 is not None and low10 < entry else stop_atr
    if stop >= entry:
        stop = entry - max(0.01 * entry, atr14 * 0.5)
    stop = round(stop, 2)
    candidate.stop = stop

    risk_per_share = entry - stop
    risk_pct = (risk_per_share / entry * 100.0) if entry else None
    candidate.risk_pct = risk_pct
    target_r = float(cfg.get("target_r", 2.5))
    candidate.target = round(entry + target_r * risk_per_share, 2)
    candidate.rr = round(target_r, 2) if risk_per_share > 0 else None

    max_stop = float(cfg.get("max_stop_pct", 8.0))
    min_rr = float(cfg.get("min_rr", 2.0))
    min_relvol = float(cfg.get("min_rel_volume", 1.5))
    max_dist = float(cfg.get("max_distance_52w_high_pct", 15.0))
    rel_vol = fundamentals.get("rel_volume") or features["rel_vol_yf"]
    earnings_ok, earnings_note = _earnings_ok(
        fundamentals, int(cfg.get("earnings_blackout_days", 5))
    )
    candidate.earnings = fundamentals.get("earnings")

    avg_volume_value = features["avg_volume50"] or fundamentals.get("avg_volume")
    market_cap = _f(meta.get("market_cap")) or fundamentals.get("market_cap")
    universe_ok = (
        close >= float(universe.get("min_price", 10))
        and (avg_volume_value or 0) >= float(universe.get("min_avg_volume", 1_000_000))
        and (market_cap or 0) >= float(universe.get("min_market_cap", 2_000_000_000))
    )

    a1 = (
        regime.label != "risk_off"
        and close > (sma50 or math.inf)
        and close > (sma200 or math.inf)
        and (sma50 or 0) > (sma200 or math.inf)
        and _gt(features["sma200_slope"], 0)
        and sector.get("aligned") is not False
    )

    # Pregunta 3: la accion contra su propio sector (no solo contra SPY).
    rs_sector21, rs_sector63 = sector_relative_strength(daily, sector)
    require_sector_rs = bool(cfg.get("require_sector_rs", True))
    sector_rs_ok = (
        not require_sector_rs or rs_sector21 is None or rs_sector21 > 0
    )

    a2 = (
        _gt(features["rs21"], 0)
        and _gt(features["rs63"], 0)
        and sector_rs_ok
        and features["dist_high"] is not None
        and features["dist_high"] >= -max_dist
        and _gt(rel_vol, min_relvol - 1e-9)
    )
    a3 = (
        setup != "none"
        and risk_pct is not None
        and risk_pct <= max_stop
        and (candidate.rr or 0) >= min_rr
        and earnings_ok
        and universe_ok
    )
    candidate.gates = {"A1": bool(a1), "A2": bool(a2), "A3": bool(a3)}

    # Score: alineación 35, fortaleza 40, entrada/riesgo 25.
    alignment = 0.0
    alignment += {"risk_on": 10.0, "neutral": 6.0, "risk_off": 0.0}[regime.label]
    alignment += 4 if _gt(close, sma20 or math.inf) else 0
    alignment += 4 if (sma20 or 0) > (sma50 or math.inf) else 0
    alignment += 4 if (sma50 or 0) > (sma200 or math.inf) else 0
    alignment += 4 if _gt(features["sma200_slope"], 0) else 0
    alignment += 5 if sector.get("aligned") else 0
    alignment += 4 if _gt(sector.get("rs21"), 0) else 0

    strength = 0.0
    if _gt(features["rs21"], 0):
        strength += 6 + (2 if features["rs21"] > 5 else 0)
    if _gt(features["rs63"], 0):
        strength += 6 + (2 if features["rs63"] > 10 else 0)
    dist = features["dist_high"]
    if dist is not None:
        if dist >= -5:
            strength += 8
        elif dist >= -10:
            strength += 6
        elif dist >= -max_dist:
            strength += 3
    if _gt(rel_vol, min_relvol - 1e-9):
        strength += 6
        if rel_vol >= 2:
            strength += 2
        if rel_vol >= 3:
            strength += 2
    if _gt(rs_sector21, 0):
        strength += 5
        if rs_sector21 > 5:
            strength += 2
    if _gt(fundamentals.get("eps_qoq"), 0):
        strength += 4
    if _gt(fundamentals.get("sales_qoq"), 0):
        strength += 2
    if _gt(fundamentals.get("roe"), 10):
        strength += 2

    entry_score = 0.0
    entry_score += 10 if setup == "breakout" else (7 if setup == "pullback" else 0)
    if risk_pct is not None:
        if risk_pct <= 4:
            entry_score += 8
        elif risk_pct <= 6:
            entry_score += 5
        elif risk_pct <= max_stop:
            entry_score += 3
    if (candidate.rr or 0) >= target_r:
        entry_score += 3
    if daily is not None and len(daily) > 1:
        last_volume = _f(daily["Volume"].iloc[-1])
        avg50 = features["avg_volume50"]
        if last_volume and avg50 and last_volume > avg50:
            entry_score += 4

    candidate.score = (
        _clamp(alignment, 35) + _clamp(strength, 40) + _clamp(entry_score, 25)
    )

    # Motivos
    candidate.reasons.append(f"Setup: {setup}" + (" (extendido)" if extended else ""))
    if sector.get("etf"):
        candidate.reasons.append(
            f"Sector {sector['etf']}: {sector.get('state') or 'sin dato'} | "
            f"RS 1m {_fmt(sector.get('rs21'), 1, ' pp')} vs SPY"
        )
    candidate.reasons.append(f"RS 1m {_fmt(features['rs21'], 1, ' pp')} vs SPY")
    candidate.reasons.append(f"RS 3m {_fmt(features['rs63'], 1, ' pp')} vs SPY")
    if sector.get("etf"):
        candidate.reasons.append(
            f"RS 1m {_fmt(rs_sector21, 1, ' pp')} vs sector"
            f" | 3m {_fmt(rs_sector63, 1, ' pp')} vs sector"
        )
    candidate.reasons.append(f"A {_fmt(dist, 1, '%')} del máximo 52s")
    candidate.reasons.append(f"RelVol {_fmt(rel_vol, 2)}")
    candidate.reasons.append(f"Stop {_fmt(risk_pct, 1, '%')} | R/R {_fmt(candidate.rr, 1)}")
    candidate.reasons.append(earnings_note)
    if features.get("extreme_move"):
        candidate.reasons.append(
            "serie diaria con salto extremo (split o dato corrupto): RS no comparable"
        )
    if not universe_ok:
        candidate.reasons.append("fuera del universo (precio/volumen/calidad)")
    if not a1:
        candidate.reasons.append("A1: falla alineación (mercado, medias o sector)")
    if not a2:
        candidate.reasons.append(
            "A2: falla fuerza relativa (vs SPY o sector), cercanía a máximos o volumen"
        )

    min_score = float(cfg.get("min_score", 70.0))
    watch_score = float(cfg.get("watch_score", 55.0))
    if not (a1 and a2 and a3):
        only_regime = a2 and a3 and regime.label == "risk_off" and candidate.score >= watch_score
        candidate.status = "Vigilancia" if only_regime else "Descartado"
        if only_regime:
            candidate.reasons.append("mercado risk-off: solo vigilancia, sin entrada")
    elif candidate.score >= min_score and not extended:
        candidate.status = "AAA listo"
    elif candidate.score >= watch_score:
        candidate.status = "Vigilancia"
    else:
        candidate.status = "Descartado"

    candidate.metrics = {
        "rs21": features["rs21"],
        "rs63": features["rs63"],
        "dist_high": dist,
        "rel_vol": rel_vol,
        "atr_pct": features["atr_pct"],
        "rsi": features["rsi14"],
        "sector_etf": sector.get("etf"),
        "sector_aligned": sector.get("aligned"),
        "sector_state": sector.get("state"),
        "sector_rs21": sector.get("rs21"),
        "rs_sector21": rs_sector21,
        "rs_sector63": rs_sector63,
        "extreme_move": bool(features.get("extreme_move")),
        "pivot20": pivot,
        "low10": low10,
        "extended": extended,
        "market_cap": market_cap,
        "bloques": {
            "alineación": _clamp(alignment, 35),
            "fortaleza": _clamp(strength, 40),
            "entrada": _clamp(entry_score, 25),
        },
    }
    return candidate


# ---------------------------------------------------------------------------
# Inversion
# ---------------------------------------------------------------------------


def evaluate_invest(
    ticker: str,
    meta: dict[str, Any],
    daily: pd.DataFrame | None,
    spy: pd.DataFrame | None,
    fundamentals: dict[str, Any],
    config: dict[str, Any],
    regime: Regime,
    sector: dict[str, Any] | None = None,
) -> Candidate:
    cfg = config.get("invest", {})
    universe = config.get("universe", {})
    candidate = Candidate(
        ticker=ticker,
        mode="invest",
        company=str(meta.get("company") or fundamentals.get("company") or ""),
        sector=str(meta.get("sector") or fundamentals.get("sector") or ""),
        industry=str(meta.get("industry") or fundamentals.get("industry") or ""),
        source=str(meta.get("preset", "finviz")),
    )
    features = _daily_features(daily, spy, config)
    if features is None:
        candidate.status = "Reject"
        candidate.reasons.append("sin datos diarios suficientes")
        return candidate
    if not fundamentals:
        candidate.status = "Reject"
        candidate.reasons.append("sin fundamentales verificables")
        return candidate

    close = features["close"]
    candidate.price = close
    candidate.last_bar = features["last_bar"]
    candidate.setup = "tendencia + calidad"

    roe = fundamentals.get("roe")
    net_margin = fundamentals.get("net_margin")
    eps_qoq = fundamentals.get("eps_qoq")
    sales_qoq = fundamentals.get("sales_qoq")
    eps_yoy = fundamentals.get("eps_yoy")
    sales_yoy = fundamentals.get("sales_yoy")
    debt = fundamentals.get("debt_equity")
    peg = fundamentals.get("peg")
    pfcf = fundamentals.get("pfcf")
    ev_ebitda = fundamentals.get("ev_ebitda")

    financial = candidate.sector in {"Financial", "Financial Services"} or "REIT" in candidate.industry
    growth_ok = (
        (eps_qoq is not None and eps_qoq >= float(cfg.get("min_eps_qoq_pct", 10)))
        or (eps_yoy is not None and eps_yoy >= float(cfg.get("min_eps_yoy_pct", 5)))
    )
    sales_ok = sales_qoq is None or sales_qoq >= float(cfg.get("min_sales_qoq_pct", 5))
    quality_ok = (
        roe is not None
        and roe >= float(cfg.get("min_roe_pct", 10))
        and net_margin is not None
        and net_margin >= float(cfg.get("min_net_margin_pct", 5))
        and growth_ok
        and sales_ok
        and (financial or debt is None or debt <= float(cfg.get("max_debt_equity", 1.5)))
    )

    avg_volume_value = features["avg_volume50"] or fundamentals.get("avg_volume")
    market_cap = _f(meta.get("market_cap")) or fundamentals.get("market_cap")
    universe_ok = (
        close >= float(universe.get("invest_min_price", 10))
        and (avg_volume_value or 0) >= float(universe.get("invest_min_avg_volume", 500_000))
        and (market_cap or 0) >= float(universe.get("min_market_cap", 2_000_000_000))
    )

    earnings_ok, earnings_note = _earnings_ok(
        fundamentals, int(cfg.get("earnings_blackout_days", 3))
    )
    candidate.earnings = fundamentals.get("earnings")

    sector = sector or {}
    rs_sector21, rs_sector63 = sector_relative_strength(daily, sector)

    trend_ok = (
        regime.label != "risk_off"
        and close > (features["sma200"] or math.inf)
        and (features["sma50"] or 0) > (features["sma200"] or math.inf)
        and features["dist_high"] is not None
        and features["dist_high"] >= -float(cfg.get("max_distance_52w_high_pct", 25))
        and sector.get("aligned") is not False
    )
    candidate.gates = {
        "A1": bool(trend_ok),
        "A2": bool(quality_ok),
        "A3": bool(universe_ok and earnings_ok),
    }

    quality = 0.0
    if roe is not None:
        quality += 10 if roe >= 20 else (8 if roe >= 15 else (6 if roe >= 10 else 0))
    if net_margin is not None:
        quality += 8 if net_margin >= 20 else (6 if net_margin >= 10 else (4 if net_margin >= 5 else 0))
    if financial:
        quality += 5
    elif debt is not None:
        quality += 6 if debt <= 0.5 else (4 if debt <= 1.0 else (2 if debt <= 1.5 else 0))
    quality += 6 if _gt(fundamentals.get("roic"), 10) else 0
    if pfcf is not None and pfcf > 0:
        quality += 5 if pfcf <= 30 else (3 if pfcf <= 50 else 1)

    growth = 0.0
    if eps_qoq is not None:
        growth += 8 if eps_qoq >= 25 else (6 if eps_qoq >= 10 else (4 if eps_qoq > 0 else 0))
    if sales_qoq is not None:
        growth += 7 if sales_qoq >= 15 else (5 if sales_qoq >= 5 else (3 if sales_qoq > 0 else 0))
    if eps_yoy is not None:
        growth += 5 if eps_yoy >= 15 else (3 if eps_yoy >= 5 else 0)
    growth += 5 if _gt(sales_yoy, 0) else 0

    valuation = 0.0
    if peg is not None and peg > 0:
        valuation += 8 if peg <= 1 else (5 if peg <= 2 else 2)
    else:
        valuation += 3
    if pfcf is not None and pfcf > 0:
        valuation += 6 if pfcf <= 20 else (4 if pfcf <= 35 else (2 if pfcf <= 50 else 0))
    if ev_ebitda is not None and ev_ebitda > 0:
        valuation += 6 if ev_ebitda <= 15 else (4 if ev_ebitda <= 25 else 0)

    trend = 0.0
    trend += 5 if _gt(close, features["sma200"] or math.inf) else 0
    trend += 4 if (features["sma50"] or 0) > (features["sma200"] or math.inf) else 0
    trend += 3 if _gt(features["rs63"], 0) else 0
    trend += 3 if (features["dist_high"] is not None and features["dist_high"] >= -10) else 0

    candidate.score = (
        _clamp(quality, 40) + _clamp(growth, 25) + _clamp(valuation, 20) + _clamp(trend, 15)
    )

    stop_pct = float(cfg.get("stop_pct", 15.0))
    candidate.entry = round(close, 2)
    candidate.stop = round(close * (1 - stop_pct / 100.0), 2)
    candidate.target = round(close * (1 + 2 * stop_pct / 100.0), 2)
    candidate.risk_pct = stop_pct
    candidate.rr = 2.0

    candidate.reasons.append(f"ROE {_fmt(roe, 1, '%')} | margen {_fmt(net_margin, 1, '%')}")
    candidate.reasons.append(f"EPS Q/Q {_fmt(eps_qoq, 1, '%')} | ventas Q/Q {_fmt(sales_qoq, 1, '%')}")
    candidate.reasons.append(f"Deuda/Equity {_fmt(debt, 2)}")
    candidate.reasons.append(f"PEG {_fmt(peg, 2)} | P/FCF {_fmt(pfcf, 1)} | EV/EBITDA {_fmt(ev_ebitda, 1)}")
    if sector.get("etf"):
        candidate.reasons.append(
            f"Sector {sector['etf']}: {sector.get('state') or 'sin dato'} | "
            f"RS 1m {_fmt(sector.get('rs21'), 1, ' pp')} vs SPY"
        )
        candidate.reasons.append(
            f"RS 1m {_fmt(rs_sector21, 1, ' pp')} vs sector"
            f" | 3m {_fmt(rs_sector63, 1, ' pp')} vs sector"
        )
    candidate.reasons.append(earnings_note)
    if not quality_ok:
        candidate.reasons.append("A2: falla la puerta de calidad")
    if not trend_ok:
        candidate.reasons.append("A1: tendencia o régimen no alineado")

    min_score = float(cfg.get("min_score", 75.0))
    watch_score = float(cfg.get("watch_score", 55.0))
    gates_ok = candidate.gates["A1"] and candidate.gates["A2"] and candidate.gates["A3"]
    if not gates_ok:
        only_regime = (
            candidate.gates["A2"]
            and candidate.gates["A3"]
            and regime.label == "risk_off"
            and candidate.score >= watch_score
        )
        candidate.status = "Watch" if only_regime else "Reject"
        if only_regime:
            candidate.reasons.append("mercado risk-off: solo vigilancia")
    elif candidate.score >= min_score:
        candidate.status = "Core"
    elif candidate.score >= watch_score:
        candidate.status = "Watch"
    else:
        candidate.status = "Reject"

    candidate.metrics = {
        "roe": roe,
        "net_margin": net_margin,
        "eps_qoq": eps_qoq,
        "sales_qoq": sales_qoq,
        "eps_yoy": eps_yoy,
        "sales_yoy": sales_yoy,
        "debt_equity": debt,
        "peg": peg,
        "pfcf": pfcf,
        "ev_ebitda": ev_ebitda,
        "rs63": features["rs63"],
        "dist_high": features["dist_high"],
        "market_cap": market_cap,
        "sector_etf": sector.get("etf"),
        "sector_aligned": sector.get("aligned"),
        "sector_state": sector.get("state"),
        "sector_rs21": sector.get("rs21"),
        "rs_sector21": rs_sector21,
        "rs_sector63": rs_sector63,
        "extreme_move": bool(features.get("extreme_move")),
        "bloques": {
            "calidad": _clamp(quality, 40),
            "crecimiento": _clamp(growth, 25),
            "valoracion": _clamp(valuation, 20),
            "tendencia": _clamp(trend, 15),
        },
    }
    return candidate


# ---------------------------------------------------------------------------
# Day trading
# ---------------------------------------------------------------------------


def _session_slice(
    intraday: pd.DataFrame | None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame] | None:
    """Devuelve (sesión regular, premarket, todas las barras de la sesión)."""
    if intraday is None or len(intraday) == 0:
        return None
    frame = intraday.copy()
    if getattr(frame.index, "tz", None) is not None:
        frame.index = frame.index.tz_convert("America/New_York")
    dates = sorted({ts.date() for ts in frame.index})
    session_date = None
    regular = None
    for day_value in reversed(dates):
        day_bars = frame[[ts.date() == day_value for ts in frame.index]]
        mask = pd.Series(
            [(t.time() >= time(9, 30) and t.time() <= time(16, 0)) for t in day_bars.index],
            index=day_bars.index,
        )
        candidate = day_bars[mask]
        if len(candidate) >= 3:
            session_date = day_value
            regular = candidate
            break
    if session_date is None or regular is None:
        return None
    day_bars = frame[[ts.date() == session_date for ts in frame.index]]
    premarket = day_bars[
        pd.Series(
            [(t.time() >= time(4, 0) and t.time() < time(9, 30)) for t in day_bars.index],
            index=day_bars.index,
        )
    ]
    return regular, premarket, day_bars


def evaluate_day(
    ticker: str,
    meta: dict[str, Any],
    daily: pd.DataFrame | None,
    intraday: pd.DataFrame | None,
    spy: pd.DataFrame | None,
    fundamentals: dict[str, Any],
    config: dict[str, Any],
    regime: Regime,
    sector: dict[str, Any] | None = None,
) -> Candidate:
    cfg = config.get("day", {})
    candidate = Candidate(
        ticker=ticker,
        mode="day",
        company=str(meta.get("company") or fundamentals.get("company") or ""),
        sector=str(meta.get("sector") or fundamentals.get("sector") or ""),
        industry=str(meta.get("industry") or fundamentals.get("industry") or ""),
        source=str(meta.get("preset", "finviz")),
    )
    if daily is None or len(daily) < 20:
        candidate.reasons.append("sin datos diarios suficientes")
        return candidate
    sector = sector or {}
    rs_sector21, rs_sector63 = sector_relative_strength(daily, sector)
    session = _session_slice(intraday)
    if session is None:
        candidate.reasons.append("sin barras intradía suficientes")
        return candidate
    regular, premarket, _ = session
    close = last_value(regular["Close"])
    candidate.price = close
    candidate.last_bar = last_timestamp(regular)

    session_date = regular.index[0].date()
    daily_dates = [ts.date() for ts in daily.index]
    history = daily[[day_value < session_date for day_value in daily_dates]]
    if len(history) < 20:
        history = daily
    prev_close = _f(history["Close"].iloc[-1]) if len(history) else None
    if prev_close is None:
        candidate.reasons.append("sin cierre previo")
        return candidate

    session_open = _f(regular["Open"].iloc[0]) or close
    gap_pct = (session_open / prev_close - 1.0) * 100.0 if prev_close else None
    gap_anomaly = gap_pct is not None and abs(gap_pct) > 50.0
    if gap_anomaly:
        candidate.reasons.append("gap anómalo (>50%): posible split o dato corrupto")
    pre_high = _f(premarket["High"].max()) if len(premarket) else _f(regular["High"].iloc[0])
    pre_low = _f(premarket["Low"].min()) if len(premarket) else _f(regular["Low"].iloc[0])
    day_high = _f(regular["High"].max())
    day_low = _f(regular["Low"].min())

    typical = (regular["High"] + regular["Low"] + regular["Close"]) / 3.0
    cumulative_volume = regular["Volume"].cumsum()
    vwap_series = (typical * regular["Volume"]).cumsum() / cumulative_volume.where(
        cumulative_volume != 0
    )
    vwap = _f(vwap_series.iloc[-1])

    avg_daily = avg_volume(history, 50) or fundamentals.get("avg_volume")
    last_time = regular.index[-1]
    elapsed = max(
        5,
        min(
            390,
            (last_time.hour * 60 + last_time.minute) - (9 * 60 + 30),
        ),
    )
    expected_volume = (avg_daily or 0) * elapsed / 390.0
    today_volume = _f(regular["Volume"].sum())
    rel_vol = (today_volume / expected_volume) if expected_volume else None
    if fundamentals.get("rel_volume") and rel_vol is None:
        rel_vol = fundamentals.get("rel_volume")

    atr14 = atr(history, 14) or (close * 0.02 if close else 0.0)
    atr_mult = float(cfg.get("atr_multiple", 1.0))
    if close > (pre_high or math.inf):
        setup = "breakout premarket"
        entry = close
    elif vwap is not None and close > vwap:
        setup = "reclaim VWAP"
        entry = close
    else:
        setup = "none"
        entry = close
    entry = round(entry, 2)
    candidate.setup = setup
    candidate.entry = entry

    stop = pre_low if pre_low and pre_low < entry else entry - atr_mult * atr14
    if not stop or stop >= entry:
        stop = entry - max(atr14 * atr_mult, entry * 0.005)
    stop = round(stop, 2)
    candidate.stop = stop
    risk_per_share = entry - stop
    risk_pct = (risk_per_share / entry * 100.0) if entry else None
    candidate.risk_pct = risk_pct
    target_r = float(cfg.get("target_r", 2.0))
    candidate.target = round(entry + target_r * risk_per_share, 2)
    candidate.rr = round(target_r, 2) if risk_per_share > 0 else None

    earnings_ok, earnings_note = _earnings_ok(
        fundamentals, int(cfg.get("earnings_blackout_days", 1))
    )
    candidate.earnings = fundamentals.get("earnings")

    universe = config.get("universe", {})
    universe_ok = (
        close >= float(universe.get("day_min_price", 5))
        and (avg_daily or 0) >= float(universe.get("day_min_avg_volume", 2_000_000))
    )

    min_gap = float(cfg.get("min_gap_pct", 2.0))
    max_gap = float(cfg.get("max_gap_pct", 10.0))
    min_relvol = float(cfg.get("min_rel_volume", 3.0))
    min_rr = float(cfg.get("min_rr", 1.5))
    max_stop = float(cfg.get("max_stop_pct", 5.0))
    vix_limit = float(config.get("regime", {}).get("day_vix_max", 28.0))

    vwap_ok = vwap is not None and close > vwap
    a1 = (
        regime.label != "risk_off"
        and (regime.vix is None or regime.vix < vix_limit)
        and vwap_ok
    )
    a2 = (
        gap_pct is not None
        and not gap_anomaly
        and min_gap <= gap_pct <= max_gap
        and _gt(rel_vol, min_relvol - 1e-9)
        and (setup != "none")
    )
    a3 = (
        setup != "none"
        and risk_pct is not None
        and risk_pct <= max_stop
        and (candidate.rr or 0) >= min_rr
        and earnings_ok
        and universe_ok
    )
    candidate.gates = {"A1": bool(a1), "A2": bool(a2), "A3": bool(a3)}

    alignment = 0.0
    alignment += {"risk_on": 10.0, "neutral": 5.0, "risk_off": 0.0}[regime.label]
    alignment += 8 if vwap_ok else 0
    alignment += 7 if (pre_high and close > pre_high) else 0

    strength = 0.0
    if gap_pct is not None:
        if 4 <= gap_pct <= 7:
            strength += 12
        elif 2 <= gap_pct < 4:
            strength += 10
        elif 7 < gap_pct <= 10:
            strength += 8
    if rel_vol is not None:
        if rel_vol >= 3:
            strength += 10
        if rel_vol >= 5:
            strength += 5
        if rel_vol >= 10:
            strength += 5
    change_today = (close / prev_close - 1.0) * 100.0 if close and prev_close else None
    strength += 8 if _gt(change_today, 0) else 0
    strength += 5 if (day_high and close >= day_high * 0.995) else 0
    strength += 5 if (_gt(fundamentals.get("rel_volume"), 2)) else 0

    entry_score = 0.0
    entry_score += 15 if setup == "breakout premarket" else (10 if setup == "reclaim VWAP" else 0)
    if risk_pct is not None:
        if risk_pct <= 2:
            entry_score += 8
        elif risk_pct <= 3.5:
            entry_score += 5
        elif risk_pct <= max_stop:
            entry_score += 3
    if (candidate.rr or 0) >= target_r:
        entry_score += 4
    entry_score += 3 if vwap_ok else 0

    candidate.score = (
        _clamp(alignment, 25) + _clamp(strength, 45) + _clamp(entry_score, 30)
    )

    candidate.reasons.append(f"Gap {_fmt(gap_pct, 2, '%')} | RelVol {_fmt(rel_vol, 2)}")
    candidate.reasons.append(f"VWAP {_fmt(vwap, 2)} | PM high {_fmt(pre_high, 2)} | PM low {_fmt(pre_low, 2)}")
    candidate.reasons.append(f"Stop {_fmt(risk_pct, 2, '%')} | R/R {_fmt(candidate.rr, 1)}")
    if sector.get("etf"):
        candidate.reasons.append(
            f"Sector {sector['etf']}: {sector.get('state') or 'sin dato'} | "
            f"RS 1m {_fmt(sector.get('rs21'), 1, ' pp')} vs SPY"
        )
    if _has_extreme_move(daily["Close"]):
        candidate.reasons.append(
            "serie diaria con salto extremo (split o dato corrupto): RS no comparable"
        )
    candidate.reasons.append(earnings_note)
    if not a1:
        candidate.reasons.append("A1: régimen o VWAP no alineado")
    if not a2:
        candidate.reasons.append("A2: gap, volumen relativo o setup insuficiente")
    if not universe_ok:
        candidate.reasons.append("fuera del universo intradía (precio/volumen)")

    min_score = float(cfg.get("min_score", 65.0))
    watch_score = float(cfg.get("watch_score", 50.0))
    if not (a1 and a2 and a3):
        only_regime = (
            a2 and a3 and regime.label == "risk_off" and candidate.score >= watch_score
        )
        candidate.status = "Vigilancia" if only_regime else "Descartado"
        if only_regime:
            candidate.reasons.append("mercado risk-off: solo vigilancia")
    elif candidate.score >= min_score and setup != "none":
        candidate.status = "Listo"
    elif candidate.score >= watch_score:
        candidate.status = "Vigilancia"
    else:
        candidate.status = "Descartado"

    candidate.metrics = {
        "gap_pct": gap_pct,
        "gap_anomaly": gap_anomaly,
        "rel_vol": rel_vol,
        "vwap": vwap,
        "pre_high": pre_high,
        "pre_low": pre_low,
        "day_high": day_high,
        "day_low": day_low,
        "atr": atr14,
        "change_today": change_today,
        "sector_etf": sector.get("etf"),
        "sector_aligned": sector.get("aligned"),
        "sector_state": sector.get("state"),
        "sector_rs21": sector.get("rs21"),
        "rs_sector21": rs_sector21,
        "rs_sector63": rs_sector63,
        "extreme_move": bool(_has_extreme_move(daily["Close"])) if daily is not None else False,
        "bloques": {
            "alineación": _clamp(alignment, 25),
            "fortaleza": _clamp(strength, 45),
            "entrada": _clamp(entry_score, 30),
        },
    }
    return candidate
