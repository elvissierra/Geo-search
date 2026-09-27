import copy
from unittest.mock import call

from rest_framework import status
from rest_framework.reverse import reverse
from django import test as dj_test

from tests.test_data import TEST_OPENSEARCH_RESPONSE, TEST_URL
from clients.opensearch import QueryTypeEnum
from geo_search_api.api.search.constants import DOCUMENT_FIELD_NAME, SEARCH_MULTI_MAP


class TestSearch:
    uri = reverse("SearchGet")

    def test_unauthorized_positive_scenario(self, test_app_unauthorized):
        response = test_app_unauthorized.get(self.uri)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in response.json()

    @dj_test.override_settings(AWS_OPENSEARCH_HOST="http://opensearch.localhost:9200")
    def test_presigned_url_generation_document_location_positive_scenario(self, mocker, test_app):
        document_location_response = self._prepare_opensearch_response(index="document_location")
        mocker.patch(
            "clients.opensearch.OpenSearchClient.search",
            return_value=(True, document_location_response),
        )
        mocker.patch("clients.s3client.S3Client.get_presigned_url", return_value=TEST_URL)

        response = test_app.get(self.uri)
        assert response.status_code == status.HTTP_200_OK

        for hit in response.json()["hits"]["hits"]:
            assert "encoded_presigned_url" in hit["_source"]

    @dj_test.override_settings(AWS_OPENSEARCH_HOST="http://opensearch.localhost:9200")
    def test_presigned_url_generation_las_files_positive_scenario(self, mocker, test_app):
        las_files_response = self._prepare_opensearch_response(index="las_files")
        mocker.patch(
            "clients.opensearch.OpenSearchClient.search",
            return_value=(True, las_files_response),
        )
        mocker.patch("clients.s3client.S3Client.get_presigned_url", return_value=TEST_URL)

        response = test_app.get(self.uri)
        assert response.status_code == status.HTTP_200_OK

        for hit in response.json()["hits"]["hits"]:
            assert "encoded_presigned_url" in hit["_source"]

    @dj_test.override_settings(AWS_OPENSEARCH_HOST="http://opensearch.localhost:9200")
    def test_presigned_url_not_generated_missing_key_las_files_scenario(self, mocker, test_app):
        basin_shape_index_response = self._prepare_opensearch_response(index="basin_shape_index")
        mocker.patch(
            "clients.opensearch.OpenSearchClient.search",
            return_value=(True, basin_shape_index_response),
        )
        mocker.patch("clients.s3client.S3Client.get_presigned_url", return_value=TEST_URL)

        response = test_app.get(self.uri)
        assert response.status_code == status.HTTP_200_OK

        for hit in response.json()["hits"]["hits"]:
            assert "encoded_presigned_url" not in hit["_source"]

    @dj_test.override_settings(AWS_OPENSEARCH_HOST="http://opensearch.localhost:9200")
    def test_presigned_url_not_generated_missing_key_wells_ontology_scenario(
        self, mocker, test_app
    ):
        wells_ontology_response = self._prepare_opensearch_response(index="wells_ontology")
        mocker.patch(
            "clients.opensearch.OpenSearchClient.search",
            return_value=(True, wells_ontology_response),
        )
        mocker.patch("clients.s3client.S3Client.get_presigned_url", return_value=TEST_URL)

        response = test_app.get(self.uri)
        assert response.status_code == status.HTTP_200_OK

        for hit in response.json()["hits"]["hits"]:
            assert "encoded_presigned_url" not in hit["_source"]

    @dj_test.override_settings(AWS_OPENSEARCH_HOST="http://opensearch.localhost:9200")
    def test_without_including_size_q_param_positive_scenario(self, mocker, test_app):
        mocked_search = mocker.patch(
            "clients.opensearch.OpenSearchClient.search",
            return_value=(True, self._prepare_opensearch_response()),
        )
        mocker.patch(
            "geo_search_api.api.search.serializers.SearchResponseSerializer.to_representation",
            return_value=self._prepare_opensearch_response(),
        )

        response = test_app.get(self.uri)
        assert response.status_code == status.HTTP_200_OK

        mocked_search.assert_called_once_with()

    @dj_test.override_settings(AWS_OPENSEARCH_HOST="http://opensearch.localhost:9200")
    def test_without_q_params_positive_scenario(self, mocker, test_app):
        mocked_search = mocker.patch(
            "clients.opensearch.OpenSearchClient.search",
            return_value=(True, self._prepare_opensearch_response()),
        )
        mocker.patch(
            "geo_search_api.api.search.serializers.SearchResponseSerializer.to_representation",
            return_value=self._prepare_opensearch_response(),
        )
        response = test_app.get(self.uri)
        assert response.status_code == status.HTTP_200_OK

        mocked_search.assert_called_once_with()

    @dj_test.override_settings(AWS_OPENSEARCH_HOST="http://opensearch.localhost:9200")
    def test_with_index_q_param_negative_scenario(self, mocker, test_app):
        mocked_exists_index = mocker.patch(
            "clients.opensearch.OpenSearchClient.exists_index", return_value=False
        )
        mocker.patch(
            "geo_search_api.api.search.serializers.SearchResponseSerializer.to_representation",
            return_value=self._prepare_opensearch_response(),
        )
        response = test_app.get(self.uri, QUERY_STRING="index=fake")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        assert "index" in response.json()
        mocked_exists_index.assert_called_once_with("fake")

    @dj_test.override_settings(AWS_OPENSEARCH_HOST="http://opensearch.localhost:9200")
    def test_with_index_q_param_positive_scenario(self, mocker, test_app):

        mocked_exists_index = mocker.patch(
            "clients.opensearch.OpenSearchClient.exists_index", return_value=True
        )
        mocked_search = mocker.patch(
            "clients.opensearch.OpenSearchClient.search",
            return_value=(True, self._prepare_opensearch_response()),
        )
        mocker.patch(
            "geo_search_api.api.search.serializers.SearchResponseSerializer.to_representation",
            return_value=self._prepare_opensearch_response(),
        )

        response = test_app.get(self.uri, QUERY_STRING="index=fake")
        assert response.status_code == status.HTTP_200_OK

        mocked_exists_index.assert_called_once_with("fake")
        mocked_search.assert_called_once_with(index="fake")

    @dj_test.override_settings(AWS_OPENSEARCH_HOST="http://opensearch.localhost:9200")
    def test_with_size_q_param_negative_scenario(self, test_app):
        response = test_app.get(self.uri, QUERY_STRING="size=-100")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        assert "size" in response.json()

    @dj_test.override_settings(AWS_OPENSEARCH_HOST="http://opensearch.localhost:9200")
    def test_with_size_q_param_positive_scenario(self, mocker, test_app):
        mocked_search = mocker.patch(
            "clients.opensearch.OpenSearchClient.search",
            return_value=(True, self._prepare_opensearch_response()),
        )
        mocker.patch(
            "geo_search_api.api.search.serializers.SearchResponseSerializer.to_representation",
            return_value=self._prepare_opensearch_response(),
        )
        response = test_app.get(self.uri, QUERY_STRING="size=2500")
        assert response.status_code == status.HTTP_200_OK

        mocked_search.assert_called_once_with(size=2500)

    @dj_test.override_settings(AWS_OPENSEARCH_HOST="http://opensearch.localhost:9200")
    def test_with_default_size_q_param_positive_scenario(self, mocker, test_app):
        mocked_search = mocker.patch(
            "clients.opensearch.OpenSearchClient.search",
            return_value=(True, self._prepare_opensearch_response()),
        )
        mocker.patch(
            "geo_search_api.api.search.serializers.SearchResponseSerializer.to_representation",
            return_value=self._prepare_opensearch_response(),
        )
        response = test_app.get(self.uri)
        assert response.status_code == status.HTTP_200_OK

        mocked_search.assert_called_once_with()

    @dj_test.override_settings(AWS_OPENSEARCH_HOST="http://opensearch.localhost:9200")
    def test_with_size_query_type_param_negative_scenario(self, test_app):
        response = test_app.get(self.uri, QUERY_STRING="query_type=FAKE")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        assert "query_type" in response.json()

    @dj_test.override_settings(AWS_OPENSEARCH_HOST="http://opensearch.localhost:9200")
    def test_with_size_query_type_param_positive_scenario(self, mocker, test_app):
        mocked_search = mocker.patch(
            "clients.opensearch.OpenSearchClient.search",
            return_value=(True, self._prepare_opensearch_response()),
        )
        mocker.patch(
            "geo_search_api.api.search.serializers.SearchResponseSerializer.to_representation",
            return_value=self._prepare_opensearch_response(),
        )
        response = test_app.get(
            self.uri, QUERY_STRING="query_type=" + QueryTypeEnum.SIMPLE_QUERY_STRING.name
        )
        assert response.status_code == status.HTTP_200_OK

        mocked_search.assert_called_once_with(query_type=QueryTypeEnum.SIMPLE_QUERY_STRING)

    @dj_test.override_settings(AWS_OPENSEARCH_HOST="http://opensearch.localhost:9200")
    def test_with_size_query_parameters_param_negative_scenario(self, test_app):
        response = test_app.get(self.uri, QUERY_STRING="query_parameters=FAKE")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        assert "query_parameters" in response.json()

    @dj_test.override_settings(AWS_OPENSEARCH_HOST="http://opensearch.localhost:9200")
    def test_with_size_query_parameters_param_positive_scenario(self, mocker, test_app):
        mocked_search = mocker.patch(
            "clients.opensearch.OpenSearchClient.search",
            return_value=(True, self._prepare_opensearch_response()),
        )
        mocker.patch(
            "geo_search_api.api.search.serializers.SearchResponseSerializer.to_representation",
            return_value=self._prepare_opensearch_response(),
        )
        response = test_app.get(
            self.uri, QUERY_STRING='query_parameters={"fields": ["attr-a"], "query": "a"}'
        )
        assert response.status_code == status.HTTP_200_OK

        mocked_search.assert_called_once_with(query_parameters={"fields": ["attr-a"], "query": "a"})

    @dj_test.override_settings(AWS_OPENSEARCH_HOST="http://opensearch.localhost:9200")
    def test_basin_shape_index_associated_positive_scenario(self, mocker, test_app):
        opensearch_response = self._prepare_opensearch_response(index="basin-shape-index")
        mocker.patch(
            "clients.opensearch.OpenSearchClient.search", return_value=(True, opensearch_response)
        )
        mocked_multi_search = mocker.patch(
            "clients.opensearch.OpenSearchClient.multi_search",
            return_value=(
                True,
                {
                    "responses": [
                        copy.deepcopy(opensearch_response),
                        copy.deepcopy(opensearch_response),
                    ]
                },
            ),
        )
        mocked_exists_index = mocker.patch(
            "clients.opensearch.OpenSearchClient.exists_index", return_value=True
        )

        response = test_app.get(
            self.uri, QUERY_STRING="associated=document_location,wells_ontology"
        )
        assert response.status_code == status.HTTP_200_OK
        assert mocked_exists_index.call_args_list == [
            mocker.call("document_location"),
            mocker.call("wells_ontology"),
        ]

        instance = opensearch_response["hits"]["hits"][0]
        mocked_multi_search.assert_called_once_with(
            index=["document_location", "wells_ontology"],
            query_type=[QueryTypeEnum.TERM, QueryTypeEnum.TERM],
            query_parameters=[
                {"field": "basin.keyword", "value": instance["_source"]["Name"]},
                {"field": "basin.keyword", "value": instance["_source"]["Name"]},
            ],
        )

    @dj_test.override_settings(AWS_OPENSEARCH_HOST="http://opensearch.localhost:9200")
    def test_wells_ontology_associated_positive_scenario(self, mocker, test_app):
        opensearch_response = self._prepare_opensearch_response(index="wells_ontology")
        mocker.patch(
            "clients.opensearch.OpenSearchClient.search", return_value=(True, opensearch_response)
        )
        mocked_multi_search = mocker.patch(
            "clients.opensearch.OpenSearchClient.multi_search",
            return_value=(
                True,
                {
                    "responses": [
                        copy.deepcopy(opensearch_response),
                        copy.deepcopy(opensearch_response),
                        copy.deepcopy(opensearch_response),
                    ]
                },
            ),
        )
        mocked_exists_index = mocker.patch(
            "clients.opensearch.OpenSearchClient.exists_index", return_value=True
        )

        response = test_app.get(
            self.uri, QUERY_STRING="associated=basin-shape-index,document_location,las_files"
        )
        assert response.status_code == status.HTTP_200_OK
        assert mocked_exists_index.call_args_list == [
            mocker.call("basin-shape-index"),
            mocker.call("document_location"),
            mocker.call("las_files"),
        ]

        instance = opensearch_response["hits"]["hits"][0]
        mocked_multi_search.assert_called_once_with(
            index=["basin-shape-index", "document_location", "las_files"],
            query_type=[QueryTypeEnum.TERM, QueryTypeEnum.TERM, QueryTypeEnum.BOOL],
            query_parameters=[
                {
                    "field": "Name.keyword",
                    "value": instance["_source"]["basin"],
                },
                {
                    "field": "well_name.keyword",
                    "value": instance["_source"]["well_name"],
                },
                {
                    "should": [
                        {
                            QueryTypeEnum.TERM: {
                                "field": "well_name.keyword",
                                "value": instance["_source"]["well_name"],
                            }
                        },
                        {
                            QueryTypeEnum.TERM: {
                                "field": "extracted_well_name.keyword",
                                "value": {
                                    "value": instance["_source"]["well_name"],
                                    "case_insensitive": True,
                                },
                            }
                        },
                    ]
                },
            ],
        )

    @dj_test.override_settings(AWS_OPENSEARCH_HOST="http://opensearch.localhost:9200")
    def test_las_files_associated_positive_scenario(self, mocker, test_app):
        opensearch_response = self._prepare_opensearch_response(index="las_files")
        mocker.patch(
            "clients.opensearch.OpenSearchClient.search", return_value=(True, opensearch_response)
        )
        mocked_multi_search = mocker.patch(
            "clients.opensearch.OpenSearchClient.multi_search",
            return_value=(True, {"responses": [copy.deepcopy(opensearch_response)]}),
        )
        mocked_exists_index = mocker.patch(
            "clients.opensearch.OpenSearchClient.exists_index", return_value=True
        )
        mocker.patch("clients.s3client.S3Client.get_presigned_url", return_value=TEST_URL)
        response = test_app.get(self.uri, QUERY_STRING="associated=wells_ontology")
        assert response.status_code == status.HTTP_200_OK
        assert mocked_exists_index.call_args_list == [mocker.call("wells_ontology")]

        instance = opensearch_response["hits"]["hits"][0]
        mocked_multi_search.assert_called_once_with(
            index=["wells_ontology"],
            query_type=[QueryTypeEnum.BOOL],
            query_parameters=[
                {
                    "should": [
                        {
                            QueryTypeEnum.TERM: {
                                "field": "well_name.keyword",
                                "value": instance["_source"]["well_name"],
                            }
                        },
                        {
                            QueryTypeEnum.TERM: {
                                "field": "well_name.keyword",
                                "value": {
                                    "value": instance["_source"]["extracted_well_name"],
                                    "case_insensitive": True,
                                },
                            }
                        },
                    ]
                }
            ],
        )

    @dj_test.override_settings(AWS_OPENSEARCH_HOST="http://opensearch.localhost:9200")
    def test_document_location_associated_positive_scenario(self, mocker, test_app):
        opensearch_response = self._prepare_opensearch_response(index="document_location")
        mocker.patch(
            "clients.opensearch.OpenSearchClient.search", return_value=(True, opensearch_response)
        )
        mocked_multi_search = mocker.patch(
            "clients.opensearch.OpenSearchClient.multi_search",
            return_value=(
                True,
                {
                    "responses": [
                        copy.deepcopy(opensearch_response),
                        copy.deepcopy(opensearch_response),
                    ]
                },
            ),
        )
        mocked_exists_index = mocker.patch(
            "clients.opensearch.OpenSearchClient.exists_index", return_value=True
        )
        mocker.patch("clients.s3client.S3Client.get_presigned_url", return_value=TEST_URL)

        response = test_app.get(
            self.uri, QUERY_STRING="associated=basin-shape-index,wells_ontology"
        )
        assert response.status_code == status.HTTP_200_OK
        assert mocked_exists_index.call_args_list == [
            mocker.call("basin-shape-index"),
            mocker.call("wells_ontology"),
        ]

        instance = opensearch_response["hits"]["hits"][0]
        mocked_multi_search.assert_called_once_with(
            index=["basin-shape-index", "wells_ontology"],
            query_type=[QueryTypeEnum.TERM, QueryTypeEnum.TERM],
            query_parameters=[
                {"field": "Name.keyword", "value": instance["_source"]["basin"]},
                {"field": "well_name.keyword", "value": instance["_source"]["well_name"]},
            ],
        )

    @dj_test.override_settings(AWS_OPENSEARCH_HOST="http://opensearch.localhost:9200")
    def test_basin_shape_index_associated_with_name_none_positive_scenario(self, mocker, test_app):

        opensearch_response = self._prepare_opensearch_response(index="basin-shape-index")
        instance = opensearch_response["hits"]["hits"][0]

        instance["_source"]["Name"] = None

        mocker.patch("clients.opensearch.OpenSearchClient.exists_index", return_value=True)
        mocker.patch(
            "clients.opensearch.OpenSearchClient.search", return_value=(True, opensearch_response)
        )
        mocked_multi_search = mocker.patch(
            "clients.opensearch.OpenSearchClient.multi_search",
            return_value=(
                True,
                {},
            ),
        )

        response = test_app.get(
            self.uri, QUERY_STRING="associated=document_location,wells_ontology"
        )
        assert response.status_code == status.HTTP_200_OK
        assert not mocked_multi_search.called

    @dj_test.override_settings(AWS_OPENSEARCH_HOST="http://opensearch.localhost:9200")
    def test_wells_ontology_associated_basin_and_well_name_none_positive_scenario(
        self, mocker, test_app
    ):
        opensearch_response = self._prepare_opensearch_response(index="wells_ontology")
        instance = opensearch_response["hits"]["hits"][0]
        instance["_source"]["basin"] = None
        instance["_source"]["well_name"] = None

        mocker.patch("clients.opensearch.OpenSearchClient.exists_index", return_value=True)
        mocker.patch(
            "clients.opensearch.OpenSearchClient.search", return_value=(True, opensearch_response)
        )
        mocked_multi_search = mocker.patch(
            "clients.opensearch.OpenSearchClient.multi_search",
            return_value=(
                True,
                {
                    "responses": [
                        copy.deepcopy(opensearch_response),
                        copy.deepcopy(opensearch_response),
                        copy.deepcopy(opensearch_response),
                    ]
                },
            ),
        )

        response = test_app.get(
            self.uri, QUERY_STRING="associated=basin-shape-index,document_location,las_files"
        )
        assert response.status_code == status.HTTP_200_OK
        assert not mocked_multi_search.called

    @dj_test.override_settings(AWS_OPENSEARCH_HOST="http://opensearch.localhost:9200")
    def test_las_files_associated_well_name_none_positive_scenario(self, mocker, test_app):
        opensearch_response = self._prepare_opensearch_response(index="las_files")
        instance = opensearch_response["hits"]["hits"][0]
        instance["_source"]["well_name"] = None

        mocker.patch("clients.opensearch.OpenSearchClient.exists_index", return_value=True)
        mocker.patch(
            "clients.opensearch.OpenSearchClient.search", return_value=(True, opensearch_response)
        )
        mocked_multi_search = mocker.patch(
            "clients.opensearch.OpenSearchClient.multi_search",
            return_value=(True, {"responses": [copy.deepcopy(opensearch_response)]}),
        )
        mocker.patch("clients.s3client.S3Client.get_presigned_url", return_value=TEST_URL)
        response = test_app.get(self.uri, QUERY_STRING="associated=wells_ontology")
        assert response.status_code == status.HTTP_200_OK
        mocked_multi_search.assert_called_once_with(
            index=["wells_ontology"],
            query_type=[QueryTypeEnum.BOOL],
            query_parameters=[
                {
                    "should": [
                        {
                            QueryTypeEnum.TERM: {
                                "field": "well_name.keyword",
                                "value": {
                                    "value": instance["_source"]["extracted_well_name"],
                                    "case_insensitive": True,
                                },
                            }
                        },
                    ]
                }
            ],
        )

    @dj_test.override_settings(AWS_OPENSEARCH_HOST="http://opensearch.localhost:9200")
    def test_las_files_associated_extracted_well_name_none_positive_scenario(
        self, mocker, test_app
    ):
        opensearch_response = self._prepare_opensearch_response(index="las_files")
        instance = opensearch_response["hits"]["hits"][0]
        instance["_source"]["extracted_well_name"] = None

        mocker.patch("clients.opensearch.OpenSearchClient.exists_index", return_value=True)
        mocker.patch(
            "clients.opensearch.OpenSearchClient.search", return_value=(True, opensearch_response)
        )
        mocked_multi_search = mocker.patch(
            "clients.opensearch.OpenSearchClient.multi_search",
            return_value=(True, {"responses": [copy.deepcopy(opensearch_response)]}),
        )
        mocker.patch("clients.s3client.S3Client.get_presigned_url", return_value=TEST_URL)
        response = test_app.get(self.uri, QUERY_STRING="associated=wells_ontology")
        assert response.status_code == status.HTTP_200_OK
        mocked_multi_search.assert_called_once_with(
            index=["wells_ontology"],
            query_type=[QueryTypeEnum.BOOL],
            query_parameters=[
                {
                    "should": [
                        {
                            QueryTypeEnum.TERM: {
                                "field": "well_name.keyword",
                                "value": instance["_source"]["well_name"],
                            }
                        },
                    ]
                }
            ],
        )

    @dj_test.override_settings(AWS_OPENSEARCH_HOST="http://opensearch.localhost:9200")
    def test_document_location_associated_basin_none_positive_scenario(self, mocker, test_app):
        opensearch_response = self._prepare_opensearch_response(index="document_location")
        instance = opensearch_response["hits"]["hits"][0]
        instance["_source"]["basin"] = None

        mocker.patch("clients.opensearch.OpenSearchClient.exists_index", return_value=True)
        mocker.patch(
            "clients.opensearch.OpenSearchClient.search", return_value=(True, opensearch_response)
        )
        mocked_multi_search = mocker.patch(
            "clients.opensearch.OpenSearchClient.multi_search",
            return_value=(
                True,
                {
                    "responses": [
                        copy.deepcopy(opensearch_response),
                        copy.deepcopy(opensearch_response),
                    ]
                },
            ),
        )
        mocker.patch("clients.s3client.S3Client.get_presigned_url", return_value=TEST_URL)
        response = test_app.get(
            self.uri, QUERY_STRING="associated=basin-shape-index,wells_ontology"
        )
        assert response.status_code == status.HTTP_200_OK
        mocked_multi_search.assert_called_once_with(
            index=["wells_ontology"],
            query_type=[QueryTypeEnum.TERM],
            query_parameters=[
                {"field": "well_name.keyword", "value": instance["_source"]["well_name"]},
            ],
        )

    @dj_test.override_settings(AWS_OPENSEARCH_HOST="http://opensearch.localhost:9200")
    def test_document_location_associated_well_name_none_positive_scenario(self, mocker, test_app):
        opensearch_response = self._prepare_opensearch_response(index="document_location")
        instance = opensearch_response["hits"]["hits"][0]
        instance["_source"]["well_name"] = None

        mocker.patch("clients.opensearch.OpenSearchClient.exists_index", return_value=True)
        mocker.patch(
            "clients.opensearch.OpenSearchClient.search", return_value=(True, opensearch_response)
        )
        mocked_multi_search = mocker.patch(
            "clients.opensearch.OpenSearchClient.multi_search",
            return_value=(
                True,
                {
                    "responses": [
                        copy.deepcopy(opensearch_response),
                        copy.deepcopy(opensearch_response),
                    ]
                },
            ),
        )
        mocker.patch("clients.s3client.S3Client.get_presigned_url", return_value=TEST_URL)
        response = test_app.get(
            self.uri, QUERY_STRING="associated=basin-shape-index,wells_ontology"
        )
        assert response.status_code == status.HTTP_200_OK
        mocked_multi_search.assert_called_once_with(
            index=["basin-shape-index"],
            query_type=[QueryTypeEnum.TERM],
            query_parameters=[
                {"field": "Name.keyword", "value": instance["_source"]["basin"]},
            ],
        )

    @staticmethod
    def _prepare_opensearch_response(index: str = None):

        opensearch_response = copy.deepcopy(TEST_OPENSEARCH_RESPONSE)
        opensearch_response["hits"]["hits"] = list(
            filter(lambda x: x["_index"] == index, opensearch_response["hits"]["hits"])
        )

        return opensearch_response


class TestSearchDataScapeClusters:
    uri = reverse("SearchDataScapeClustersGet")

    def test_unauthorized_positive_scenario(self, test_app_unauthorized):
        response = test_app_unauthorized.get(self.uri)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in response.json()

    @dj_test.override_settings(AWS_OPENSEARCH_HOST="http://opensearch.localhost:9200")
    def test_with_default_q_params_positive_scenario(self, mocker, test_app):
        mocker.patch(
            "geo_search_api.api.search.serializers.SearchDataScapeClustersSerializer.to_representation",
            return_value={"idx_a": []},
        )
        mocked_exists_index = mocker.patch(
            "clients.opensearch.OpenSearchClient.exists_index", return_value=True
        )
        mocked_get_geo_bounding_box_clusters = mocker.patch(
            "clients.opensearch.OpenSearchClient.get_geo_bounding_box_clusters",
            return_value=(True, {"idx_a": []}),
        )
        response = test_app.get(self.uri)
        assert response.status_code == status.HTTP_200_OK
        assert mocked_exists_index.call_count == 3
        mocked_get_geo_bounding_box_clusters.assert_called_once_with(
            index=["wells_ontology", "las_files", "document_location"],
            bottom_right={"lat": -90.0, "lon": 180.0},
            top_left={"lat": 90.0, "lon": -180.0},
            precision=1,
        )

    @dj_test.override_settings(AWS_OPENSEARCH_HOST="http://opensearch.localhost:9200")
    def test_with_specified_q_params_positive_scenario(self, mocker, test_app):
        mocker.patch(
            "geo_search_api.api.search.serializers.SearchDataScapeClustersSerializer.to_representation",
            return_value={"idx_a": []},
        )
        mocked_exists_index = mocker.patch(
            "clients.opensearch.OpenSearchClient.exists_index", return_value=True
        )
        mocked_get_geo_bounding_box_clusters = mocker.patch(
            "clients.opensearch.OpenSearchClient.get_geo_bounding_box_clusters",
            return_value=(True, {"idx_a": []}),
        )
        response = test_app.get(
            self.uri,
            QUERY_STRING="index=wells_ontology&top_left=50,-100&bottom_right=-50,100&precision=8",
        )
        assert response.status_code == status.HTTP_200_OK
        assert mocked_exists_index.call_count == 1
        mocked_get_geo_bounding_box_clusters.assert_called_once_with(
            index=["wells_ontology"],
            bottom_right={"lat": -50.0, "lon": 100.0},
            top_left={"lat": 50.0, "lon": -100.0},
            precision=8,
        )

    @dj_test.override_settings(AWS_OPENSEARCH_HOST="http://opensearch.localhost:9200")
    def test_with_index_q_param_negative_scenario(self, mocker, test_app):
        mocked_exists_index = mocker.patch(
            "clients.opensearch.OpenSearchClient.exists_index", return_value=False
        )
        response = test_app.get(self.uri, QUERY_STRING="index=fake")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        assert "index" in response.json()
        mocked_exists_index.assert_called_once_with("fake")


class TestSearchDataScapePoints:
    uri = reverse("SearchDataScapeDocumentsPointsGet")

    def test_unauthorized_positive_scenario(self, test_app_unauthorized):
        response = test_app_unauthorized.get(self.uri)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in response.json()

    @dj_test.override_settings(AWS_OPENSEARCH_HOST="http://opensearch.localhost:9200")
    def test_fails_without_index(self, mocker, test_app):
        mocker.patch(
            "geo_search_api.api.search.serializers.SearchDataScapeDocumentsPointsSerializer.to_representation",
            return_value={"idx_a": []},
        )
        mocked_exists_index = mocker.patch(
            "clients.opensearch.OpenSearchClient.exists_index", return_value=True
        )
        mocked_get_geo_bounding_box_points = mocker.patch(
            "clients.opensearch.OpenSearchClient.get_documents_in_bounding_box",
            return_value=(True, {"idx_a": []}),
        )
        response = test_app.get(self.uri)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert mocked_exists_index.call_count == 0
        mocked_get_geo_bounding_box_points.assert_not_called()

    @dj_test.override_settings(AWS_OPENSEARCH_HOST="http://opensearch.localhost:9200")
    def test_with_index_positive_scenario(self, mocker, test_app):
        mocker.patch(
            "geo_search_api.api.search.serializers.SearchDataScapeDocumentsPointsSerializer.to_representation",
            return_value={"idx_a": []},
        )
        mocked_exists_index = mocker.patch(
            "clients.opensearch.OpenSearchClient.exists_index", return_value=True
        )
        mocked_get_geo_bounding_box_points = mocker.patch(
            "clients.opensearch.OpenSearchClient.get_documents_in_bounding_box",
            return_value=(True, {"idx_a": []}),
        )
        response = test_app.get(
            self.uri,
            QUERY_STRING="index=wells_ontology&top_left=50,-100&bottom_right=-50,100&precision=8",
        )
        assert response.status_code == status.HTTP_200_OK
        assert mocked_exists_index.call_count == 1
        mocked_get_geo_bounding_box_points.assert_called_once_with(
            index="wells_ontology",
            bottom_right={"lat": -50.0, "lon": 100.0},
            top_left={"lat": 50.0, "lon": -100.0},
        )

    @dj_test.override_settings(AWS_OPENSEARCH_HOST="http://opensearch.localhost:9200")
    def test_with_index_negative_scenario(self, mocker, test_app):
        mocked_exists_index = mocker.patch(
            "clients.opensearch.OpenSearchClient.exists_index", return_value=False
        )
        response = test_app.get(self.uri, QUERY_STRING="index=fake")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        assert "index" in response.json()
        mocked_exists_index.assert_called_once_with("fake")

    @dj_test.override_settings(AWS_OPENSEARCH_HOST="http://opensearch.localhost:9200")
    def test_fails_with_corrupted_coordinates(self, mocker, test_app):
        mocked_exists_index = mocker.patch(
            "clients.opensearch.OpenSearchClient.exists_index", return_value=True
        )
        mocked_get_geo_bounding_box_points = mocker.patch(
            "clients.opensearch.OpenSearchClient.get_documents_in_bounding_box",
            return_value=(True, {"idx_a": []}),
        )
        response = test_app.get(
            self.uri,
            QUERY_STRING="index=wells_ontology&top_left=120,-100&bottom_right=-50,100&precision=8",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert mocked_exists_index.call_count == 1
        mocked_get_geo_bounding_box_points.assert_not_called()


class TestSearchDataScapeDocuments:
    uri = reverse("SearchDataScapeDocumentsPost")

    def test_unauthorized_positive_scenario(self, test_app_unauthorized):
        response = test_app_unauthorized.post(self.uri)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in response.json()

    @dj_test.override_settings(AWS_OPENSEARCH_HOST="http://opensearch.localhost:9200")
    def test_get_one_document_positive_scenario(self, mocker, test_app):
        mocker.patch(
            "geo_search_api.api.search.serializers.SearchDataScapeDocumentsSerializer.to_representation",
            return_value={"idx_a": []},
        )
        mocked_exists_index = mocker.patch(
            "clients.opensearch.OpenSearchClient.exists_index", return_value=True
        )
        mocked_get_documents = mocker.patch(
            "clients.opensearch.OpenSearchClient.get_documents", return_value=(True, {"idx_a": []})
        )
        body = [{"index": "wells_ontology", "document_ids": ["test_id"]}]
        response = test_app.post(self.uri, body, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert mocked_exists_index.call_count == 1
        mocked_get_documents.assert_called_once_with(
            index="wells_ontology", document_ids=["test_id"]
        )

    @dj_test.override_settings(AWS_OPENSEARCH_HOST="http://opensearch.localhost:9200")
    def test_get_bunch_of_documents_positive_scenario(self, mocker, test_app):
        mocker.patch(
            "geo_search_api.api.search.serializers.SearchDataScapeDocumentsSerializer.to_representation",
            return_value={"idx_a": []},
        )
        mocked_exists_index = mocker.patch(
            "clients.opensearch.OpenSearchClient.exists_index", return_value=True
        )
        mocked_get_documents = mocker.patch(
            "clients.opensearch.OpenSearchClient.get_documents", return_value=(True, {"idx_a": []})
        )
        body = [
            {"index": "wells_ontology", "document_ids": ["test_id"]},
            {"index": "document_location", "document_ids": ["test_id_2"]},
        ]
        response = test_app.post(self.uri, body, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert mocked_exists_index.call_count == 2
        mocked_get_documents.assert_has_calls(
            [
                call(index="wells_ontology", document_ids=["test_id"]),
                call(index="document_location", document_ids=["test_id_2"]),
            ]
        )

    @dj_test.override_settings(AWS_OPENSEARCH_HOST="http://opensearch.localhost:9200")
    def test_get_document_fails_when_wrong_json_body(self, mocker, test_app):
        mocker.patch(
            "geo_search_api.api.search.serializers.SearchDataScapeDocumentsSerializer.to_representation",
            return_value={"idx_a": []},
        )

        body = [{"wrong": "wells_ontology", "wrong_2": ["test_id"]}]
        response = test_app.post(self.uri, body, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()[0] == {
            "index": ["This field is required."],
            "document_ids": ["This field is required."],
        }

    @dj_test.override_settings(AWS_OPENSEARCH_HOST="http://opensearch.localhost:9200")
    def test_get_document_fails_when_index_not_exist(self, mocker, test_app):
        mocker.patch(
            "geo_search_api.api.search.serializers.SearchDataScapeDocumentsSerializer.to_representation",
            return_value={"idx_a": []},
        )
        mocked_exists_index = mocker.patch(
            "clients.opensearch.OpenSearchClient.exists_index", return_value=False
        )
        mocked_get_documents = mocker.patch(
            "clients.opensearch.OpenSearchClient.get_documents", return_value=(True, {"idx_a": []})
        )
        body = [{"index": "fake", "document_ids": ["test_id"]}]
        response = test_app.post(self.uri, body, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()[0] == {"index": ["The index `fake` does not exists."]}
        assert mocked_exists_index.call_count == 1
        mocked_get_documents.assert_not_called()


class TestSearchDataScapeAutocomplete:
    uri = reverse("SearchDataScapeAutocompleteGet")

    def test_unauthorized_positive_scenario(self, test_app_unauthorized):
        response = test_app_unauthorized.get(self.uri)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in response.json()

    def test_without_q_params_positive_scenario(self, test_app):
        response = test_app.get(self.uri)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @dj_test.override_settings(AWS_OPENSEARCH_HOST="http://opensearch.localhost:9200")
    def test_with_short_query_negative_scenario(self, mocker, test_app):
        mocked_multi_search = mocker.patch("clients.opensearch.OpenSearchClient.multi_search")

        response = test_app.get(self.uri, QUERY_STRING="query=1")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert not mocked_multi_search.called

    @dj_test.override_settings(AWS_OPENSEARCH_HOST="http://opensearch.localhost:9200")
    def test_with_q_params_query_negative_scenario(self, mocker, test_app):
        mocked_to_representation = mocker.patch(
            "geo_search_api.api.search.serializers.SearchDataScapeAutocompleteResponseSerializer.to_representation",
            return_value={"idx_a": {"suggestions": []}},
        )
        mocked_multi_search = mocker.patch(
            "clients.opensearch.OpenSearchClient.multi_search",
            return_value=(
                False,
                {},
            ),
        )

        response = test_app.get(self.uri, QUERY_STRING="query=test")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert mocked_multi_search.called
        assert not mocked_to_representation.called

    @dj_test.override_settings(AWS_OPENSEARCH_HOST="http://opensearch.localhost:9200")
    def test_with_phrase_positive_scenario(self, mocker, test_app):
        mocker.patch(
            "geo_search_api.api.search.serializers.SearchDataScapeAutocompleteResponseSerializer.to_representation",
            return_value={"idx_a": {"suggestions": []}},
        )
        mocked_multi_search = mocker.patch(
            "clients.opensearch.OpenSearchClient.multi_search",
            return_value=(
                True,
                {},
            ),
        )

        response = test_app.get(self.uri, QUERY_STRING="query=super test")
        assert response.status_code == status.HTTP_200_OK
        mocked_multi_search.assert_called_once_with(
            index=[
                "basin-shape-index",
                "wells_ontology",
                "wells_ontology",
                "wells_ontology",
                "wells_ontology",
                "las_files",
                "document_location",
                "document_location",
            ],
            query_type=[QueryTypeEnum.QUERY_STRING for _ in range(8)],
            query_parameters=[
                {
                    "fields": [f"Name.{DOCUMENT_FIELD_NAME}"],
                    "query": "*super test* OR super* OR test*",
                    "kwargs": {"_source": ["Name"]},
                },
                {
                    "fields": [f"well_name.{DOCUMENT_FIELD_NAME}"],
                    "query": "*super test* OR super* OR test*",
                    "kwargs": {"_source": ["well_name"]},
                },
                {
                    "fields": [f"uwi.{DOCUMENT_FIELD_NAME}"],
                    "query": "*super test* OR super* OR test*",
                    "kwargs": {"_source": ["uwi"]},
                },
                {
                    "fields": [f"operator.{DOCUMENT_FIELD_NAME}"],
                    "query": "*super test* OR super* OR test*",
                    "kwargs": {"_source": ["operator"]},
                },
                {
                    "fields": [f"region.{DOCUMENT_FIELD_NAME}"],
                    "query": "*super test* OR super* OR test*",
                    "kwargs": {"_source": ["region"]},
                },
                {
                    "fields": [f"document_name.{DOCUMENT_FIELD_NAME}"],
                    "query": "*super test* OR super* OR test*",
                    "kwargs": {"_source": ["document_name"]},
                },
                {
                    "fields": [f"document_name.{DOCUMENT_FIELD_NAME}"],
                    "query": "*super test* OR super* OR test*",
                    "kwargs": {"_source": ["document_name"]},
                },
                {
                    "fields": [f"country.{DOCUMENT_FIELD_NAME}"],
                    "query": "*super test* OR super* OR test*",
                    "kwargs": {"_source": ["country"]},
                },
            ],
            size=3,
        )

    @dj_test.override_settings(AWS_OPENSEARCH_HOST="http://opensearch.localhost:9200")
    def test_with_single_word_positive_scenario(self, mocker, test_app):
        mocker.patch(
            "geo_search_api.api.search.serializers.SearchDataScapeAutocompleteResponseSerializer.to_representation",
            return_value={"idx_a": {"suggestions": []}},
        )
        mocked_multi_search = mocker.patch(
            "clients.opensearch.OpenSearchClient.multi_search",
            return_value=(
                True,
                {},
            ),
        )

        response = test_app.get(self.uri, QUERY_STRING="query=supertest")
        assert response.status_code == status.HTTP_200_OK
        mocked_multi_search.assert_called_once_with(
            index=[
                "basin-shape-index",
                "wells_ontology",
                "wells_ontology",
                "wells_ontology",
                "wells_ontology",
                "las_files",
                "document_location",
                "document_location",
            ],
            query_type=[QueryTypeEnum.QUERY_STRING for _ in range(8)],
            query_parameters=[
                {
                    "fields": [f"Name.{DOCUMENT_FIELD_NAME}"],
                    "query": "supertest*",
                    "kwargs": {"_source": ["Name"]},
                },
                {
                    "fields": [f"well_name.{DOCUMENT_FIELD_NAME}"],
                    "query": "supertest*",
                    "kwargs": {"_source": ["well_name"]},
                },
                {
                    "fields": [f"uwi.{DOCUMENT_FIELD_NAME}"],
                    "query": "supertest*",
                    "kwargs": {"_source": ["uwi"]},
                },
                {
                    "fields": [f"operator.{DOCUMENT_FIELD_NAME}"],
                    "query": "supertest*",
                    "kwargs": {"_source": ["operator"]},
                },
                {
                    "fields": [f"region.{DOCUMENT_FIELD_NAME}"],
                    "query": "supertest*",
                    "kwargs": {"_source": ["region"]},
                },
                {
                    "fields": [f"document_name.{DOCUMENT_FIELD_NAME}"],
                    "query": "supertest*",
                    "kwargs": {"_source": ["document_name"]},
                },
                {
                    "fields": [f"document_name.{DOCUMENT_FIELD_NAME}"],
                    "query": "supertest*",
                    "kwargs": {"_source": ["document_name"]},
                },
                {
                    "fields": [f"country.{DOCUMENT_FIELD_NAME}"],
                    "query": "supertest*",
                    "kwargs": {"_source": ["country"]},
                },
            ],
            size=3,
        )


class TestSearchDataScapeMulti:
    uri = reverse("SearchDataScapeMultiGet")

    def test_unauthorized_positive_scenario(self, test_app_unauthorized):
        response = test_app_unauthorized.get(self.uri)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in response.json()

    @dj_test.override_settings(AWS_OPENSEARCH_HOST="http://opensearch.localhost:9200")
    def test_without_q_params_positive_scenario(self, mocker, test_app):
        mocker.patch("clients.opensearch.OpenSearchClient.exists_index", return_value=True)
        response = test_app.get(self.uri)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @dj_test.override_settings(AWS_OPENSEARCH_HOST="http://opensearch.localhost:9200")
    def test_with_short_query_negative_scenario(self, mocker, test_app):
        mocker.patch("clients.opensearch.OpenSearchClient.exists_index", return_value=True)
        mocked_multi_search = mocker.patch("clients.opensearch.OpenSearchClient.multi_search")

        response = test_app.get(self.uri, QUERY_STRING="query=1")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert not mocked_multi_search.called

    @dj_test.override_settings(AWS_OPENSEARCH_HOST="http://opensearch.localhost:9200")
    def test_with_q_params_query_negative_scenario(self, mocker, test_app):
        mocked_to_representation = mocker.patch(
            "geo_search_api.api.search.serializers.SearchDataScapeMultiResponseSerializer.to_representation",
            return_value={"idx_a": []},
        )
        mocked_exists_index = mocker.patch(
            "clients.opensearch.OpenSearchClient.exists_index", return_value=True
        )
        mocked_multi_search = mocker.patch(
            "clients.opensearch.OpenSearchClient.multi_search",
            return_value=(
                False,
                {},
            ),
        )

        response = test_app.get(self.uri, QUERY_STRING="query=test")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        assert mocked_multi_search.called
        assert not mocked_to_representation.called
        assert mocked_exists_index.call_count == 4

    @dj_test.override_settings(AWS_OPENSEARCH_HOST="http://opensearch.localhost:9200")
    def test_with_phrase_positive_scenario(self, mocker, test_app):
        mocker.patch(
            "geo_search_api.api.search.serializers.SearchDataScapeMultiResponseSerializer.to_representation",
            return_value={"idx_a": []},
        )
        mocker.patch("clients.opensearch.OpenSearchClient.exists_index", return_value=True)
        mocked_multi_search = mocker.patch(
            "clients.opensearch.OpenSearchClient.multi_search",
            return_value=(
                True,
                {},
            ),
        )

        response = test_app.get(self.uri, QUERY_STRING="query=super test&size=100")
        assert response.status_code == status.HTTP_200_OK

        mocked_multi_search.assert_called_once_with(
            index=list(SEARCH_MULTI_MAP.keys()),
            query_type=[QueryTypeEnum.QUERY_STRING for _ in range(4)],
            query_parameters=[
                {"query": "*super test* OR super* OR test*", "fields": o.get("fields")}
                for _, o in SEARCH_MULTI_MAP.items()
            ],
            size=100,
            highlight=[o.get("highlight") for _, o in SEARCH_MULTI_MAP.items()],
        )

    @dj_test.override_settings(AWS_OPENSEARCH_HOST="http://opensearch.localhost:9200")
    def test_with_single_word_positive_scenario(self, mocker, test_app):
        mocker.patch(
            "geo_search_api.api.search.serializers.SearchDataScapeMultiResponseSerializer.to_representation",
            return_value={"idx_a": []},
        )
        mocker.patch("clients.opensearch.OpenSearchClient.exists_index", return_value=True)
        mocked_multi_search = mocker.patch(
            "clients.opensearch.OpenSearchClient.multi_search",
            return_value=(
                True,
                {},
            ),
        )

        response = test_app.get(self.uri, QUERY_STRING="query=supertest&size=100")
        assert response.status_code == status.HTTP_200_OK

        mocked_multi_search.assert_called_once_with(
            index=list(SEARCH_MULTI_MAP.keys()),
            query_type=[QueryTypeEnum.QUERY_STRING for _ in range(4)],
            query_parameters=[
                {"query": "supertest*", "fields": o.get("fields")}
                for _, o in SEARCH_MULTI_MAP.items()
            ],
            size=100,
            highlight=[o.get("highlight") for _, o in SEARCH_MULTI_MAP.items()],
        )
