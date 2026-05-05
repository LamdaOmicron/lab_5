from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class CustomPageNumberPagination(PageNumberPagination):
    page_size = 10                     # значение по умолчанию
    page_size_query_param = 'limit'    # параметр для указания размера страницы
    max_page_size = 100                # максимальный лимит

    def get_paginated_response(self, data):
        return Response({
            'data': data,
            'meta': {
                'total': self.page.paginator.count,
                'page': self.page.number,
                'limit': self.get_page_size(self.request),
                'totalPages': self.page.paginator.num_pages,
            }
        })