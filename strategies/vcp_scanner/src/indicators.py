import pandas as pd


def ema(series, period):
    return series.ewm(span=period, adjust=False).mean()


def avg_volume(df, days):
    return df["Volume"].tail(days).mean()