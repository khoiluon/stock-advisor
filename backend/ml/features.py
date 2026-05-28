"""
Feature Engineering Pipeline — Tính ~50 technical features từ adjusted OHLCV.

RULE: Chỉ dùng .shift(n) với n > 0 (lookback). KHÔNG BAO GIỜ dùng .shift(-n).
Tất cả features tại ngày T chỉ dùng data ≤ T.

Input:  DataFrame với columns [stock_id, date, adj_open, adj_high, adj_low, adj_close, adj_volume, exchange, industry]
Output: DataFrame gốc + ~50 feature columns
"""
import pandas as pd
import numpy as np
import pandas_ta_classic as ta


def _compute_single_stock_features(df: pd.DataFrame) -> pd.DataFrame:
    """Tính features cho 1 mã cổ phiếu. df đã sort by date ascending."""
    o = df['adj_open']
    h = df['adj_high']
    l = df['adj_low']
    c = df['adj_close']
    v = df['adj_volume']


    # ===== TREND =====
    df['sma_20'] = ta.sma(c, length=20)
    df['sma_50'] = ta.sma(c, length=50)
    df['sma_150'] = ta.sma(c, length=150)

    df['price_vs_sma20'] = (c - df['sma_20']) / df['sma_20']
    df['price_vs_sma50'] = (c - df['sma_50']) / df['sma_50']
    df['price_vs_sma150'] = (c - df['sma_150']) / df['sma_150']

    df['sma_cross_20_50'] = (df['sma_20'] > df['sma_50']).astype(int)
    df['sma_cross_50_150'] = (df['sma_50'] > df['sma_150']).astype(int)

    adx_df = ta.adx(h, l, c, length=14)
    if adx_df is not None and 'ADX_14' in adx_df.columns:
        df['adx_14'] = adx_df['ADX_14']
    else:
        df['adx_14'] = np.nan

    bb = ta.bbands(c, length=20, std=2)

    if bb is not None:
        bbu = bb.filter(like='BBU').iloc[:, 0]
        bbl = bb.filter(like='BBL').iloc[:, 0]
        bbm = bb.filter(like='BBM').iloc[:, 0]
        bb_range = bbu - bbl
        df['bb_percent'] = np.where(bb_range != 0, (c - bbl) / bb_range, 0.5)
        df['bb_width'] = np.where(bbm != 0, bb_range / bbm, 0)
    else:
        df['bb_percent'] = np.nan
        df['bb_width'] = np.nan

    high_252 = h.rolling(window=252, min_periods=60).max()
    df['close_vs_52w_high'] = np.where(high_252 != 0, c / high_252, np.nan)

    # ===== MOMENTUM =====
    df['rsi_14'] = ta.rsi(c, length=14)

    macd_df = ta.macd(c, fast=12, slow=26, signal=9)
    if macd_df is not None:
        macd_col = macd_df.filter(like='MACDh').iloc[:, 0] if macd_df.filter(like='MACDh').shape[1] > 0 else macd_df.iloc[:, 2]
        df['macd_hist'] = macd_col
    else:
        df['macd_hist'] = np.nan
    df['macd_hist_diff'] = df['macd_hist'].diff(1)

    stoch = ta.stoch(h, l, c, k=14, d=3)
    if stoch is not None:
        df['stoch_k'] = stoch.iloc[:, 0]
        df['stoch_d'] = stoch.iloc[:, 1]
    else:
        df['stoch_k'] = np.nan
        df['stoch_d'] = np.nan

    wr = ta.willr(h, l, c, length=14)
    df['williams_r'] = wr if wr is not None else np.nan

    df['roc_10'] = ta.roc(c, length=10)

    # ===== VOLUME & MONEY FLOW =====
    vol_sma_50 = ta.sma(v, length=50)
    df['rvol'] = np.where(vol_sma_50 != 0, v / vol_sma_50, 0)
    df['rvol'] = df['rvol'].replace([np.inf, -np.inf], 0)

    obv = ta.obv(c, v)
    df['obv'] = obv if obv is not None else np.nan
    df['obv_change_5'] = df['obv'].pct_change(5).replace([np.inf, -np.inf], 0).fillna(0)

    cmf = ta.cmf(h, l, c, v, length=20)
    df['cmf_20'] = cmf if cmf is not None else np.nan
    df['cmf_trend'] = df['cmf_20'].diff(5)

    df['mfi_14'] = ta.mfi(h, l, c, v, length=14)

    vol_mean_20 = v.rolling(20).mean()
    vol_std_20 = v.rolling(20).std()
    df['volume_zscore_20'] = np.where(vol_std_20 != 0, (v - vol_mean_20) / vol_std_20, 0)

    trade_value = c * v
    tv_mean_20 = trade_value.rolling(20).mean()
    tv_std_20 = trade_value.rolling(20).std()
    df['trade_value_zscore'] = np.where(tv_std_20 != 0, (trade_value - tv_mean_20) / tv_std_20, 0)

    # ===== PRICE ACTION & VOLATILITY =====
    df['return_1d'] = c.pct_change(1)
    df['return_3d'] = c.pct_change(3)
    df['return_5d'] = c.pct_change(5)
    df['return_10d'] = c.pct_change(10)
    df['return_20d'] = c.pct_change(20)

    df['volatility_10d'] = df['return_1d'].rolling(10).std()
    df['volatility_20d'] = df['return_1d'].rolling(20).std()

    atr = ta.atr(h, l, c, length=14)
    df['atr_14'] = atr if atr is not None else np.nan
    df['atr_percent'] = np.where(c != 0, df['atr_14'] / c, np.nan)

    df['high_low_range'] = np.where(c != 0, (h - l) / c, 0)
    df['gap_percent'] = np.where(c.shift(1) != 0, (o - c.shift(1)) / c.shift(1), 0)

    body_top = pd.concat([o, c], axis=1).max(axis=1)
    body_bot = pd.concat([o, c], axis=1).min(axis=1)
    candle_range = h - l
    df['upper_shadow_ratio'] = np.where(candle_range != 0, (h - body_top) / candle_range, 0)
    df['lower_shadow_ratio'] = np.where(candle_range != 0, (body_bot - l) / candle_range, 0)

    # ===== SIDEWAY / RANGE DETECTION =====
    # ADX < 20 = xu hướng yếu, tiềm năng sideway
    df['adx_weak'] = (df['adx_14'] < 20).astype(int)

    # Bollinger squeeze: giá nằm giữa dải (30%-70%) = sideway
    df['bb_squeeze'] = ((df['bb_percent'] > 0.3) & (df['bb_percent'] < 0.7)).astype(int)

    # Biên độ dao động 10 ngày / SMA20 — nhỏ = đi ngang
    h_10d = h.rolling(10).max()
    l_10d = l.rolling(10).min()
    df['range_pct'] = np.where(df['sma_20'] != 0, (h_10d - l_10d) / df['sma_20'], np.nan)

    # Khoảng cách giá vs MA5 — nhỏ = giá đứng yên
    ma5 = ta.sma(c, length=5)
    df['close_vs_ma5_pct'] = np.where(c != 0, (c - ma5).abs() / c, np.nan)

    # Sức mạnh xu hướng — abs(close - close 10d ago) / ATR
    df['trend_strength'] = np.where(df['atr_14'] != 0, (c - c.shift(10)).abs() / df['atr_14'], np.nan)

    # ADX slope: ADX đang giảm = xu hướng yếu đi → sideway
    df['adx_slope'] = df['adx_14'] - df['adx_14'].shift(5)

    # ===== REGIME DETECTION =====
    # KAMA — Kaufman Adaptive Moving Average (theo noise)
    _kama = _compute_kama(c.values)
    df['kama'] = _kama
    df['price_vs_kama'] = np.where(_kama != 0, (c.values - _kama) / _kama, np.nan)

    # Hurst Exponent — >0.5 trend, <0.5 mean-revert (rolling 100)
    df['hurst_exponent'] = _compute_rolling_hurst(c.values, window=100)

    # Choppiness Index — 100=sideway, 0=strong trend
    df['choppiness_index'] = _compute_choppiness(h.values, l.values, c.values)

    # ===== LAG FEATURES =====
    df['rsi_lag_1'] = df['rsi_14'].shift(1)
    df['rsi_lag_3'] = df['rsi_14'].shift(3)
    df['rsi_lag_5'] = df['rsi_14'].shift(5)

    df['macd_hist_lag_1'] = df['macd_hist'].shift(1)
    df['macd_hist_lag_3'] = df['macd_hist'].shift(3)
    df['macd_hist_lag_5'] = df['macd_hist'].shift(5)

    df['return_lag_1'] = df['return_1d'].shift(1)
    df['return_lag_3'] = df['return_1d'].shift(3)
    df['return_lag_5'] = df['return_1d'].shift(5)

    df['volume_zscore_lag_1'] = df['volume_zscore_20'].shift(1)
    df['volume_zscore_lag_3'] = df['volume_zscore_20'].shift(3)

    # ===== WARNING FEATURES (Early Warning for survivorship) =====
    df['days_zero_volume'] = (v == 0).rolling(30, min_periods=1).sum()
    df['price_below_par'] = (c < 10000).astype(int)
    vol_sma_20 = ta.sma(v, length=20)
    vol_sma_120 = ta.sma(v, length=120)
    df['avg_volume_decline'] = np.where(vol_sma_120 != 0, vol_sma_20 / vol_sma_120, 1.0)

    # ===== CALENDAR =====
    if pd.api.types.is_datetime64_any_dtype(df['date']):
        df['day_of_week'] = df['date'].dt.dayofweek
        df['month'] = df['date'].dt.month
    else:
        dt = pd.to_datetime(df['date'])
        df['day_of_week'] = dt.dt.dayofweek
        df['month'] = dt.dt.month

    return df


# ==============================================================================
# REGIME DETECTION HELPERS
# ==============================================================================
def _compute_kama(close: np.ndarray) -> np.ndarray:
    """Kaufman Adaptive Moving Average — phản ứng nhanh khi trend, chậm khi sideway."""
    n = len(close)
    if n < 10:
        return np.full(n, np.nan)

    er_period = 10
    fast_n, slow_n = 2, 30
    fast_sc = 2.0 / (fast_n + 1)
    slow_sc = 2.0 / (slow_n + 1)

    # Efficiency Ratio = abs(direction) / volatility
    direction = np.abs(close[er_period:] - close[:-er_period])
    volatility = np.zeros(n - er_period)
    for i in range(er_period, n):
        volatility[i - er_period] = np.sum(np.abs(np.diff(close[i - er_period:i + 1])))

    er = np.zeros(n)
    with np.errstate(divide='ignore', invalid='ignore'):
        er[er_period:] = np.where(volatility != 0, direction / volatility, 0.0)

    # Smoothing Constant
    sc = (er * (fast_sc - slow_sc) + slow_sc) ** 2

    # Recursive KAMA
    kama = np.full(n, np.nan)
    kama[er_period] = close[er_period]
    for i in range(er_period + 1, n):
        kama[i] = kama[i - 1] + sc[i] * (close[i] - kama[i - 1])

    return kama


def _compute_rolling_hurst(close: np.ndarray, window: int = 100) -> np.ndarray:
    """Rolling Hurst Exponent (R/S method). >0.5=trending, <0.5=mean-reverting."""
    n = len(close)
    hurst = np.full(n, np.nan)
    if n < window + 2:
        return hurst

    log_close = np.log(close)
    for i in range(window, n):
        seg = log_close[i - window:i + 1]
        returns = np.diff(seg)
        if len(returns) < 2:
            continue
        r_mean = returns.mean()
        cum_dev = np.cumsum(returns - r_mean)
        R = cum_dev.max() - cum_dev.min()
        S = returns.std(ddof=1)
        if S > 1e-12 and R > 0:
            hurst[i] = np.log(R / S) / np.log(window)

    return hurst


def _compute_choppiness(high: np.ndarray, low: np.ndarray, close: np.ndarray) -> np.ndarray:
    """Choppiness Index — 100=sideway, 0=strong trend. Dựa trên ATR và biên độ."""
    n = len(high)
    period = 14
    ci = np.full(n, np.nan)

    if n < period + 1:
        return ci

    # True Range
    tr = np.maximum(
        high - low,
        np.maximum(
            np.abs(high - np.roll(close, 1)),
            np.abs(low - np.roll(close, 1)),
        ),
    )
    tr[0] = high[0] - low[0]

    # Tổng True Range và biên độ 14 ngày
    for i in range(period, n):
        sum_tr = np.sum(tr[i - period + 1:i + 1])
        max_high = np.max(high[i - period + 1:i + 1])
        min_low = np.min(low[i - period + 1:i + 1])
        denom = max_high - min_low
        if sum_tr > 0 and denom > 0:
            ci[i] = 100.0 * np.log10(sum_tr / denom) / np.log10(period)

    return ci


def compute_features(df: pd.DataFrame, apply_liquidity_filter: bool = True) -> pd.DataFrame:
    from .config import (
        NUMERIC_FEATURES, MIN_ADTV, MIN_PRICE,
        MAX_ZERO_VOL_RATIO, LIQUIDITY_WINDOW, ZERO_VOL_LOOKBACK,
    )

    df = df.copy()
    df = df.sort_values(['stock_id', 'date']).reset_index(drop=True)

    results = []
    grouped = df.groupby('stock_id')
    total = len(grouped)

    for i, (ticker, group) in enumerate(grouped, 1):
        if len(group) < 160:
            # Cần ít nhất 160 rows: 150 (SMA150 warmup) + 10 (TBM_TIME_LIMIT)
            continue

        try:
            featured = _compute_single_stock_features(group.copy())
            results.append(featured)
        except Exception as e:
            print(f"[WARN] Lỗi compute features cho {ticker}: {e}")
            continue

        if i % 200 == 0:
            print(f"  Feature engineering: {i}/{total} stocks...")

    if not results:
        raise ValueError("Không có stock nào đủ data để tính features!")

    df_all = pd.concat(results, ignore_index=True)

    # Drop warmup rows (NaN do rolling windows)
    # Giữ lại rows có ít nhất 80% features không NaN
    available = [f for f in NUMERIC_FEATURES if f in df_all.columns]
    nan_ratio = df_all[available].isna().mean(axis=1)
    df_all = df_all[nan_ratio < 0.2].reset_index(drop=True)

    print(f"Feature engineering hoàn tất: {df_all.shape[0]} rows, {len(available)} numeric features")

    # ── Liquidity filter ──
    if apply_liquidity_filter:
        before = df_all['stock_id'].nunique()
        df_all = _filter_illiquid_stocks(
            df_all,
            min_adtv=MIN_ADTV,
            min_price=MIN_PRICE,
            max_zero_vol_ratio=MAX_ZERO_VOL_RATIO,
            adtv_window=LIQUIDITY_WINDOW,
            zero_vol_lookback=ZERO_VOL_LOOKBACK,
        )
        after = df_all['stock_id'].nunique()
        print(f"Liquidity filter: {before} → {after} stocks "
              f"(loại {before - after} mã thanh khoản thấp, "
              f"ADTV≥{MIN_ADTV/1e6:.0f}M, price≥{MIN_PRICE}, "
              f"zero_vol<{MAX_ZERO_VOL_RATIO:.0%})")

    return df_all


def _filter_illiquid_stocks(
    df: pd.DataFrame,
    min_adtv: float,
    min_price: float,
    max_zero_vol_ratio: float,
    adtv_window: int = 20,
    zero_vol_lookback: int = 60,
) -> pd.DataFrame:

    drop_tickers = set()

    for ticker, group in df.groupby('stock_id'):
        g = group.sort_values('date')
        c = g['adj_close']
        v = g['adj_volume']

        # 1. giá trị trung bình giao dịch thấp
        trade_value = c * v
        adtv_20 = trade_value.rolling(adtv_window, min_periods=10).mean()
        median_adtv = adtv_20.median()
        if pd.isna(median_adtv) or median_adtv < min_adtv:
            drop_tickers.add(ticker)
            continue

        # 2. giá thấp
        median_price = c.median()
        if pd.isna(median_price) or median_price < min_price:
            drop_tickers.add(ticker)
            continue

        # 3. 30% trong 60 ngày gần nhất có volume = 0
        recent = v.tail(zero_vol_lookback)
        zero_ratio = (recent == 0).sum() / len(recent)
        if zero_ratio > max_zero_vol_ratio:
            drop_tickers.add(ticker)
            continue

    df_filtered = df[~df['stock_id'].isin(drop_tickers)].reset_index(drop=True)
    return df_filtered
