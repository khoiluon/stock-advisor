import pandas as pd
import pandas_ta as ta
import decimal
import numpy as np
from scipy.signal import argrelextrema
from .analysis_config import (
    MASTER_WEIGHTS, SIGNAL_SCORES, MAX_SCORES, MIN_DATA_POINTS,
    MIN_AVG_TRADE_VALUE, FINAL_SCORE_THRESHOLD
)


def _detect_rsi_bearish_divergence(df, lookback=20):
    """Tìm phân kỳ âm RSI trong khoảng thời gian gần nhất."""
    if len(df) < lookback: return False
    recent = df.iloc[-lookback:].reset_index(drop=True)
    price_peaks = argrelextrema(recent['close'].values, np.greater, order=3)[0]
    rsi_peaks = argrelextrema(recent['RSI_14'].values, np.greater, order=3)[0]
    if len(price_peaks) < 2 or len(rsi_peaks) < 2: return False

    last_price_peak_idx = price_peaks[-1]
    prev_price_peak_idx = price_peaks[-2]
    last_rsi_peak_idx = rsi_peaks[-1]
    prev_rsi_peak_idx = rsi_peaks[-2]

    if (recent.iloc[last_price_peak_idx]['close'] > recent.iloc[prev_price_peak_idx]['close'] and
            recent.iloc[last_rsi_peak_idx]['RSI_14'] < recent.iloc[prev_rsi_peak_idx]['RSI_14']):
        return True
    return False


def run_analysis_on_data(df_all, scan_full_history=False):
    """
    Hàm phân tích ADMRS cốt lõi.
    - scan_full_history=False (mặc định): Chỉ phân tích ngày cuối cùng.
    - scan_full_history=True: Quét toàn bộ lịch sử để tìm tín hiệu cho backtest.
    """
    all_potential_stocks = []

    for ticker, df_stock in df_all.groupby('stock_id'):
        df_stock = df_stock.sort_values(by='date').reset_index(drop=True)

        # --- Sàng lọc Ban đầu (Từ file gốc của bạn) ---
        if len(df_stock) < MIN_DATA_POINTS:
            continue

        # Nhân với 1000 để quy đổi đơn vị giá cho đúng
        df_stock['trade_value'] = df_stock['close'] * 1000 * df_stock['volume']
        avg_trade_value_20d = df_stock['trade_value'].rolling(window=20).mean().iloc[-1]
        if pd.isna(avg_trade_value_20d) or avg_trade_value_20d < MIN_AVG_TRADE_VALUE:
            continue

        # --- Tính toán Indicators (Từ file gốc của bạn) ---
        try:
            df_stock['SMA20'] = ta.sma(df_stock['close'], length=20)
            df_stock['SMA50'] = ta.sma(df_stock['close'], length=50)
            df_stock['SMA150'] = ta.sma(df_stock['close'], length=150)
            df_stock['RSI_14'] = ta.rsi(df_stock['close'], length=14)
            macd = ta.macd(df_stock['close'], fast=12, slow=26, signal=9)
            df_stock['MACD'] = macd['MACD_12_26_9']
            df_stock['MACDs'] = macd['MACDs_12_26_9']
            df_stock['Volume_SMA_50'] = ta.sma(df_stock['volume'], length=50)
            df_stock['RVOL'] = df_stock['volume'] / df_stock['Volume_SMA_50']
            df_stock['52_Week_High'] = df_stock['high'].rolling(window=252).max()
            df_stock['CMF_20'] = ta.cmf(df_stock['high'], df_stock['low'], df_stock['close'], df_stock['volume'],
                                        length=20)
            df_stock['ATR_14'] = ta.atr(df_stock['high'], df_stock['low'], df_stock['close'], length=14)
            df_stock['CDL_ENGULFING'] = ta.cdl_pattern(df_stock['open'], df_stock['high'], df_stock['low'],
                                                       df_stock['close'], name="engulfing")
        except Exception:
            continue

        # Xác định phạm vi quét
        start_index = MIN_DATA_POINTS if scan_full_history else len(df_stock) - 1
        end_index = len(df_stock)

        for i in range(start_index, end_index):
            if i < 1: continue
            last_day = df_stock.iloc[i]

            required_cols = ['RSI_14', 'ATR_14', 'MACD', 'MACDs', 'SMA20', 'SMA50', 'SMA150', 'CMF_20', 'Volume_SMA_50',
                             'CDL_ENGULFING']
            if pd.isna(last_day[required_cols]).any():
                continue

            # --- Chấm điểm (Logic từ file gốc của bạn) ---
            trend_score, momentum_score, volume_score, risk_score = 0, 0, 0, 0
            key_reasons = []

            if last_day['close'] > last_day['SMA150']: trend_score += SIGNAL_SCORES[
                'PRICE_ABOVE_SMA150']; key_reasons.append("Uptrend Dài hạn")
            if last_day['close'] > last_day['SMA50']: trend_score += SIGNAL_SCORES[
                'PRICE_ABOVE_SMA50']; key_reasons.append("Uptrend Trung hạn")
            if last_day['SMA50'] > last_day['SMA150']: trend_score += SIGNAL_SCORES[
                'SMA50_ABOVE_SMA150']; key_reasons.append("Cấu trúc Tăng giá")
            if last_day['close'] >= last_day['52_Week_High'] * 0.85: trend_score += SIGNAL_SCORES[
                'NEAR_52_WEEK_HIGH_15_PERCENT']; key_reasons.append("Gần Vùng Đỉnh")
            if last_day['close'] >= last_day['52_Week_High'] * 0.95: trend_score += SIGNAL_SCORES[
                'NEAR_52_WEEK_HIGH_5_PERCENT']; key_reasons.append("Sẵn sàng Bứt phá")

            if last_day['RSI_14'] > 50: momentum_score += SIGNAL_SCORES['RSI_ABOVE_50']; key_reasons.append(
                "RSI Tích cực")
            if last_day['RSI_14'] > 60: momentum_score += SIGNAL_SCORES['RSI_ABOVE_60']; key_reasons.append("RSI Mạnh")
            if last_day['MACD'] > last_day['MACDs']: momentum_score += SIGNAL_SCORES[
                'MACD_ABOVE_SIGNAL']; key_reasons.append("MACD Bullish")

            recent_macd_slice = df_stock[['MACD', 'MACDs']].iloc[max(0, i - 2):i + 1]
            if any(recent_macd_slice['MACD'] > recent_macd_slice['MACDs']) and any(
                    recent_macd_slice['MACD'] <= recent_macd_slice['MACDs']):
                momentum_score += SIGNAL_SCORES['MACD_RECENT_CROSSOVER'];
                key_reasons.append("KÍCH HOẠT: MACD Crossover")

            recent_sma_slice = df_stock[['SMA20', 'SMA50']].iloc[max(0, i - 4):i + 1]
            if any(recent_sma_slice['SMA20'] > recent_sma_slice['SMA50']) and any(
                    recent_sma_slice['SMA20'] <= recent_sma_slice['SMA50']):
                momentum_score += SIGNAL_SCORES['SMA20_RECENT_CROSSOVER_SMA50'];
                key_reasons.append("KÍCH HOẠT: Golden Cross")

            if last_day['RVOL'] > 1.5: volume_score += SIGNAL_SCORES['RVOL_ABOVE_1_5']; key_reasons.append(
                "Dòng tiền Chú ý")
            if last_day['RVOL'] > 2.5: volume_score += SIGNAL_SCORES['RVOL_ABOVE_2_5']; key_reasons.append(
                "Dòng tiền Lớn Tham gia")
            if last_day['CMF_20'] > 0: volume_score += SIGNAL_SCORES['CMF_ABOVE_ZERO']; key_reasons.append("Áp lực Mua")

            if last_day['CDL_ENGULFING'] < 0: risk_score += SIGNAL_SCORES[
                'BEARISH_ENGULFING_CANDLE']; key_reasons.append("CẢNH BÁO: Nến Xấu")
            if _detect_rsi_bearish_divergence(df_stock.iloc[:i + 1]): risk_score += SIGNAL_SCORES[
                'RSI_BEARISH_DIVERGENCE']; key_reasons.append("CẢNH BÁO: Phân kỳ Âm RSI")

            # --- Tổng hợp (Logic từ file gốc của bạn) ---
            norm_trend = (trend_score / MAX_SCORES['TREND']) if MAX_SCORES['TREND'] > 0 else 0
            norm_momentum = (momentum_score / MAX_SCORES['MOMENTUM']) if MAX_SCORES['MOMENTUM'] > 0 else 0
            norm_volume = (volume_score / MAX_SCORES['VOLUME']) if MAX_SCORES['VOLUME'] > 0 else 0
            final_score = (norm_trend * MASTER_WEIGHTS['TREND']) + (norm_momentum * MASTER_WEIGHTS['MOMENTUM']) + (
                        norm_volume * MASTER_WEIGHTS['VOLUME']) + risk_score
            final_score = max(0, final_score)

            if final_score >= FINAL_SCORE_THRESHOLD:
                base_confidence = 50 + ((final_score - FINAL_SCORE_THRESHOLD) / (100 - FINAL_SCORE_THRESHOLD)) * 45
                confidence_adjustment = 0
                has_crossover = "KÍCH HOẠT: MACD Crossover" in key_reasons or "KÍCH HOẠT: Golden Cross" in key_reasons
                has_high_volume = "Dòng tiền Lớn Tham gia" in key_reasons
                if has_crossover: confidence_adjustment += 5
                if has_high_volume: confidence_adjustment += 5
                if has_crossover and has_high_volume: confidence_adjustment += 5
                risk_penalty = 0
                if "CẢNH BÁO: Nến Xấu" in key_reasons: risk_penalty -= 10
                if "CẢNH BÁO: Phân kỳ Âm RSI" in key_reasons: risk_penalty -= 15
                final_confidence = int(max(0, min(95, base_confidence + confidence_adjustment + risk_penalty)))

                if norm_momentum >= 0.7 and norm_volume >= 0.6:
                    timeframe = "Ngắn hạn"
                elif norm_trend >= 0.8 and norm_momentum < 0.7:
                    timeframe = "Trung hạn"
                else:
                    timeframe = "Theo dõi"

                current_price_decimal = decimal.Decimal(str(last_day['close']))
                atr_decimal = decimal.Decimal(str(last_day['ATR_14']))
                target_price = (current_price_decimal + (decimal.Decimal('2') * atr_decimal)).quantize(
                    decimal.Decimal('0.01'))
                stop_loss = (current_price_decimal - (decimal.Decimal('1.5') * atr_decimal)).quantize(
                    decimal.Decimal('0.01'))

                all_potential_stocks.append({
                    'stock_id': ticker, 'analysis_date': last_day['date'],
                    'current_price': current_price_decimal, 'target_price': target_price,
                    'stop_loss': stop_loss, 'timeframe': timeframe,
                    'confidence': final_confidence, 'score': round(final_score / 10, 1),
                    'key_reasons': ", ".join(list(dict.fromkeys(key_reasons))),
                    'reason': f"Trend:{norm_trend:.2f},Mom:{norm_momentum:.2f},Vol:{norm_volume:.2f}"
                })

    return all_potential_stocks