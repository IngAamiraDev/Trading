import pandas as pd
import MetaTrader5 as mt5

SYMBOL = "EURUSD"
TIMEFRAME = mt5.TIMEFRAME_M5

# Conectar
mt5.initialize()

# Descargar históricos
rates = mt5.copy_rates_range(SYMBOL, TIMEFRAME, "2023-01-01", "2023-12-31")
df = pd.DataFrame(rates)
df['time'] = pd.to_datetime(df['time'], unit='s')

# --- Estrategia ---
df['MA5'] = df['close'].rolling(5).mean()
df['MA20'] = df['close'].rolling(20).mean()

delta = df['close'].diff()
gain = delta.clip(lower=0).rolling(14).mean()
loss = -delta.clip(upper=0).rolling(14).mean()
rs = gain / loss
df['RSI'] = 100 - (100 / (1 + rs))

# Generar señales
df['signal'] = "HOLD"
df.loc[(df['MA5'] > df['MA20']) & (df['RSI'] < 70), 'signal'] = "BUY"
df.loc[(df['MA5'] < df['MA20']) & (df['RSI'] > 30), 'signal'] = "SELL"

# Simulación simple
capital = 1000
lot = 0.1
position = None
entry_price = 0

for i, row in df.iterrows():
    if row['signal'] == "BUY" and position is None:
        position = "LONG"
        entry_price = row['close']
    elif row['signal'] == "SELL" and position is None:
        position = "SHORT"
        entry_price = row['close']
    elif row['signal'] == "SELL" and position == "LONG":
        pnl = (row['close'] - entry_price) * 10000 * lot
        capital += pnl
        position = None
    elif row['signal'] == "BUY" and position == "SHORT":
        pnl = (entry_price - row['close']) * 10000 * lot
        capital += pnl
        position = None

print("💰 Capital final:", capital)