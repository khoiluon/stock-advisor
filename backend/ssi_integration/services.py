# ssi_integration/services.py

from datetime import date, timedelta
from django.utils import timezone
from ssi_fc_data.fc_md_client import MarketDataClient
from ssi_fc_data.model.model import daily_ohlc
from .ssi_config import get_ssi_config
from api.models import Stock, StockData


def update_historical_data(ticker: str):
    """
    Kiểm tra và cập nhật dữ liệu lịch sử bị thiếu cho một mã cổ phiếu.
    Lưu cả adj_close (closepriceadjusted) từ SSI và dùng totalmatchvol cho volume.
    Có OHLC validation và pagination.
    """
    print("\n" + "=" * 20 + f" BẮT ĐẦU CẬP NHẬT CHO {ticker} " + "=" * 20)
    try:
        stock = Stock.objects.get(ticker=ticker)
    except Stock.DoesNotExist:
        print(f"[DEBUG] Lỗi: Mã {ticker} không tồn tại trong database.")
        print("=" * 60 + "\n")
        return

    last_entry = StockData.objects.filter(stock=stock).order_by('-date').first()
    today = timezone.now().date()
    print(f"[DEBUG] Ngày hôm nay (theo server): {today.strftime('%Y-%m-%d')}")

    if last_entry:
        from_date = last_entry.date + timedelta(days=1)
        print(f"[DEBUG] Ngày dữ liệu cuối cùng trong DB: {last_entry.date.strftime('%Y-%m-%d')}")
    else:
        from_date = today - timedelta(days=365 * 5)
        print(f"[DEBUG] Không có dữ liệu trong DB. Lấy từ: {from_date.strftime('%Y-%m-%d')}")

    if from_date > today:
        print(f"[DEBUG] Dữ liệu cho mã {ticker} đã được cập nhật. Không cần gọi API.")
        print("=" * 60 + "\n")
        return

    print(f"Đang lấy dữ liệu cho mã {ticker} từ {from_date.strftime('%d/%m/%Y')} đến {today.strftime('%d/%m/%Y')}...")

    try:
        config = get_ssi_config()
        client = MarketDataClient(config)

        # Pagination loop — SSI giới hạn pageSize, lấy hết tất cả các trang
        page_index = 1
        page_size = 2000
        all_new_points = []

        while True:
            request_obj = daily_ohlc(
                symbol=ticker,
                fromDate=from_date.strftime('%d/%m/%Y'),
                toDate=today.strftime('%d/%m/%Y'),
                pageIndex=page_index,
                pageSize=page_size,
            )

            response = client.daily_ohlc(config, request_obj)

            response_status = response.get('status')
            if not ((response_status == 200 or str(response_status).lower() == 'success') and response.get('data')):
                if page_index == 1:
                    print(f"Không có dữ liệu mới từ SSI cho mã {ticker}. Response: {response}")
                break

            page_data = response['data']
            print(f"  Trang {page_index}: {len(page_data)} bản ghi")

            for item in page_data:
                trading_date_str = item.get('TradingDate')
                if not trading_date_str:
                    continue

                try:
                    day, month, year = map(int, trading_date_str.split('/'))
                    open_price = float(item.get('Open', 0))
                    high_price = float(item.get('High', 0))
                    low_price = float(item.get('Low', 0))
                    close_price = float(item.get('Close', 0))

                    # Ưu tiên totalmatchvol (khớp lệnh) — loại giao dịch thoả thuận
                    raw_volume = item.get('TotalMatchVol') or item.get('Volume', 0)
                    volume = int(raw_volume)

                    # Lấy giá đã điều chỉnh (adjusted close)
                    raw_adj = item.get('ClosePrice_Adjusted') or item.get('closepriceadjusted')
                    adj_close = float(raw_adj) if raw_adj is not None else None

                    # OHLC validation
                    if close_price <= 0 or open_price <= 0:
                        continue
                    if volume < 0:
                        continue
                    if low_price > high_price:
                        continue
                    if low_price > min(open_price, close_price) * 1.001:
                        # Cho phép sai số nhỏ do làm tròn
                        continue
                    if high_price < max(open_price, close_price) * 0.999:
                        continue

                    new_point = StockData(
                        stock=stock,
                        date=date(year, month, day),
                        open=open_price,
                        high=high_price,
                        low=low_price,
                        close=close_price,
                        volume=volume,
                        adj_close=adj_close,
                    )
                    all_new_points.append(new_point)
                except (ValueError, TypeError) as e:
                    print(f"Bỏ qua bản ghi không hợp lệ cho {ticker}: {e}")
                    continue

            # Nếu trả về ít hơn pageSize → đã hết data
            if len(page_data) < page_size:
                break
            page_index += 1

        if all_new_points:
            StockData.objects.bulk_create(all_new_points, ignore_conflicts=True)
            print(f"ĐÃ LƯU THÀNH CÔNG {len(all_new_points)} NGÀY DỮ LIỆU MỚI CHO MÃ {ticker}.")
        else:
            print(f"Không có dữ liệu mới để lưu cho mã {ticker}.")

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Lỗi nghiêm trọng khi cập nhật dữ liệu cho mã {ticker}: {e}")

    print("=" * 60 + "\n")