from drf_spectacular.utils import OpenApiExample

post_presigned_url_example = OpenApiExample(
    "PostPresigned",
    value={
        "data": [
            {"original_url": "data_science/test_file1.las", "presigned_url": "http:/test.com/1"},
            {"original_url": "data_science/test_file2.las", "presigned_url": "http:/test.com/2"},
        ]
    },
    response_only=True,
)
