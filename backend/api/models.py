from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# ==============================================================================
# 1. Mở rộng User Profile
# ==============================================================================

class Profile(models.Model):
    """
    Mở rộng model User mặc định để lưu thêm thông tin.
    Ví dụ: người dùng có chọn nhận email thông báo hay không.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    receive_email_alerts = models.BooleanField(
        default=True,
        help_text="Người dùng có nhận email cảnh báo không"
    )

    def __str__(self):
        return f"Profile của {self.user.username}"


# Tự động tạo Profile khi một User mới được tạo
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


# Tự động lưu Profile mỗi khi User được lưu
@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


# ==============================================================================
# 2. Model lưu thông tin cơ bản về cổ phiếu
# ==============================================================================
class Stock(models.Model):
    class ExchangeChoices(models.TextChoices):
        HOSE = 'HOSE', 'Sở Giao dịch Chứng khoán TP.HCM'
        HNX = 'HNX', 'Sở Giao dịch Chứng khoán Hà Nội'
        UPCOM = 'UPCOM', 'Thị trường UPCOM'
        OTHER = 'OTHER', 'Khác'

    ticker = models.CharField(max_length=20, unique=True, primary_key=True)
    company_name = models.CharField(max_length=255)
    exchange = models.CharField(
        max_length=10,
        choices=ExchangeChoices.choices,
        default=ExchangeChoices.HOSE
    )
    industry = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.ticker


# ==============================================================================
# 3. Model lưu dữ liệu giá lịch sử (OHLCV)
# ==============================================================================

class StockData(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='data_points')
    date = models.DateField()
    open = models.DecimalField(max_digits=10, decimal_places=2)
    high = models.DecimalField(max_digits=10, decimal_places=2)
    low = models.DecimalField(max_digits=10, decimal_places=2)
    close = models.DecimalField(max_digits=10, decimal_places=2)
    volume = models.BigIntegerField()

    class Meta:
        unique_together = ('stock', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.stock.ticker} - {self.date}"


# ==============================================================================
# 4. Watchlist - danh sách cổ phiếu yêu thích
# ==============================================================================

class Watchlist(models.Model):
    """
    Liên kết giữa User và Stock: cổ phiếu mà người dùng theo dõi.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watchlist')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='watchers')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'stock')
        verbose_name = "Danh sách theo dõi"
        verbose_name_plural = "Danh sách theo dõi"

    def __str__(self):
        return f"{self.user.username} theo dõi {self.stock.ticker}"


# ==============================================================================
# 5. Alert - Cảnh báo/nhắc lịch
# ==============================================================================

class Alert(models.Model):
    """
    Lưu thông tin cảnh báo do người dùng đặt.
    Hệ thống nền (Celery/CRON job) sẽ quét bảng này để gửi thông báo khi điều kiện thoả mãn.
    """
    class ConditionType(models.TextChoices):
        PRICE_ABOVE = 'PRICE_ABOVE', 'Giá vượt lên trên'
        PRICE_BELOW = 'PRICE_BELOW', 'Giá giảm xuống dưới'
        RSI_ABOVE = 'RSI_ABOVE', 'RSI vượt lên trên'
        RSI_BELOW = 'RSI_BELOW', 'RSI giảm xuống dưới'
        MA_CROSS_ABOVE = 'MA_CROSS_ABOVE', 'MA ngắn cắt lên MA dài'
        VOLUME_SPIKE = 'VOLUME_SPIKE', 'Khối lượng tăng đột biến'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='alerts')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='alerts')
    condition_type = models.CharField(
        max_length=20,
        choices=ConditionType.choices,
        help_text="Điều kiện cảnh báo"
    )
    value = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
        help_text="Ngưỡng so sánh (VD: 100.5 cho giá, 70 cho RSI)"
    )
    is_active = models.BooleanField(default=True, help_text="Cảnh báo có đang hoạt động không?")
    triggered_at = models.DateTimeField(null=True, blank=True, help_text="Lần cuối được kích hoạt")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Thời gian tạo cảnh báo")

    class Meta:
        verbose_name = "Cảnh báo"
        verbose_name_plural = "Cảnh báo"

    def __str__(self):
        return f"Cảnh báo {self.user.username} - {self.stock.ticker} ({self.get_condition_type_display()})"


# ==============================================================================
# 6. PotentialStock - Cổ phiếu tiềm năng
# ==============================================================================

class PotentialStock(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    analysis_date = models.DateField()

    # --- CÁC TRƯỜNG MỚI, ĐÃ ĐƯỢC HOÀN THIỆN ---

    # Dùng `default=0` để đảm bảo không có lỗi khi migrate hoặc tạo đối tượng
    current_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Giá tại ngày phân tích")
    target_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Giá mục tiêu dự kiến")

    # Dùng `default=''` và `blank=True` để linh hoạt
    timeframe = models.CharField(max_length=50, default='', blank=True,
                                 help_text="Khung thời gian gợi ý (Ngắn hạn, Trung hạn)")
    confidence = models.PositiveIntegerField(default=0, help_text="Độ tự tin của gợi ý (0-100%)")
    score = models.FloatField(default=0.0, help_text="Điểm số trên thang 10")

    # Thay thế JSONField bằng TextField để tương thích rộng hơn và dễ dùng hơn.
    # Chúng ta sẽ lưu danh sách các tag dưới dạng một chuỗi, ngăn cách bởi dấu phẩy.
    # Ví dụ: "MA crossover bullish,Volume surge,Positive MACD"
    key_reasons = models.TextField(default='', blank=True,
                                   help_text="Danh sách các lý do chính, cách nhau bởi dấu phẩy")

    # Trường này vẫn hữu ích để mô tả chiến lược tổng thể
    reason = models.TextField(default='', blank=True, help_text="Mô tả chi tiết chiến lược")

    class Meta:
        unique_together = ('stock', 'analysis_date')
        ordering = ['-confidence', '-score']  # Sắp xếp theo độ tự tin và điểm số

    def __str__(self):
        return f"{self.stock.ticker} ({self.timeframe}) - {self.analysis_date}"

# ==============================================================================
# 7. Tin tức - Nguồn và Bài viết
# ==============================================================================

class NewsSource(models.Model):
    """
    Nguồn tin tức (VD: VnExpress, CafeF).
    Giúp quản lý và mở rộng khi thêm nguồn mới.
    """
    name = models.CharField(max_length=100, unique=True, help_text="Tên nguồn tin (VD: VnExpress, CafeF)")
    base_url = models.URLField(max_length=255, help_text="URL trang chủ nguồn tin")
    crawl_selector = models.CharField(
        max_length=255,
        null=True, blank=True,
        help_text="CSS selector để extract bài viết (nếu dùng Firecrawl với selectors)"
    )

    class Meta:
        verbose_name = "Nguồn tin tức"
        verbose_name_plural = "Nguồn tin tức"

    def __str__(self):
        return self.name


class Article(models.Model):
    """
    Lưu bài viết tin tức đã crawl từ các nguồn.
    Mỗi bài có thể liên quan đến nhiều cổ phiếu.
    """
    source = models.ForeignKey(
        NewsSource,
        on_delete=models.CASCADE,
        related_name='articles',
        help_text="Nguồn của bài viết"
    )
    title = models.CharField(max_length=255, help_text="Tiêu đề bài viết")
    description = models.TextField(null=True, blank=True, help_text="Mô tả ngắn/sapo")
    content_markdown = models.TextField(help_text="Nội dung bài viết dạng Markdown (từ Firecrawl)")
    url = models.URLField(max_length=500, unique=True, help_text="URL gốc, dùng để tránh trùng lặp")
    published_at = models.DateTimeField(help_text="Ngày xuất bản")
    crawled_at = models.DateTimeField(auto_now_add=True, help_text="Ngày hệ thống crawl bài viết")
    author = models.CharField(max_length=255, null=True, blank=True, help_text="Tác giả bài viết")
    thumbnail_url = models.URLField(max_length=500, null=True, blank=True, help_text="URL ảnh thumbnail")
    is_processed = models.BooleanField(default=False, help_text="Bài viết đã được phân tích related_stocks chưa?")

    # Liên kết nhiều-nhiều: một bài viết có thể nhắc nhiều cổ phiếu
    related_stocks = models.ManyToManyField(
        Stock,
        related_name='articles',
        blank=True,
        help_text="Các mã cổ phiếu được đề cập"
    )

    class Meta:
        ordering = ['-published_at']
        verbose_name = "Bài viết"
        verbose_name_plural = "Bài viết"

    def __str__(self):
        return self.title
