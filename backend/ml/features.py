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
    df['obv'] = obv if obv is not None else 0
    df['obv_change_5'] = df['obv'].pct_change(5).replace([np.inf, -np.inf], 0)

    df['cmf_20'] = ta.cmf(h, l, c, v, length=20)
    df['cmf_trend'] = df['cmf_20'].diff(5) if 'cmf_20' in df.columns else np.nan

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


def compute_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Tính features cho tất cả stocks.

    Input:  DataFrame với columns [stock_id, date, adj_open, adj_high, adj_low, adj_close,
            adj_volume, exchange, industry]
    Output: DataFrame gốc + ~50 feature columns, đã drop warmup NaN rows.
    """
    df = df.copy()
    df = df.sort_values(['stock_id', 'date']).reset_index(drop=True)

    results = []
    grouped = df.groupby('stock_id')
    total = len(grouped)

    for i, (ticker, group) in enumerate(grouped, 1):
        if len(group) < 60:
            # Cần ít nhất 60 rows cho rolling windows cơ bản
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
    from .config import NUMERIC_FEATURES
    available = [f for f in NUMERIC_FEATURES if f in df_all.columns]
    nan_ratio = df_all[available].isna().mean(axis=1)
    df_all = df_all[nan_ratio < 0.2].reset_index(drop=True)

    print(f"Feature engineering hoàn tất: {df_all.shape[0]} rows, {len(available)} numeric features")
    return df_all
