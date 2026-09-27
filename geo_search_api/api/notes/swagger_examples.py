from drf_spectacular.utils import OpenApiExample
from geo_search_api.api.likes.swagger_examples import paginated_likes_sum_up_example


note_example = OpenApiExample(
    "Note",
    value={
        "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "category": "Post",
        "owner": "string",
        "content": "string",
        "created_at": "2023-02-17T16:23:10.172Z",
        "updated_at": "2023-02-17T16:23:10.172Z",
        "comments_count": 2,
        "likes": paginated_likes_sum_up_example.value,
    },
)

paginated_notes_example = OpenApiExample(
    "Posts|Ideas",
    value={
        "next": False,
        "previous": False,
        "count": 1,
        "total_pages": 1,
        "results": [note_example.value],
    },
)
