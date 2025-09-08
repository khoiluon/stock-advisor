from rest_framework.pagination import PageNumberPagination

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10  # Số lượng bài viết trên mỗi trang
    page_size_query_param = 'page_size' # Cho phép client tự định nghĩa page_size, ví dụ: /api/news/?page_size=20
    max_page_size = 100 # Giới hạn page_size tối đa