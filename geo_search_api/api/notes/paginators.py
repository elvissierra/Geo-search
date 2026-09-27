from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class NotesPageNumberPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"

    def get_paginated_response(self, data):
        return Response(
            {
                "next": bool(self.get_next_link()),
                "previous": bool(self.get_previous_link()),
                "count": self.page.paginator.count,
                "total_pages": self.page.paginator.num_pages,
                "results": data,
            }
        )


class CommentsPageNumberPagination(NotesPageNumberPagination):
    pass


class LikesPageNumberPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"

    def get_paginated_response(self, data):
        return Response(
            {
                "next": bool(self.get_next_link()),
                "previous": bool(self.get_previous_link()),
                "count": self.page.paginator.count,
                "total_pages": self.page.paginator.num_pages,
                "is_current_user_liked": data["is_current_user_liked"],
                "results": data["results"],
            }
        )
