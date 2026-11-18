"""Modelos de datos compartidos por el motor AAA."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Regime:
    """Lectura del contexto general del mercado."""

    label: str  # risk_on | neutral | risk_off
    vix: float | None = None
    indices: dict[str, dict[str, Any]] = field(default_factory=dict)
    leaders: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def allows_new_longs(self) -> bool:
        return self.label in {"risk_on", "neutral"}

    @property
    def size_multiplier(self) -> float:
        if self.label == "risk_on":
            return 1.0
        if self.label == "neutral":
            return 0.5
        return 0.0


@dataclass
class Candidate:
    """Candidato evaluado por uno de los modos."""

    ticker: str
    mode: str
    company: str = ""
    sector: str = ""
    industry: str = ""
    status: str = "Descartado"
    score: float = 0.0
    price: float | None = None
    entry: float | None = None
    stop: float | None = None
    target: float | None = None
    rr: float | None = None
    risk_pct: float | None = None
    shares: int | None = None
    setup: str = ""
    earnings: str | None = None
    last_bar: str | None = None
    gates: dict[str, bool] = field(default_factory=dict)
    reasons: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    source: str = ""
    selected: bool = False

    @property
    def is_actionable(self) -> bool:
        return self.status in {"AAA listo", "Core", "Listo"}

    def to_row(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "ticker": self.ticker,
            "company": self.company,
            "sector": self.sector,
            "industry": self.industry,
            "status": self.status,
            "score": round(self.score, 1),
            "a1": self.gates.get("A1"),
            "a2": self.gates.get("A2"),
            "a3": self.gates.get("A3"),
            "setup": self.setup,
            "price": _round(self.price),
            "entry": _round(self.entry),
            "stop": _round(self.stop),
            "target": _round(self.target),
            "rr": _round(self.rr, 2),
            "risk_pct": _round(self.risk_pct, 2),
            "shares": self.shares,
            "earnings": self.earnings,
            "last_bar": self.last_bar,
            "source": self.source,
            "reasons": " | ".join(self.reasons),
        }


@dataclass
class ScanResult:
    """Resultado de un escaneo de un modo."""

    mode: str
    candidates: list[Candidate] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)

    @property
    def actionable(self) -> list[Candidate]:
        return [c for c in self.candidates if c.is_actionable]

    @property
    def watchlist(self) -> list[Candidate]:
        return [
            c
            for c in self.candidates
            if c.status in {"Vigilancia", "Watch"}
        ]


def _round(value: float | None, digits: int = 2) -> float | None:
    if value is None:
        return None
    try:
        return round(float(value), digits)
    except (TypeError, ValueError):
        return None
