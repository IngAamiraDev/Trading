#!/usr/bin/env python3
"""
Script: finviz_shiller_screen.py
Author: IngAamira
Description:
    Combina análisis técnico (Finviz) y fundamental (Shiller P/E proxy)
    para identificar oportunidades swing trading rentables.
"""

from finvizfinance.screener.overview import Overview
import yfinance as yf
import pandas as pd
import time
import numpy as np

# ==============================
# CONFIGURACIÓN
# ==============================
LIMIT = 60  # número de acciones a revisar
OUTPUT_FILE = "screener_shiller_results.csv"

filters = {
    "Country": "USA",
    "Market Cap.": "+Mid (over $2bln)",
    "Price": "Over $15",
    "Average Volume": "Over 1M",
    "Current Volume": "Over 2M",
    "Beta": "Over 1",
    "RSI (14)": "Not Overbought (<60)",
    "20-Day Simple Moving Average": "Price above SMA20",
    "50-Day Simple Moving Average": "Price above SMA50",
    "200-Day Simple Moving Average": "Price above SMA200"
}

# ==============================
# 1️⃣ OBTENER DATOS DESDE FINVIZ
# ==============================
print("📊 Obteniendo tickers desde Finviz...")

stock_screener = Overview()
stock_screener.set_filter(filters_dict=filters)
df_finviz = stock_screener.screener_view(order="Price")

if df_finviz.empty:
    raise ValueError("❌ No se obtuvieron resultados de Finviz. Revisa los filtros.")

tickers = df_finviz["Ticker"].tolist()[:LIMIT]
print(f"✅ {len(tickers)} tickers obtenidos: {tickers}")

# ==============================
# 2️⃣ FUNCIÓN PARA CALCULAR RSI (14)
# ==============================
def get_rsi(ticker, period=14):
    """Calcula el RSI usando datos de cierre de yfinance"""
    try:
        data = yf.download(ticker, period="6mo", interval="1d", progress=False, auto_adjust=True)
        if data.empty:
            return None

        # Asegurar que tengamos una sola columna 'Close'
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        if "Close" not in data.columns:
            return None

        close = data["Close"].astype(float)
        delta = close.diff()

        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)

        avg_gain = pd.Series(gain).rolling(window=period, min_periods=period).mean()
        avg_loss = pd.Series(loss).rolling(window=period, min_periods=period).mean()

        # Evitar divisiones por cero
        avg_loss = avg_loss.replace(0, np.nan)
        rs = avg_gain / avg_loss

        rsi = 100 - (100 / (1 + rs))
        if rsi.empty or pd.isna(rsi.iloc[-1]):
            return None

        return float(round(rsi.iloc[-1], 2))

    except Exception as e:
        print(f"⚠️ Error al calcular RSI para {ticker}: {e}")
        return None

# ==============================
# 3️⃣ FUNCIÓN PARA OBTENER P/E (PROXY SHILLER)
# ==============================
def get_shiller_pe(ticker):
    """Obtiene el Trailing P/E como proxy del Shiller P/E desde yfinance"""
    try:
        info = yf.Ticker(ticker).info
        pe_ratio = info.get("trailingPE")
        if pe_ratio is not None and pe_ratio > 0:
            return round(pe_ratio, 2)
    except Exception as e:
        print(f"⚠️ Error al obtener proxy Shiller P/E para {ticker}: {e}")
    return None

# ==============================
# 4️⃣ PROCESAR RESULTADOS
# ==============================
rows = []
print("\n🔍 Calculando RSI y Shiller P/E (proxy)...")

for ticker in tickers:
    price = df_finviz.loc[df_finviz["Ticker"] == ticker, "Price"].values[0]
    sector = df_finviz.loc[df_finviz["Ticker"] == ticker, "Sector"].values[0]

    rsi = get_rsi(ticker)
    shiller = get_shiller_pe(ticker)
    time.sleep(1)

    # Evaluación RSI
    if rsi is None:
        rsi_eval = "⚪ Sin datos RSI"
    elif rsi >= 70:
        rsi_eval = "🔴 Sobrecomprado"
    elif rsi <= 30:
        rsi_eval = "🟢 Sobrevendido"
    else:
        rsi_eval = "🟡 Neutral"

    # Evaluación Shiller P/E proxy
    if shiller is None:
        pe_eval = "⚪ Sin datos"
    elif shiller <= 15:
        pe_eval = "🟢 Infravalorado"
    elif shiller > 35:
        pe_eval = "🔴 Sobrevalorado"
    else:
        pe_eval = "✅ Valor razonable"

    rows.append({
        "Ticker": ticker,
        "Price": price,
        "Sector": sector,
        "RSI(14)": rsi,
        "Eval RSI": rsi_eval,
        "Shiller P/E (proxy)": shiller,
        "Eval Shiller": pe_eval
    })

# ==============================
# 5️⃣ RESULTADOS
# ==============================
df = pd.DataFrame(rows)

print("\n📈 Resultados combinados:")
print(df)

df.to_csv(OUTPUT_FILE, index=False)
print(f"\n💾 Archivo guardado: {OUTPUT_FILE}")