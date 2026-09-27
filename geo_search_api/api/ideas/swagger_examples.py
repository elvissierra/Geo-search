from drf_spectacular.utils import OpenApiExample


idea_example = OpenApiExample(
    "Idea",
    value={
        "id": "9ddcd538-f655-40b9-844d-3bb63e9cd5c7",
        "title": "Title *HERE*",
        "description": "444 desc",
        "status": "Active",
        "owner": "63ff6d13d93a692c22bc2dc0",
        "attachments": ["file", "attch"],
        "topic": "6030ffb6-d24c-11ed-afa1-0242ac120002",
        "is_trending": False,
        "engagement_rate": 0,
        "created_at": "2023-02-17T16:23:10.172Z",
        "updated_at": "2023-02-17T16:23:10.172Z",
    },
    response_only=True,
)

idea_post_example = OpenApiExample(
    "post_idea",
    value={
        "title": "Title *HERE*",
        "description": "444 desc",
        "topic": "6030ffb6-d24c-11ed-afa1-0242ac120002",
        "attachments": ["url", "file"],
    },
    request_only=True,
)

idea_post_status_example = OpenApiExample(
    "idea status",
    value={"id": "6030ffb6-d24c-11ed-afa1-0242ac120002", "status": "Active"},
    request_only=True,
)
