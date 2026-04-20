import json
import time
from collections import Counter
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from ssi_fc_data.fc_md_client import MarketDataClient
from ssi_fc_data.model.model import daily_stock_price

from api.models import Stock, StockData
from ssi_integration.ssi_config import get_ssi_config


class Command(BaseCommand):
    help = (
        "Debug SSI DailyStockPrice API: probe date-window limits and test chunked crawling strategy."
    )

    def add_arguments(self, parser):
        parser.add_argument("--ticker", required=True, help="Ticker symbol, e.g. FPT")
        parser.add_argument(
            "--from-date",
            default=(timezone.now().date() - timedelta(days=120)).isoformat(),
            help="Start date in YYYY-MM-DD",
        )
        parser.add_argument(
            "--to-date",
            default=timezone.now().date().isoformat(),
            help="End date in YYYY-MM-DD",
        )
        parser.add_argument(
            "--probe",
            action="store_true",
            help="Probe date window sizes to detect API limit behavior",
        )
        parser.add_argument(
            "--crawl",
            action="store_true",
            help="Run chunked crawl across the date range",
        )
        parser.add_argument(
            "--probe-sizes",
            default="7,14,30,31,45,60",
            help="Comma-separated probe window sizes in days",
        )
        parser.add_argument(
            "--chunk-days",
            type=int,
            default=30,
            help="Chunk size in days for crawl mode",
        )
        parser.add_argument(
            "--page-size",
            type=int,
            default=1000,
            help="SSI pageSize (DailyStockPrice max is typically 1000)",
        )
        parser.add_argument(
            "--pause",
            type=float,
            default=0.0,
            help="Sleep seconds between API calls to reduce rate-limit risk",
        )
        parser.add_argument(
            "--min-interval",
            type=float,
            default=1.1,
            help="Minimum seconds between consecutive API requests (SSI is ~1 req/s)",
        )
        parser.add_argument(
            "--max-429-retries",
            type=int,
            default=3,
            help="Maximum retries when API returns 429 quota exceeded",
        )
        parser.add_argument(
            "--retry-wait",
            type=float,
            default=1.2,
            help="Base wait seconds before retry after 429",
        )
        parser.add_argument(
            "--dump-sample",
            action="store_true",
            help="Print key names from first row to verify field naming",
        )
        parser.add_argument(
            "--save-json",
            default="",
            help="Optional output path to save deduplicated API rows as JSON",
        )
        parser.add_argument(
            "--write-db",
            action="store_true",
            help="Upsert crawled rows directly into StockData",
        )

    def handle(self, *args, **options):
        ticker = options["ticker"].upper().strip()
        from_date = self._parse_iso_date(options["from_date"], "from-date")
        to_date = self._parse_iso_date(options["to_date"], "to-date")

        if from_date > to_date:
            raise CommandError("from-date must be <= to-date")
        if options["chunk_days"] <= 0:
            raise CommandError("chunk-days must be > 0")
        if options["page_size"] <= 0:
            raise CommandError("page-size must be > 0")
        if options["pause"] < 0:
            raise CommandError("pause must be >= 0")
        if options["min_interval"] < 0:
            raise CommandError("min-interval must be >= 0")
        if options["max_429_retries"] < 0:
            raise CommandError("max-429-retries must be >= 0")
        if options["retry_wait"] < 0:
            raise CommandError("retry-wait must be >= 0")

        do_probe = options["probe"] or (not options["probe"] and not options["crawl"])
        do_crawl = options["crawl"] or (not options["probe"] and not options["crawl"])
        write_db = options["write_db"]

        if write_db and not do_crawl:
            raise CommandError("--write-db requires crawl mode")

        self.min_interval = options["min_interval"]
        self.max_429_retries = options["max_429_retries"]
        self.retry_wait = options["retry_wait"]
        self._last_api_call_ts = 0.0

        config = get_ssi_config()
        client = MarketDataClient(config)

        self.stdout.write("=" * 80)
        self.stdout.write(f"Ticker: {ticker}")
        self.stdout.write(f"Range : {from_date} -> {to_date}")
        self.stdout.write("=" * 80)

        if do_probe:
            probe_sizes = self._parse_probe_sizes(options["probe_sizes"])
            self._probe_window_limits(
                client=client,
                config=config,
                ticker=ticker,
                end_date=to_date,
                sizes=probe_sizes,
                page_size=options["page_size"],
                pause=options["pause"],
                dump_sample=options["dump_sample"],
            )

        dedup_rows = {}
        if do_crawl:
            dedup_rows = self._crawl_in_chunks(
                client=client,
                config=config,
                ticker=ticker,
                from_date=from_date,
                to_date=to_date,
                chunk_days=options["chunk_days"],
                page_size=options["page_size"],
                pause=options["pause"],
                dump_sample=options["dump_sample"],
            )

        save_path = options["save_json"].strip()
        if save_path and dedup_rows:
            self._save_rows_json(save_path, dedup_rows)

        if write_db and dedup_rows:
            self._upsert_to_db(ticker=ticker, dedup_rows=dedup_rows)

    def _parse_iso_date(self, raw: str, arg_name: str) -> date:
        try:
            return datetime.strptime(raw, "%Y-%m-%d").date()
        except ValueError as exc:
            raise CommandError(f"Invalid --{arg_name}: {raw}. Expected YYYY-MM-DD") from exc

    def _parse_probe_sizes(self, raw_sizes: str):
        try:
            values = [int(x.strip()) for x in raw_sizes.split(",") if x.strip()]
        except ValueError as exc:
            raise CommandError("--probe-sizes must be comma-separated integers") from exc

        if not values:
            raise CommandError("--probe-sizes cannot be empty")
        for value in values:
            if value <= 0:
                raise CommandError("--probe-sizes values must be > 0")
        return values

    def _fetch_page(self, client, config, ticker, start_date, end_date, page_index, page_size):
        req = daily_stock_price(
            symbol=ticker,
            fromDate=start_date.strftime("%d/%m/%Y"),
            toDate=end_date.strftime("%d/%m/%Y"),
            pageIndex=page_index,
            pageSize=page_size,
        )

        for attempt in range(self.max_429_retries + 1):
            self._respect_min_interval()
            response = client.daily_stock_price(config, req)
            self._last_api_call_ts = time.monotonic()

            status = response.get("status")
            message = str(response.get("message") or "")
            status_str = str(status).lower()
            is_429 = status == 429 or status_str == "429" or "quota exceeded" in message.lower()

            if is_429 and attempt < self.max_429_retries:
                wait_seconds = max(self.min_interval, self.retry_wait * (attempt + 1))
                self.stdout.write(
                    self.style.WARNING(
                        f"  [429] {ticker} {start_date}->{end_date} page={page_index}; "
                        f"retry {attempt + 1}/{self.max_429_retries} after {wait_seconds:.2f}s"
                    )
                )
                time.sleep(wait_seconds)
                continue

            data = response.get("data")
            ok = (status == 200 or status_str == "success") and isinstance(data, list)
            return ok, response

        # Defensive fallback; loop always returns.
        return False, {"status": "Error", "message": "Unexpected retry flow", "data": []}

    def _respect_min_interval(self):
        if self.min_interval <= 0:
            return

        now = time.monotonic()
        elapsed = now - self._last_api_call_ts
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)

    def _probe_window_limits(
        self,
        client,
        config,
        ticker,
        end_date,
        sizes,
        page_size,
        pause,
        dump_sample,
    ):
        self.stdout.write("\n[Probe] Testing date-window behavior")
        for days in sizes:
            start_date = end_date - timedelta(days=days - 1)
            ok, response = self._fetch_page(
                client=client,
                config=config,
                ticker=ticker,
                start_date=start_date,
                end_date=end_date,
                page_index=1,
                page_size=page_size,
            )

            data = response.get("data") or []
            status = response.get("status")
            message = response.get("message")

            self.stdout.write(
                f"  - {days:>3} days | {start_date} -> {end_date} | "
                f"status={status} ok={ok} rows={len(data)} message={message}"
            )

            if dump_sample and data:
                keys = sorted(data[0].keys())
                self.stdout.write(f"    sample keys: {keys}")

            if pause > 0:
                time.sleep(pause)

    def _crawl_in_chunks(
        self,
        client,
        config,
        ticker,
        from_date,
        to_date,
        chunk_days,
        page_size,
        pause,
        dump_sample,
    ):
        self.stdout.write(
            f"\n[Crawl] Running chunked crawl with chunk_days={chunk_days}, page_size={page_size}"
        )

        cursor = from_date
        chunk_idx = 0
        dedup_rows = {}
        raw_count = 0

        while cursor <= to_date:
            chunk_idx += 1
            chunk_end = min(cursor + timedelta(days=chunk_days - 1), to_date)
            page_index = 1
            chunk_raw_count = 0

            while True:
                ok, response = self._fetch_page(
                    client=client,
                    config=config,
                    ticker=ticker,
                    start_date=cursor,
                    end_date=chunk_end,
                    page_index=page_index,
                    page_size=page_size,
                )

                data = response.get("data") or []
                status = response.get("status")

                if not ok:
                    self.stdout.write(
                        self.style.WARNING(
                            "  "
                            + f"chunk={chunk_idx} page={page_index} "
                            + f"{cursor}->{chunk_end} returned status={status} "
                            + f"message={response.get('message')}"
                        )
                    )
                    break

                if not data:
                    break

                if dump_sample and page_index == 1:
                    keys = sorted(data[0].keys())
                    self.stdout.write(f"  chunk={chunk_idx} sample keys: {keys}")

                for row in data:
                    trading_date = row.get("TradingDate")
                    if not trading_date:
                        continue
                    dedup_rows[trading_date] = row
                    raw_count += 1
                    chunk_raw_count += 1

                if len(data) < page_size:
                    break

                page_index += 1
                if pause > 0:
                    time.sleep(pause)

            self.stdout.write(
                "  "
                + f"chunk={chunk_idx} {cursor}->{chunk_end} "
                + f"raw_rows={chunk_raw_count} unique_total={len(dedup_rows)}"
            )

            cursor = chunk_end + timedelta(days=1)
            if pause > 0:
                time.sleep(pause)

        self._print_summary(raw_count, dedup_rows)
        return dedup_rows

    def _print_summary(self, raw_count, dedup_rows):
        unique_count = len(dedup_rows)
        duplicate_count = max(raw_count - unique_count, 0)

        self.stdout.write("\n[Summary]")
        self.stdout.write(f"  raw rows fetched   : {raw_count}")
        self.stdout.write(f"  unique by date     : {unique_count}")
        self.stdout.write(f"  duplicates removed : {duplicate_count}")

        if not dedup_rows:
            return

        date_values = []
        field_counter = Counter()
        for trading_date, row in dedup_rows.items():
            try:
                day, month, year = map(int, trading_date.split("/"))
                date_values.append(date(year, month, day))
            except Exception:
                continue

            for key in (
                "ClosePriceAdjusted",
                "closepriceadjusted",
                "ClosePrice_Adjusted",
            ):
                value = row.get(key)
                if value not in (None, ""):
                    field_counter[key] += 1

        if date_values:
            self.stdout.write(f"  min date           : {min(date_values)}")
            self.stdout.write(f"  max date           : {max(date_values)}")

        if field_counter:
            self.stdout.write("  adjusted field hits:")
            for key, count in field_counter.items():
                self.stdout.write(f"    - {key}: {count}")
        else:
            self.stdout.write("  adjusted field hits: none")

    def _save_rows_json(self, output_path, dedup_rows):
        payload = {
            "count": len(dedup_rows),
            "rows": [dedup_rows[key] for key in sorted(dedup_rows.keys())],
        }
        with open(output_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=True, indent=2)

        self.stdout.write(self.style.SUCCESS(f"Saved JSON debug output: {output_path}"))

    def _pick_value(self, row, keys, default=None):
        for key in keys:
            if key in row and row[key] not in (None, ""):
                return row[key]
        return default

    def _to_decimal_2(self, raw):
        if raw in (None, ""):
            return None
        try:
            return Decimal(str(raw)).quantize(Decimal("0.01"))
        except (InvalidOperation, TypeError, ValueError):
            return None

    def _to_int(self, raw, default=0):
        if raw in (None, ""):
            return default
        try:
            return int(float(raw))
        except (TypeError, ValueError):
            return default

    def _extract_row_for_stockdata(self, row):
        trading_date = row.get("TradingDate")
        if not trading_date:
            return None

        try:
            day, month, year = map(int, trading_date.split("/"))
            trade_date = date(year, month, day)
        except Exception:
            return None

        open_price = self._to_decimal_2(self._pick_value(row, ("OpenPrice", "Open")))
        high_price = self._to_decimal_2(self._pick_value(row, ("HighestPrice", "High")))
        low_price = self._to_decimal_2(self._pick_value(row, ("LowestPrice", "Low")))
        close_price = self._to_decimal_2(self._pick_value(row, ("ClosePrice", "Close")))

        if not all([open_price, high_price, low_price, close_price]):
            return None

        volume = self._to_int(self._pick_value(row, ("TotalMatchVol", "Volume"), 0), default=0)
        adj_close = self._to_decimal_2(
            self._pick_value(
                row,
                (
                    "ClosePriceAdjusted",
                    "closepriceadjusted",
                    "ClosePrice_Adjusted",
                ),
                None,
            )
        )

        return trade_date, {
            "open": open_price,
            "high": high_price,
            "low": low_price,
            "close": close_price,
            "volume": volume,
            "adj_close": adj_close,
        }

    def _upsert_to_db(self, ticker, dedup_rows):
        try:
            stock = Stock.objects.get(ticker=ticker)
        except Stock.DoesNotExist as exc:
            raise CommandError(f"Ticker {ticker} does not exist in Stock table") from exc

        parsed_items = []
        skipped = 0
        for _, row in dedup_rows.items():
            extracted = self._extract_row_for_stockdata(row)
            if not extracted:
                skipped += 1
                continue
            parsed_items.append(extracted)

        if not parsed_items:
            self.stdout.write(self.style.WARNING("No valid rows to write into DB."))
            return

        date_list = [trade_date for trade_date, _ in parsed_items]
        existing_qs = StockData.objects.filter(stock=stock, date__in=date_list)
        existing_map = {obj.date: obj for obj in existing_qs}

        to_create = []
        to_update = []

        for trade_date, values in parsed_items:
            existing = existing_map.get(trade_date)
            if existing:
                existing.open = values["open"]
                existing.high = values["high"]
                existing.low = values["low"]
                existing.close = values["close"]
                existing.volume = values["volume"]
                existing.adj_close = values["adj_close"]
                to_update.append(existing)
            else:
                to_create.append(
                    StockData(
                        stock=stock,
                        date=trade_date,
                        open=values["open"],
                        high=values["high"],
                        low=values["low"],
                        close=values["close"],
                        volume=values["volume"],
                        adj_close=values["adj_close"],
                    )
                )

        if to_create:
            StockData.objects.bulk_create(to_create, batch_size=1000)

        if to_update:
            StockData.objects.bulk_update(
                to_update,
                fields=["open", "high", "low", "close", "volume", "adj_close"],
                batch_size=1000,
            )

        self.stdout.write("\n[DB Write]")
        self.stdout.write(f"  ticker            : {ticker}")
        self.stdout.write(f"  created rows      : {len(to_create)}")
        self.stdout.write(f"  updated rows      : {len(to_update)}")
        self.stdout.write(f"  skipped invalid   : {skipped}")
        self.stdout.write(self.style.SUCCESS("  DB upsert completed."))