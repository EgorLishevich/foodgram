from rest_framework.pagination import PageNumberPagination

from foodgram.consts import DEFAULT_PAGE_SIZE


class PagePagination(PageNumberPagination):
    page_size_query_param = 'limit'
    page_size = DEFAULT_PAGE_SIZE
