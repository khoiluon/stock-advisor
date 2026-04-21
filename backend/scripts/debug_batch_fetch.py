"""Debug script: test batch fetch from SSI daily_stock_price API."""
import os
import sys
import time
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "investcore.settings")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from ssi_fc_data.fc_md_client import MarketDataClient
from ssi_fc_data.model.model import daily_stock_price
from ssi_integration.ssi_config import get_ssi_config
from ssi_integration.services import _throttled_request, _response_ok

config = get_ssi_config()
client = MarketDataClient(config)

# Test: fetch page 1 WITH symbol=FPT for recent date
print("=" * 60)
print("TEST 1: symbol=FPT, recent dates")
req = daily_stock_price(
    symbol="FPT",
    fromDate="13/04/2026",
    toDate="20/04/2026",
    pageIndex=1,
    pageSize=1000,
    market="HOSE",
)
t0 = time.time()
resp = _throttled_request(client.daily_stock_price, config, req, context="test-FPT p1")
elapsed = time.time() - t0
data = resp.get("data", [])
print(f"Status: {resp.get('status')}, Rows: {len(data)}, Time: {elapsed:.1f}s")
if data:
    symbols = set(item.get("Symbol", "") for item in data)
    dates = set(item.get("TradingDate", "") for item in data)
    print(f"Unique symbols: {len(symbols)}, Dates: {sorted(dates)}")
    print(f"Sample symbols: {sorted(symbols)[:10]}")

time.sleep(1.5)

# Test: fetch page 1 WITHOUT symbol filter
print("\n" + "=" * 60)
print("TEST 2: symbol='', recent dates (batch)")
req2 = daily_stock_price(
    symbol="",
    fromDate="17/04/2026",
    toDate="20/04/2026",
    pageIndex=1,
    pageSize=1000,
    market="",
)
t0 = time.time()
resp2 = _throttled_request(client.daily_stock_price, config, req2, context="test-all p1")
elapsed2 = time.time() - t0
data2 = resp2.get("data", [])
print(f"Status: {resp2.get('status')}, Rows: {len(data2)}, Time: {elapsed2:.1f}s")
if data2:
    symbols2 = set(item.get("Symbol", "") for item in data2)
    dates2 = set(item.get("TradingDate", "") for item in data2)
    print(f"Unique symbols: {len(symbols2)}, Dates: {sorted(dates2)}")
    # Check if FPT is in there
    fpt_rows = [item for item in data2 if (item.get("Symbol") or "").upper() == "FPT"]
    print(f"FPT rows in batch: {len(fpt_rows)}")

time.sleep(1.5)

# Test: paginate ALL pages for 1-day range
print("\n" + "=" * 60)
print("TEST 3: Paginate all data for 1 day (17/04/2026)")
all_data = {}
page = 1
total_time = 0
while True:
    req3 = daily_stock_price(
        symbol="",
        fromDate="17/04/2026",
        toDate="17/04/2026",
        pageIndex=page,
        pageSize=1000,
        market="",
    )
    t0 = time.time()
    resp3 = _throttled_request(client.daily_stock_price, config, req3, context=f"test-1day p{page}")
    pt = time.time() - t0
    total_time += pt
    data3 = resp3.get("data", [])
    if not data3:
        print(f"  Page {page}: 0 rows (api={pt:.1f}s) → STOP")
        break
    for item in data3:
        sym = (item.get("Symbol") or "").upper()
        if sym:
            all_data.setdefault(sym, []).append(item)
    print(f"  Page {page}: {len(data3)} rows, cumul_symbols={len(all_data)} (api={pt:.1f}s)")
    if len(data3) < 1000:
        break
    page += 1
    time.sleep(1.0)

print(f"\nTotal: {len(all_data)} unique symbols, {sum(len(v) for v in all_data.values())} rows, {total_time:.1f}s")
fpt = all_data.get("FPT", [])
if fpt:
    print(f"FPT: {len(fpt)} rows")
    for r in fpt:
        print(f"  {r.get('TradingDate')} Close={r.get('ClosePrice')} AdjClose={r.get('ClosePriceAdjusted')}")
