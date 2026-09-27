DOCUMENT_FIELD_NAME = "keyword_lowercase"

AUTOCOMPLETE_MAP = {
    "basin-shape-index": ["Name"],
    "wells_ontology": [
        "well_name",
        "uwi",
        "operator",
        "region",
    ],
    "las_files": ["document_name"],
    "document_location": ["document_name", "country"],
}

SEARCH_MULTI_MAP = {
    "basin-shape-index": {
        "fields": (
            "Name.keyword_lowercase^16",
            "Basin_Type.keyword_lowercase^8",
            "Location.keyword_lowercase^4",
            "Expl_Statu.keyword_lowercase^2",
            "Pet_System.keyword_lowercase",
        ),
        "highlight": {
            "fields": {
                "Name.keyword_lowercase": {},
                "Basin_Type.keyword_lowercase": {},
                "Location.keyword_lowercase": {},
                "Expl_Statu.keyword_lowercase": {},
                "Pet_System.keyword_lowercase": {},
            },
            "pre_tags": "<specialDivider>",
            "post_tags": "<specialDivider>",
            "order": "score",
        },
    },
    "wells_ontology": {
        "fields": (
            "well_name.keyword_lowercase^128",
            "uwi.keyword_lowercase^64",
            "operator.keyword_lowercase^32",
            "region.keyword_lowercase^16",
            "basin.keyword_lowercase^8",
            "ubhi.keyword_lowercase^4",
            "content.keyword_lowercase^2",
            "asset_type.keyword_lowercase",
        ),
        "highlight": {
            "fields": {
                "well_name.keyword_lowercase": {},
                "uwi.keyword_lowercase": {},
                "operator.keyword_lowercase": {},
                "region.keyword_lowercase": {},
                "basin.keyword_lowercase": {},
                "ubhi.keyword_lowercase": {},
                "content.keyword_lowercase": {},
                "asset_type.keyword_lowercase": {},
            },
            "pre_tags": "<specialDivider>",
            "post_tags": "<specialDivider>",
            "order": "score",
        },
    },
    "las_files": {
        "fields": (
            "document_name.keyword_lowercase^64",
            "document_path.keyword_lowercase^32",
            "well_name.keyword_lowercase^16",
            "extracted_well_name.keyword_lowercase^8",
            "extracted_country.keyword_lowercase^4",
            "bucket_name.keyword_lowercase^2",
            "plot_file_path.keyword_lowercase",
        ),
        "highlight": {
            "fields": {
                "document_name.keyword_lowercase": {},
                "document_path.keyword_lowercase": {},
                "well_name.keyword_lowercase": {},
                "extracted_well_name.keyword_lowercase": {},
                "extracted_country.keyword_lowercase": {},
                "bucket_name.keyword_lowercase": {},
                "plot_file_path.keyword_lowercase": {},
            },
            "pre_tags": "<specialDivider>",
            "post_tags": "<specialDivider>",
            "order": "score",
        },
    },
    "document_location": {
        "fields": (
            "document_name.keyword_lowercase^64",
            "country.keyword_lowercase^32",
            "well_name.keyword_lowercase^16",
            "document_path.keyword_lowercase^8",
            "document_summary.keyword_lowercase^4",
            "basin.keyword_lowercase^2",
            "bucket_name.keyword_lowercase",
        ),
        "highlight": {
            "fields": {
                "document_name.keyword_lowercase": {},
                "country.keyword_lowercase": {},
                "well_name.keyword_lowercase": {},
                "document_path.keyword_lowercase": {},
                "document_summary.keyword_lowercase": {},
                "basin.keyword_lowercase": {},
                "bucket_name.keyword_lowercase": {},
            },
            "pre_tags": "<specialDivider>",
            "post_tags": "<specialDivider>",
            "order": "score",
        },
    },
}
