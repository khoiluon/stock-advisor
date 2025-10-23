# ssi_integration/ssi_config.py

from django.conf import settings

class SSIConfig:
    """
    Lớp này tạo ra một đối tượng config tương thích với thư viện ssi-fc-data,
    lấy thông tin từ file settings.py của Django.
    """
    def __init__(self):
        self.auth_type = 'Bearer'
        self.consumerID = settings.SSI_FCDATA_CONSUMER_ID
        self.consumerSecret = settings.SSI_FCDATA_CONSUMER_SECRET
        self.url = settings.SSI_FCDATA_URL
        self.stream_url = settings.SSI_FCDATA_STREAM_URL

def get_ssi_config():
    """Hàm helper để lấy đối tượng config."""
    return SSIConfig()