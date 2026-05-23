"""
ML Configuration — Tất cả hyperparameters, feature lists, paths tập trung 1 file.
Đây là Single Source of Truth cho toàn bộ ML pipeline.
"""
from pathlib import Path

# ==============================================================================
# PATHS
# ==============================================================================
BASE_DIR = Path(__file__).resolve().parent.parent  # backend/
DATA_DIR = BASE_DIR / 'data'
RAW_DATA_PATH = DATA_DIR / 'raw' / 'ohlcv_adjusted.parquet'
STOCK_META_PATH = DATA_DIR / 'raw' / 'stock_metadata.parquet'
FEATURES_PATH = DATA_DIR / 'features' / 'features.parquet'
MARKET_STATE_PATH = DATA_DIR / 'features' / 'market_state.parquet'
MODELS_DIR = DATA_DIR / 'models'

# Active model version — thay đổi ở đây khi retrain/tune
# v4: TBM_TP_MULTIPLIER=1.0 (R:R 1:1), same-day TP+SL hit → NaN (loại khỏi training)
MODEL_VERSION = 'v4'

# Đảm bảo thư mục tồn tại
for d in [DATA_DIR / 'raw', DATA_DIR / 'features', MODELS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ==============================================================================
# DATA PARAMS
# ==============================================================================
DATA_START_DATE = '2021-01-01'
TEST_START_DATE = '2025-01-01'

# ==============================================================================
# LIQUIDITY FILTER — Lọc cổ phiếu thanh khoản thấp trước training & prediction
# ==============================================================================
# ADTV = Average Daily Trade Value (close × volume) tính trung bình 20 ngày
MIN_ADTV = 100_000_000        # 100M VND/ngày — cần ít nhất 10× vị thế giao dịch
MIN_PRICE = 1_000             # Loại penny stock dưới 1,000 VND
MAX_ZERO_VOL_RATIO = 0.30     # Max 30% ngày zero volume trong 60 ngày gần nhất
LIQUIDITY_WINDOW = 20         # Số ngày tính ADTV trung bình
ZERO_VOL_LOOKBACK = 60        # Số ngày nhìn lại tính zero volume ratio

# ==============================================================================
# TRIPLE BARRIER METHOD
# ==============================================================================
TBM_TP_MULTIPLIER = 1.0      # Take Profit = 1.0 × ATR (R:R = 1:1) — v4: hạ ngưỡng để tăng tỷ lệ UP/DOWN, giảm SIDEWAY
TBM_SL_MULTIPLIER = 1.0      # Stop Loss = 1 × ATR
TBM_TIME_LIMIT = 10           # 10 trading days
TBM_ATR_PERIOD = 14

# ==============================================================================
# ENSEMBLE SUB-SAMPLING
# ==============================================================================
NUM_SUBSETS = 10
STRIDE = 10            # STRIDE = TBM_TIME_LIMIT → zero label overlap per subset
EMBARGO_DAYS = 10      # Loại EMBARGO_DAYS rows trước TEST_START_DATE → tránh train/test leakage

# ==============================================================================
# FEATURE LISTS
# ==============================================================================

TREND_FEATURES = [
    'sma_20', 'sma_50', 'sma_150',
    'price_vs_sma20', 'price_vs_sma50', 'price_vs_sma150',
    'sma_cross_20_50', 'sma_cross_50_150',
    'adx_14',
    'bb_percent', 'bb_width',
    'close_vs_52w_high',
]

MOMENTUM_FEATURES = [
    'rsi_14',
    'macd_hist', 'macd_hist_diff',
    'stoch_k', 'stoch_d',
    'williams_r',
    'roc_10',
]

VOLUME_FEATURES = [
    'rvol',
    'obv', 'obv_change_5',
    'cmf_20', 'cmf_trend',
    'mfi_14',
    'volume_zscore_20', 'trade_value_zscore',
]

PRICE_ACTION_FEATURES = [
    'return_1d', 'return_3d', 'return_5d', 'return_10d', 'return_20d',
    'volatility_10d', 'volatility_20d',
    'atr_14', 'atr_percent',
    'high_low_range', 'gap_percent',
    'upper_shadow_ratio', 'lower_shadow_ratio',
]

LAG_FEATURES = [
    'rsi_lag_1', 'rsi_lag_3', 'rsi_lag_5',
    'macd_hist_lag_1', 'macd_hist_lag_3', 'macd_hist_lag_5',
    'return_lag_1', 'return_lag_3', 'return_lag_5',
    'volume_zscore_lag_1', 'volume_zscore_lag_3',
]

CATEGORICAL_FEATURES = [
    'exchange', 'industry', 'day_of_week', 'month',
]

WARNING_FEATURES = [
    'days_zero_volume', 'price_below_par', 'avg_volume_decline',
]

# Tổng hợp tất cả numeric features (không gồm categorical)
NUMERIC_FEATURES = (
    TREND_FEATURES
    + MOMENTUM_FEATURES
    + VOLUME_FEATURES
    + PRICE_ACTION_FEATURES
    + LAG_FEATURES
    + WARNING_FEATURES
)

ALL_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES

# ==============================================================================
# LABEL
# ==============================================================================
LABEL_COL = 'label'
LABEL_MAP = {'UP': 0, 'DOWN': 1, 'SIDEWAY': 2}
LABEL_MAP_INV = {v: k for k, v in LABEL_MAP.items()}

# ==============================================================================
# LIGHTGBM DEFAULTS
# ==============================================================================
LGBM_PARAMS = {
    'num_leaves': 63,
    'max_depth': 8,
    'learning_rate': 0.05,
    'n_estimators': 500,
    'min_child_samples': 50,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'reg_alpha': 0.1,
    'reg_lambda': 0.1,
    'class_weight': 'balanced',
    'random_state': 42,
    'verbose': -1,
    'n_jobs': -1,
}

# ==============================================================================
# XGBOOST DEFAULTS
# ==============================================================================
XGB_PARAMS = {
    'max_depth': 8,
    'learning_rate': 0.05,
    'n_estimators': 500,
    'min_child_weight': 50,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'reg_alpha': 0.1,
    'reg_lambda': 0.1,
    'random_state': 42,
    'verbosity': 0,
    'n_jobs': -1,
    'eval_metric': 'mlogloss',
    # 'use_label_encoder' removed — param deleted in XGBoost 2.0+
}

# ==============================================================================
# ISOLATION FOREST (ANOMALY DETECTION)
# ==============================================================================
ISOLATION_FOREST_PARAMS = {
    'contamination': 0.05,
    'n_estimators': 200,
    'random_state': 42,
    'n_jobs': -1,
}

ANOMALY_FEATURES = [
    'volume_zscore_20', 'trade_value_zscore', 'rvol',
    'cmf_20', 'obv_change_5', 'mfi_14',
]

# Anomaly rules thresholds
ANOMALY_VOLUME_ZSCORE_THRESHOLD = 3.0
ANOMALY_RETURN_THRESHOLD = 0.03

# ==============================================================================
# MARKET STATE (RULE-BASED)
# ==============================================================================
MARKET_STATE_MAP = {'UPTREND': 0, 'DOWNTREND': 1, 'SIDEWAY': 2}
MARKET_STATE_MAP_INV = {v: k for k, v in MARKET_STATE_MAP.items()}
MARKET_BREADTH_UPTREND = 0.60    # breadth > 60% → UPTREND
MARKET_BREADTH_DOWNTREND = 0.35  # breadth < 35% → DOWNTREND

# ==============================================================================
# BACKTEST
# ==============================================================================
BACKTEST_INITIAL_CAPITAL = 100_000_000  # 100M VND
BACKTEST_POSITION_SIZE = 0.10           # 10% per position
BACKTEST_MAX_POSITIONS = 10
BACKTEST_SLIPPAGE = 0.002               # 0.2%
BACKTEST_COMMISSION = 0.0025            # 0.25% per side
BACKTEST_MIN_CONFIDENCE = 50            # Chỉ trade khi confidence >= 50%
