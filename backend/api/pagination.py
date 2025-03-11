from rest_framework.pagination import PageNumberPagination

PAGE_PAGINATION_SIZE = 6


class PagePagination(PageNumberPagination):
    page_size_query_param = 'limit'
    page_size = PAGE_PAGINATION_SIZE
