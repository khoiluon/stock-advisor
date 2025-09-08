# backend/debug_firecrawl.py

from firecrawl import FirecrawlApp

print("--- Bắt đầu thăm dò thư viện Firecrawl ---")

try:
    # Khởi tạo app như bình thường
    app = FirecrawlApp(api_key='fc-b2526744ad5845258c5c15c90bfa8fe6')

    # 1. In ra tất cả các phương thức có sẵn của đối tượng 'app'
    print("\n[INFO] Các phương thức có sẵn trong đối tượng FirecrawlApp:")
    # Lọc ra các phương thức không bắt đầu bằng dấu gạch dưới
    methods = [method for method in dir(app) if not method.startswith('_')]
    print(methods)

    # 2. In ra tài liệu hướng dẫn (docstring) của phương thức 'scrape'
    # Đây là bước quan trọng nhất, nó sẽ cho chúng ta biết các tham số chính xác
    if 'scrape' in methods:
        print("\n[INFO] Hướng dẫn sử dụng của phương thức 'scrape':")
        help(app.scrape)
    else:
        print("\n[ERROR] Không tìm thấy phương thức 'scrape'. Có thể nó có tên khác?")

except Exception as e:
    print(f"\n[ERROR] Đã xảy ra lỗi khi khởi tạo hoặc thăm dò: {e}")

print("\n--- Kết thúc thăm dò ---")