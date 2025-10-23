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
        print(f"[DEBUG] Sẽ bắt đầu lấy dữ liệu từ ngày: {from_date.strftime('%Y-%m-%d')}")
    else:
        from_date = today - timedelta(days=365 * 5)
        print(f"[DEBUG] Không có dữ liệu trong DB. Sẽ bắt đầu lấy dữ liệu từ ngày: {from_date.strftime('%Y-%m-%d')}")

    if from_date > today:  # Sửa thành '>' để tránh trường hợp from_date == today
        print(f"[DEBUG] Điều kiện dừng được kích hoạt: from_date ({from_date}) > today ({today}).")
        print(f"[DEBUG] Kết luận: Dữ liệu cho mã {ticker} đã được cập nhật. Không cần gọi API.")
        print("=" * 60 + "\n")
        return

    print(f"[DEBUG] Điều kiện dừng KHÔNG được kích hoạt. Bắt đầu gọi API SSI...")
    print(f"Đang lấy dữ liệu cho mã {ticker} từ {from_date.strftime('%d/%m/%Y')} đến {today.strftime('%d/%m/%Y')}...")

    try:
        config = get_ssi_config()
        client = MarketDataClient(config)

        request_obj = daily_ohlc(
            symbol=ticker,
            fromDate=from_date.strftime('%d/%m/%Y'),
            toDate=today.strftime('%d/%m/%Y'),
            pageSize=2000
        )

        response = client.daily_ohlc(config, request_obj)

        # ==============================================================================
        # SỬA LỖI LOGIC KIỂM TRA RESPONSE
        # Chấp nhận cả status là số 200 hoặc chuỗi 'Success'
        # ==============================================================================
        response_status = response.get('status')
        if (response_status == 200 or str(response_status).lower() == 'success') and response.get('data'):
            new_data_points = []
            for item in response['data']:
                trading_date_str = item.get('TradingDate')
                day, month, year = map(int, trading_date_str.split('/'))

                # Bỏ qua các bản ghi có giá trị không hợp lệ
                try:
                    new_point = StockData(
                        stock=stock,
                        date=date(year, month, day),
                        open=float(item.get('Open')),
                        high=float(item.get('High')),
                        low=float(item.get('Low')),
                        close=float(item.get('Close')),
                        volume=int(item.get('Volume'))
                    )
                    new_data_points.append(new_point)
                except (ValueError, TypeError):
                    print(f"Bỏ qua bản ghi không hợp lệ: {item}")
                    continue

            if new_data_points:
                # Dùng ignore_conflicts để tránh lỗi nếu có ngày bị trùng
                StockData.objects.bulk_create(new_data_points, ignore_conflicts=True)
                print(f"ĐÃ LƯU THÀNH CÔNG {len(new_data_points)} NGÀY DỮ LIỆU MỚI CHO MÃ {ticker}.")
        else:
            print(f"Không có dữ liệu mới hoặc có lỗi từ API SSI cho mã {ticker}. Response: {response}")

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Lỗi nghiêm trọng khi cập nhật dữ liệu cho mã {ticker}: {e}")

    print("=" * 60 + "\n")