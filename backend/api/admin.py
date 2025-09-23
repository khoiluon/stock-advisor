from django.contrib import admin
from .models import Profile, Stock, StockData, Watchlist, Alert, PotentialStock, NewsSource, Article

# 1. Profile Admin
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'receive_email_alerts')  # Các cột hiển thị trong list view
    search_fields = ('user__username', 'user__email')  # Tìm kiếm theo username/email

# 2. Stock Admin
@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('ticker', 'company_name', 'exchange', 'industry')
    search_fields = ('ticker', 'company_name')  # Tìm kiếm theo ticker hoặc tên công ty
    list_filter = ('exchange',)  # Lọc theo sàn giao dịch

# 3. StockData Admin
@admin.register(StockData)
class StockDataAdmin(admin.ModelAdmin):
    list_display = ('stock', 'date', 'open', 'close', 'volume')
    search_fields = ('stock__ticker',)  # Tìm kiếm theo ticker cổ phiếu
    list_filter = ('date',)  # Lọc theo ngày
    # Để tránh load chậm với dữ liệu lớn, có thể thêm raw_id_fields = ('stock',)

# 4. Watchlist Admin
@admin.register(Watchlist)
class WatchlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'stock', 'added_at')
    search_fields = ('user__username', 'stock__ticker')
    list_filter = ('added_at',)

# 5. Alert Admin
@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('user', 'stock', 'condition_type', 'value', 'is_active', 'created_at')
    search_fields = ('user__username', 'stock__ticker', 'condition_type')
    list_filter = ('is_active', 'condition_type', 'created_at')  # Lọc theo trạng thái, loại, thời gian

# 6. PotentialStock Admin
@admin.register(PotentialStock)
class PotentialStockAdmin(admin.ModelAdmin):
    list_display = ('stock', 'analysis_date', 'timeframe', 'confidence', 'score', 'current_price')
    search_fields = ('stock__ticker',)
    list_filter = ('analysis_date', 'timeframe')
    ordering = ('-confidence', '-score')

# 7. NewsSource Admin
@admin.register(NewsSource)
class NewsSourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'base_url')
    search_fields = ('name',)

# 8. Article Admin
@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'source', 'published_at', 'crawled_at')
    search_fields = ('title', 'description', 'content_markdown')  # Tìm kiếm theo tiêu đề/nội dung
    list_filter = ('source', 'published_at')  # Lọc theo nguồn và ngày xuất bản
    readonly_fields = ('crawled_at',)  # Không cho chỉnh sửa thời gian crawl
    # Để hiển thị related_stocks, có thể dùng filter_horizontal = ('related_stocks',) nếu cần chỉnh ManyToMany