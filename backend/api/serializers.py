from django.contrib.auth.models import User
from rest_framework import serializers, validators
from .models import Stock, Watchlist

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