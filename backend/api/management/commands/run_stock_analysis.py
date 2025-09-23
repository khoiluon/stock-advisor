# backend/api/management/commands/run_stock_analysis.py

import pandas as pd
from django.core.management.base import BaseCommand
from django.db import transaction
from api.models import Stock, StockData, PotentialStock
from api.analysis_logic import run_analysis_on_data

class Command(BaseCommand):
    help = 'Analyzes stocks for the LATEST DAY using the ADMRS.'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("=== Bắt đầu ADMRS cho ngày gần nhất ==="))

        all_data = StockData.objects.all().values('stock_id', 'date', 'open', 'high', 'low', 'close', 'volume')
        if not all_data.exists(): return

        df_all = pd.DataFrame(list(all_data))
        # Chuyển đổi kiểu dữ liệu ngay từ đầu
        numeric_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_cols:
            df_all[col] = pd.to_numeric(df_all[col], errors='coerce', downcast='float')
        df_all = df_all.dropna(subset=numeric_cols)

        self.stdout.write("-> Đang gọi bộ não phân tích...")
        potential_stocks_data = run_analysis_on_data(df_all, scan_full_history=False)

        if not potential_stocks_data:
            self.stdout.write(self.style.SUCCESS("Hoàn tất. Không tìm thấy cổ phiếu nào."))
            return

        self.stdout.write(f"Tìm thấy {len(potential_stocks_data)} cổ phiếu tiềm năng. Đang lưu...")

        analysis_date = potential_stocks_data[0]['analysis_date'].date()
        PotentialStock.objects.filter(analysis_date=analysis_date).delete()

        stock_map = {s.ticker: s for s in Stock.objects.all()}
        final_objects = []
        for data in potential_stocks_data:
            stock_instance = stock_map.get(data['stock_id'])
            if stock_instance:
                obj_data = data.copy()
                obj_data['stock'] = stock_instance
                del obj_data['stock_id']
                final_objects.append(PotentialStock(**obj_data))

        PotentialStock.objects.bulk_create(final_objects)
        self.stdout.write(self.style.SUCCESS(f"HOÀN TẤT: Đã lưu {len(final_objects)} cổ phiếu tiềm năng."))