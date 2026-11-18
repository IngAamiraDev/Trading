"""Tests del motor AAA. Sin red: usan datos sinteticos."""

from __future__ import annotations

import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.indicators import (  # noqa: E402
    atr,
    avg_volume,
    pct_change,
    pct_from_high,
    relative_strength,
    rsi,
    slope_pct,
    sma,
    volume_ratio,
)
from src.models import Candidate, Regime  # noqa: E402
from src.report import build_plan, write_reports  # noqa: E402
from src.risk import apply_risk, position_size, risk_budget  # noqa: E402
from src.scoring import evaluate_day, evaluate_invest, evaluate_swing  # noqa: E402


def make_daily(days: int = 300, start: float = 50.0, end: float = 100.0) -> pd.DataFrame:
    index = pd.bdate_range(end=pd.Timestamp("2026-11-16"), periods=days)
    closes = np.linspace(start, end, days)
    # Base lateral en los ultimos 20 dias y ruptura en la ultima barra.
    closes[-20:] = np.linspace(end * 0.97, end * 0.99, 20)
    closes[-1] = end * 1.01
    highs = closes * 1.01
    lows = closes * 0.985
    highs[-21:-1] = end * 0.995
    volume = np.full(days, 1_000_000.0)
    volume[-1] = 3_000_000.0
    return pd.DataFrame(
        {
            "Open": closes * 0.997,
            "High": highs,
            "Low": lows,
            "Close": closes,
            "Volume": volume,
        },
        index=index,
    )


def make_spy(days: int = 300) -> pd.DataFrame:
    index = pd.bdate_range(end=pd.Timestamp("2026-11-16"), periods=days)
    closes = np.linspace(400, 450, days)
    return pd.DataFrame(
        {
            "Open": closes,
            "High": closes * 1.005,
            "Low": closes * 0.995,
            "Close": closes,
            "Volume": np.full(days, 50_000_000.0),
        },
        index=index,
    )


def make_sector(days: int = 250) -> pd.DataFrame:
    index = pd.bdate_range(end=pd.Timestamp("2026-11-16"), periods=days)
    closes = np.linspace(100, 140, days)
    return pd.DataFrame(
        {
            "Open": closes,
            "High": closes * 1.005,
            "Low": closes * 0.995,
            "Close": closes,
            "Volume": np.full(days, 5_000_000.0),
        },
        index=index,
    )


def base_config() -> dict:
    return {
        "account": {
            "capital": 10_000,
            "risk_per_trade_pct": 0.5,
            "max_open_risk_pct": 2.0,
            "max_positions_per_mode": {"swing": 6, "day": 3, "invest": 10},
            "max_positions_per_sector": 2,
        },
        "universe": {
            "min_price": 10.0,
            "min_avg_volume": 1_000_000,
            "min_market_cap": 2_000_000_000,
            "day_min_price": 5.0,
            "day_min_avg_volume": 2_000_000,
            "invest_min_price": 10.0,
            "invest_min_avg_volume": 500_000,
        },
        "regime": {
            "index_symbols": ["SPY", "QQQ"],
            "vix_symbol": "^VIX",
            "sma_fast": 50,
            "sma_slow": 200,
            "vix_max": 25.0,
            "day_vix_max": 28.0,
        },
        "swing": {
            "sma_fast": 20,
            "sma_mid": 50,
            "sma_slow": 200,
            "rs_windows": [21, 63],
            "max_distance_52w_high_pct": 15.0,
            "min_rel_volume": 1.5,
            "min_rr": 2.0,
            "target_r": 2.5,
            "max_stop_pct": 8.0,
            "earnings_blackout_days": 5,
            "pivot_days": 20,
            "stop_lookback_days": 10,
            "atr_multiple": 1.5,
            "min_score": 70.0,
            "watch_score": 55.0,
        },
        "day": {
            "min_gap_pct": 2.0,
            "max_gap_pct": 10.0,
            "min_rel_volume": 3.0,
            "min_rr": 1.5,
            "target_r": 2.0,
            "atr_multiple": 1.0,
            "max_stop_pct": 5.0,
            "earnings_blackout_days": 1,
            "min_score": 65.0,
            "watch_score": 50.0,
        },
        "invest": {
            "min_eps_qoq_pct": 10.0,
            "min_sales_qoq_pct": 5.0,
            "min_eps_yoy_pct": 5.0,
            "min_roe_pct": 10.0,
            "min_net_margin_pct": 5.0,
            "max_debt_equity": 1.5,
            "min_score": 75.0,
            "watch_score": 55.0,
            "max_distance_52w_high_pct": 25.0,
            "earnings_blackout_days": 3,
            "stop_pct": 15.0,
        },
    }


def good_fundamentals() -> dict:
    return {
        "company": "Test Corp",
        "sector": "Technology",
        "industry": "Software",
        "market_cap": 50_000_000_000,
        "eps_qoq": 25.0,
        "sales_qoq": 15.0,
        "eps_yoy": 18.0,
        "sales_yoy": 12.0,
        "roe": 20.0,
        "roic": 15.0,
        "net_margin": 20.0,
        "debt_equity": 0.4,
        "pe": 25.0,
        "peg": 1.5,
        "pfcf": 25.0,
        "ev_ebitda": 14.0,
        "high_52w": 101.0,
        "atr": 1.5,
        "rel_volume": 2.5,
        "avg_volume": 1_000_000,
        "earnings": "2027-01-15",
        "earnings_days": 60,
    }


def risk_on() -> Regime:
    return Regime(
        label="risk_on",
        vix=15.0,
        indices={
            "SPY": {"close": 450, "sma_fast": 440, "sma_slow": 420, "above_fast": True, "above_slow": True},
            "QQQ": {"close": 400, "sma_fast": 390, "sma_slow": 370, "above_fast": True, "above_slow": True},
        },
    )


class IndicatorTests(unittest.TestCase):
    def test_sma_and_slope(self):
        series = pd.Series(np.arange(1, 51, dtype=float))
        self.assertAlmostEqual(sma(series, 5), 48.0)
        self.assertGreater(slope_pct(series, 10), 0)
        self.assertIsNone(sma(series, 100))

    def test_rsi_uptrend(self):
        series = pd.Series(np.arange(1, 60, dtype=float))
        self.assertAlmostEqual(rsi(series), 100.0)

    def test_atr(self):
        frame = make_daily()
        value = atr(frame, 14)
        self.assertIsNotNone(value)
        self.assertGreater(value, 0)

    def test_pct_and_rs(self):
        asset = pd.Series([100.0] + [0.0] * 20 + [110.0])
        bench = pd.Series([100.0] + [0.0] * 20 + [105.0])
        self.assertAlmostEqual(pct_change(asset, 21), 10.0)
        self.assertAlmostEqual(relative_strength(asset, bench, 21), 5.0)
        self.assertAlmostEqual(pct_from_high(90, 100), -10.0)

    def test_volume_ratio(self):
        frame = make_daily()
        self.assertGreater(volume_ratio(frame, 50), 1.0)
        self.assertLessEqual(avg_volume(frame, 50), frame["Volume"].max())


class RiskTests(unittest.TestCase):
    def test_position_size(self):
        self.assertEqual(position_size(10_000, 0.5, 100, 95), 10)
        self.assertIsNone(position_size(None, 0.5, 100, 95))
        self.assertIsNone(position_size(10_000, 0.5, 100, 100))
        self.assertEqual(position_size(100, 0.5, 100, 99), 0)

    def test_risk_budget(self):
        budget = risk_budget(base_config(), 10_000)
        self.assertEqual(budget["max_positions_by_risk"], 4)
        self.assertAlmostEqual(budget["risk_per_trade_usd"], 50.0)
        self.assertAlmostEqual(budget["max_open_risk_usd"], 200.0)

    def test_apply_risk_limits(self):
        config = base_config()
        candidates = []
        for idx in range(6):
            candidates.append(
                Candidate(
                    ticker=f"T{idx}",
                    mode="swing",
                    status="AAA listo",
                    score=90 - idx,
                    sector=f"S{idx}",
                    entry=100.0,
                    stop=95.0,
                )
            )
        ordered = apply_risk(candidates, config, 10_000, risk_on())
        selected = [c for c in ordered if c.selected]
        self.assertEqual(len(selected), 4)
        self.assertTrue(all(c.shares == 10 for c in selected))

    def test_apply_risk_sector_cap(self):
        config = base_config()
        config["account"]["max_open_risk_pct"] = 10.0
        candidates = [
            Candidate(
                ticker=f"T{idx}",
                mode="swing",
                status="AAA listo",
                score=90 - idx,
                sector="Tech",
                entry=100.0,
                stop=95.0,
            )
            for idx in range(5)
        ]
        ordered = apply_risk(candidates, config, 10_000, risk_on())
        self.assertEqual(len([c for c in ordered if c.selected]), 2)


class SwingTests(unittest.TestCase):
    def test_breakout_is_aaa(self):
        candidate = evaluate_swing(
            "TEST",
            {"company": "Test", "sector": "Technology", "industry": "Software", "market_cap": 5e10},
            make_daily(),
            make_spy(),
            {"etf": "XLK", "aligned": True, "rs21": 3.0},
            good_fundamentals(),
            base_config(),
            risk_on(),
        )
        self.assertTrue(candidate.gates["A1"])
        self.assertTrue(candidate.gates["A2"])
        self.assertTrue(candidate.gates["A3"])
        self.assertEqual(candidate.status, "AAA listo")
        self.assertGreaterEqual(candidate.score, 70)
        self.assertLessEqual(candidate.risk_pct, 8.0)
        self.assertAlmostEqual(candidate.rr, 2.5)

    def test_risk_off_is_watch_not_actionable(self):
        candidate = evaluate_swing(
            "TEST",
            {"company": "Test", "sector": "Technology", "industry": "Software", "market_cap": 5e10},
            make_daily(),
            make_spy(),
            {"etf": "XLK", "aligned": True, "rs21": 3.0},
            good_fundamentals(),
            base_config(),
            Regime(label="risk_off", vix=30.0),
        )
        self.assertFalse(candidate.gates["A1"])
        self.assertEqual(candidate.status, "Vigilancia")
        self.assertFalse(candidate.is_actionable)

    def test_earnings_blackout_rejects(self):
        fundamentals = good_fundamentals()
        fundamentals["earnings_days"] = 2
        candidate = evaluate_swing(
            "TEST",
            {"company": "Test", "sector": "Technology", "industry": "Software", "market_cap": 5e10},
            make_daily(),
            make_spy(),
            {"etf": "XLK", "aligned": True, "rs21": 3.0},
            fundamentals,
            base_config(),
            risk_on(),
        )
        self.assertFalse(candidate.gates["A3"])
        self.assertEqual(candidate.status, "Descartado")


class InvestTests(unittest.TestCase):
    def test_quality_core(self):
        candidate = evaluate_invest(
            "TEST",
            {"company": "Test", "sector": "Technology", "industry": "Software", "market_cap": 5e10},
            make_daily(),
            make_spy(),
            good_fundamentals(),
            base_config(),
            risk_on(),
        )
        self.assertTrue(all(candidate.gates.values()))
        self.assertEqual(candidate.status, "Core")
        self.assertGreaterEqual(candidate.score, 75)

    def test_missing_fundamentals_rejected(self):
        candidate = evaluate_invest(
            "TEST",
            {"company": "Test", "sector": "Technology", "industry": "Software", "market_cap": 5e10},
            make_daily(),
            make_spy(),
            {},
            base_config(),
            risk_on(),
        )
        self.assertEqual(candidate.status, "Reject")
        self.assertIn("sin fundamentales verificables", candidate.reasons)

    def test_low_quality_rejected(self):
        fundamentals = good_fundamentals()
        fundamentals.update({"roe": 2.0, "net_margin": 1.0, "eps_qoq": 1.0, "eps_yoy": 1.0})
        candidate = evaluate_invest(
            "TEST",
            {"company": "Test", "sector": "Technology", "industry": "Software", "market_cap": 5e10},
            make_daily(),
            make_spy(),
            fundamentals,
            base_config(),
            risk_on(),
        )
        self.assertFalse(candidate.gates["A2"])
        self.assertEqual(candidate.status, "Reject")


def make_intraday() -> pd.DataFrame:
    start = datetime(2026, 11, 17, 9, 30)
    rows = []
    index = []
    price = 104.0
    for step in range(20):
        stamp = start + timedelta(minutes=5 * step)
        open_price = price
        price += 0.1
        rows.append(
            {
                "Open": open_price,
                "High": price + 0.05,
                "Low": open_price - 0.05,
                "Close": price,
                "Volume": 60_000.0,
            }
        )
        index.append(stamp)
    # Premarket
    pre_start = datetime(2026, 11, 17, 8, 0)
    for step in range(12):
        stamp = pre_start + timedelta(minutes=5 * step)
        rows.insert(
            step,
            {
                "Open": 104.0,
                "High": 104.8,
                "Low": 103.5,
                "Close": 104.0,
                "Volume": 20_000.0,
            },
        )
        index.insert(step, stamp)
    frame = pd.DataFrame(rows, index=index)
    return frame.sort_index()


class DayTests(unittest.TestCase):
    def day_config(self) -> dict:
        config = base_config()
        config["universe"]["day_min_avg_volume"] = 500_000
        return config

    def test_gap_and_volume_is_ready(self):
        candidate = evaluate_day(
            "TEST",
            {"company": "Test", "sector": "Technology", "industry": "Software", "market_cap": 5e10},
            make_daily(),
            make_intraday(),
            make_spy(),
            good_fundamentals(),
            self.day_config(),
            risk_on(),
        )
        self.assertTrue(candidate.gates["A1"])
        self.assertTrue(candidate.gates["A2"])
        self.assertTrue(candidate.gates["A3"])
        self.assertEqual(candidate.status, "Listo")
        self.assertGreaterEqual(candidate.score, 65)

    def test_small_gap_not_ready(self):
        frame = make_intraday()
        frame.loc[pd.Timestamp("2026-11-17 09:30:00"), "Open"] = 100.0
        candidate = evaluate_day(
            "TEST",
            {"company": "Test", "sector": "Technology", "industry": "Software", "market_cap": 5e10},
            make_daily(),
            frame,
            make_spy(),
            good_fundamentals(),
            self.day_config(),
            risk_on(),
        )
        self.assertEqual(candidate.status, "Descartado")


class PresetTests(unittest.TestCase):
    def test_presets_match_finviz_options(self):
        from finvizfinance.constants import filter_dict

        from src.finviz_presets import PRESETS, _ensure_filters

        _ensure_filters()
        for name, preset in PRESETS.items():
            for key, value in preset["filters"].items():
                self.assertIn(key, filter_dict, f"{name}: filtro desconocido {key}")
                self.assertIn(
                    value,
                    filter_dict[key]["option"],
                    f"{name}: opcion desconocida {value}",
                )

    def test_sales_growth_ttm_injected(self):
        from finvizfinance.constants import filter_dict

        from src.finviz_presets import _ensure_filters

        _ensure_filters()
        self.assertEqual(filter_dict["Sales growth ttm"]["prefix"], "fa_salesyoyttm")


class ReportTests(unittest.TestCase):
    def test_write_reports(self):
        import tempfile

        candidate = evaluate_swing(
            "TEST",
            {"company": "Test", "sector": "Technology", "industry": "Software", "market_cap": 5e10},
            make_daily(),
            make_spy(),
            {"etf": "XLK", "aligned": True, "rs21": 3.0},
            good_fundamentals(),
            base_config(),
            risk_on(),
        )
        from src.models import ScanResult

        result = ScanResult(mode="swing", candidates=[candidate])
        results = {"swing": result}
        with tempfile.TemporaryDirectory() as tmp:
            paths = write_reports(
                results,
                risk_on(),
                base_config(),
                risk_budget(base_config(), 10_000),
                output_dir=tmp,
            )
            self.assertTrue(paths["plan"].exists())
            self.assertTrue(paths["csv"].exists())
            self.assertTrue(paths["watchlist"].exists())
            self.assertTrue(paths["summary"].exists())
            text = paths["plan"].read_text(encoding="utf-8")
            self.assertIn("Plan AAA", text)
            self.assertIn("TEST", text)
            self.assertIn("## 1. Régimen de mercado", text)
            watchlist = paths["watchlist"].read_text(encoding="utf-8")
            self.assertIn("TEST", watchlist)


if __name__ == "__main__":
    unittest.main()
