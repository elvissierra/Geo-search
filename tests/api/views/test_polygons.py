from rest_framework import status
from rest_framework.reverse import reverse
from django import test as dj_test

from clients.opensearch import QueryTypeEnum

from geo_search_api.api.polygons.constants import PolygonApiConfig


class TestPolygonRegistryGetView:
    @property
    def uri(self):
        return reverse("PolygonsRegistryGet")

    def test_unauthorized_positive_scenario(self, test_app_unauthorized):
        response = test_app_unauthorized.get(self.uri)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in response.json()

    @dj_test.override_settings(AWS_OPENSEARCH_HOST="http://opensearch.localhost:9200")
    def test_positive_scenario(self, mocker, test_app):
        mocked_search = mocker.patch(
            "clients.opensearch.OpenSearchClient.search",
            return_value=(True, {"status": "FakeOkay"}),
        )

        response = test_app.get(self.uri)
        assert response.status_code == status.HTTP_200_OK

        assert {"status": "FakeOkay"} == response.json()
        mocked_search.assert_called_once_with(index=PolygonApiConfig.registry_opensearch_index_name)


class TestPolygonGetView:
    @property
    def uri(self):
        return reverse("PolygonsGet")

    def test_unauthorized_positive_scenario(self, test_app_unauthorized):
        response = test_app_unauthorized.get(self.uri)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in response.json()

    def test_without_query_params_negative_scenario(self, test_app):
        response = test_app.get(self.uri)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "index" in response.json()

    @dj_test.override_settings(AWS_OPENSEARCH_HOST="http://opensearch.localhost:9200")
    def test_with_index_query_params_negative_scenario(self, mocker, test_app):

        mocker.patch("clients.opensearch.OpenSearchClient.exists_index", return_value=True)
        mocker.patch(
            "clients.opensearch.OpenSearchClient.multi_search",
            return_value=(False, {"status": "FakeError"}),
        )

        response = test_app.get(self.uri, QUERY_STRING="index=FakeIndexA,FakeIndexB")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {"detail": {"status": "FakeError"}}

    @dj_test.override_settings(AWS_OPENSEARCH_HOST="http://opensearch.localhost:9200")
    def test_with_index_query_params_positive_scenario(self, mocker, test_app):

        mocked_exists_index = mocker.patch(
            "clients.opensearch.OpenSearchClient.exists_index", return_value=True
        )
        mocked_multi_search = mocker.patch(
            "clients.opensearch.OpenSearchClient.multi_search",
            return_value=(True, {"status": "FakeOkay"}),
        )

        response = test_app.get(self.uri, QUERY_STRING="index=FakeIndexA,FakeIndexB")

        assert response.json() == {"status": "FakeOkay"}
        assert mocked_exists_index.call_args_list == [
            mocker.call("FakeIndexA"),
            mocker.call("FakeIndexB"),
        ]
        mocked_multi_search.assert_called_once_with(
            index=["FakeIndexA", "FakeIndexB"],
            query_type=[QueryTypeEnum.MATCH_ALL, QueryTypeEnum.MATCH_ALL],
            query_parameters=[
                {"kwargs": {"_source": True}},
                {"kwargs": {"_source": True}},
            ],
        )

    @dj_test.override_settings(AWS_OPENSEARCH_HOST="http://opensearch.localhost:9200")
    def test_with_include_source_query_params_positive_scenario(self, mocker, test_app):

        mocker.patch("clients.opensearch.OpenSearchClient.exists_index", return_value=True)
        mocked_multi_search = mocker.patch(
            "clients.opensearch.OpenSearchClient.multi_search",
            return_value=(True, {"status": "FakeOkay"}),
        )

        test_app.get(
            self.uri,
            QUERY_STRING="index=FakeIndexA,FakeIndexB&include_source=false",
        )

        mocked_multi_search.assert_called_once_with(
            index=["FakeIndexA", "FakeIndexB"],
            query_type=[QueryTypeEnum.MATCH_ALL, QueryTypeEnum.MATCH_ALL],
            query_parameters=[
                {"kwargs": {"_source": False}},
                {"kwargs": {"_source": False}},
            ],
        )


class TestPolygonsDocumentsPost:
    uri = reverse("PolygonsDocumentsPost")

    def test_unauthorized_positive_scenario(self, test_app_unauthorized):
        response = test_app_unauthorized.post(self.uri)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in response.json()

    @dj_test.override_settings(AWS_OPENSEARCH_HOST="http://opensearch.localhost:9200")
    def test_get_one_document_positive_scenario(self, mocker, test_app):
        mocker.patch(
            "geo_search_api.api.polygons.serializers.PolygonsDocumentsPostResponseSerializer.to_representation",
            return_value={"FakeIndex": []},
        )
        mocked_exists_index = mocker.patch(
            "clients.opensearch.OpenSearchClient.exists_index", return_value=True
        )
        mocked_multi_search = mocker.patch(
            "clients.opensearch.OpenSearchClient.multi_search",
            return_value=(True, {"FakeIndex": []}),
        )

        response = test_app.post(
            self.uri, [{"index": "FakeIndex", "document_ids": ["DocId"]}], format="json"
        )

        assert response.json() == {"FakeIndex": []}
        assert mocked_exists_index.call_args_list == [
            mocker.call("FakeIndex"),
        ]
        mocked_multi_search.assert_called_once_with(
            index=["FakeIndex"],
            query_type=[QueryTypeEnum.IDS],
            query_parameters=[{"values": ["DocId"]}],
        )

    @dj_test.override_settings(AWS_OPENSEARCH_HOST="http://opensearch.localhost:9200")
    def test_get_bunch_of_documents_positive_scenario(self, mocker, test_app):
        mocker.patch(
            "geo_search_api.api.polygons.serializers.PolygonsDocumentsPostResponseSerializer.to_representation",
            return_value={"FakeIndex": []},
        )
        mocked_exists_index = mocker.patch(
            "clients.opensearch.OpenSearchClient.exists_index", return_value=True
        )
        mocked_multi_search = mocker.patch(
            "clients.opensearch.OpenSearchClient.multi_search",
            return_value=(True, {"FakeIndex": []}),
        )

        body = [
            {"index": "FakeIndexA", "document_ids": ["DocId1"]},
            {"index": "FakeIndexB", "document_ids": ["DocId2"]},
        ]
        response = test_app.post(self.uri, body, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert mocked_exists_index.call_args_list == [
            mocker.call("FakeIndexA"),
            mocker.call("FakeIndexB"),
        ]
        mocked_multi_search.assert_called_once_with(
            index=["FakeIndexA", "FakeIndexB"],
            query_type=[QueryTypeEnum.IDS, QueryTypeEnum.IDS],
            query_parameters=[{"values": ["DocId1"]}, {"values": ["DocId2"]}],
        )

    @dj_test.override_settings(AWS_OPENSEARCH_HOST="http://opensearch.localhost:9200")
    def test_get_document_fails_when_wrong_json_body(self, mocker, test_app):
        mocker.patch(
            "geo_search_api.api.polygons.serializers.PolygonsDocumentsPostResponseSerializer.to_representation",
            return_value={"FakeIndexA": []},
        )

        response = test_app.post(
            self.uri, [{"wrong": "WrongIndex", "break": ["WrongDocId"]}], format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()[0] == {
            "index": ["This field is required."],
            "document_ids": ["This field is required."],
        }

    @dj_test.override_settings(AWS_OPENSEARCH_HOST="http://opensearch.localhost:9200")
    def test_get_document_fails_when_index_not_exist(self, mocker, test_app):
        mocker.patch(
            "geo_search_api.api.polygons.serializers.PolygonsDocumentsPostResponseSerializer.to_representation",
            return_value={"FakeIndexA": []},
        )
        mocked_exists_index = mocker.patch(
            "clients.opensearch.OpenSearchClient.exists_index", return_value=False
        )
        mocked_multi_search = mocker.patch(
            "clients.opensearch.OpenSearchClient.multi_search",
            return_value=(True, {"FakeIndexA": []}),
        )

        response = test_app.post(
            self.uri, [{"index": "FakeIndexA", "document_ids": ["DocId"]}], format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()[0] == {"index": ["The index `FakeIndexA` does not exists."]}
        assert mocked_exists_index.call_count == 1
        mocked_multi_search.assert_not_called()
