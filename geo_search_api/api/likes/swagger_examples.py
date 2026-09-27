from drf_spectacular.utils import OpenApiExample


like_example = OpenApiExample(
    "Like",
    value={
        "user_id": "string",
        "created_at": "2023-03-15T12:24:45.152Z",
    },
)

paginated_likes_sum_up_example = OpenApiExample(
    "Likes",
    value={
        "count": 1,
        "is_current_user_liked": True,
        "results": [like_example.value],
    },
)

paginated_likes_example = OpenApiExample(
    "Likes",
    value={
        "next": False,
        "previous": False,
        "count": 1,
        "total_pages": 1,
        "is_current_user_liked": False,
        "results": [like_example.value],
    },
)
