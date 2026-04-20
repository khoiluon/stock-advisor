"""
Market State Module — Xác định trạng thái thị trường (UPTREND/DOWNTREND/SIDEWAY).

Thiết kế Swappable:
- RuleBasedMarketState: dùng Market Breadth từ features.parquet (hiện tại)
- MLMarketState: stub cho khi có VNINDEX OHLCV data (tương lai)
- Interface duy nhất: get_market_state_series() — Phase 5/6 gọi hàm này

Khi có VNINDEX data → implement MLMarketState.compute() → đổi use_ml=True
→ rebuild market_state.parquet → retrain. Không cần thay đổi Phase 5/6.

Không import Django, không import ORM.
"""
from abc import ABC, abstractmethod

import numpy as np
import pandas as pd

from .config import (
    MARKET_BREADTH_DOWNTREND,
    MARKET_BREADTH_UPTREND,
    MARKET_STATE_MAP,
)


class BaseMarketState(ABC):
    """Interface chung cho tất cả Market State providers."""

    @abstractmethod
    def compute(self, df_features: pd.DataFrame) -> pd.DataFrame:
        """
        Tính market state cho mỗi ngày giao dịch.

        Parameters
        ----------
        df_features : DataFrame chứa features đã tính (output của features.py).
                      Phải có columns: date, stock_id, adj_close, sma_50, return_5d.

        Returns
        -------
        DataFrame với columns: date, state (str), confidence (int 0-100), breadth_pct (float)
        """
        ...


class RuleBasedMarketState(BaseMarketState):
    """
    Market State dựa trên Market Breadth — KHÔNG cần VNINDEX.

    Logic:
    - breadth_pct = % stocks có close > SMA_50 (tính per ngày từ toàn bộ stocks)
    - avg_market_return_5d = mean(return_5d) toàn market

    Rules:
    - breadth > 60% → UPTREND,   confidence = (breadth - 0.60) / 0.40 * 100
    - breadth < 35% → DOWNTREND, confidence = (0.35 - breadth) / 0.35 * 100
    - else           → SIDEWAY,   confidence = 50 - abs(breadth - 0.475) * 200
    """

    def __init__(
        self,
        uptrend_threshold: float = MARKET_BREADTH_UPTREND,
        downtrend_threshold: float = MARKET_BREADTH_DOWNTREND,
    ) -> None:
        self.uptrend_threshold = uptrend_threshold
        self.downtrend_threshold = downtrend_threshold

    def compute(self, df_features: pd.DataFrame) -> pd.DataFrame:
        """Tính market state per ngày từ toàn bộ stocks."""
        required_cols = {'date', 'stock_id', 'adj_close', 'sma_50', 'return_5d'}
        missing = required_cols - set(df_features.columns)
        if missing:
            raise ValueError(
                f"Thiếu columns: {missing}. "
                f"Chạy feature engineering pipeline trước."
            )

        df = df_features[['date', 'stock_id', 'adj_close', 'sma_50', 'return_5d']].copy()
        df['date'] = pd.to_datetime(df['date'])

        # Loại rows thiếu SMA_50 (warmup period)
        df = df.dropna(subset=['sma_50'])

        # Per ngày: breadth = % stocks có close > sma_50
        df['above_sma50'] = (df['adj_close'] > df['sma_50']).astype(int)

        daily = df.groupby('date').agg(
            breadth_pct=('above_sma50', 'mean'),
            avg_market_return_5d=('return_5d', 'mean'),
            n_stocks=('stock_id', 'count'),
        ).reset_index()

        # Classify state + confidence
        states = []
        confidences = []

        for _, row in daily.iterrows():
            breadth = row['breadth_pct']

            if breadth > self.uptrend_threshold:
                state = 'UPTREND'
                # Confidence: breadth = 0.60 → 0%, breadth = 1.0 → 100%
                conf = min(100, int((breadth - self.uptrend_threshold)
                                    / (1.0 - self.uptrend_threshold) * 100))
            elif breadth < self.downtrend_threshold:
                state = 'DOWNTREND'
                # Confidence: breadth = 0.35 → 0%, breadth = 0.0 → 100%
                conf = min(100, int((self.downtrend_threshold - breadth)
                                    / self.downtrend_threshold * 100))
            else:
                state = 'SIDEWAY'
                # Confidence cao nhất ở giữa (0.475), thấp nhất ở rìa
                midpoint = (self.uptrend_threshold + self.downtrend_threshold) / 2
                max_dist = (self.uptrend_threshold - self.downtrend_threshold) / 2
                dist = abs(breadth - midpoint)
                conf = max(0, min(100, int((1 - dist / max_dist) * 100)))

            states.append(state)
            confidences.append(conf)

        daily['state'] = states
        daily['confidence'] = confidences

        result = daily[['date', 'state', 'confidence', 'breadth_pct']].copy()
        result = result.sort_values('date').reset_index(drop=True)

        print(f"Market state computed: {len(result)} trading days")
        print(f"  State distribution:\n{result['state'].value_counts().to_string()}")

        return result


class MLMarketState(BaseMarketState):
    """
    TODO: Implement khi có VNINDEX OHLCV data.

    Plan:
    - Train single LightGBM trên VNINDEX features
      (SMA 20/50/200, RSI, MACD, volatility, breadth)
    - Label: TBM trên VNINDEX
    - Confidence từ predict_proba
    """

    def compute(self, df_features: pd.DataFrame) -> pd.DataFrame:
        raise NotImplementedError(
            "MLMarketState chưa implement. Cần VNINDEX OHLCV data.\n"
            "Xem RuleBasedMarketState để dùng tạm."
        )


# ==============================================================================
# Public Interface — Phase 5/6 chỉ gọi hàm này
# ==============================================================================


def get_market_state_series(
    df_features: pd.DataFrame,
    use_ml: bool = False,
) -> pd.DataFrame:
    """
    Return DataFrame(date, state, confidence, breadth_pct) cho mọi ngày.

    Parameters
    ----------
    df_features : DataFrame chứa features đã tính.
    use_ml      : True → dùng MLMarketState (cần VNINDEX data).
                  False → dùng RuleBasedMarketState (default).

    Returns
    -------
    DataFrame với columns: date, state, confidence, breadth_pct
    """
    provider: BaseMarketState = MLMarketState() if use_ml else RuleBasedMarketState()
    return provider.compute(df_features)


def merge_market_state(
    df_features: pd.DataFrame,
    df_market_state: pd.DataFrame,
) -> pd.DataFrame:
    """
    Merge market_state vào features DataFrame theo date.

    Thêm column 'market_state' (int: 0=UPTREND, 1=DOWNTREND, 2=SIDEWAY)
    dùng làm categorical feature cho model.

    Parameters
    ----------
    df_features     : Features DataFrame (output của build_features)
    df_market_state : Market state DataFrame (output của get_market_state_series)

    Returns
    -------
    DataFrame gốc + column 'market_state' (int encoded)
    """
    df_features = df_features.copy()
    df_features['date'] = pd.to_datetime(df_features['date'])

    ms = df_market_state[['date', 'state']].copy()
    ms['date'] = pd.to_datetime(ms['date'])
    ms['market_state'] = ms['state'].map(MARKET_STATE_MAP)

    df_merged = df_features.merge(
        ms[['date', 'market_state']],
        on='date',
        how='left',
    )

    # Fill NaN (ngày trước khi có đủ SMA_50 data) bằng SIDEWAY (2)
    df_merged['market_state'] = (
        df_merged['market_state'].fillna(MARKET_STATE_MAP['SIDEWAY']).astype(int)
    )

    n_merged = df_merged['market_state'].notna().sum()
    print(f"Merged market_state: {n_merged:,} / {len(df_merged):,} rows")
    print(f"  Distribution: {df_merged['market_state'].value_counts().to_dict()}")

    return df_merged
