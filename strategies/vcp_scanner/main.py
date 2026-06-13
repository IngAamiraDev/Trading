import os
import pandas as pd
import yfinance as yf

from tqdm import tqdm

from src.scorer import calculate_score

# =====================================
# Crear carpetas
# =====================================

os.makedirs("output", exist_ok=True)

# =====================================
# Leer tickers
# =====================================

with open("input/tickers.txt", "r") as f:

    tickers = [
        t.strip().upper()
        for t in f.read().split(",")
        if t.strip()
    ]

print(f"Tickers encontrados: {len(tickers)}")

# =====================================
# SPY benchmark
# =====================================

spy = yf.download(
    "SPY",
    period="1y",
    auto_adjust=True,
    progress=False
)

if isinstance(spy.columns, pd.MultiIndex):
    spy.columns = spy.columns.get_level_values(0)

spy_return = (
    float(spy["Close"].iloc[-1])
    / float(spy["Close"].iloc[-90])
) - 1

# =====================================
# Scan
# =====================================

results = []

for ticker in tqdm(tickers):

    try:

        df = yf.download(
            ticker,
            period="1y",
            auto_adjust=True,
            progress=False
        )

        if len(df) < 200:
            continue

        # Corrige MultiIndex
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        result = calculate_score(
            df,
            spy_return
        )

        results.append({
            "Ticker": ticker,
            "Score": result["score"],
            "RS": result["rs"],
            "Breakout %": result["breakout_pct"],
            "52W High %": result["distance_high"],
            "Vol Dry-Up": result["volume_dry_up"],
            "EMA21": result["close_above_ema21"]
        })

    except Exception as e:

        print(f"\nERROR {ticker}: {e}")

# =====================================
# Validación
# =====================================

if len(results) == 0:

    print("\nNo se generaron resultados.")
    quit()

# =====================================
# Ranking
# =====================================

ranking = pd.DataFrame(results)

ranking = ranking.sort_values(
    by="Score",
    ascending=False
)

# =====================================
# Exportaciones
# =====================================

ranking.to_csv(
    "output/all_ranked.csv",
    index=False
)

top20 = ranking.head(20)

top20.to_csv(
    "output/top20.csv",
    index=False
)

ready = ranking[
    ranking["Score"] >= 70
]

ready.to_csv(
    "output/ready_to_breakout.csv",
    index=False
)

# Watchlist TradingView

watchlist = ",".join(
    ready["Ticker"].tolist()
)

with open(
    "output/tradingview_watchlist.txt",
    "w"
) as f:

    f.write(watchlist)

# =====================================
# Consola
# =====================================

print("\nTOP 20")
print(top20)

print(
    f"\nAnalizados: {len(results)} tickers"
)

print(
    f"Listos para revisar: {len(ready)}"
)