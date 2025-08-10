from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# 1. Mở rộng Model User có sẵn để lưu thêm thông tin người dùng
# ==============================================================================
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    receive_email_alerts = models.BooleanField(default=True)

    def __str__(self):
        return f"Profile của {self.user.username}"

# Tự động tạo Profile khi một User mới được tạo
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


# 2. Model lưu thông tin cơ bản của các mã cổ phiếu
# ==============================================================================
class Stock(models.Model):
    """
    Lưu thông tin định danh của một mã cổ phiếu.
    """
    class ExchangeChoices(models.TextChoices):
        HOSE = 'HOSE', 'Sở Giao dịch Chứng khoán TP.HCM'
        HNX = 'HNX', 'Sở Giao dịch Chứng khoán Hà Nội'
        UPCOM = 'UPCOM', 'Thị trường Giao dịch Cổ phiếu Công ty Đại chúng chưa niêm yết'
        OTHER = 'OTHER', 'Khác'

    ticker = models.CharField(max_length=20, unique=True, primary_key=True, help_text="Mã cổ phiếu (VD: FPT, VCB)")
    company_name = models.CharField(max_length=255, help_text="Tên đầy đủ của công ty")
    exchange = models.CharField(max_length=10, choices=ExchangeChoices.choices, default=ExchangeChoices.HOSE, help_text="Sàn niêm yết")
    industry = models.CharField(max_length=255, null=True, blank=True, help_text="Ngành nghề kinh doanh")

    def __str__(self):
        return self.ticker


# 3. Model lưu dữ liệu giá lịch sử của cổ phiếu
# ==============================================================================
class StockData(models.Model):
    """
    Lưu dữ liệu giá lịch sử (OHLCV) cho mỗi cổ phiếu theo ngày.
    Đây là bảng lớn nhất trong database.
    """
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='data_points')
    date = models.DateField(help_text="Ngày giao dịch")
    # Sử dụng DecimalField cho dữ liệu tài chính để đảm bảo độ chính xác tuyệt đối
    open = models.DecimalField(max_digits=10, decimal_places=2, help_text="Giá mở cửa")
    high = models.DecimalField(max_digits=10, decimal_places=2, help_text="Giá cao nhất")
    low = models.DecimalField(max_digits=10, decimal_places=2, help_text="Giá thấp nhất")
    close = models.DecimalField(max_digits=10, decimal_places=2, help_text="Giá đóng cửa")
    # Volume có thể là số rất lớn, dùng BigIntegerField
    volume = models.BigIntegerField(help_text="Khối lượng giao dịch")

    class Meta:
        # Đảm bảo không có dữ liệu trùng lặp cho cùng một cổ phiếu trong một ngày
        unique_together = ('stock', 'date')
        # Mặc định sắp xếp dữ liệu mới nhất lên đầu khi truy vấn
        ordering = ['-date']

    def __str__(self):
        return f"{self.stock.ticker} - {self.date}"


# 4. Model cho chức năng "Danh sách yêu thích" (Watchlist)
# ==============================================================================
class Watchlist(models.Model):
    """
    Liên kết giữa User và Stock, thể hiện cổ phiếu người dùng đang theo dõi.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watchlist')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='watchers')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Mỗi người dùng chỉ có thể thêm một cổ phiếu vào watchlist một lần
        unique_together = ('user', 'stock')

    def __str__(self):
        return f"{self.user.username} theo dõi {self.stock.ticker}"


# 5. Model cho chức năng "Đặt nhắc lịch/cảnh báo"
# ==============================================================================
class Alert(models.Model):
    """
    Lưu các cảnh báo do người dùng thiết lập.
    Một tác vụ nền (Celery) sẽ quét bảng này để kiểm tra điều kiện và gửi thông báo.
    """
    class ConditionType(models.TextChoices):
        PRICE_ABOVE = 'PRICE_ABOVE', 'Giá vượt lên trên'
        PRICE_BELOW = 'PRICE_BELOW', 'Giá giảm xuống dưới'
        RSI_ABOVE = 'RSI_ABOVE', 'RSI vượt lên trên'
        RSI_BELOW = 'RSI_BELOW', 'RSI giảm xuống dưới'
        MA_CROSS_ABOVE = 'MA_CROSS_ABOVE', 'Đường MA ngắn cắt lên đường MA dài'
        VOLUME_SPIKE = 'VOLUME_SPIKE', 'Khối lượng tăng đột biến'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='alerts')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    condition_type = models.CharField(max_length=20, choices=ConditionType.choices)
    # Giá trị để so sánh (VD: 105.50 cho giá, 70 cho RSI)
    value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True, help_text="Cảnh báo có đang hoạt động không?")
    triggered_at = models.DateTimeField(null=True, blank=True, help_text="Lần cuối cảnh báo được kích hoạt")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cảnh báo cho {self.user.username} về {self.stock.ticker} khi {self.get_condition_type_display()}"


# 6. Model lưu kết quả phân tích, xếp hạng cổ phiếu tiềm năng
# ==============================================================================
class PotentialStock(models.Model):
    """
    Lưu kết quả phân tích hàng ngày.
    Thay vì tính toán lại mỗi khi người dùng yêu cầu, một tác vụ nền sẽ chạy,
    phân tích và lưu các cổ phiếu tiềm năng vào bảng này để truy xuất tức thì.
    """
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    analysis_date = models.DateField(auto_now_add=True)
    rank = models.PositiveIntegerField(help_text="Thứ hạng tiềm năng")
    score = models.FloatField(help_text="Điểm số kỹ thuật tổng hợp")
    reason = models.TextField(help_text="Lý do/Tín hiệu được đề xuất (VD: MA20 cắt lên MA50, RSI < 30)")

    class Meta:
        unique_together = ('stock', 'analysis_date')
        ordering = ['rank', 'analysis_date']

    def __str__(self):
        return f"Hạng {self.rank}: {self.stock.ticker} ngày {self.analysis_date}"