"""Gestión de riesgo: tamaño de posición y límites de cartera."""

from __future__ import annotations

import math
from typing import Any

from .models import Candidate, Regime


def position_size(
    capital: float | None,
    risk_pct: float,
    entry: float | None,
    stop: float | None,
) -> int | None:
    """Numero entero de acciones para arriesgar `risk_pct` del capital."""
    if not capital or capital <= 0 or not entry or not stop:
        return None
    risk_per_share = entry - stop
    if risk_per_share <= 0:
        return None
    risk_amount = capital * (risk_pct / 100.0)
    shares = math.floor(risk_amount / risk_per_share)
    return max(shares, 0)


def risk_budget(config: dict[str, Any], capital: float | None) -> dict[str, Any]:
    account = config.get("account", {})
    risk_pct = float(account.get("risk_per_trade_pct", 0.5))
    max_open = float(account.get("max_open_risk_pct", 2.0))
    budget = {
        "capital": capital,
        "risk_per_trade_pct": risk_pct,
        "max_open_risk_pct": max_open,
        "risk_per_trade_usd": (capital * risk_pct / 100.0) if capital else None,
        "max_open_risk_usd": (capital * max_open / 100.0) if capital else None,
        "max_positions_by_risk": (
            int(max_open // risk_pct) if risk_pct > 0 else None
        ),
        "max_positions_per_mode": account.get("max_positions_per_mode", {}),
        "max_positions_per_sector": int(
            account.get("max_positions_per_sector", 2)
        ),
    }
    return budget


def apply_risk(
    candidates: list[Candidate],
    config: dict[str, Any],
    capital: float | None,
    regime: Regime,
) -> list[Candidate]:
    """Asigna tamaño y marca seleccionados respetando límites de cartera.

    No modifica el estado de los candidatos que no son accionables.
    """
    account = config.get("account", {})
    risk_pct = float(account.get("risk_per_trade_pct", 0.5))
    max_open_pct = float(account.get("max_open_risk_pct", 2.0))
    per_mode = account.get("max_positions_per_mode", {}) or {}
    per_sector = int(account.get("max_positions_per_sector", 2))
    multiplier = regime.size_multiplier

    ordered = sorted(candidates, key=lambda c: c.score, reverse=True)

    open_risk = 0.0
    counts_by_mode: dict[str, int] = {}
    counts_by_sector: dict[str, int] = {}

    for candidate in ordered:
        if not candidate.is_actionable:
            candidate.shares = None
            continue
        mode_cap = int(per_mode.get(candidate.mode, 6))
        sector = candidate.sector or "Sin sector"
        if counts_by_mode.get(candidate.mode, 0) >= mode_cap:
            candidate.reasons.append("no seleccionado: límite de posiciones del modo")
            continue
        if counts_by_sector.get(sector, 0) >= per_sector:
            candidate.reasons.append("no seleccionado: límite por sector")
            continue
        if open_risk + risk_pct * multiplier > max_open_pct + 1e-9:
            candidate.reasons.append("no seleccionado: presupuesto de riesgo agotado")
            continue
        if candidate.entry is None or candidate.stop is None:
            candidate.reasons.append("no seleccionado: sin entrada/stop")
            continue

        effective_risk = risk_pct * multiplier
        shares = position_size(capital, effective_risk, candidate.entry, candidate.stop)
        if shares is None:
            candidate.reasons.append("no seleccionado: capital no definido")
            continue
        if shares < 1:
            candidate.reasons.append("no seleccionado: tamaño menor a 1 acción")
            continue

        candidate.shares = shares
        candidate.selected = True
        candidate.metrics["risk_usd"] = (
            shares * (candidate.entry - candidate.stop)
        )
        candidate.metrics["effective_risk_pct"] = effective_risk
        open_risk += effective_risk
        counts_by_mode[candidate.mode] = counts_by_mode.get(candidate.mode, 0) + 1
        counts_by_sector[sector] = counts_by_sector.get(sector, 0) + 1

    return ordered
