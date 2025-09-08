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

from .models import Article, NewsSource, Stock, StockData
import requests
from decouple import config

load_dotenv()

logger = logging.getLogger(__name__)

# ==================== CONFIGURATION ====================
API_KEY = os.getenv('FIRE_CRAWL_API_KEY')
BASE_URL = 'https://cafef.vn/thi-truong-chung-khoan.chn'
DOMAIN = 'https://cafef.vn'

# Rate limiting configuration
MAX_ARTICLES_PER_RUN = 15
BASE_DELAY_SECONDS = 4
MAX_DELAY_SECONDS = 8

# Stock tagging configuration
AMBIGUOUS_TICKERS = {'CEO', 'GAS', 'TIN', 'HAG', 'GIL', 'PET', 'FIT', 'VIX', 'BCG', 'PNG'}
FINANCIAL_KEYWORDS = {
    'CỔ PHIẾU', 'MÃ CK', 'MÃ CHỨNG KHOÁN', 'THỊ TRƯỜNG', 'GIAO DỊCH',
    'VN-INDEX', 'HNX-INDEX', 'SÀN HOSE', 'SÀN HNX', 'UPCOM',
    'TĂNG', 'GIẢM', 'KHỐI LƯỢNG', 'THANH KHOẢN', 'CÔNG TY CỔ PHẦN', 'CTCP'
}


# ==================== HELPER FUNCTIONS ====================

def get_scrape_options():
    """Return standardized scraping options."""
    return {
        'headers': {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'},
        'timeout': 30000,
        'block_ads': True,
        'formats': ['html']
    }


def normalize_url(domain, url):
    """Normalize URL and handle edge cases."""
    if not url:
        return ""

    full_url = urljoin(domain, url)

    # Log warning for potentially truncated URLs
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
            # Check context for ambiguous tickers
            for match in re.finditer(ticker_pattern, search_text):
                context_start = max(0, match.start() - 50)
                context_end = match.end() + 50
                context = search_text[context_start:context_end]

                if any(keyword in context for keyword in FINANCIAL_KEYWORDS):
                    found_tickers.add(ticker)
                    break
        else:
            # Direct match for unambiguous tickers
            if re.search(ticker_pattern, search_text):
                found_tickers.add(ticker)

    return found_tickers


def parse_articles_from_section(soup, domain, session_urls, existing_urls,
                                item_selector, title_selector, desc_selector, img_selector):
    """Extract articles from a specific page section."""
    articles = []

    for item in soup.select(item_selector):
        # Extract title and URL
        title_element = item.select_one(title_selector)
        if not title_element or not title_element.get("href"):
            continue

        url = normalize_url(domain, title_element["href"])
        if not url or is_duplicate_url(url, session_urls, existing_urls):
            continue

        # Mark URL as processed
        session_urls.add(url)

        # Extract article data
        title = title_element.get_text(strip=True)

        description_element = item.select_one(desc_selector)
        description = description_element.get_text(strip=True) if description_element else ''

        image_element = item.select_one(img_selector)
        thumbnail_url = ''
        if image_element and image_element.get("src"):
            thumbnail_url = normalize_url(domain, image_element["src"])

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
    """Save article to database and tag with related stocks."""
    try:
        # Create article
        article = Article.objects.create(
            source=source,
            title=article_data['title'],
            description=article_data['description'],
            content_markdown=article_data['content'],
            url=article_data['url'],
            thumbnail_url=article_data['thumbnail_url'],
            published_at=article_data['published_at']
        )

        # Tag with stocks
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
        if '1062' in str(e) and 'Duplicate entry' in str(e):
            logger.info(f"    -> URL already exists: {article_data['url']}")
        else:
            logger.error(f"    -> Database integrity error: {e}")
        return False

    except Exception as e:
        logger.error(f"    -> Error saving article: {e}", exc_info=True)
        return False


# ==================== MAIN TASK ====================

@shared_task
def crawl_news_task():
    """Main task to crawl and process news articles."""
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
        # Scrape main page
        logger.info(f"Scraping main page: {BASE_URL}")
        main_page_data = app.scrape(url=BASE_URL, **get_scrape_options())

        if not hasattr(main_page_data, 'html') or not main_page_data.html:
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

        # Limit articles to prevent rate limiting
        logger.info(f"Found {len(articles_to_process)} new articles to process")

        # Process each article
        successful_saves = 0

        for index, article_info in enumerate(articles_to_process, 1):
            logger.info(f"Processing article {index}/{len(articles_to_process)}: {article_info['title']}")

            try:
                # Scrape article detail
                detail_data = app.scrape(url=article_info['url'], **get_scrape_options())

                if not hasattr(detail_data, 'markdown') or not detail_data.markdown:
                    logger.warning(f"    -> No content available for: {article_info['url']}")
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

            # Simple delay to avoid rate limiting (skip for last article)
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


@shared_task
def fetch_daily_data_task():
    """
    Celery task to fetch the latest end-of-day data for ALL stocks
    in a single API call using the Bulk EOD endpoint.
    """
    logger.info("=" * 60)
    logger.info("STARTING DAILY STOCK DATA FETCH TASK (BULK MODE)")
    API_KEY = config('EODHD_API_KEY', default=None)
    if not API_KEY:
        logger.error("EODHD_API_KEY not found.")
        return "Task failed: API Key not found."

    # --- BƯỚC 1: GỌI API BULK (1 REQUEST) ---
    bulk_url = f"https://eodhistoricaldata.com/api/eod-bulk-last-day/VSE?api_token={API_KEY}&fmt=json"

    try:
        logger.info("Fetching bulk data...")
        response = requests.get(bulk_url)
        response.raise_for_status()
        bulk_data = response.json()
        logger.info(f"Successfully fetched bulk data for {len(bulk_data)} tickers.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch bulk EOD data: {e}")
        return f"Task failed: {e}"

    # --- BƯỚC 2: XỬ LÝ VÀ LƯU DỮ LIỆU ---
    all_stocks_map = {stock.ticker: stock for stock in Stock.objects.all()}
    newly_created_count = 0
    updated_count = 0

    for record in bulk_data:
        # API trả về 'code' đã được chuẩn hóa (VD: "VIC")
        ticker = record.get('code')

        stock_instance = all_stocks_map.get(ticker)
        if not stock_instance:
            continue

        record_date = datetime.strptime(record['date'], '%Y-%m-%d').date()

        obj, created = StockData.objects.update_or_create(
            stock=stock_instance,
            date=record_date,
            defaults={
                'open': record['open'], 'high': record['high'],
                'low': record['low'], 'close': record['close'],
                'volume': record['volume']
            }
        )

        if created:
            newly_created_count += 1
        else:
            updated_count += 1

    summary = f"COMPLETED: Processed data. Created {newly_created_count} new records, updated {updated_count} existing records."
    logger.info(summary)
    return summary