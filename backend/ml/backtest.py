"""Vectorized ML Portfolio Backtest Engine.

Logic mua/bán:
  - MUA: Mỗi ngày chọn Top-K mã có confidence >= 65% prediction UP.
    Mua tại giá open ngày sau, nhân (1 + BUY_COST).
  - BÁN: Kiểm tra intraday TP/SL.
    + high >= TP -> bán tại giá TP
    + low  <= SL -> bán tại giá SL
    + Cả 2 cùng ngày -> giả định SL trước (conservative)
    + Hết 10 ngày -> bán tại close
  - T+2.5: Không kiểm tra TP/SL trong 2 ngày đầu sau khi mua.
    Cổ phiếu mua T0 về tài khoản chiều T+2, chỉ bán được từ T+3.
  - Quản lý vốn: Max 10 vị thế, 10% vốn/vị thế, lot 100 cổ phiếu.
  - Chi phí: BUY_COST khi mua, SELL_COST khi bán (đã bao gồm slippage + phí + thuế).

Không import Django; nhận pandas DataFrame, trả về dataclass + DataFrame.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from .config import (
    BACKTEST_BUY_COST,
    BACKTEST_INITIAL_CAPITAL,
    BACKTEST_LOT_SIZE,
    BACKTEST_MAX_POSITIONS,
    BACKTEST_MIN_CONFIDENCE,
    BACKTEST_POSITION_SIZE,
    BACKTEST_SELL_COST,
    BACKTEST_SETTLEMENT_DAYS,
    BACKTEST_TIME_LIMIT,
    BACKTEST_TOP_K,
    BACKTEST_TRAILING_MULTIPLIER,
    DATA_DIR,
    MODEL_VERSION,
)


# ==============================================================================
# DATACLASSES
# ==============================================================================
@dataclass
class Position:
    """Vị thế đang mở."""
    stock_id: str
    entry_date: pd.Timestamp
    entry_price: float          # Giá thực trả (đã +buy_cost)
    raw_entry_price: float      # Giá open gốc (chưa cộng phí) — debug
    tp_price: float
    sl_price: float
    shares: int
    trailing_high: float = 0.0    # Đỉnh cao nhất từ khi mua (trailing stop)
    sl_gap: float = 0.0           # Khoảng cách SL từ entry (ATR-based)
    days_held: int = 0          # Tăng mỗi ngày trading, dùng cho T+2.5 + time limit


@dataclass
class Trade:
    """Giao dịch đã đóng."""
    stock_id: str
    entry_date: pd.Timestamp
    exit_date: pd.Timestamp
    entry_price: float
    exit_price: float           # Giá thực nhận (đã -sell_cost)
    raw_exit_price: float       # Giá gốc tại điểm bán (chưa trừ phí)
    shares: int
    reason: str                 # 'TP' | 'SL' | 'SL_SAME_DAY' | 'TIME_EXIT' | 'EOB_CLOSE'
    pnl: float                  # VND, sau phí mua + bán
    pnl_pct: float              # % trên vốn ban đầu của lệnh


@dataclass
class BacktestResult:
    """Kết quả backtest."""
    equity_curve: pd.DataFrame  # columns: date, portfolio_value, cash, holdings_value
    trades: pd.DataFrame        # columns theo Trade
    metrics: Dict[str, float] = field(default_factory=dict)
    params: Dict[str, float] = field(default_factory=dict)


# ==============================================================================
# CORE BACKTEST ENGINE
# ==============================================================================
def run_backtest(
    df_features: pd.DataFrame,
    df_predictions: pd.DataFrame,
    initial_capital: float = BACKTEST_INITIAL_CAPITAL,
    position_size: float = BACKTEST_POSITION_SIZE,
    max_positions: int = BACKTEST_MAX_POSITIONS,
    top_k: int = BACKTEST_TOP_K,
    min_confidence: int = BACKTEST_MIN_CONFIDENCE,
    lot_size: int = BACKTEST_LOT_SIZE,
    buy_cost: float = BACKTEST_BUY_COST,
    sell_cost: float = BACKTEST_SELL_COST,
    settlement_days: int = BACKTEST_SETTLEMENT_DAYS,
    time_limit: int = BACKTEST_TIME_LIMIT,
    verbose: bool = True,
) -> BacktestResult:
    """Chạy backtest walk-forward trên test set.

    Parameters
    ----------
    df_features : DataFrame với OHLCV adjusted (cần adj_open, adj_high, adj_low,
                  adj_close, stock_id, date). Chỉ cần các columns này cho engine
                  — features khác để predict_all() sinh df_predictions.
    df_predictions : Output của predict_all(). Cần: stock_id, date, trend_class,
                  confidence_score, target_price, stop_loss.
    """
    # 1. CHUẨN BỊ DỮ LIỆU --------------------------------------------------
    needed_feat_cols = ['stock_id', 'date', 'adj_open', 'adj_high', 'adj_low', 'adj_close']
    missing_feat = [c for c in needed_feat_cols if c not in df_features.columns]
    if missing_feat:
        raise ValueError(f"df_features thiếu columns: {missing_feat}")

    needed_pred_cols = [
        'stock_id', 'date', 'trend_class', 'confidence_score',
        'target_price', 'stop_loss',
    ]
    missing_pred = [c for c in needed_pred_cols if c not in df_predictions.columns]
    if missing_pred:
        raise ValueError(f"df_predictions thiếu columns: {missing_pred}")

    df_feat = df_features[needed_feat_cols].copy()
    df_feat['date'] = pd.to_datetime(df_feat['date'])
    df_pred = df_predictions[needed_pred_cols].copy()
    df_pred['date'] = pd.to_datetime(df_pred['date'])

    # Merge predictions vào features để có OHLCV cùng prediction theo (stock, date)
    df = df_feat.merge(df_pred, on=['stock_id', 'date'], how='left')
    df = df.sort_values(['date', 'stock_id']).reset_index(drop=True)

    # ── Market state per date (breadth-based: % stocks above SMA50) ──
    market_states: Dict[pd.Timestamp, str] = {}
    if 'sma_50' in df_features.columns and 'adj_close' in df_features.columns:
        breadth = (
            df_features[['date', 'stock_id', 'adj_close', 'sma_50']]
            .dropna(subset=['sma_50'])
            .assign(above_sma=lambda x: (x['adj_close'] > x['sma_50']).astype(int))
            .groupby('date')['above_sma']
            .agg(['sum', 'count'])
        )
        breadth['pct'] = breadth['sum'] / breadth['count']
        for d, row in breadth.iterrows():
            pct = row['pct']
            if pct >= 0.60:
                market_states[d] = 'UPTREND'
            elif pct < 0.35:
                market_states[d] = 'DOWNTREND'
            else:
                market_states[d] = 'SIDEWAY'
        if verbose:
            u = sum(1 for v in market_states.values() if v == 'UPTREND')
            dw = sum(1 for v in market_states.values() if v == 'DOWNTREND')
            sw = sum(1 for v in market_states.values() if v == 'SIDEWAY')
            print(f"Market states: UPTREND={u}, DOWNTREND={dw}, SIDEWAY={sw}")

    # Lookup tables để truy cập O(1):
    # ohlc_lookup[(date, stock_id)] = row dict
    # Vì stock_id là string ngắn, dùng dict lồng cũng OK.
    ohlc_lookup: Dict[pd.Timestamp, Dict[str, Dict[str, float]]] = {}
    pred_by_date: Dict[pd.Timestamp, pd.DataFrame] = {}

    for d, group in df.groupby('date', sort=True):
        ohlc_lookup[d] = {
            row.stock_id: {
                'open': float(row.adj_open) if pd.notna(row.adj_open) else np.nan,
                'high': float(row.adj_high) if pd.notna(row.adj_high) else np.nan,
                'low': float(row.adj_low) if pd.notna(row.adj_low) else np.nan,
                'close': float(row.adj_close) if pd.notna(row.adj_close) else np.nan,
            }
            for row in group.itertuples(index=False)
        }
        # Chỉ giữ rows có prediction (signals candidate) — bỏ rows chỉ có OHLC
        # không có trend_class.
        preds_today = group.dropna(subset=['trend_class', 'confidence_score'])
        if not preds_today.empty:
            pred_by_date[d] = preds_today

    trading_days: List[pd.Timestamp] = sorted(ohlc_lookup.keys())
    if len(trading_days) < 2:
        raise ValueError(f"Cần ít nhất 2 trading days, có {len(trading_days)}.")

    if verbose:
        print(
            f"Backtest range: {trading_days[0].date()} → {trading_days[-1].date()} "
            f"({len(trading_days)} trading days)"
        )

    # 2. VÒNG LẶP CHÍNH ----------------------------------------------------
    cash: float = float(initial_capital)
    open_positions: List[Position] = []
    closed_trades: List[Trade] = []
    equity_records: List[Dict[str, float]] = []

    for i, today in enumerate(trading_days):
        next_day: Optional[pd.Timestamp] = (
            trading_days[i + 1] if i + 1 < len(trading_days) else None
        )

        # a. EXIT PHASE ---------------------------------------------------
        positions_still_open: List[Position] = []
        for pos in open_positions:
            pos.days_held += 1

            day_ohlc = ohlc_lookup.get(today, {}).get(pos.stock_id)
            if day_ohlc is None or any(
                pd.isna(day_ohlc[k]) for k in ('high', 'low', 'close')
            ):
                # Không có data hôm nay (delisted/halted) — giữ vị thế
                positions_still_open.append(pos)
                continue

            # T+2.5: settlement_days đầu chưa được bán → giữ
            if pos.days_held <= settlement_days:
                positions_still_open.append(pos)
                continue

            day_high = day_ohlc['high']
            day_low = day_ohlc['low']
            day_close = day_ohlc['close']

            # Trailing stop: kéo SL lên theo đỉnh mới
            if pos.trailing_high > 0 and pos.sl_gap > 0:
                if day_high > pos.trailing_high:
                    pos.trailing_high = day_high
                trailing_sl = pos.trailing_high - pos.sl_gap * BACKTEST_TRAILING_MULTIPLIER
                if trailing_sl > pos.sl_price:
                    pos.sl_price = trailing_sl

            exit_raw_price: Optional[float] = None
            exit_reason: Optional[str] = None

            # Phân biệt trailing stop exit (có thể lời) vs fixed SL (luôn lỗ)
            orig_sl = pos.raw_entry_price - pos.sl_gap if pos.sl_gap > 0 else pos.sl_price
            trailing_used = pos.sl_price > orig_sl * 1.001  # đã được kéo lên

            if day_high >= pos.tp_price and day_low <= pos.sl_price:
                exit_raw_price = pos.sl_price
                exit_reason = 'TRAIL_SAME_DAY' if trailing_used else 'SL_SAME_DAY'
            elif day_low <= pos.sl_price:
                exit_raw_price = pos.sl_price
                exit_reason = 'TRAIL' if trailing_used else 'SL'
            elif day_high >= pos.tp_price:
                exit_raw_price = pos.tp_price
                exit_reason = 'TP'
            elif pos.days_held >= time_limit:
                exit_raw_price = day_close
                exit_reason = 'TIME_EXIT'

            if exit_raw_price is None:
                positions_still_open.append(pos)
                continue

            # Đóng vị thế
            net_exit_price = exit_raw_price * (1 - sell_cost)
            proceeds = pos.shares * net_exit_price
            cost_basis = pos.shares * pos.entry_price
            pnl = proceeds - cost_basis
            pnl_pct = net_exit_price / pos.entry_price - 1.0

            cash += proceeds
            closed_trades.append(Trade(
                stock_id=pos.stock_id,
                entry_date=pos.entry_date,
                exit_date=today,
                entry_price=pos.entry_price,
                exit_price=net_exit_price,
                raw_exit_price=exit_raw_price,
                shares=pos.shares,
                reason=exit_reason,
                pnl=pnl,
                pnl_pct=pnl_pct,
            ))

        open_positions = positions_still_open

        # b. ENTRY PHASE --------------------------------------------------
        # Tín hiệu hôm nay → mua open ngày next_day. Cần next_day tồn tại.
        # Market state filter: CHỈ vào lệnh khi thị trường UPTREND
        ms = market_states.get(today, 'UNKNOWN')
        if ms != 'UPTREND':
            pass  # skip all buys unless market is trending up
        elif next_day is not None and today in pred_by_date:
            preds_today = pred_by_date[today]
            candidates = preds_today[
                (preds_today['trend_class'] == 'UP')
                & (preds_today['confidence_score'] >= min_confidence)
            ].sort_values('confidence_score', ascending=False).head(top_k)

            currently_held = {p.stock_id for p in open_positions}
            n_slots = max_positions - len(open_positions)

            # Portfolio value tại thời điểm quyết định mua (dùng close hôm nay)
            holdings_value_now = _portfolio_holdings_value(
                open_positions, ohlc_lookup.get(today, {}), today,
            )
            portfolio_value_now = cash + holdings_value_now

            for cand in candidates.itertuples(index=False):
                if n_slots <= 0:
                    break
                if cand.stock_id in currently_held:
                    continue

                # Volume filter: skip if volume < average
                vol_z = getattr(cand, 'volume_zscore_20', 0) or 0
                if vol_z < 0:
                    continue

                next_ohlc = ohlc_lookup.get(next_day, {}).get(cand.stock_id)
                if next_ohlc is None or pd.isna(next_ohlc['open']) or next_ohlc['open'] <= 0:
                    continue
                raw_entry = next_ohlc['open']
                gross_entry_price = raw_entry * (1 + buy_cost)

                position_value = portfolio_value_now * position_size
                # Mua theo lot size, làm tròn xuống
                shares = int(position_value // (gross_entry_price * lot_size)) * lot_size
                if shares <= 0:
                    continue

                actual_cost = shares * gross_entry_price
                if actual_cost > cash:
                    continue

                cash -= actual_cost
                # Tính TP/SL dựa trên entry price, tránh gap phá R:R
                adj_close_cand = float(getattr(cand, 'adj_close', 0) or 0)
                if adj_close_cand > 0 and float(cand.target_price) > adj_close_cand:
                    tp_mult = float(cand.target_price) / adj_close_cand - 1.0
                    tp_price = raw_entry * (1.0 + tp_mult)
                    sl_mult = 1.0 - float(cand.stop_loss) / adj_close_cand
                    sl_price = raw_entry * (1.0 - sl_mult)
                else:
                    tp_price = float(cand.target_price)
                    sl_price = float(cand.stop_loss)
                sl_gap = raw_entry - sl_price
                open_positions.append(Position(
                    stock_id=cand.stock_id,
                    entry_date=next_day,
                    entry_price=gross_entry_price,
                    raw_entry_price=raw_entry,
                    tp_price=tp_price,
                    sl_price=sl_price,
                    trailing_high=raw_entry,
                    sl_gap=sl_gap,
                    shares=shares,
                    days_held=0,
                ))
                currently_held.add(cand.stock_id)
                n_slots -= 1

        # c. EQUITY UPDATE ------------------------------------------------
        holdings_value = _portfolio_holdings_value(
            open_positions, ohlc_lookup.get(today, {}), today,
        )
        portfolio_value = cash + holdings_value
        equity_records.append({
            'date': today,
            'portfolio_value': portfolio_value,
            'cash': cash,
            'holdings_value': holdings_value,
            'n_open_positions': len(open_positions),
        })

    # 3. ĐÓNG VỊ THẾ CÒN MỞ TẠI close NGÀY CUỐI ---------------------------
    last_day = trading_days[-1]
    last_ohlc_map = ohlc_lookup.get(last_day, {})
    for pos in open_positions:
        last_ohlc = last_ohlc_map.get(pos.stock_id)
        if last_ohlc is None or pd.isna(last_ohlc['close']):
            # Không có giá để đóng → bỏ qua, ghi nhận pnl = 0 trên trade này
            continue
        raw_exit = last_ohlc['close']
        net_exit = raw_exit * (1 - sell_cost)
        proceeds = pos.shares * net_exit
        cost_basis = pos.shares * pos.entry_price
        cash += proceeds
        closed_trades.append(Trade(
            stock_id=pos.stock_id,
            entry_date=pos.entry_date,
            exit_date=last_day,
            entry_price=pos.entry_price,
            exit_price=net_exit,
            raw_exit_price=raw_exit,
            shares=pos.shares,
            reason='EOB_CLOSE',
            pnl=proceeds - cost_basis,
            pnl_pct=net_exit / pos.entry_price - 1.0,
        ))
    open_positions = []

    # 4. TỔNG HỢP KẾT QUẢ -------------------------------------------------
    equity_curve = pd.DataFrame(equity_records).set_index('date')
    trades_df = pd.DataFrame([t.__dict__ for t in closed_trades])
    if not trades_df.empty:
        trades_df['entry_date'] = pd.to_datetime(trades_df['entry_date'])
        trades_df['exit_date'] = pd.to_datetime(trades_df['exit_date'])
        trades_df['holding_days'] = (
            trades_df['exit_date'] - trades_df['entry_date']
        ).dt.days

    params = {
        'initial_capital': initial_capital,
        'position_size': position_size,
        'max_positions': max_positions,
        'top_k': top_k,
        'min_confidence': min_confidence,
        'lot_size': lot_size,
        'buy_cost': buy_cost,
        'sell_cost': sell_cost,
        'settlement_days': settlement_days,
        'time_limit': time_limit,
    }

    metrics = _compute_metrics(equity_curve, trades_df, initial_capital)

    if verbose:
        _print_summary(metrics, trades_df)

    return BacktestResult(
        equity_curve=equity_curve,
        trades=trades_df,
        metrics=metrics,
        params=params,
    )


# ==============================================================================
# HELPERS
# ==============================================================================
def _portfolio_holdings_value(
    positions: List[Position],
    ohlc_today: Dict[str, Dict[str, float]],
    current_date: pd.Timestamp,
) -> float:
    """Tính giá trị holdings tại close hôm nay (chưa trừ sell_cost — đó là
    mark-to-market, không phải giá thanh lý).

    Nếu position vừa được tạo trong cùng iteration (entry_date > current_date),
    cash đã bị trừ nhưng cổ phiếu sẽ về tại next_day. Để giữ tính nhất quán
    cash + holdings = portfolio_value, mark theo entry_price (bù lại đúng phần
    cash đã trừ → portfolio_value không bị "biến mất").
    """
    total = 0.0
    for pos in positions:
        if pos.entry_date > current_date:
            # Pending entry — mark theo cost basis
            total += pos.shares * pos.entry_price
            continue
        ohlc = ohlc_today.get(pos.stock_id)
        if ohlc is None or pd.isna(ohlc['close']):
            # Không có giá → định giá theo entry (giả định không đổi)
            total += pos.shares * pos.entry_price
        else:
            total += pos.shares * ohlc['close']
    return total


def _compute_metrics(
    equity_curve: pd.DataFrame,
    trades_df: pd.DataFrame,
    initial_capital: float,
) -> Dict[str, float]:
    """Tính metrics cơ bản, không phụ thuộc QuantStats (đảm bảo chạy được dù
    chưa cài). generate_backtest_report() bổ sung thêm metric QuantStats."""
    if equity_curve.empty:
        return {}

    final_value = float(equity_curve['portfolio_value'].iloc[-1])
    total_return = final_value / initial_capital - 1.0

    daily_returns = equity_curve['portfolio_value'].pct_change().dropna()

    n_days = len(equity_curve)
    if n_days > 1 and final_value > 0:
        cagr = (final_value / initial_capital) ** (252.0 / n_days) - 1.0
    else:
        cagr = float('nan')

    if not daily_returns.empty and daily_returns.std() > 0:
        sharpe = float(np.sqrt(252) * daily_returns.mean() / daily_returns.std())
    else:
        sharpe = float('nan')

    rolling_max = equity_curve['portfolio_value'].cummax()
    drawdown = equity_curve['portfolio_value'] / rolling_max - 1.0
    max_dd = float(drawdown.min()) if not drawdown.empty else float('nan')

    calmar = (cagr / abs(max_dd)) if (max_dd is not None and max_dd < 0) else float('nan')

    metrics: Dict[str, float] = {
        'initial_capital': float(initial_capital),
        'final_value': final_value,
        'total_return': total_return,
        'cagr': cagr,
        'sharpe': sharpe,
        'max_drawdown': max_dd,
        'calmar': calmar,
        'n_trading_days': float(n_days),
    }

    if trades_df is not None and not trades_df.empty:
        wins = trades_df[trades_df['pnl'] > 0]
        losses = trades_df[trades_df['pnl'] <= 0]
        gross_profit = float(wins['pnl'].sum()) if not wins.empty else 0.0
        gross_loss = float(-losses['pnl'].sum()) if not losses.empty else 0.0
        metrics.update({
            'total_trades': float(len(trades_df)),
            'win_rate': float(len(wins) / len(trades_df)),
            'avg_holding_days': float(trades_df['holding_days'].mean()),
            'avg_pnl_pct': float(trades_df['pnl_pct'].mean()),
            'profit_factor': (gross_profit / gross_loss) if gross_loss > 0 else float('inf'),
            'gross_profit': gross_profit,
            'gross_loss': gross_loss,
        })
    else:
        metrics.update({
            'total_trades': 0.0,
            'win_rate': float('nan'),
            'avg_holding_days': float('nan'),
            'avg_pnl_pct': float('nan'),
            'profit_factor': float('nan'),
            'gross_profit': 0.0,
            'gross_loss': 0.0,
        })

    return metrics


def _print_summary(metrics: Dict[str, float], trades_df: pd.DataFrame) -> None:
    print("\n" + "=" * 60)
    print("BACKTEST SUMMARY")
    print("=" * 60)
    print(f"  Initial capital     : {metrics.get('initial_capital', 0):>18,.0f} VND")
    print(f"  Final value         : {metrics.get('final_value', 0):>18,.0f} VND")
    print(f"  Total return        : {metrics.get('total_return', 0) * 100:>17.2f} %")
    print(f"  CAGR                : {metrics.get('cagr', 0) * 100:>17.2f} %")
    print(f"  Sharpe              : {metrics.get('sharpe', 0):>18.2f}")
    print(f"  Max drawdown        : {metrics.get('max_drawdown', 0) * 100:>17.2f} %")
    print(f"  Calmar              : {metrics.get('calmar', 0):>18.2f}")
    print(f"  Total trades        : {int(metrics.get('total_trades', 0)):>18d}")
    print(f"  Win rate            : {metrics.get('win_rate', 0) * 100:>17.2f} %")
    print(f"  Profit factor       : {metrics.get('profit_factor', 0):>18.2f}")
    print(f"  Avg holding days    : {metrics.get('avg_holding_days', 0):>18.2f}")
    print(f"  Avg pnl per trade   : {metrics.get('avg_pnl_pct', 0) * 100:>17.2f} %")

    if trades_df is not None and not trades_df.empty:
        reason_counts = trades_df['reason'].value_counts()
        print("  Exit reason breakdown:")
        labels = {
            'TP': 'Chốt lời (TP)',
            'TRAIL': 'Trailing stop (có lời)',
            'TRAIL_SAME_DAY': 'Trailing same-day',
            'SL': 'Cắt lỗ (lỗ)',
            'SL_SAME_DAY': 'Cắt lỗ same-day (lỗ)',
            'TIME_EXIT': 'Hết thời gian',
            'EOB_CLOSE': 'Đóng cuối kỳ',
        }
        for reason, cnt in reason_counts.items():
            label = labels.get(reason, reason)
            print(f"    {label:<28} {cnt:>5d}  ({cnt / len(trades_df) * 100:>5.1f}%)")

        # Phân biệt lời/lỗ rõ ràng
        wins = trades_df[trades_df['pnl'] > 0]
        loss = trades_df[trades_df['pnl'] <= 0]
        print(f"\n  Lệnh có lời: {len(wins)} ({len(wins)/len(trades_df)*100:.1f}%)")
        print(f"  Lệnh lỗ:     {len(loss)} ({len(loss)/len(trades_df)*100:.1f}%)")
        print(f"  Lời TB:      {wins['pnl_pct'].mean()*100:+.2f}%")
        print(f"  Lỗ TB:       {loss['pnl_pct'].mean()*100:+.2f}%")
    print("=" * 60 + "\n")


# ==============================================================================
# REPORT (QuantStats)
# ==============================================================================
def generate_backtest_report(
    result: BacktestResult,
    benchmark_df: Optional[pd.DataFrame] = None,
    output_dir: Optional[Path] = None,
    version: str = MODEL_VERSION,
) -> Dict[str, float]:
    """Tạo QuantStats HTML report (nếu có) + augment metrics.

    Parameters
    ----------
    result        : Output của run_backtest().
    benchmark_df  : Optional DataFrame index=date, column 'close' của VNINDEX
                    (hoặc benchmark khác). Nếu None, không so sánh.
    output_dir    : Thư mục lưu HTML + CSV. Mặc định: backend/data/backtest/.

    Returns metrics dict đã augment.
    """
    if output_dir is None:
        output_dir = DATA_DIR / 'backtest'
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    metrics = dict(result.metrics)

    # Lưu CSV để inspect ngoài Python
    equity_csv = output_dir / f'equity_curve_{version}.csv'
    trades_csv = output_dir / f'trades_{version}.csv'
    result.equity_curve.to_csv(equity_csv)
    if not result.trades.empty:
        result.trades.to_csv(trades_csv, index=False)
    print(f"Equity curve → {equity_csv}")
    print(f"Trades       → {trades_csv}")

    # Daily returns cho QuantStats
    returns = result.equity_curve['portfolio_value'].pct_change().dropna()
    returns.index = pd.to_datetime(returns.index)

    benchmark_returns: Optional[pd.Series] = None
    if benchmark_df is not None and not benchmark_df.empty:
        bench = benchmark_df.copy()
        if 'close' not in bench.columns:
            print("benchmark_df thiếu column 'close' — bỏ qua benchmark.")
        else:
            bench.index = pd.to_datetime(bench.index)
            bench_aligned = bench['close'].reindex(returns.index, method='ffill')
            benchmark_returns = bench_aligned.pct_change().dropna()

    # QuantStats — wrap try/except để không vỡ pipeline nếu chưa cài
    try:
        import quantstats as qs  # type: ignore

        # Thêm metrics phong phú từ QuantStats
        metrics.update({
            'qs_sharpe': float(qs.stats.sharpe(returns)) if len(returns) > 1 else float('nan'),
            'qs_sortino': float(qs.stats.sortino(returns)) if len(returns) > 1 else float('nan'),
            'qs_max_drawdown': float(qs.stats.max_drawdown(returns)) if len(returns) > 1 else float('nan'),
            'qs_calmar': float(qs.stats.calmar(returns)) if len(returns) > 1 else float('nan'),
            'qs_volatility': float(qs.stats.volatility(returns)) if len(returns) > 1 else float('nan'),
        })

        report_path = output_dir / f'backtest_report_{version}.html'
        try:
            qs.reports.html(
                returns,
                benchmark=benchmark_returns,
                title=f'Triple Barrier + Ensemble Strategy ({version})',
                output=str(report_path),
            )
            print(f"QuantStats report → {report_path}")
        except Exception as exc:  # pylint: disable=broad-except
            print(f"QuantStats HTML report failed: {exc}")
    except ImportError:
        print("quantstats chưa được cài → bỏ qua HTML report, chỉ in metrics cơ bản.")

    # In benchmark comparison nếu có
    if benchmark_returns is not None and not benchmark_returns.empty:
        bench_total = float((1 + benchmark_returns).prod() - 1)
        strat_total = metrics.get('total_return', float('nan'))
        print(f"\n  Strategy total return : {strat_total * 100:>7.2f} %")
        print(f"  Benchmark total return: {bench_total * 100:>7.2f} %")
        print(f"  Excess return         : {(strat_total - bench_total) * 100:>7.2f} %\n")
        metrics['benchmark_total_return'] = bench_total
        metrics['excess_return'] = strat_total - bench_total

    return metrics
