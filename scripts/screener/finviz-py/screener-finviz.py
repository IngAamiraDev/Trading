from finvizfinance.screener.overview import Overview

LIMIT = 60  # número de acciones a revisar

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