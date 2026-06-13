#!/usr/bin/env python3
"""
Script: swing_trading_advanced_safe.py
Author: IngAamira
Description:
    Identifica acciones estadounidenses con potencial de ganancia para swing trading.
    Incluye soportes, resistencias, stop-loss y señales de entrada.
    Maneja tickers sin datos y evita errores de KeyError.
"""

import yfinance as yf
import pandas as pd
from ta.momentum import RSIIndicator

# ==============================
# 1️⃣ LISTA DE TICKERS DE FINVIZ
# ==============================
tickers = ['EOSE', 'COMM', 'QS', 'AEO', 'RUN', 'NLY', 'IVZ', 'BEAM', 'IPG', 'HPQ', 'NE', 'ALGM', 'QBTS', 'CSX', 'GLXY', 'ALLY', 'BWA', 'SEI', 'FLR', 'CFG', 'ON', 'DAL', 'CELH', 'IBKR', 'SYM', 'SYF', 'ASTS', 'XYZ', 'DD', 'W', 'MRVL', 'TEM', 'SCHW', 'ALB', 'UBER', 'C', 'BK', 'STT', 'EMR', 'PSX', 'NUE', 'DDOG', 'BA', 'COF', 'NET', 'AMZN', 'STX', 'JPM', 'CDNS', 'COIN', 'TSLA', 'APP', 'META'] # reemplazar con tu lista real

# ==============================
# 2️⃣ FILTRO DE SWING TRADING
# ==============================
swing_candidates = []

for ticker in tickers:
    try:
        # Se aumenta el periodo y se define interval explícitamente
        df = yf.Ticker(ticker).history(period="6mo", interval="1d")
        if df.empty or len(df) < 50:
            print(f"⚠️ {ticker}: datos insuficientes, se omite")
            continue

        # Indicadores técnicos
        df['RSI'] = RSIIndicator(df['Close'], window=14).rsi()
        df['SMA20'] = df['Close'].rolling(20).mean()
        df['SMA50'] = df['Close'].rolling(50).mean()
        df['SMA200'] = df['Close'].rolling(200).mean()

        last_close = df['Close'].iloc[-1]
        last_sma20 = df['SMA20'].iloc[-1]
        last_sma50 = df['SMA50'].iloc[-1]
        last_rsi = df['RSI'].iloc[-1]

        # Tendencia alcista + RSI moderado
        if last_close > last_sma20 and last_close > last_sma50 and 40 <= last_rsi <= 60:
            support = df['Close'].min()
            resistance = df['Close'].max()
            stop_loss = round(support * 0.97, 2)  # 3% debajo del soporte
            target_price = round(last_close * 1.15, 2)  # objetivo +15%

            # Señal de entrada: últimas 3 velas verdes consecutivas
            recent = df['Close'].iloc[-3:]
            entry_signal = "✅ Entrada" if all(recent.diff().dropna() > 0) else "⚠️ Revisar"

            swing_candidates.append({
                "Ticker": ticker,
                "Close": round(last_close, 2),
                "SMA20": round(last_sma20, 2),
                "SMA50": round(last_sma50, 2),
                "RSI": round(last_rsi, 2),
                "Support": round(support, 2),
                "Resistance": round(resistance, 2),
                "Stop-Loss": stop_loss,
                "Target Price": target_price,
                "Entry Signal": entry_signal
            })
    except Exception as e:
        print(f"⚠️ Error con {ticker}: {e}")

# ==============================
# 3️⃣ TOP 5 CANDIDATOS
# ==============================
df_candidates = pd.DataFrame(swing_candidates)

if not df_candidates.empty:
    df_candidates = df_candidates.sort_values(by="Target Price", ascending=True).head(60)
    print("📊 Top candidatos para swing trading avanzado:")
    print(df_candidates.to_string(index=False))
else:
    print("❌ No se encontraron candidatos válidos. Revisa los tickers o filtros.")