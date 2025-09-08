from django.contrib.auth.models import User
from rest_framework import serializers, validators
from .models import Stock, Watchlist, StockData, Alert, PotentialStock, Article

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'password', 'email', 'first_name', 'last_name')
        extra_kwargs = {
            "password": {"write_only": True}, # Mật khẩu chỉ dùng để ghi, không trả về
            "email": {
                "required": True,
                "allow_blank": False,
                "validators": [
                    validators.UniqueValidator(
                        User.objects.all(), "Một người dùng với email này đã tồn tại."
                    )
                ]
            }
        }

    def create(self, validated_data):
        # Dùng create_user để hash mật khẩu một cách an toàn
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        return user


class StockSerializer(serializers.ModelSerializer):
    """
    Serializer đơn giản để hiển thị thông tin cơ bản của một mã cổ phiếu.
    """
    class Meta:
        model = Stock
        fields = ('ticker', 'company_name', 'exchange', 'industry')

class WatchlistSerializer(serializers.ModelSerializer):
    stock = StockSerializer(read_only=True)
    stock_id = serializers.PrimaryKeyRelatedField(queryset=Stock.objects.all(), source='stock', write_only=True)

    class Meta:
        model = Watchlist
        fields = ['id', 'stock', 'stock_id', 'added_at']


class ArticleSerializer(serializers.ModelSerializer):
    """
    Serializer để hiển thị thông tin bài viết tin tức.
    """
    # Dùng StringRelatedField để hiển thị tên của nguồn tin (VD: "CafeF")
    source = serializers.StringRelatedField()

    # Dùng SlugRelatedField để hiển thị một danh sách các mã ticker (VD: ["FPT", "VCB"])
    # thay vì một danh sách các ID số khó hiểu.
    related_stocks = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field='ticker'
    )

    class Meta:
        model = Article
        fields = [
            'id',
            'title',
            'description',
            'url',
            'thumbnail_url',
            'published_at',
            'source',
            'related_stocks'
        ]


class PotentialStockSerializer(serializers.ModelSerializer):
    """
    Serializer để hiển thị danh sách các cổ phiếu tiềm năng.
    Chuyển đổi dữ liệu từ model để phù hợp với giao diện.
    """
    # Lồng StockSerializer để hiển thị thông tin chi tiết của cổ phiếu
    stock = StockSerializer(read_only=True)

    # Dùng SerializerMethodField để xử lý logic chuyển đổi cho key_reasons
    key_reasons = serializers.SerializerMethodField()

    class Meta:
        model = PotentialStock
        # Liệt kê tất cả các trường đã hoàn thiện trong model
        fields = (
            'stock',
            'analysis_date',
            'current_price',
            'target_price',
            'timeframe',
            'confidence',
            'score',
            'key_reasons',  # Trường đã được xử lý
            'reason'
        )

    def get_key_reasons(self, obj):
        """
        Hàm này sẽ được tự động gọi cho trường 'key_reasons'.
        Nó nhận vào đối tượng PotentialStock (obj) và thực hiện chuyển đổi.
        Input: "MA Crossover Bullish,Volume Surge,Positive MACD"
        Output: ["MA Crossover Bullish", "Volume Surge", "Positive MACD"]
        """
        if obj.key_reasons:
            # Tách chuỗi bằng dấu phẩy và loại bỏ các khoảng trắng thừa
            return [reason.strip() for reason in obj.key_reasons.split(',')]
        return []  # Trả về mảng rỗng nếu không có reason