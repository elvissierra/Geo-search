from drf_spectacular.utils import OpenApiExample


search_example = OpenApiExample(
    "search",
    value={
        "took": 1,
        "timed_out": False,
        "_shards": {"total": 1, "successful": 1, "skipped": 0, "failed": 0},
        "hits": {
            "total": {"value": 3, "relation": "eq"},
            "max_score": 0.13353139,
            "hits": [
                {
                    "_index": "test-a",
                    "_id": "CZlTM4gBsmN6eHbw62OO",
                    "_score": 0.13353139,
                    "_source": {"attribute-a": "value-a", "attribute-b": "value-b"},
                    "_associated": {},
                },
                {
                    "_index": "test-a",
                    "_id": "CplVM4gBsmN6eHbwXGNT",
                    "_score": 0.13353139,
                    "_source": {"attribute-a": "value-a", "attribute-b": "value-b"},
                    "_associated": {},
                },
            ],
        },
    },
)

search_data_scape_example = OpenApiExample(
    "search_data_scape",
    value={
        "idx1": [
            {
                "doc_count": 1,
                "document_ids": ["document_id"],
                "asset_location": {
                    "coordinates": ["-90 (latitude)", "180 (Longitude)"],
                    "type": "point",
                },
            },
            "...",
        ],
        "idx2": [
            {
                "doc_count": 3,
                "document_ids": ["first_document_id", "second_document_id", "third_document_id"],
                "asset_location": {
                    "coordinates": ["-90 (latitude)", "180 (Longitude)"],
                    "type": "point",
                },
            },
            "...",
        ],
    },
)

search_data_scape_points_example = OpenApiExample(
    "search_data_scape_points",
    value={
        "index": [
            {
                "document_id": "document_id",
                "asset_location": {
                    "coordinates": ["-90 (latitude)", "180 (Longitude)"],
                    "type": "point",
                },
            },
            "...",
        ],
    },
)

search_data_scape_documents_example = OpenApiExample(
    "search_data_scape",
    value={
        "idx1": [
            {
                "_index": "idx1",
                "_id": "CplVM4gBsmN6eHbwXGNT",
                "_score": 0.13353139,
                "_source": {"attribute-a": "value-a", "attribute-b": "value-b"},
            },
            "...",
        ],
        "idx2": [
            {
                "_index": "idx2",
                "_id": "CZlTM4gBsmN6eHbw62OO",
                "_score": 0.13353139,
                "_source": {"attribute-a": "value-a", "attribute-b": "value-b"},
            },
            "...",
        ],
    },
    response_only=True,
)

search_autocomplete_example = OpenApiExample(
    "search_autocomplete",
    value={
        "idx1": {
            "suggestions": [
                "String A",
                "String B",
                "...",
            ]
        },
        "idx2": {
            "suggestions": [
                "String C",
                "String D",
                "...",
            ]
        },
    },
    response_only=True,
)


search_multi_example = OpenApiExample(
    "search_multi",
    value={
        "idx1": [
            {
                "doc_type": {"attribute_a": "Value", "attribute_b": "Value", "...": "..."},
                "highlight": {"attribute_name": ["<specialDivider>Value<specialDivider>"]},
            },
            "...",
        ],
        "idx2": [
            {
                "doc_type": {"attribute_a": "Value", "attribute_b": "Value", "...": "..."},
                "highlight": {"attribute_name": ["<specialDivider>Value<specialDivider>"]},
            },
            "...",
        ],
    },
    response_only=True,
)
