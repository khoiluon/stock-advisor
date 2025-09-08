# backend/crawl_cafef.py
import re
from datetime import datetime
from urllib.parse import urljoin
from django.core.management.base import BaseCommand
from firecrawl import FirecrawlApp
from bs4 import BeautifulSoup
from api.models import Article, NewsSource, Stock
from django.utils import timezone

class Command(BaseCommand):
    help = 'Crawls news articles from CafeF Business section.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Bắt đầu quá trình crawl tin tức từ CafeF..."))

        API_KEY = 'fc-b2526744ad5845258c5c15c90bfa8fe6'
        BASE_URL = 'https://cafef.vn/thi-truong-chung-khoan.chn'
        DOMAIN = 'https://cafef.vn'
        app = FirecrawlApp(api_key=API_KEY)

        source, _ = NewsSource.objects.get_or_create(
            name='CafeF',
            defaults={'base_url': DOMAIN}
        )
        all_tickers = list(Stock.objects.values_list('ticker', flat=True))
        processed_urls = set()

        try:
            self.stdout.write(f"--- Đang crawl trang chính: {BASE_URL} ---")
            scrape_options = {
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
                },
                'timeout': 20000,
                'block_ads': True
            }
            main_page = app.scrape(url=BASE_URL, formats=['html'], **scrape_options)

            html_content = getattr(main_page, 'html', None) if main_page else None
            if not html_content:
                self.stdout.write(self.style.ERROR("Không lấy được HTML từ trang chính. Dừng lại."))
                return

            soup = BeautifulSoup(html_content, 'html.parser')

            articles_to_process = []
            articles_to_process.extend(self._parse_featured_articles(soup, DOMAIN, processed_urls))
            articles_to_process.extend(self._parse_main_list_articles(soup, DOMAIN, processed_urls))

            self.stdout.write(self.style.SUCCESS(f"\nTổng hợp: Tìm thấy {len(articles_to_process)} bài viết mới."))

            new_articles_total = 0
            for article_info in articles_to_process:
                if self._process_article_detail(app, source, all_tickers, article_info, scrape_options):
                    new_articles_total += 1

            self.stdout.write(self.style.SUCCESS(f"\nHOÀN TẤT! Đã crawl và lưu {new_articles_total} bài viết mới."))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Lỗi nghiêm trọng trong quá trình crawl: {e}"))

    def _parse_featured_articles(self, soup, domain, processed_urls):
        featured_articles = []
        for item in soup.select('div.tlitem'):
            a = item.select_one('h3 a')
            if not a or not a.get("href"):
                continue

            url = self._normalize_url(domain, a["href"])
            if url in processed_urls:
                continue

            title = a.get_text(strip=True)

            # Lấy description nếu có
            description_tag = item.select_one('p.sapo') or item.select_one('p')
            description = description_tag.get_text(strip=True) if description_tag else ''

            # Lấy thumbnail nếu có
            img_tag = item.select_one('img')
            thumbnail_url = self._normalize_url(domain, img_tag["src"]) if img_tag and img_tag.get("src") else ''

            featured_articles.append({
                'title': title,
                'url': url,
                'description': description,
                'thumbnail_url': thumbnail_url
            })
            processed_urls.add(url)

        return featured_articles

    def _parse_main_list_articles(self, soup, domain, processed_urls):
        main_articles = []
        for item in soup.select('ul.list_news li'):
            a = item.select_one('h3 a')
            if not a or not a.get("href"):
                continue

            url = self._normalize_url(domain, a["href"])
            if url in processed_urls:
                continue

            title = a.get_text(strip=True)

            # Lấy description nếu có
            description_tag = item.select_one('p')
            description = description_tag.get_text(strip=True) if description_tag else ''

            # Lấy thumbnail nếu có
            img_tag = item.select_one('img')
            thumbnail_url = self._normalize_url(domain, img_tag["src"]) if img_tag and img_tag.get("src") else ''

            main_articles.append({
                'title': title,
                'url': url,
                'description': description,
                'thumbnail_url': thumbnail_url
            })
            processed_urls.add(url)

        return main_articles

    def _normalize_url(self, domain, url):
        return urljoin(domain, url)

    def _process_article_detail(self, app, source, all_tickers, article_info, options):
        try:
            self.stdout.write(f"  -> Đang xử lý chi tiết: {article_info['title']}")
            detail_data = app.scrape(url=article_info['url'], **options)

            # Kiểm tra xem có nội dung markdown không
            if not hasattr(detail_data, 'markdown') or not detail_data.markdown:
                self.stdout.write(self.style.WARNING("    -> Không lấy được nội dung markdown."))
                return False

            # Lấy metadata một cách an toàn
            metadata = detail_data.metadata if hasattr(detail_data, 'metadata') else None

            # Giá trị mặc định: thời điểm hiện tại (timezone aware)
            published_date = timezone.now()

            if metadata and hasattr(metadata, 'publishedTime') and metadata.publishedTime:
                published_date_str = metadata.publishedTime
                try:
                    # Parse ISO format
                    published_date = datetime.fromisoformat(published_date_str.replace('Z', '+00:00'))

                    # Nếu datetime là naive thì ép thành aware
                    if timezone.is_naive(published_date):
                        published_date = timezone.make_aware(published_date)

                except ValueError:
                    self.stdout.write(self.style.WARNING(
                        f"    -> Không thể phân tích định dạng ngày: {published_date_str}. Sử dụng ngày hiện tại."
                    ))

            new_article = Article.objects.create(
                source=source,
                title=article_info['title'],
                description=article_info['description'],
                content_markdown=detail_data.markdown,
                url=article_info['url'],
                thumbnail_url=article_info['thumbnail_url'],
                published_at=published_date
            )

            self._tag_stocks_in_article(new_article, all_tickers)
            return True

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"    -> Lỗi khi xử lý chi tiết bài viết: {e}"))
            return False

    def _tag_stocks_in_article(self, article: Article, all_tickers: list):
        """
        Quét nội dung bài viết để tìm và gắn thẻ các mã cổ phiếu một cách thông minh hơn.
        """
        # --- DANH SÁCH CÁC TICKER NGẮN, DỄ GÂY NHẦM LẪN ---
        # Bạn có thể bổ sung thêm vào danh sách này
        AMBIGUOUS_TICKERS = {'CEO', 'GAS', 'TIN', 'HAG', 'GIL', 'PET', 'FIT', 'VIX', 'BCG', 'PNG'}

        # --- DANH SÁCH CÁC TỪ KHÓA TÀI CHÍNH ĐỂ XÁC NHẬN NGỮ CẢNH ---
        FINANCIAL_KEYWORDS = {
            'CỔ PHIẾU', 'MÃ CK', 'MÃ CHỨNG KHOÁN', 'THỊ TRƯỜNG', 'GIAO DỊCH',
            'VN-INDEX', 'HNX-INDEX', 'SÀN HOSE', 'SÀN HNX', 'UPCOM',
            'GIÁ TRẦN', 'GIÁ SÀN', 'TĂNG', 'GIẢM', 'KHỐI LƯỢNG', 'THANH KHOẢN',
            'CÔNG TY CỔ PHẦN', 'CTCP'
        }

        def remove_markdown_links(text):
            """Hàm phụ để loại bỏ các URL khỏi markdown, chỉ giữ lại text."""
            return re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\1', text)

        # 1. Tiền xử lý: Lấy nội dung gốc và dọn dẹp
        title = article.title
        content = remove_markdown_links(article.content_markdown)

        # Tạo một phiên bản viết hoa để quét không phân biệt chữ hoa/thường
        content_to_scan_upper = (title + ' ' + content).upper()

        found_tickers = set()

        for ticker in all_tickers:
            # 2. Phân loại và áp dụng logic phù hợp
            if ticker in AMBIGUOUS_TICKERS:
                # --- Logic xử lý nghiêm ngặt cho các Ticker mơ hồ ---
                # Tìm tất cả các vị trí xuất hiện của ticker
                for match in re.finditer(r'\b' + re.escape(ticker) + r'\b', content_to_scan_upper):
                    # Lấy một đoạn văn bản xung quanh vị trí tìm thấy (ngữ cảnh)
                    start, end = match.start(), match.end()
                    # Lấy 50 ký tự trước và 50 ký tự sau
                    context_window = content_to_scan_upper[max(0, start - 50):end + 50]

                    # Kiểm tra xem có từ khóa tài chính nào trong ngữ cảnh không
                    if any(keyword in context_window for keyword in FINANCIAL_KEYWORDS):
                        found_tickers.add(ticker)
                        break  # Đã xác nhận, không cần kiểm tra các vị trí khác của cùng ticker này
            else:
                # --- Logic xử lý thông thường cho các Ticker không mơ hồ ---
                if re.search(r'\b' + re.escape(ticker) + r'\b', content_to_scan_upper):
                    found_tickers.add(ticker)

        # 3. Gắn thẻ vào bài viết
        if found_tickers:
            self.stdout.write(f"    -> Tìm thấy các mã: {', '.join(found_tickers)}")
            stocks_to_add = Stock.objects.filter(ticker__in=found_tickers)
            article.related_stocks.add(*stocks_to_add)