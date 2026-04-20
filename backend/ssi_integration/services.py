# ssi_integration/services.py

import time
import concurrent.futures
from datetime import date, timedelta
from django.utils import timezone
from ssi_fc_data.fc_md_client import MarketDataClient
from ssi_fc_data.model.model import daily_ohlc
from .ssi_config import get_ssi_config
from api.models import Stock, StockData

_API_CALL_TIMEOUT = 30  # seconds

# --- Hằng số cho retry ---
_MAX_RETRIES_429 = 5
_RETRY_BACKOFF_BASE = 1.5
_REQUEST_INTERVAL = 0.5


def _response_ok(response) -> bool:
    """Kiểm tra response từ SSI có thành công không."""
    if not response:
        return False
    status = response.get('status')
    return status == 200 or str(status).lower() == 'success'


def _throttled_request(func, config, req, context: str = "", timeout: int = _API_CALL_TIMEOUT):
    """
    Gọi hàm API SSI với retry tự động khi bị rate-limit (429).
    Có timeout để tránh API call bị treo vô hạn.
    Trả về response dict hoặc {} nếu hết retry/timeout.
    """
    for attempt in range(_MAX_RETRIES_429 + 1):
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(func, config, req)
                response = future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            print(f"[WARN] {context}: API call timeout ({timeout}s), attempt {attempt + 1}")
            if attempt >= _MAX_RETRIES_429:
                return {}
            time.sleep(_RETRY_BACKOFF_BASE * (attempt + 1))
            continue
        except Exception as e:
            print(f"[ERROR] {context}: API call error: {e}")
            return {}

        status = response.get('status')
        if status != 429:
            return response
        if attempt >= _MAX_RETRIES_429:
            print(f"[WARN] {context}: Rate limit vượt quá {_MAX_RETRIES_429} lần retry.")
            return response
        wait = _RETRY_BACKOFF_BASE * (attempt + 1)
        print(f"[WARN] {context}: 429 Rate limit, retry {attempt + 1}/{_MAX_RETRIES_429} sau {wait:.1f}s...")
        time.sleep(wait)
    return {}


def _parse_ohlcv_item(item, ticker):
    """
    Parse một bản ghi OHLCV từ SSI API, trả về tuple hoặc None nếu không hợp lệ.
    """
    trading_date_str = item.get('TradingDate')
    if not trading_date_str:
        return None
    try:
        day, month, year = map(int, trading_date_str.split('/'))
        open_price = float(item.get('Open', 0))
        high_price = float(item.get('High', 0))
        low_price = float(item.get('Low', 0))
        close_price = float(item.get('Close', 0))
        raw_volume = item.get('TotalMatchVol') or item.get('Volume', 0)
        volume = int(raw_volume)
        raw_adj = item.get('ClosePrice_Adjusted') or item.get('closepriceadjusted')
        adj_close = float(raw_adj) if raw_adj is not None else None

        # OHLC validation
        if close_price <= 0 or open_price <= 0:
            return None
        if volume < 0:
            return None
        if low_price > high_price:
            return None
        if low_price > min(open_price, close_price) * 1.001:
            return None
        if high_price < max(open_price, close_price) * 0.999:
            return None

        return date(year, month, day), open_price, high_price, low_price, close_price, volume, adj_close
    except (ValueError, TypeError) as e:
        print(f"Bỏ qua bản ghi không hợp lệ cho {ticker}: {e}")
        return None


def update_historical_data_with_client(client, config, ticker: str):
    """
    Như update_historical_data nhưng nhận client & config đã khởi tạo sẵn,
    tránh tạo lại client cho mỗi ticker khi chạy batch.
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
        response = _throttled_request(client.daily_ohlc, config, request_obj, context=f"daily_ohlc {ticker} p{page_index}")

        if not (_response_ok(response) and response.get('data')):
            if page_index == 1:
                print(f"Không có dữ liệu mới từ SSI cho mã {ticker}. Response: {response}")
            break

        page_data = response['data']
        print(f"  Trang {page_index}: {len(page_data)} bản ghi")

        for item in page_data:
            parsed = _parse_ohlcv_item(item, ticker)
            if parsed is None:
                continue
            trading_date, open_p, high_p, low_p, close_p, vol, adj_close = parsed
            all_new_points.append(StockData(
                stock=stock, date=trading_date,
                open=open_p, high=high_p, low=low_p, close=close_p,
                volume=vol, adj_close=adj_close,
            ))

        if len(page_data) < page_size:
            break
        page_index += 1
        time.sleep(_REQUEST_INTERVAL)

    if all_new_points:
        StockData.objects.bulk_create(all_new_points, ignore_conflicts=True)
        print(f"ĐÃ LƯU THÀNH CÔNG {len(all_new_points)} NGÀY DỮ LIỆU MỚI CHO MÃ {ticker}.")
    else:
        print(f"Không có dữ liệu mới để lưu cho mã {ticker}.")
    print("=" * 60 + "\n")


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