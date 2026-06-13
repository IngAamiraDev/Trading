import os
import time
import pandas as pd
import MetaTrader5 as mt5
from dotenv import load_dotenv

# -------------------
# Cargar credenciales MT5
# -------------------
load_dotenv()
LOGIN = int(os.getenv("MT5_LOGIN"))
PASSWORD = os.getenv("MT5_PASSWORD")
SERVER = os.getenv("MT5_SERVER")

SYMBOL = "EURUSD"
TIMEFRAME = mt5.TIMEFRAME_M15
LOT_SIZE = 0.1  # Tamaño de lote
SL_PCT = 0.007  # 0.7%
TP_PCT = 0.03   # 3%
SLEEP_TIME = 60  # Segundos entre checks

# -------------------
# Inicializar MT5
# -------------------
if not mt5.initialize(login=LOGIN, password=PASSWORD, server=SERVER):
    print("❌ No se pudo conectar a MT5:", mt5.last_error())
    quit()

# -------------------
# Funciones de indicador Parabolic SAR
# -------------------
def calculate_sar(data, af=0.02, max_af=0.2):
    """Calcula Parabolic SAR simple"""
    sar = [data['close'][0]]  # inicial SAR
    ep = data['high'][0]      # extreme point
    trend_up = True           # tendencia inicial
    af_current = af

    for i in range(1, len(data)):
        prev_sar = sar[-1]

        if trend_up:
            new_sar = prev_sar + af_current * (ep - prev_sar)
            if data['low'][i] < new_sar:
                trend_up = False
                new_sar = ep
                ep = data['low'][i]
                af_current = af
            else:
                if data['high'][i] > ep:
                    ep = data['high'][i]
                    af_current = min(af_current + af, max_af)
        else:
            new_sar = prev_sar - af_current * (prev_sar - ep)
            if data['high'][i] > new_sar:
                trend_up = True
                new_sar = ep
                ep = data['high'][i]
                af_current = af
            else:
                if data['low'][i] < ep:
                    ep = data['low'][i]
                    af_current = min(af_current + af, max_af)

        sar.append(new_sar)
    return sar

# -------------------
# Función para ejecutar órdenes
# -------------------
def send_order(symbol, action, lot, sl, tp):
    price = mt5.symbol_info_tick(symbol).ask if action == "buy" else mt5.symbol_info_tick(symbol).bid
    deviation = 20
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": mt5.ORDER_TYPE_BUY if action == "buy" else mt5.ORDER_TYPE_SELL,
        "price": price,
        "sl": sl,
        "tp": tp,
        "deviation": deviation,
        "magic": 123456,
        "comment": "SAR_Bot",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print("❌ Orden fallida:", result)
    else:
        print(f"✅ {action.upper()} ejecutado: {price}, SL={sl}, TP={tp}")

# -------------------
# Loop principal del bot
# -------------------
def run_bot():
    while True:
        rates = mt5.copy_rates_from_pos(SYMBOL, TIMEFRAME, 0, 100)
        df = pd.DataFrame(rates)

        if 'time' not in df.columns:
            print("❌ La columna 'time' no existe en los datos descargados.")
            print("Estructura de los datos:", df.head())
            mt5.shutdown()
            quit()

        df['time'] = pd.to_datetime(df['time'], unit='s')
        df['sar'] = calculate_sar(df)

        last_close = df['close'].iloc[-1]
        last_sar = df['sar'].iloc[-1]

        # Comprobar posiciones abiertas
        positions = mt5.positions_get(symbol=SYMBOL)
        has_position = len(positions) > 0

        if last_close > last_sar and not has_position:
            sl_price = last_close * (1 - SL_PCT)
            tp_price = last_close * (1 + TP_PCT)
            send_order(SYMBOL, "buy", LOT_SIZE, sl_price, tp_price)

        elif last_close < last_sar and not has_position:
            sl_price = last_close * (1 + SL_PCT)
            tp_price = last_close * (1 - TP_PCT)
            send_order(SYMBOL, "sell", LOT_SIZE, sl_price, tp_price)

        time.sleep(SLEEP_TIME)

if __name__ == "__main__":
    try:
        run_bot()
    except KeyboardInterrupt:
        print("Bot detenido manualmente")
        mt5.shutdown()