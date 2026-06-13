import os
import pandas as pd
import MetaTrader5 as mt5
import backtrader as bt
from dotenv import load_dotenv

# -------------------
# Cargar credenciales
# -------------------
load_dotenv()
LOGIN = int(os.getenv("MT5_LOGIN"))
PASSWORD = os.getenv("MT5_PASSWORD")
SERVER = os.getenv("MT5_SERVER")

if not mt5.initialize(login=LOGIN, password=PASSWORD, server=SERVER):
    print("❌ Error al conectar MT5:", mt5.last_error())
    quit()

# -------------------
# Descargar datos
# -------------------
symbol = "EURUSD"
timeframe = mt5.TIMEFRAME_M15
rates = mt5.copy_rates_range(symbol, timeframe,
                             pd.to_datetime("2025-01-01"),
                             pd.to_datetime("2025-12-31"))
mt5.shutdown()

data = pd.DataFrame(rates)
data["time"] = pd.to_datetime(data["time"], unit="s")
data.set_index("time", inplace=True)

if "volume" not in data.columns:
    data["volume"] = 0
data["volume"] = data["volume"].replace([float("inf"), float("-inf")], float("nan")).fillna(0)

# Guardar datos para revisión
os.makedirs("logs", exist_ok=True)
data.to_csv("logs/historical_data.csv")

# -------------------
# Estrategia MA + RSI con SL y TP fijos
# -------------------
class MARSI_Strategy(bt.Strategy):
    params = (("sl_pct", 0.007), ("tp_pct", 0.03),)  # SL=0.7%, TP=3%

    def __init__(self):
        self.ma5 = bt.ind.SMA(period=5)
        self.ma20 = bt.ind.SMA(period=20)
        self.rsi = bt.ind.RSI(period=14)

    def next(self):
        if not self.position:
            if self.ma5[0] > self.ma20[0] and self.rsi[0] < 70:
                sl_price = self.data.close[0] * (1 - self.p.sl_pct)
                tp_price = self.data.close[0] * (1 + self.p.tp_pct)
                self.buy_bracket(limitprice=tp_price, stopprice=sl_price)

            elif self.ma20[0] > self.ma5[0] and self.rsi[0] > 30:
                sl_price = self.data.close[0] * (1 + self.p.sl_pct)
                tp_price = self.data.close[0] * (1 - self.p.tp_pct)
                self.sell_bracket(limitprice=tp_price, stopprice=sl_price)

# -------------------
# Backtest
# -------------------
cerebro = bt.Cerebro()
feed = bt.feeds.PandasData(dataname=data)
cerebro.adddata(feed)
cerebro.addstrategy(MARSI_Strategy)
cerebro.broker.set_cash(200)               # Capital inicial
cerebro.broker.setcommission(commission=0.0002)  # Comisión 0.02%

print("💰 Capital inicial:", cerebro.broker.getvalue())
cerebro.run()
final_value = round(cerebro.broker.getvalue(), 2)
print("📊 Capital final:", final_value)
print("📈 Ganancia/Pérdida:", round(final_value - 200, 2))

# -------------------
# Gráfico de resultados
# -------------------
cerebro.plot()