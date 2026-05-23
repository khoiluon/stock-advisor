"""
Triple Barrier Method — Gán nhãn UP/DOWN/SIDEWAY cho mỗi observation.

Logic (De Prado):
- Tại thời điểm T, tính ATR(14) tại T.
- Take Profit barrier = close_T + TP_MULT × ATR(14)
- Stop Loss barrier   = close_T - SL_MULT × ATR(14)
- Time Limit = 10 trading days.
- Quét forward từ T+1 → T+10:
  + Nếu adj_high chạm TP TRƯỚC khi adj_low chạm SL → UP
  + Nếu adj_low chạm SL TRƯỚC khi adj_high chạm TP → DOWN
  + Cả hai chạm trong CÙNG 1 ngày → AMBIGUOUS → gán NaN (loại khỏi training thay vì
    ép về DOWN gây bias dữ liệu).
  + Hết 10 ngày mà không chạm barrier nào → SIDEWAY
- Giữ nguyên rows có label=NaN (warmup ATR, 10 ngày cuối stock, ambiguous);
  training pipeline sẽ dropna(label) trước khi fit.

Output columns: label (nullable Int64: 0=UP, 1=DOWN, 2=SIDEWAY, <NA>=ambiguous/no-data),
                target_price (TP barrier), stop_loss (SL barrier)
"""
import numpy as np
import pandas as pd
import pandas_ta_classic as ta

from .config import (
    TBM_TP_MULTIPLIER,
    TBM_SL_MULTIPLIER,
    TBM_TIME_LIMIT,
    TBM_ATR_PERIOD,
    LABEL_MAP,
)


def _apply_tbm_single_stock(df: pd.DataFrame) -> pd.DataFrame:
    """Apply Triple Barrier Method cho 1 mã. df đã sort by date asc."""
    c = df['adj_close'].values
    h = df['adj_high'].values
    l = df['adj_low'].values

    # ATR tính bằng pandas-ta-classic rồi lấy .values
    atr_series = ta.atr(
        pd.Series(h), pd.Series(l), pd.Series(c),
        length=TBM_ATR_PERIOD
    )
    atr = atr_series.values if atr_series is not None else np.full(len(c), np.nan)

    n = len(c)
    labels = np.full(n, np.nan)
    target_prices = np.full(n, np.nan)
    stop_losses = np.full(n, np.nan)

    # Không label được TBM_TIME_LIMIT rows cuối (thiếu forward data)
    for i in range(n - TBM_TIME_LIMIT):
        atr_i = atr[i]
        if np.isnan(atr_i) or atr_i <= 0:
            continue

        close_i = c[i]
        tp_barrier = close_i + TBM_TP_MULTIPLIER * atr_i
        sl_barrier = close_i - TBM_SL_MULTIPLIER * atr_i

        target_prices[i] = tp_barrier
        stop_losses[i] = sl_barrier

        hit = LABEL_MAP['SIDEWAY']  # default: time limit reached
        for j in range(i + 1, min(i + 1 + TBM_TIME_LIMIT, n)):
            hit_tp = h[j] >= tp_barrier
            hit_sl = l[j] <= sl_barrier

            if hit_tp and hit_sl:
                # Cả hai barrier cùng bị chạm trong 1 ngày — không thể xác định
                # TP trước hay SL trước nếu chỉ có OHLC. Trước đây ép về DOWN gây
                # bias label (over-count DOWN); giờ gán NaN để loại khỏi training.
                hit = np.nan
                break
            elif hit_tp:
                hit = LABEL_MAP['UP']
                break
            elif hit_sl:
                hit = LABEL_MAP['DOWN']
                break

        labels[i] = hit

    df = df.copy()
    df['label'] = labels
    df['target_price'] = target_prices
    df['stop_loss'] = stop_losses

    # KHÔNG dropna ở đây nữa (v4): giữ nguyên rows có label=NaN cho:
    #   - warmup ATR (rows đầu)
    #   - TBM_TIME_LIMIT rows cuối stock (không đủ forward data)
    #   - ambiguous same-day TP+SL hit
    # Training pipeline sẽ dropna(label) trước khi fit; backtest/walk-forward
    # vẫn cần các rows này để biết feature tại thời điểm chưa label được.
    # Dùng pandas nullable Int64 để giữ kiểu integer mà cho phép NA.
    df['label'] = df['label'].astype('Int64')

    return df


def apply_triple_barrier(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply Triple Barrier Method cho tất cả stocks.

    Input: DataFrame phải có columns [stock_id, date, adj_close, adj_high, adj_low]
    Output: DataFrame gốc + columns [label, target_price, stop_loss]
    """
    df = df.sort_values(['stock_id', 'date']).reset_index(drop=True)

    results = []
    grouped = df.groupby('stock_id')
    total = len(grouped)

    for i, (ticker, group) in enumerate(grouped, 1):
        if len(group) < TBM_ATR_PERIOD + TBM_TIME_LIMIT + 1:
            continue

        try:
            labeled = _apply_tbm_single_stock(group)
            results.append(labeled)
        except Exception as e:
            print(f"[WARN] Lỗi TBM cho {ticker}: {e}")
            continue

        if i % 200 == 0:
            print(f"  Labeling: {i}/{total} stocks...")

    if not results:
        raise ValueError("Không có stock nào đủ data để label!")

    df_all = pd.concat(results, ignore_index=True)

    # Thống kê phân bố label — base = số rows có label (không tính NaN)
    n_total = len(df_all)
    n_na = int(df_all['label'].isna().sum())
    n_labeled = n_total - n_na
    counts = df_all['label'].value_counts(dropna=True).sort_index()
    label_inv = {v: k for k, v in LABEL_MAP.items()}
    print(f"\nLabel distribution (base = {n_labeled:,} labeled rows):")
    for lbl, cnt in counts.items():
        pct = (cnt / n_labeled * 100) if n_labeled > 0 else 0.0
        print(f"  {label_inv.get(int(lbl), lbl)}: {cnt:,} ({pct:.1f}%)")
    print(f"  NaN  (warmup + last 10 rows + ambiguous): {n_na:,} ({n_na / n_total * 100:.1f}% of total)")
    print(f"  Total rows kept: {n_total:,} (labeled + NaN)")

    return df_all


# Alias dùng trong scripts/build_features.py
create_labeled_dataset = apply_triple_barrier
