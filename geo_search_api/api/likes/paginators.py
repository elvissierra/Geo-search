from geo_search_api.api.paginators import BasePageNumberPagination


class LikesPagination(BasePageNumberPagination):
    def get_response_data(self, data):
        _data = super().get_response_data(data)
        _data.update(
            {"is_current_user_liked": data["is_current_user_liked"], "results": data["results"]}
        )
        return _data
