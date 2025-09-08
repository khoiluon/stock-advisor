import pandas as pd
import decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from api.models import Stock, StockData, PotentialStock

# --- Lớp 1: Hằng số cho việc Sàng lọc Cơ bản ---
MIN_DATA_POINTS = 120
MIN_AVG_VOLUME = 100000
VOLUME_SPIKE_FACTOR = 2.0


class Command(BaseCommand):
    help = 'Analyzes all stocks using a multi-layered screening system and saves the results.'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Bắt đầu Hệ thống Lọc Gợi ý Đa tầng..."))

        # --- Bước 1: Chuẩn bị dữ liệu ---
        self.stdout.write("  -> Bước 1: Đang tải và chuẩn bị dữ liệu...")
        all_data = StockData.objects.all().values('stock_id', 'date', 'close', 'volume')
        if not all_data.exists():
            self.stdout.write(self.style.WARNING("Không có dữ liệu để phân tích. Dừng lại."))
            return

        df_all = pd.DataFrame(list(all_data), columns=['stock_id', 'date', 'close', 'volume'])
        df_all['date'] = pd.to_datetime(df_all['date'])
        analysis_date = df_all['date'].max().date()
        self.stdout.write(self.style.SUCCESS(f"  -> Ngày phân tích được xác định là: {analysis_date}"))
        PotentialStock.objects.filter(analysis_date=analysis_date).delete()

        # --- Bước 2: Phân tích và Chấm điểm ---
        self.stdout.write("  -> Bước 2: Đang lặp qua từng cổ phiếu để phân tích...")
        potential_stocks = []

        for ticker, df_stock in df_all.groupby('stock_id'):
            df_stock = df_stock.sort_values(by='date').reset_index(drop=True)

            # --- Áp dụng Lớp 1: Sàng lọc Điều kiện Cơ bản ---
            if len(df_stock) < MIN_DATA_POINTS: continue

            # Tính toán các chỉ báo
            df_stock.ta.sma(length=20, close='close', append=True, col_names=('SMA_20',))
            df_stock.ta.sma(length=50, close='close', append=True, col_names=('SMA_50',))
            df_stock.ta.sma(length=100, close='close', append=True, col_names=('SMA_100',))
            df_stock.ta.rsi(length=14, close='close', append=True, col_names=('RSI_14',))
            df_stock.ta.macd(fast=12, slow=26, signal=9, close='close', append=True,
                             col_names=('MACD', 'MACDh', 'MACDs'))
            df_stock['Volume_SMA_20'] = df_stock['volume'].rolling(window=20).mean()

            last_day = df_stock.iloc[-1]
            prev_day = df_stock.iloc[-2]

            if last_day['Volume_SMA_20'] < MIN_AVG_VOLUME: continue

            # --- Áp dụng Lớp 2: Xác định Xu hướng Chủ đạo ---
            is_uptrend = last_day['SMA_20'] > last_day['SMA_50'] > last_day['SMA_100']
            if not is_uptrend: continue

            # --- Áp dụng Lớp 3: Phân loại Chiến lược & Chấm điểm ---
            score = 0
            key_reasons = []
            strategies_found = []

            # Chiến lược 1: "Breakout Momentum"
            is_golden_cross = prev_day['SMA_20'] <= prev_day['SMA_50'] and last_day['SMA_20'] > last_day['SMA_50']
            is_volume_spike = last_day['volume'] > last_day['Volume_SMA_20'] * VOLUME_SPIKE_FACTOR
            is_strong_rsi = last_day['RSI_14'] > 60

            if is_golden_cross and is_volume_spike and is_strong_rsi:
                score += 8  # Tín hiệu rất mạnh
                key_reasons.extend(["MA Crossover Bullish", "Volume Surge", "Strong RSI"])
                strategies_found.append("Ngắn hạn: Bùng nổ theo Đà")

            # Chiến lược 2: "Buy the Dip"
            is_in_dip_zone = last_day['SMA_50'] < last_day['close'] < last_day['SMA_20']
            is_healthy_rsi = 45 < last_day['RSI_14'] < 60
            is_low_volume = last_day['volume'] < last_day['Volume_SMA_20']

            if is_in_dip_zone and is_healthy_rsi and is_low_volume:
                score += 6  # Tín hiệu tốt, an toàn hơn
                key_reasons.extend(["Support Level Hold", "Healthy Pullback", "Low Volume"])
                strategies_found.append("Trung hạn: Mua khi Điều chỉnh")

            # Cộng điểm phụ cho các tín hiệu tốt khác
            if last_day['MACD'] > last_day['MACDs']:
                score += 1
                key_reasons.append("Positive MACD")

            # --- Áp dụng Lớp 4: Tổng hợp & Xếp hạng ---
            if strategies_found:
                current_price = last_day['close']
                timeframe = "Trung hạn" if "Trung hạn" in " ".join(strategies_found) else "Ngắn hạn"

                # Công thức tính toán có cơ sở hơn
                confidence = min(int(score * 8 + 20), 95)  # Ánh xạ điểm số sang % độ tự tin
                target_price_multiplier = decimal.Decimal('1.10') if timeframe == "Ngắn hạn" else decimal.Decimal(
                    '1.20')
                target_price = current_price * target_price_multiplier

                potential_stocks.append(
                    PotentialStock(
                        stock_id=ticker,
                        analysis_date=analysis_date,
                        current_price=current_price,
                        target_price=target_price.quantize(decimal.Decimal('0.01')),
                        timeframe=timeframe,
                        confidence=confidence,
                        score=round(score / 10, 1),  # Chuyển điểm về thang 10
                        key_reasons=", ".join(list(dict.fromkeys(key_reasons))),  # Loại bỏ tag trùng lặp
                        reason=" | ".join(strategies_found)
                    )
                )

        # --- Bước 3: Lưu kết quả vào database ---
        self.stdout.write(f"  -> Bước 3: Tìm thấy {len(potential_stocks)} cổ phiếu tiềm năng. Đang lưu...")
        if not potential_stocks:
            self.stdout.write(self.style.SUCCESS("Hoàn tất. Không tìm thấy cổ phiếu nào thỏa mãn tiêu chí."))
            return

        PotentialStock.objects.bulk_create(potential_stocks)
        self.stdout.write(
            self.style.SUCCESS(f"HOÀN TẤT: Đã phân tích và lưu {len(potential_stocks)} cổ phiếu tiềm năng."))