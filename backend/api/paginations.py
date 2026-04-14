from rest_framework import pagination

from core.constants import PAGE_SIZE


class LimitPagination(pagination.PageNumberPagination):
    """Класс пагинации с возможностью задать лимит."""

    page_size_query_param = 'limit'
    page_size = PAGE_SIZE
