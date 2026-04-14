from rest_framework.pagination import PageNumberPagination

from core.constants import PAGE_SIZE


class LimitPagination(PageNumberPagination):
    """Класс пагинации с возможностью задать лимит."""

    page_size_query_param = 'limit'
    page_size = PAGE_SIZE
