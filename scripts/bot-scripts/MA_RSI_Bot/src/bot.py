import os
import MetaTrader5 as mt5
import pandas as pd
from dotenv import load_dotenv
import ta
from datetime import datetime

# Cargar credenciales desde .env
load_dotenv()
LOGIN = int(os.getenv("MT5_LOGIN"))
PASSWORD = os.getenv("MT5_PASSWORD")
SERVER = os.getenv("MT5_SERVER")

# Inicializar MT5
def connect_mt5():
    if not mt5.initialize(login=LOGIN, password=PASSWORD, server=SERVER):
        print("❌ Conexión fallida:", mt5.last_error())
        return False
    print("✅ Conectado a MT5")
    return True

# Configuración del bot
SYMBOL = "EURUSD"
TIMEFRAME = mt5.TIMEFRAME_M5
LOT = 0.1

# Obtener data
def get_data(symbol, timeframe, n=200):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, n)
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df

# Estrategia MA + RSI
def signal_generator(df):
    df['ma5'] = df['close'].rolling(5).mean()
    df['ma20'] = df['close'].rolling(20).mean()
    df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()

    last = df.iloc[-1]
    if last['ma5'] > last['ma20'] and last['rsi'] < 70:
        return "BUY"
    elif last['ma5'] < last['ma20'] and last['rsi'] > 30:
        return "SELL"
    else:
        return "HOLD"

# Enviar orden
def send_order(signal):
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": SYMBOL,
        "volume": LOT,
        "type": mt5.ORDER_TYPE_BUY if signal == "BUY" else mt5.ORDER_TYPE_SELL,
        "price": mt5.symbol_info_tick(SYMBOL).ask if signal == "BUY" else mt5.symbol_info_tick(SYMBOL).bid,
        "deviation": 10,
        "magic": 1001,
        "comment": "MA_RSI_Bot",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    result = mt5.order_send(request)
    return result

# Guardar logs
def log_trade(signal, result):
    log_file = "trade_logs.csv"
    trade_data = {
        "time": datetime.now(),
        "symbol": SYMBOL,
        "signal": signal,
        "result": result.comment if result.retcode == mt5.TRADE_RETCODE_DONE else str(result),
    }
    df = pd.DataFrame([trade_data])
    if not os.path.isfile(log_file):
        df.to_csv(log_file, index=False)
    else:
        df.to_csv(log_file, mode='a', header=False, index=False)

# Proceso principal
def run_bot():
    if not connect_mt5():
        return
    data = get_data(SYMBOL, TIMEFRAME)
    signal = signal_generator(data)
    print(f"📊 Señal actual: {signal}")

    if signal in ["BUY", "SELL"]:
        result = send_order(signal)
        log_trade(signal, result)
        print("📌 Trade ejecutado y logueado.")
    else:
        print("⏸ Sin señal, no se ejecuta orden.")

    mt5.shutdown()
