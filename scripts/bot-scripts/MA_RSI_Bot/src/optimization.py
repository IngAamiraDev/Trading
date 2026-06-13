import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ===============================
# Configuración
# ===============================
DATA_FILE = "logs/historical_data.csv"  # Cambia si tu CSV tiene otro nombre
INITIAL_CAPITAL = 200

# Mejores 3 configuraciones (puedes cambiar si quieres otras)
BEST_CONFIGS = [
    {"Fast_MA": 15, "Slow_MA": 100, "RSI_Period": 14, "SL": 0.007, "TP": 0.03},
    {"Fast_MA": 15, "Slow_MA": 50, "RSI_Period": 21, "SL": 0.007, "TP": 0.03},
    {"Fast_MA": 10, "Slow_MA": 100, "RSI_Period": 21, "SL": 0.007, "TP": 0.03},
]

# ===============================
# Cargar datos
# ===============================
df = pd.read_csv(DATA_FILE)
df['time'] = pd.to_datetime(df['time'])
df.set_index('time', inplace=True)

# ===============================
# Funciones de indicadores
# ===============================
def SMA(series, period):
    return series.rolling(period).mean()

def RSI(series, period):
    delta = series.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# ===============================
# Función de backtest para curva de capital
# ===============================
def backtest_curve(df, fast_ma, slow_ma, rsi_period, sl_pct, tp_pct):
    data = df.copy()
    data['fast_ma'] = SMA(data['close'], fast_ma)
    data['slow_ma'] = SMA(data['close'], slow_ma)
    data['rsi'] = RSI(data['close'], rsi_period)

    balance = INITIAL_CAPITAL
    position = None
    entry_price = 0
    capital_curve = []

    for i in range(len(data)):
        price = data['close'].iloc[i]
        if np.isnan(data['fast_ma'].iloc[i]) or np.isnan(data['slow_ma'].iloc[i]) or np.isnan(data['rsi'].iloc[i]):
            capital_curve.append(balance)
            continue

        if position is None:
            if data['fast_ma'].iloc[i] > data['slow_ma'].iloc[i] and data['rsi'].iloc[i] < 70:
                position = "long"
                entry_price = price
            elif data['fast_ma'].iloc[i] < data['slow_ma'].iloc[i] and data['rsi'].iloc[i] > 30:
                position = "short"
                entry_price = price
        else:
            # Stop Loss / Take Profit
            if position == "long":
                if price <= entry_price * (1 - sl_pct):
                    balance *= (1 - sl_pct)
                    position = None
                elif price >= entry_price * (1 + tp_pct):
                    balance *= (1 + tp_pct)
                    position = None
            elif position == "short":
                if price >= entry_price * (1 + sl_pct):
                    balance *= (1 - sl_pct)
                    position = None
                elif price <= entry_price * (1 - tp_pct):
                    balance *= (1 + tp_pct)
                    position = None

        capital_curve.append(balance)

    return capital_curve

# ===============================
# Generar curvas y graficar
# ===============================
plt.figure(figsize=(12, 6))
for idx, config in enumerate(BEST_CONFIGS):
    curve = backtest_curve(df, config['Fast_MA'], config['Slow_MA'],
                           config['RSI_Period'], config['SL'], config['TP'])
    plt.plot(df.index, curve, label=f"Config {idx+1}: FMA{config['Fast_MA']}-SMA{config['Slow_MA']}-RSI{config['RSI_Period']}")

plt.title("Curvas de Capital - Mejores 3 Configuraciones")
plt.xlabel("Fecha")
plt.ylabel("Capital (USD)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()