"""Indicadores tecnicos sin dependencias externas mas alla de pandas/numpy."""

from __future__ import annotations

import math

import pandas as pd


def _clean(value: float | int | None) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(number) or math.isinf(number):
        return None
    return number


def sma(series: pd.Series, period: int) -> float | None:
    if series is None or len(series) < period:
        return None
    return _clean(series.rolling(period).mean().iloc[-1])


def ema(series: pd.Series, period: int) -> float | None:
    if series is None or len(series) < period:
        return None
    return _clean(series.ewm(span=period, adjust=False).mean().iloc[-1])


def atr(df: pd.DataFrame, period: int = 14) -> float | None:
    """Average True Range clasico (Wilder simplificado con media simple)."""
    if df is None or len(df) < period + 1:
        return None
    high = df["High"]
    low = df["Low"]
    prev_close = df["Close"].shift(1)
    ranges = pd.concat(
        [
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return _clean(ranges.rolling(period).mean().iloc[-1])


def rsi(series: pd.Series, period: int = 14) -> float | None:
    if series is None or len(series) < period + 1:
        return None
    delta = series.diff()
    gains = delta.clip(lower=0).rolling(period).mean()
    losses = (-delta.clip(upper=0)).rolling(period).mean()
    last_loss = _clean(losses.iloc[-1])
    last_gain = _clean(gains.iloc[-1])
    if last_loss is None or last_gain is None:
        return None
    if last_loss == 0:
        return 100.0 if last_gain > 0 else 50.0
    rs = last_gain / last_loss
    return _clean(100 - (100 / (1 + rs)))


def avg_volume(df: pd.DataFrame, days: int) -> float | None:
    if df is None or len(df) == 0:
        return None
    return _clean(df["Volume"].tail(days).mean())


def pct_change(series: pd.Series, periods: int) -> float | None:
    """Variacion porcentual entre el ultimo valor y el de hace N barras."""
    if series is None or len(series) <= periods:
        return None
    end = _clean(series.iloc[-1])
    start = _clean(series.iloc[-1 - periods])
    if end is None or start in (None, 0):
        return None
    return (end / start - 1.0) * 100.0


def relative_strength(
    series: pd.Series, benchmark: pd.Series, periods: int
) -> float | None:
    """Diferencia de rentabilidad (activo - benchmark) en puntos porcentuales."""
    asset = pct_change(series, periods)
    bench = pct_change(benchmark, periods)
    if asset is None or bench is None:
        return None
    return asset - bench


def pct_from_high(close: float | None, high: float | None) -> float | None:
    """Distancia porcentual al máximo (negativa si está por debajo)."""
    if close is None or not high:
        return None
    return (close / high - 1.0) * 100.0


def slope_pct(series: pd.Series, periods: int = 20) -> float | None:
    """Pendiente relativa de una media movil en las ultimas N barras."""
    if series is None or len(series) <= periods:
        return None
    end = _clean(series.iloc[-1])
    start = _clean(series.iloc[-1 - periods])
    if end is None or start in (None, 0):
        return None
    return (end / start - 1.0) * 100.0


def last_value(series: pd.Series) -> float | None:
    if series is None or len(series) == 0:
        return None
    return _clean(series.iloc[-1])


def last_timestamp(df: pd.DataFrame) -> str | None:
    if df is None or len(df) == 0:
        return None
    try:
        return pd.Timestamp(df.index[-1]).isoformat()
    except Exception:  # pragma: no cover - indices exoticos
        return None


def volume_ratio(df: pd.DataFrame, days: int = 50) -> float | None:
    if df is None or len(df) < 2:
        return None
    current = _clean(df["Volume"].iloc[-1])
    average = avg_volume(df.iloc[:-1], days)
    if current is None or not average:
        return None
    return current / average
