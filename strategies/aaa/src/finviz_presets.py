"""Presets de Finviz equivalentes a los 7 screeners del PDF de swing.

Cada preset replica los filtros del enlace publicado en
`Docs/Finviz screener swing.pdf`. Finviz no expone un filtro directo para
"Sales growth TTM" en esta version de finvizfinance, asi que se inyecta la
clave oficial `fa_salesyoyttm` con las mismas opciones que el resto de
crecimientos. Es una equivalencia documentada, no una copia del método CDI.
"""

from __future__ import annotations

import time
from typing import Any

import pandas as pd
from finvizfinance.constants import filter_dict
from finvizfinance.screener.overview import Overview

_GROWTH_OPTIONS = {
    "Any": "",
    "Negative (<0%)": "neg",
    "Positive (>0%)": "pos",
    "Positive Low (0-10%)": "poslow",
    "High (>25%)": "high",
    "Under 5%": "u5",
    "Under 10%": "u10",
    "Under 15%": "u15",
    "Under 20%": "u20",
    "Under 25%": "u25",
    "Under 30%": "u30",
    "Over 5%": "o5",
    "Over 10%": "o10",
    "Over 15%": "o15",
    "Over 20%": "o20",
    "Over 25%": "o25",
    "Over 30%": "o30",
}


def _ensure_filters() -> None:
    """Completa claves que Finviz soporta pero finvizfinance no lista."""
    if "Sales growth ttm" not in filter_dict:
        filter_dict["Sales growth ttm"] = {
            "prefix": "fa_salesyoyttm",
            "option": dict(_GROWTH_OPTIONS),
        }


PRESETS: dict[str, dict[str, Any]] = {
    "volumen_climatico": {
        "label": "Volumen climatico",
        "description": "Gran capitalizacion, sube hoy/semana/mes con volumen muy superior.",
        "order": "Change",
        "filters": {
            "Market Cap.": "Large ($10bln to $200bln)",
            "Industry": "Stocks only (ex-Funds)",
            "Current Volume": "Over 5M",
            "Relative Volume": "Over 1.5",
            "Change": "Up",
            "Performance": "Week Up",
            "Performance 2": "Month Up",
        },
    },
    "ganadores_semanales": {
        "label": "Ganadores semanales",
        "description": "Subida superior al 20% en la ultima semana con liquidez minima.",
        "order": "Change",
        "filters": {
            "Average Volume": "Over 100K",
            "Price": "Over $5",
            "Performance": "Week +20%",
        },
    },
    "strong_up_trend_1": {
        "label": "Strong up trend 1",
        "description": "Mid/large cap, gap alcista, nuevo máximo de 52 semanas y canal ascendente.",
        "order": "Change",
        "filters": {
            "Market Cap.": "+Mid (over $2bln)",
            "Average Volume": "Over 200K",
            "Price": "Over $10",
            "Relative Volume": "Over 2",
            "Gap": "Up",
            "52-Week High/Low": "New High",
            "Pattern": "Channel Up",
            "RSI (14)": "Overbought (60)",
            "200-Day Simple Moving Average": "Price above SMA200",
        },
    },
    "strong_up_trend_2": {
        "label": "Strong up trend 2",
        "description": "Precio sobre SMA20, SMA50 y SMA200 con volumen relativo > 2.",
        "order": "Performance (Year To Date)",
        "filters": {
            "Market Cap.": "+Mid (over $2bln)",
            "Average Volume": "Over 200K",
            "Price": "Over $10",
            "Relative Volume": "Over 2",
            "20-Day Simple Moving Average": "Price above SMA20",
            "50-Day Simple Moving Average": "Price above SMA50",
            "200-Day Simple Moving Average": "Price above SMA200",
        },
    },
    "strong_up_trend_3": {
        "label": "Strong up trend 3",
        "description": "Nuevos máximos anuales, gap alcista, canal ascendente y RSI > 60.",
        "order": "Change",
        "filters": {
            "Average Volume": "Over 200K",
            "Price": "Over $10",
            "Gap": "Up",
            "52-Week High/Low": "New High",
            "Pattern": "Channel Up",
            "RSI (14)": "Overbought (60)",
            "200-Day Simple Moving Average": "Price above SMA200",
        },
    },
    "momentum": {
        "label": "Momentum",
        "description": "Crecimiento de EPS/ventas, ROE y margen positivos, tendencia alcista.",
        "order": "Performance (Year To Date)",
        "filters": {
            "Market Cap.": "+Small (over $300mln)",
            "EPS growthqtr over qtr": "Over 25%",
            "EPS growth ttm": "Positive (>0%)",
            "Net Profit Margin": "Positive (>0%)",
            "Return on Equity": "Positive (>0%)",
            "Sales growthqtr over qtr": "Over 10%",
            "Sales growth ttm": "Positive (>0%)",
            "Average Volume": "Over 100K",
            "Price": "Over $10",
            "52-Week High/Low": "50% or more above Low",
            "20-Day Simple Moving Average": "SMA20 above SMA50",
            "50-Day Simple Moving Average": "Price above SMA50",
            "200-Day Simple Moving Average": "Price above SMA200",
        },
    },
    "fortaleza_extrema": {
        "label": "Fortaleza extrema",
        "description": "Rendimiento anual y mensual positivo, ATR > 1 y 20% sobre SMA50.",
        "order": "50-Day SMA (Relative)",
        "filters": {
            "Market Cap.": "+Small (over $300mln)",
            "Industry": "Stocks only (ex-Funds)",
            "Average Volume": "Over 200K",
            "Average True Range": "Over 1",
            "52-Week High/Low": "40% or more above Low",
            "Performance": "YTD Up",
            "Performance 2": "Month Up",
            "20-Day Simple Moving Average": "Price above SMA20",
            "200-Day Simple Moving Average": "Price above SMA200",
            "50-Day Simple Moving Average": "Price 20% above SMA50",
        },
    },
}


def preset_filters(name: str) -> dict[str, str]:
    if name not in PRESETS:
        raise KeyError(f"Preset desconocido: {name}")
    return dict(PRESETS[name]["filters"])


def run_preset(name: str, limit: int = 60, sleep_sec: float = 0.8) -> pd.DataFrame:
    """Ejecuta un preset y devuelve sus filas. Vacio si Finviz falla."""
    _ensure_filters()
    preset = PRESETS[name]
    try:
        overview = Overview()
        overview.set_filter(filters_dict=preset["filters"])
        frame = overview.screener_view(
            order=preset.get("order", "Ticker"),
            limit=max(int(limit), 1),
            verbose=0,
            sleep_sec=sleep_sec,
        )
    except Exception as exc:  # pragma: no cover - red / bloqueo de Finviz
        raise RuntimeError(f"Finviz fallo en preset {name}: {exc}") from exc

    if frame is None or frame.empty:
        return pd.DataFrame()
    frame = frame.copy()
    frame["preset"] = name
    return frame


def run_presets(
    names: list[str],
    limit: int = 60,
    sleep_sec: float = 0.8,
    pause: float = 0.6,
) -> tuple[pd.DataFrame, list[str], list[str]]:
    """Ejecuta varios presets y deduplica por ticker conservando el orden.

    Returns:
        (dataframe, errores, notas)
    """
    frames: list[pd.DataFrame] = []
    errors: list[str] = []
    notes: list[str] = []
    for name in names:
        try:
            frame = run_preset(name, limit=limit, sleep_sec=sleep_sec)
        except RuntimeError as exc:
            errors.append(str(exc))
            continue
        if frame.empty:
            notes.append(f"El preset {name} no devolvió resultados.")
        else:
            frames.append(frame)
        time.sleep(pause)

    if not frames:
        return pd.DataFrame(), errors, notes

    combined = pd.concat(frames, ignore_index=True)
    combined["Ticker"] = combined["Ticker"].astype(str).str.upper()
    before = len(combined)
    combined = combined.drop_duplicates(subset=["Ticker"], keep="first")
    removed = before - len(combined)
    if removed == 1:
        notes.append("Se eliminó 1 duplicado entre presets.")
    elif removed:
        notes.append(f"Se eliminaron {removed} duplicados entre presets.")
    return combined.reset_index(drop=True), errors, notes
