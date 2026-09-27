from uuid import uuid4

TEST_DOC_ID = "test_id"
TEST_INDEX = "test/index"
TEST_FILE_PATH = "data_science/test_file.las"
TEST_BUCKET_NAME = "data_science_bucket"
TEST_URL = "http://test.com"
TEST_FILE_PATHS = ["data_science/test_file1.las", "data_science/test_file2.las"]
TEST_URLS = ["http://test.com/1", "http://test.com/2"]
TEST_ORIGIN_OWNER = "test_id"
TEST_ANOTHER_OWNER = "test_id_2"
POST_UUID_1 = str(uuid4())
POST_UUID_2 = str(uuid4())
POST_UUID_3 = str(uuid4())
IDEA_UUID = str(uuid4())
TEST_NOTES = [
    {
        "id": POST_UUID_1,
        "category": "Post",
        "content": "my test post 1",
        "owner": TEST_ORIGIN_OWNER,
    },
    {
        "id": POST_UUID_2,
        "category": "Post",
        "content": "my test post 2",
        "owner": TEST_ORIGIN_OWNER,
    },
    {
        "id": POST_UUID_3,
        "category": "Post",
        "content": "my test post 3",
        "owner": TEST_ANOTHER_OWNER,
    },
    {"id": IDEA_UUID, "category": "Idea", "content": "my test idea", "owner": TEST_ORIGIN_OWNER},
]

TEST_LIKES = [
    {"user_id": TEST_ORIGIN_OWNER},
    {"user_id": TEST_ANOTHER_OWNER},
]

TEST_INDEX = "test_index_name"
TEST_GEODOC = [
    {"index": {"_id": 0, "_index": TEST_INDEX}},
    {
        "Basin_Type": "Retro-arc Foreland (Ocean - Continent)",
        "Expl_Statu": "Well Explored",
        "Location": "Onshore",
        "Name": "Catatumbo",
        "Pet_System": "Producing fields",
        "geometry": {
            "coordinates": [
                [
                    [
                        [-73.16877678344362, 8.881851367806364],
                        [-73.13834479198374, 8.984903028866055],
                        [-73.07237466741121, 9.095881733520429],
                        [-72.99701578172338, 9.198933681292552],
                    ]
                ]
            ],
            "type": "MultiPolygon",
        },
    },
    {"index": {"_id": 1, "_index": TEST_INDEX}},
    {
        "Basin_Type": "Retro-arc Foreland (Ocean - Continent)",
        "Expl_Statu": "Well Explored",
        "Location": "Onshore",
        "Name": "Catatumbo",
        "Pet_System": "Producing fields",
        "geometry": {
            "coordinates": [
                [
                    [
                        [-73.16877678344362, 8.881851367806364],
                        [-73.13834479198374, 8.984903028866055],
                        [-73.07237466741121, 9.095881733520429],
                        [-72.99701578172338, 9.198933681292552],
                    ]
                ]
            ],
            "type": "MultiPolygon",
        },
    },
]

TEST_OPENSEARCH_RESPONSE = {
    "took": 5,
    "timed_out": False,
    "_shards": {"total": 5, "successful": 5, "skipped": 0, "failed": 0},
    "hits": {
        "total": {"value": 2, "relation": "eq"},
        "max_score": 1.0,
        "hits": [
            {
                "_index": "basin-shape-index",
                "_type": "_doc",
                "_id": "1",
                "_score": 1.0,
                "_source": {
                    "Name": "Amazonas",
                    "Expl_Statu": "Partially Explored",
                    "Location": "Onshore",
                    "Basin_Type": "Retro-arc Foreland (Ocean - Continent)",
                    "Pet_System": "Producing fields",
                    "geometry": {
                        "type": "MultiPolygon",
                        "coordinates": [
                            [
                                [
                                    [-74.41345012376551, -0.563005023072929],
                                    [-74.20226541052337, -0.358744319153303],
                                    [-74.47741497062322, -0.702273683658992],
                                    [-74.41345012376551, -0.563005023072929],
                                ]
                            ]
                        ],
                    },
                },
            },
            {
                "_index": "wells_ontology",
                "_type": "_doc",
                "_id": "2",
                "_score": 1.0,
                "_source": {
                    "asset_type": "well",
                    "asset_location": {"coordinates": [179.2940606, -45.5694131], "type": "point"},
                    "operator": None,
                    "region": "new zealand",
                    "basin": "Basin-Z3",
                    "ubhi": "tawa_abc-1_23",
                    "borehole_name": None,
                    "uwi": "tawa_abc-1_23",
                    "well_name": "tawa_abc-1_23",
                    "content": ["unreported"],
                },
            },
            {
                "_index": "las_files",
                "_type": "_doc",
                "_id": "123_28-1_ABCD_JWDL_QC.las",
                "_score": 1.0,
                "_source": {
                    "document_path": "123_28-1_ABCD_JWDL_QC.las",
                    "bucket_name": "geo-search",
                    "plot_file_path": "",
                    "is_readable": True,
                    "search_type": "las header",
                    "well_name": "123/28-1",
                    "ontology_score": 100,
                    "extracted_country": "",
                    "extracted_well_name": "123_28-1",
                    "asset_location": {"type": "point", "coordinates": [-44.53330194, 6.16396194]},
                },
            },
            {
                "_index": "document_location",
                "_type": "_doc",
                "_id": "123_01-_1.pdf",
                "_score": 1.0,
                "_source": {
                    "document_path": "123_01-_1.pdf",
                    "country": None,
                    "basin": "123",
                    "well_name": "123_01-_1",
                    "asset_location": {"coordinates": [-33.83041944, 6.99245444], "type": "point"},
                    "document_summary": "",
                    "bucket_name": "geo-search",
                },
            },
        ],
    },
}
