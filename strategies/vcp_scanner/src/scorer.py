from src.indicators import ema
from src.indicators import avg_volume


def calculate_score(df, spy_return):

    score = 0

    close = float(df["Close"].iloc[-1])

    df["EMA21"] = ema(df["Close"], 21)
    df["EMA50"] = ema(df["Close"], 50)
    df["EMA200"] = ema(df["Close"], 200)

    ema21 = float(df["EMA21"].iloc[-1])
    ema50 = float(df["EMA50"].iloc[-1])
    ema200 = float(df["EMA200"].iloc[-1])

    # Tendencia
    if close > ema21:
        score += 10

    if ema21 > ema50:
        score += 10

    if ema50 > ema200:
        score += 10

    # Volumen seco
    vol10 = float(avg_volume(df, 10))
    vol50 = float(avg_volume(df, 50))

    volume_dry_up = vol10 < (vol50 * 0.8)

    if volume_dry_up:
        score += 20

    # Resistencia cercana
    resistance = float(df["High"].tail(60).max())

    breakout_pct = (
        (resistance - close) / close
    ) * 100

    if breakout_pct <= 3:
        score += 15
    elif breakout_pct <= 5:
        score += 10

    # Relative Strength
    stock_return = (
        close / float(df["Close"].iloc[-90])
    ) - 1

    rs = stock_return - spy_return

    if rs > 0:
        score += min(15, rs * 100)

    # Cercanía a máximos 52 semanas
    high_52 = float(df["High"].tail(252).max())

    distance_high = (
        (high_52 - close) / high_52
    ) * 100

    if distance_high <= 5:
        score += 20
    elif distance_high <= 10:
        score += 10

    score = min(round(score, 2), 100)

    return {
        "score": score,
        "rs": round(rs * 100, 2),
        "breakout_pct": round(breakout_pct, 2),
        "distance_high": round(distance_high, 2),
        "volume_dry_up": volume_dry_up,
        "close_above_ema21": close > ema21,
    }