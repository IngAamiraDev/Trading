#!/usr/bin/env python3
"""
Script: smart_screener.py
Author: IngAamira
Description:
    Smart Screener para identificar los mejores sectores y acciones
    con potencial de compra o venta en el mercado estadounidense (swing trading).
    Combina momentum sectorial, RSI, y momentum individual de precio.
"""

import time
import pandas as pd
import yfinance as yf
from finvizfinance.screener.overview import Overview
from ta.momentum import RSIIndicator
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)

# ===============================
# 1️⃣ ETFs sectoriales
# ===============================
SECTOR_ETFS = {
    "Technology": "XLK",
    "Communication Services": "XLC",
    "Healthcare": "XLV",
    "Financial": "XLF",
    "Consumer Discretionary": "XLY",
    "Consumer Staples": "XLP",
    "Energy": "XLE",
    "Materials": "XLB",
    "Industrials": "XLI",
    "Utilities": "XLU",
    "Real Estate": "XLRE",
}


def get_sector_momentum():
    """Calcula el momentum (variación %) de cada sector en los últimos 3 meses."""
    print("📊 Evaluando sectores líderes...")
    data_list = []

    for sector, ticker in SECTOR_ETFS.items():
        try:
            data = yf.download(ticker, period="3mo", interval="1d", progress=False)
            if len(data) < 2:
                continue
            start_price = float(data["Close"].iloc[0])
            end_price = float(data["Close"].iloc[-1])
            momentum = ((end_price - start_price) / start_price) * 100
            data_list.append({"Sector": sector, "ETF": ticker, "MomentumScore": round(momentum, 2)})
        except Exception as e:
            print(f"⚠️ Error al procesar {sector}: {e}")

    df = pd.DataFrame(data_list)
    df.sort_values("MomentumScore", ascending=False, inplace=True)
    print("\n🏆 Sectores con mejor momentum:")
    print(df)
    return df


# ===============================
# 2️⃣ Filtro Finviz
# ===============================
def get_top_stocks(top_sectors):
    """Obtiene las mejores acciones de los sectores líderes desde Finviz."""
    overview = Overview()
    all_results = []

    filters_base = {
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

    for sector in top_sectors:
        try:
            filters = filters_base.copy()
            filters["Sector"] = sector
            overview.set_filter(filters_dict=filters)
            df = overview.screener_view(order="Price")

            if not df.empty:
                df["Sector"] = sector
                all_results.append(df.head(5))
            else:
                print(f"⚠️ No se encontraron acciones para {sector}.")
            time.sleep(1)

        except Exception as e:
            print(f"⚠️ Error en sector {sector}: {e}")

    if not all_results:
        print("❌ No se encontraron acciones en ningún sector.")
        return pd.DataFrame()

    combined = pd.concat(all_results, ignore_index=True)
    print(f"\n✅ {len(combined)} acciones obtenidas desde Finviz.")

    expected_cols = ["Ticker", "Company", "Sector", "Price", "Change", "Perf Month", "RSI (14)"]
    cols_present = [col for col in expected_cols if col in combined.columns]
    return combined[cols_present]


# ===============================
# 3️⃣ RSI y Momentum individual
# ===============================
def compute_rsi_and_momentum(df):
    """Calcula RSI y momentum (30 días) con yfinance."""
    print("\n🔍 Calculando RSI y Momentum de precio (30 días)...")
    results = []

    for ticker in df["Ticker"]:
        try:
            data = yf.download(ticker, period="6mo", interval="1d", progress=False)
            if data.empty or len(data) < 30:
                continue

            # Asegurar que Close sea 1D
            close_prices = data["Close"]
            if isinstance(close_prices, pd.DataFrame):
                close_prices = close_prices.squeeze()

            # Calcular RSI y momentum de 30 días
            data["RSI"] = RSIIndicator(close_prices, window=14).rsi()
            start_price = close_prices.iloc[-30]
            end_price = close_prices.iloc[-1]
            momentum_30d = round(((end_price - start_price) / start_price) * 100, 2)

            latest_rsi = round(data["RSI"].iloc[-1], 2)
            last_price = round(end_price, 2)

            # Señales combinadas
            if latest_rsi < 40 and momentum_30d > 0:
                signal = "🟢 BUY"
            elif latest_rsi > 60 and momentum_30d < 0:
                signal = "🔴 SELL"
            else:
                signal = "⚪ HOLD"

            results.append({
                "Ticker": ticker,
                "Last Price": last_price,
                "RSI": latest_rsi,
                "Momentum 30D (%)": momentum_30d,
                "Signal": signal
            })

        except Exception as e:
            print(f"⚠️ Error en {ticker}: {e}")

    return pd.DataFrame(results)


# ===============================
# 4️⃣ MAIN SCRIPT
# ===============================
if __name__ == "__main__":
    # Paso 1: Momentum sectorial
    sectors_df = get_sector_momentum()
    top_sectors = sectors_df.head(3)["Sector"].tolist()

    # Paso 2: Acciones líderes
    stocks_df = get_top_stocks(top_sectors)

    if not stocks_df.empty:
        # Paso 3: RSI + Momentum individual
        final_df = compute_rsi_and_momentum(stocks_df)

        if final_df.empty:
            print("\n⚠️ No se pudo calcular RSI/Momentum (datos insuficientes).")
            merged = stocks_df
        else:
            merged = pd.merge(stocks_df, final_df, on="Ticker", how="left")

        # Ordenar: primero BUY con mejor momentum
        merged["Momentum 30D (%)"] = pd.to_numeric(merged["Momentum 30D (%)"], errors="coerce")
        merged = merged.sort_values(by=["Signal", "Momentum 30D (%)"], ascending=[True, False])

        print("\n📈 Resultado final:")
        print(merged[["Ticker", "Company", "Sector", "Last Price", "RSI", "Momentum 30D (%)", "Signal"]].head(15))

        # Exportar
        filename = f"smart_screener_{pd.Timestamp.today().strftime('%Y-%m-%d')}.csv"
        merged.to_csv(filename, index=False)
        print(f"\n💾 Resultados guardados en: {filename}")

    else:
        print("❌ No se encontraron acciones con los filtros definidos.")