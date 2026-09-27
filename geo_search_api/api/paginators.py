from rest_framework import pagination as drf_pagination
from rest_framework import response as drf_response


class BasePageNumberPagination(drf_pagination.PageNumberPagination):
    """
    Base page number paginator
    """

    page_size = 20
    page_size_query_param = "page_size"

    def get_response_data(self, data):
        """
        Get data for response

        Overwrite this method if you need to change to structure of the response.
        """
        return {
            "next": bool(self.get_next_link()),
            "previous": bool(self.get_previous_link()),
            "count": self.page.paginator.count,
            "total_pages": self.page.paginator.num_pages,
            "results": data,
        }

    def get_paginated_response(self, data):
        return drf_response.Response(self.get_response_data(data))
