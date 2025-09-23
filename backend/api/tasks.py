import re
import time
import random
import logging
import os
from dotenv import load_dotenv
from datetime import datetime
from urllib.parse import urljoin

from celery import shared_task
from firecrawl import FirecrawlApp
from bs4 import BeautifulSoup
from django.utils import timezone
from django.db import IntegrityError

from vnstock import Listing, Quote
from .models import Article, NewsSource, Stock, StockData
import requests
from decouple import config
import pandas as pd
from datetime import datetime, timedelta

# NEW imports
import redis

load_dotenv()

logger = logging.getLogger(__name__)

# ==================== CONFIGURATION ====================

# Data News
API_KEY = os.getenv('FIRE_CRAWL_API_KEY')
BASE_URL = 'https://cafef.vn/thi-truong-chung-khoan.chn'
DOMAIN = 'https://cafef.vn'

# Giới hạn số bài viết (hằng số để chỉnh sau)
MAX_ARTICLES = 20

# Rate limiting configuration
BASE_DELAY_SECONDS = 4
MAX_DELAY_SECONDS = 8

# Stock tagging configuration
AMBIGUOUS_TICKERS = {'CEO', 'GAS', 'TIN', 'HAG', 'GIL', 'PET', 'FIT', 'VIX', 'BCG', 'PNG'}
FINANCIAL_KEYWORDS = {
    'CỔ PHIẾU', 'MÃ CK', 'MÃ CHỨNG KHOÁN', 'THỊ TRƯỜNG', 'GIAO DỊCH',
    'VN-INDEX', 'HNX-INDEX', 'SÀN HOSE', 'SÀN HNX', 'UPCOM',
    'TĂNG', 'GIẢM', 'KHỐI LƯỢNG', 'THANH KHOẢN', 'CÔNG TY CỔ PHẦN', 'CTCP'
}

# Data Stock
MAX_GENERAL_RETRIES = 2
MAX_RATE_LIMIT_RETRIES = 30
RETRY_DELAY = 2
RATE_LIMIT_BASE_WAIT = 30  # Giảm để nhanh
INITIAL_DELAY = 2  # Giảm để nhanh

# New: chunk size for DB writes and processed bookkeeping
CHUNK_SIZE = 200

# Redis connection (used for cooldown locking and processed set)
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
try:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
except Exception as e:
    logger.warning(f"Cannot connect to Redis at {REDIS_URL}: {e}")
    redis_client = None

# ==================== HELPER FUNCTIONS ====================

def get_main_scrape_options():
    """Return scraping options for main page (HTML format)."""
    return {
        'headers': {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'},
        'timeout': 30000,
        'block_ads': True,
        'formats': ['html']
    }


def get_detail_scrape_options():
    """Return scraping options for detail page (default markdown)."""
    return {
        'headers': {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'},
        'timeout': 30000,
        'block_ads': True
    }


def normalize_url(domain, url):
    """Normalize URL and handle edge cases."""
    if not url:
        return ""

    full_url = urljoin(domain, url)
    if full_url.endswith('-'):
        logger.warning(f"Potentially truncated URL: {full_url}")
    return full_url


def is_duplicate_url(url, session_urls, existing_urls):
    """Check if URL is duplicate in current session or database."""
    return url in session_urls or url in existing_urls


def calculate_delay(current_index, total_articles):
    """Calculate delay time with progressive backoff and jitter."""
    progress_ratio = current_index / total_articles
    progressive_delay = BASE_DELAY_SECONDS + (progress_ratio * MAX_DELAY_SECONDS)
    jitter = random.uniform(1, 3)
    return progressive_delay + jitter


def remove_markdown_links(text):
    """Remove markdown link syntax from text."""
    return re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\1', text)


def extract_tickers_from_content(title, content, all_tickers):
    """Extract stock tickers from article content with context awareness."""
    content_text = remove_markdown_links(content)
    search_text = (title + ' ' + content_text).upper()
    found_tickers = set()

    for ticker in all_tickers:
        ticker_pattern = r'\b' + re.escape(ticker) + r'\b'

        if ticker in AMBIGUOUS_TICKERS:
            for match in re.finditer(ticker_pattern, search_text):
                context_start = max(0, match.start() - 50)
                context_end = match.end() + 50
                context = search_text[context_start:context_end]

                if any(keyword in context for keyword in FINANCIAL_KEYWORDS):
                    found_tickers.add(ticker)
                    break
        else:
            if re.search(ticker_pattern, search_text):
                found_tickers.add(ticker)

    return found_tickers


def parse_articles_from_section(soup, domain, session_urls, existing_urls,
                               item_selector, title_selector, desc_selector, img_selector):
    """Extract articles from a specific page section."""
    articles = []

    for item in soup.select(item_selector):
        title_element = item.select_one(title_selector)
        if not title_element or not title_element.get("href"):
            continue

        url = normalize_url(domain, title_element["href"])
        if not url or is_duplicate_url(url, session_urls, existing_urls):
            continue

        session_urls.add(url)

        title = title_element.get_text(strip=True)

        description_element = item.select_one(desc_selector)
        description = description_element.get_text(strip=True) if description_element else ''

        image_element = item.select_one(img_selector)
        thumbnail_url = ''
        if image_element and image_element.get("src"):
            thumbnail_url = normalize_url(domain, image_element.get("src"))

        articles.append({
            'title': title,
            'url': url,
            'description': description,
            'thumbnail_url': thumbnail_url
        })

    return articles


def parse_published_date(metadata):
    """Parse published date from metadata with fallback to current time."""
    if not metadata or not hasattr(metadata, 'publishedTime') or not metadata.publishedTime:
        return timezone.now()

    try:
        date_str = metadata.publishedTime.replace('Z', '+00:00')
        parsed_date = datetime.fromisoformat(date_str)

        if timezone.is_naive(parsed_date):
            parsed_date = timezone.make_aware(parsed_date)

        return parsed_date

    except ValueError:
        logger.warning(f"Could not parse date: {metadata.publishedTime}")
        return timezone.now()


def save_article_with_stocks(article_data, source, all_tickers):
    """Save article and tag stocks."""
    try:
        article = Article.objects.create(
            source=source,
            title=article_data['title'],
            description=article_data['description'],
            content_markdown=article_data['content'],
            url=article_data['url'],
            thumbnail_url=article_data['thumbnail_url'],
            published_at=article_data['published_at']
        )

        found_tickers = extract_tickers_from_content(
            article.title,
            article.content_markdown,
            all_tickers
        )

        if found_tickers:
            logger.info(f"    -> Found tickers: {', '.join(found_tickers)}")
            stocks = Stock.objects.filter(ticker__in=found_tickers)
            article.related_stocks.add(*stocks)

        logger.info(f"    -> Successfully saved: {article_data['title']}")
        return True

    except IntegrityError as e:
        if '1062' in str(e) or 'Duplicate entry' in str(e):
            logger.info(f"    -> URL already exists: {article_data['url']}")
        else:
            logger.error(f"    -> Database integrity error: {e}")
        return False

    except Exception as e:
        logger.error(f"    -> Error saving article: {e}", exc_info=True)
        return False

# ==================== News TASK ====================

@shared_task
def crawl_news_task():
    """Main task to crawl and process up to MAX_ARTICLES news articles."""
    start_time = time.time()
    logger.info("=" * 60)
    logger.info("STARTING NEWS CRAWL TASK")
    logger.info(f"Start time: {timezone.now()}")
    logger.info("=" * 60)

    # Initialize
    app = FirecrawlApp(api_key=API_KEY)
    source, _ = NewsSource.objects.get_or_create(
        name='CafeF',
        defaults={'base_url': DOMAIN}
    )
    all_tickers = list(Stock.objects.values_list('ticker', flat=True))
    existing_urls = set(Article.objects.values_list('url', flat=True))

    logger.info(f"Loaded {len(existing_urls)} existing URLs from database")
    logger.info(f"Loaded {len(all_tickers)} stock tickers")

    try:
        # Scrape main page (HTML format)
        logger.info(f"Scraping main page: {BASE_URL}")
        main_page_data = app.scrape(url=BASE_URL, **get_main_scrape_options())

        if not hasattr(main_page_data, 'html') or not main_page_data.html:
            logger.error("Failed: Could not fetch main page HTML")
            return "Failed: Could not fetch main page HTML"

        # Parse articles from different sections
        soup = BeautifulSoup(main_page_data.html, 'html.parser')
        session_urls = set()
        articles_to_process = []

        # Section 1: Featured articles
        articles_to_process.extend(
            parse_articles_from_section(
                soup, DOMAIN, session_urls, existing_urls,
                'div.tlitem', 'h3 a', 'p.sapo', 'img'
            )
        )

        # Section 2: News list
        articles_to_process.extend(
            parse_articles_from_section(
                soup, DOMAIN, session_urls, existing_urls,
                'ul.list_news li', 'h3 a', 'p', 'img'
            )
        )

        # Limit articles to MAX_ARTICLES
        articles_to_process = articles_to_process[:MAX_ARTICLES]
        logger.info(f"Found {len(articles_to_process)} new articles to process (limited to {MAX_ARTICLES})")

        # Process each article
        successful_saves = 0

        for index, article_info in enumerate(articles_to_process, 1):
            logger.info(f"Processing article {index}/{len(articles_to_process)}: {article_info['title']}")

            try:
                # Scrape article detail (default markdown)
                detail_data = app.scrape(url=article_info['url'], **get_detail_scrape_options())

                if not hasattr(detail_data, 'markdown') or not detail_data.markdown:
                    logger.warning(f"    -> No content available for: {article_info['url']}")
                    logger.debug(f"    -> Detail data: {vars(detail_data) if detail_data else 'None'}")
                    continue

                # Prepare article data
                article_data = {
                    'title': article_info['title'],
                    'description': article_info['description'],
                    'content': detail_data.markdown,
                    'url': article_info['url'],
                    'thumbnail_url': article_info['thumbnail_url'],
                    'published_at': parse_published_date(getattr(detail_data, 'metadata', None))
                }

                # Save article
                if save_article_with_stocks(article_data, source, all_tickers):
                    successful_saves += 1

            except Exception as e:
                logger.error(f"    -> Error processing {article_info['url']}: {e}")
                continue

            # Delay to avoid rate limiting (skip for last article)
            if index < len(articles_to_process):
                delay = calculate_delay(index, len(articles_to_process))
                logger.info(f"    -> Waiting {delay:.1f}s to avoid rate limiting...")
                time.sleep(delay)

        # Final summary
        execution_time = time.time() - start_time
        summary = f"COMPLETED: {successful_saves}/{len(articles_to_process)} articles saved in {execution_time:.1f}s"
        logger.info(summary)
        return summary

    except Exception as e:
        logger.error(f"Critical error in crawl task: {e}", exc_info=True)
        return f"Task failed: {e}"

# ==================== Stock Data TASK (PATCHED) ====================

@shared_task(bind=True)
def fetch_daily_data_vnstock_task(self):
    """
    Task gộp: Lấy EOD cho 9/9/2025 (hoặc daily) dùng loop tuyến tính, tối ưu retry/delay.

    Tối ưu chính:
    - Dùng Redis để ghi 'processed' set (đánh dấu ticker đã xong) để task có thể resume
    - Khi phát hiện rate-limit: đặt cooldown key vào Redis và **re-queue task** với countdown
      để worker hiện tại **không bị block** (giúp hiệu năng cao hơn)
    - Ghi DB theo chunk để tránh mất dữ liệu nếu task bị re-queued/kill
    """
    logger.info("=" * 60)
    logger.info("BẮT ĐẦU TASK LẤY DỮ LIỆU HÀNG NGÀY TỪ VNSTOCK 3.2.6 (LOOP TỐI ƯU)")

    today_str = '2025-09-09'
    today = datetime.strptime(today_str, '%Y-%m-%d').date()

    cooldown_key = f"vnstock:rate_limit_cooldown"
    processed_set = f"vnstock:processed:{today_str}"

    try:
        # BƯỚC 1: LẤY DANH SÁCH TICKER
        logger.info("Đang lấy danh sách ticker từ Listing...")
        listing_client = Listing()
        df_all_symbols = listing_client.all_symbols()

        all_tickers = df_all_symbols['symbol'].tolist()
        original_count = len(all_tickers)
        all_tickers = [
            ticker for ticker in all_tickers
            if 3 <= len(ticker) <= 5 and ticker.isalpha() and not any(c.isdigit() for c in ticker)
        ]
        skipped_count = original_count - len(all_tickers)
        logger.info(f"Lọc thành công: {len(all_tickers)} ticker hợp lệ (bỏ qua {skipped_count}).")

        all_stocks_map = {stock.ticker: stock for stock in Stock.objects.all()}
        # Only keep tickers that exist in DB
        all_tickers = [t for t in all_tickers if t in all_stocks_map]
        logger.info(f"Sau khi khớp DB: {len(all_tickers)} ticker cần xử lý.")

        # If Redis processed set exists, filter out already processed tickers
        if redis_client:
            try:
                processed_members = redis_client.smembers(processed_set) or set()
                if processed_members:
                    before = len(all_tickers)
                    all_tickers = [t for t in all_tickers if t not in processed_members]
                    logger.info(f"Đã lọc {before - len(all_tickers)} tickers đã xử lý trước đó.")
            except Exception as e:
                logger.warning(f"Không thể đọc processed_set từ Redis: {e}")

        # BƯỚC 2: LẤY DỮ LIỆU EOD
        buffer = []  # buffer để bulk_create theo chunk
        success_count = 0
        error_count = 0
        start_time = datetime.now()

        for i, ticker in enumerate(all_tickers, 1):
            # Before calling API, check global cooldown (if set by other worker)
            if redis_client:
                try:
                    if redis_client.exists(cooldown_key):
                        ttl = redis_client.ttl(cooldown_key) or 10
                        logger.info(f"Cooldown active (set by another worker). Re-queueing task after {ttl}s and exiting current run.")
                        # Re-queue task to resume after TTL + small margin
                        fetch_daily_data_vnstock_task.apply_async(countdown=ttl + 5)
                        return f"Re-queued due to cooldown (ttl={ttl})"
                except Exception as e:
                    logger.warning(f"Error checking cooldown key in Redis: {e}")

            general_retry_count = 0
            rate_limit_retry_count = 0
            ticker_processed = False

            while (general_retry_count < MAX_GENERAL_RETRIES or rate_limit_retry_count < MAX_RATE_LIMIT_RETRIES) and not ticker_processed:
                try:
                    logger.info(f"Xử lý {i}/{len(all_tickers)}: {ticker} (Retry: G{general_retry_count}, RL{rate_limit_retry_count})")

                    quote_client = Quote(symbol=ticker, source='TCBS')
                    df_history = quote_client.history(start=today_str, end=today_str, resolution='1d')

                    if df_history is None or df_history.empty:
                        logger.warning(f"Không có dữ liệu cho {ticker} ngày {today_str}. Bỏ qua.")
                        error_count += 1
                        ticker_processed = True
                        # mark processed to avoid retrying repeatedly
                        if redis_client:
                            try:
                                redis_client.sadd(processed_set, ticker)
                            except Exception:
                                pass
                        continue

                    # Lấy row cuối
                    row = df_history.iloc[-1]
                    date_str = row.name if df_history.index.name == 'time' else row.get('time', today_str)
                    date_obj = pd.to_datetime(date_str, errors='coerce').date()

                    if date_obj != today:
                        logger.warning(f"Dữ liệu {ticker} không phải {today_str}. Bỏ qua.")
                        error_count += 1
                        ticker_processed = True
                        if redis_client:
                            try:
                                redis_client.sadd(processed_set, ticker)
                            except Exception:
                                pass
                        continue

                    if row.get('volume', 0) == 0:
                        logger.warning(f"Volume=0 cho {ticker} ngày {today_str}. Bỏ qua.")
                        error_count += 1
                        ticker_processed = True
                        if redis_client:
                            try:
                                redis_client.sadd(processed_set, ticker)
                            except Exception:
                                pass
                        continue

                    stock_data = StockData(
                        stock=all_stocks_map[ticker],
                        date=date_obj,
                        open=float(row['open']),
                        high=float(row['high']),
                        low=float(row['low']),
                        close=float(row['close']),
                        volume=int(row['volume'])
                    )
                    buffer.append(stock_data)

                    # Mark as processed in Redis so resume skips it
                    if redis_client:
                        try:
                            redis_client.sadd(processed_set, ticker)
                        except Exception:
                            pass

                    success_count += 1
                    ticker_processed = True

                except Exception as e:
                    error_msg = str(e).lower()
                    is_rate_limit = any(phrase in error_msg for phrase in ["rate limit", "quá nhiều", "429", "throttled", "too many requests"]) or ('429' in error_msg)

                    if is_rate_limit:
                        # Try to extract Retry-After from exception.response.headers if present
                        wait_time = None
                        resp = getattr(e, 'response', None)
                        try:
                            if resp is not None and getattr(resp, 'headers', None):
                                ra = resp.headers.get('Retry-After')
                                if ra:
                                    try:
                                        wait_time = int(float(ra))
                                    except Exception:
                                        wait_time = None
                        except Exception:
                            wait_time = None

                        # fallback exponential backoff
                        rate_limit_retry_count += 1
                        if wait_time is None:
                            wait_time = min(RATE_LIMIT_BASE_WAIT * (2 ** (rate_limit_retry_count - 1)), 600)

                        logger.warning(f"⚠️ Rate limit detected for {ticker}. Will wait {wait_time}s and re-queue task.")

                        # Set cooldown in Redis so other workers also pause
                        try:
                            if redis_client:
                                redis_client.set(cooldown_key, '1', nx=True, ex=int(wait_time))
                        except Exception as ex_redis:
                            logger.warning(f"Could not set cooldown key in Redis: {ex_redis}")

                        # Persist buffer so far to DB to avoid data loss
                        if buffer:
                            try:
                                StockData.objects.bulk_create(buffer, ignore_conflicts=True)
                                logger.info(f"Flushed {len(buffer)} records to DB before cooldown.")
                                buffer = []
                            except Exception as ex_db:
                                logger.error(f"Error bulk inserting buffer before cooldown: {ex_db}")

                        # Re-queue the same task to resume after wait_time + small margin
                        try:
                            fetch_daily_data_vnstock_task.apply_async(countdown=int(wait_time) + 5)
                            logger.info("Task requeued to resume after cooldown.")
                        except Exception as ex_apply:
                            logger.error(f"Failed to requeue task: {ex_apply}")

                        # Exit current run to free worker slot
                        return f"Rate limited on {ticker}. Requeued to resume after {wait_time}s"

                    else:
                        general_retry_count += 1
                        if general_retry_count < MAX_GENERAL_RETRIES:
                            logger.warning(f"Lỗi tạm thời cho {ticker}: {str(e)[:200]}... Retry sau {RETRY_DELAY}s.")
                            time.sleep(RETRY_DELAY)
                        else:
                            logger.error(f"Lỗi cố định cho {ticker}: {e}")
                            error_count += 1
                            # mark processed so we won't retry forever
                            if redis_client:
                                try:
                                    redis_client.sadd(processed_set, ticker)
                                except Exception:
                                    pass
                            ticker_processed = True

            # small spacing between tickers to reduce risk of hitting rate limit
            time.sleep(INITIAL_DELAY)

            # flush buffer to DB by chunk
            if len(buffer) >= CHUNK_SIZE:
                try:
                    StockData.objects.bulk_create(buffer, ignore_conflicts=True)
                    logger.info(f"Bulk inserted {len(buffer)} records into DB.")
                    buffer = []
                except Exception as ex_db:
                    logger.error(f"Error bulk inserting buffer: {ex_db}")

            # Cập nhật tiến độ logging
            elapsed = (datetime.now() - start_time).total_seconds()
            processed = i
            avg_time = elapsed / processed if processed > 0 else 0
            remaining = (len(all_tickers) - processed) * avg_time
            eta = datetime.now() + timedelta(seconds=remaining)
            logger.info(f"Tiến độ: {processed}/{len(all_tickers)} | Success: {success_count} | Errors: {error_count} | ETA: {remaining / 60:.1f} phút (~{eta.strftime('%H:%M:%S')})")

        # BƯỚC 3: LƯU DB (flush remaining buffer)
        if buffer:
            try:
                StockData.objects.bulk_create(buffer, ignore_conflicts=True)
                logger.info(f"Final bulk insert: {len(buffer)} records into DB.")
            except Exception as ex_db:
                logger.error(f"Error bulk inserting final buffer: {ex_db}")

        # cleanup Redis processed set and cooldown if you want to reuse same key later
        if redis_client:
            try:
                redis_client.delete(cooldown_key)
                # Optionally keep processed_set for next resume (useful if you run repeatedly)
                # If you want to clear processed set after successful full run, uncomment:
                # redis_client.delete(processed_set)
            except Exception:
                pass

        total_time = (datetime.now() - start_time).total_seconds()
        summary = f"HOÀN TẤT: {success_count} ticker thành công, {error_count} lỗi. Thời gian: {total_time / 60:.1f} phút."
        logger.info(summary)
        return summary

    except Exception as e:
        logger.error(f"Lỗi nghiêm trọng trong task: {e}", exc_info=True)
        return f"Task thất bại: {e}"
