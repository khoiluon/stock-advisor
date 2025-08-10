import os
import pandas as pd
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import transaction
from api.models import Stock, StockData


class Command(BaseCommand):
    help = 'Imports stock data from CSV files for HSX, HNX, and UPCOM into the database.'

    def handle(self, *args, **options):
        file_info = [
            {'file_name': 'CafeF.HSX.Upto23.07.2025.csv', 'exchange': 'HOSE'},
            {'file_name': 'CafeF.HNX.Upto23.07.2025.csv', 'exchange': 'HNX'},
            {'file_name': 'CafeF.UPCOM.Upto23.07.2025.csv', 'exchange': 'UPCOM'},
        ]

        with transaction.atomic():
            self.stdout.write(self.style.WARNING("Bắt đầu quá trình nhập dữ liệu. Xóa tất cả dữ liệu cũ..."))
            Stock.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("Đã xóa dữ liệu cũ thành công."))

            # BƯỚC 1: TỔNG HỢP CÁC MÃ TICKER DUY NHẤT
            self.stdout.write("Bước 1: Đang tổng hợp các mã cổ phiếu duy nhất...")
            unique_tickers_map = {}
            for info in file_info:
                file_path = os.path.join(settings.BASE_DIR, 'data', info['file_name'])
                if not os.path.exists(file_path): continue
                df = pd.read_csv(file_path, usecols=['<Ticker>'])
                df.columns = df.columns.str.replace('<', '').str.replace('>', '')
                df.dropna(subset=['Ticker'], inplace=True)
                for ticker in df['Ticker'].unique():
                    normalized_ticker = str(ticker).upper()
                    if normalized_ticker not in unique_tickers_map:
                        unique_tickers_map[normalized_ticker] = info['exchange']
            self.stdout.write(
                self.style.SUCCESS(f"  -> Đã tìm thấy {len(unique_tickers_map)} mã duy nhất trên tất cả các sàn."))

            # BƯỚC 2: TẠO CÁC ĐỐI TƯỢNG STOCK
            self.stdout.write("Bước 2: Đang tạo các đối tượng Stock trong database...")
            stocks_to_create = [
                Stock(ticker=ticker, company_name=f"{ticker} Company", exchange=exchange)
                for ticker, exchange in unique_tickers_map.items()
            ]
            Stock.objects.bulk_create(stocks_to_create)
            self.stdout.write(self.style.SUCCESS("  -> Đã tạo xong các đối tượng Stock."))

            # BƯỚC 3: TẠO CÁC ĐỐI TƯỢNG STOCKDATA
            self.stdout.write("Bước 3: Đang chuẩn bị dữ liệu lịch sử để nhập...")
            all_stocks_map = {stock.ticker: stock for stock in Stock.objects.all()}
            stock_data_to_create = []

            # === SỬA LỖI QUAN TRỌNG: DÙNG SET ĐỂ LỌC TRÙNG DỮ LIỆU LỊCH SỬ ===
            processed_entries = set()

            for info in file_info:
                file_path = os.path.join(settings.BASE_DIR, 'data', info['file_name'])
                if not os.path.exists(file_path): continue

                self.stdout.write(f"  -> Đang đọc dữ liệu từ {info['file_name']}...")
                df = pd.read_csv(file_path)
                df.columns = df.columns.str.replace('<', '').str.replace('>', '')
                df.dropna(subset=['Ticker', 'DTYYYYMMDD'], inplace=True)

                for index, row in df.iterrows():
                    normalized_ticker = str(row['Ticker']).upper()
                    stock_instance = all_stocks_map.get(normalized_ticker)

                    if stock_instance:
                        date_object = pd.to_datetime(row['DTYYYYMMDD'], format='%Y%m%d').date()

                        # Tạo một key duy nhất cho mỗi cặp (ticker, date)
                        entry_key = (normalized_ticker, date_object)

                        # Chỉ thêm vào danh sách nếu cặp này chưa được xử lý
                        if entry_key not in processed_entries:
                            stock_data_to_create.append(
                                StockData(
                                    stock=stock_instance,
                                    date=date_object,
                                    open=row['Open'],
                                    high=row['High'],
                                    low=row['Low'],
                                    close=row['Close'],
                                    volume=row['Volume']
                                )
                            )
                            # Đánh dấu cặp (ticker, date) này là đã xử lý
                            processed_entries.add(entry_key)

            self.stdout.write(self.style.SUCCESS(
                f"Bắt đầu nhập {len(stock_data_to_create)} điểm dữ liệu lịch sử (đã lọc trùng). Quá trình này có thể mất vài phút..."))
            StockData.objects.bulk_create(stock_data_to_create, batch_size=2000)
            self.stdout.write(self.style.SUCCESS("  -> Đã nhập xong dữ liệu lịch sử."))

        self.stdout.write(self.style.SUCCESS("HOÀN TẤT: Toàn bộ dữ liệu đã được nhập vào database thành công!"))