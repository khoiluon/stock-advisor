MASTER_WEIGHTS = {
    'TREND': 40,
    'MOMENTUM': 30,
    'VOLUME': 30,
}

SIGNAL_SCORES = {
    'PRICE_ABOVE_SMA150': 4,
    'PRICE_ABOVE_SMA50': 3,
    'SMA50_ABOVE_SMA150': 3,
    'NEAR_52_WEEK_HIGH_15_PERCENT': 2,
    'NEAR_52_WEEK_HIGH_5_PERCENT': 2,
    'RSI_ABOVE_50': 2,
    'RSI_ABOVE_60': 2,
    'MACD_ABOVE_SIGNAL': 2,
    'MACD_RECENT_CROSSOVER': 4,
    'SMA20_RECENT_CROSSOVER_SMA50': 5,
    'RVOL_ABOVE_1_5': 3,
    'RVOL_ABOVE_2_5': 3,
    'CMF_ABOVE_ZERO': 4,
    'BEARISH_ENGULFING_CANDLE': -5,
    'RSI_BEARISH_DIVERGENCE': -8,
}

MAX_SCORES = {
    'TREND': sum(v for k, v in SIGNAL_SCORES.items() if ('SMA' in k or 'HIGH' in k) and v > 0),
    'MOMENTUM': sum(v for k, v in SIGNAL_SCORES.items() if ('RSI' in k or 'MACD' in k) and v > 0),
    'VOLUME': sum(v for k, v in SIGNAL_SCORES.items() if ('RVOL' in k or 'CMF' in k) and v > 0),
}

MIN_DATA_POINTS = 252
MIN_AVG_TRADE_VALUE = 1_000_000_000
FINAL_SCORE_THRESHOLD = 65