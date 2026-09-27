from drf_spectacular.utils import OpenApiExample
from geo_search_api.api.likes.swagger_examples import paginated_likes_sum_up_example


comment_example = OpenApiExample(
    "Comment|Reply",
    value={
        "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "owner": "string",
        "content": "string",
        "created_at": "2023-02-17T16:27:58.166Z",
        "updated_at": "2023-02-17T16:27:58.166Z",
        "note_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "parent_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "replies": [],
        "likes": paginated_likes_sum_up_example.value,
    },
)

paginated_comments_example = OpenApiExample(
    "Comments",
    value={
        "next": False,
        "previous": False,
        "count": 1,
        "total_pages": 1,
        "results": [comment_example.value],
    },
)
