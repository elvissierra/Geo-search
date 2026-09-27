import json

from rest_framework import status
from unittest.mock import patch
from rest_framework.response import Response
from rest_framework.reverse import reverse
from django.conf import settings

from geo_search_api.environments import PossibleEnvironments


from tests.test_data import (
    TEST_DOC_ID,
    TEST_INDEX,
)


class TestOpenSearch:
    COMMON_PAYLOAD = {
        "id": TEST_DOC_ID,
        "document": {"text": "test"},
    }

    @patch("geo_search_api.api.opensearch.views.OpenSearchClient")
    def test_get_positive_scenario(self, opensearch_mock, test_app):
        url = reverse("OpenSearch", (TEST_INDEX,))
        mock_response = Response({"data": {"id": TEST_DOC_ID}}, status.HTTP_200_OK)
        opensearch_mock.return_value.get.return_value = mock_response
        response = test_app.generic(
            method="GET",
            path=url,
            data=json.dumps(self.COMMON_PAYLOAD),
            content_type="application/json",
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["data"]["id"] == TEST_DOC_ID

    @patch("geo_search_api.api.opensearch.views.OpenSearchClient")
    def test_post_positive_scenario(self, opensearch_mock, test_app):
        url = reverse("OpenSearch", (TEST_INDEX,))
        mock_response = Response({"data": {"id": TEST_DOC_ID}}, status.HTTP_200_OK)
        opensearch_mock.return_value.create.return_value = mock_response
        response = test_app.post(url, self.COMMON_PAYLOAD, format="json")
        assert response.status_code == status.HTTP_200_OK

    @patch("geo_search_api.api.opensearch.views.OpenSearchClient")
    def test_put_positive_scenario(self, opensearch_mock, test_app):
        url = reverse("OpenSearch", (TEST_INDEX,))
        mock_response = Response({"data": {"id": TEST_DOC_ID}}, status.HTTP_200_OK)
        opensearch_mock.return_value.update.return_value = mock_response
        response = test_app.put(url, self.COMMON_PAYLOAD, format="json")
        assert response.status_code == status.HTTP_200_OK

    @patch("geo_search_api.api.opensearch.views.OpenSearchClient")
    def test_delete_positive_scenario(self, opensearch_mock, test_app):
        url = reverse("OpenSearch", (TEST_INDEX,))
        mock_response = Response({"data": {"id": TEST_DOC_ID}}, status.HTTP_200_OK)
        opensearch_mock.return_value.delete.return_value = mock_response
        response = test_app.delete(url, self.COMMON_PAYLOAD, format="json")
        assert response.status_code == status.HTTP_200_OK

    @patch("geo_search_api.api.opensearch.views.OpenSearchClient")
    def test_post_negative_scenario(self, opensearch_mock, test_app):
        settings.CURRENT_ENVIRONMENT = PossibleEnvironments.STAGE
        url = reverse("OpenSearch", (TEST_INDEX,))
        # mock_response = Response({"data": {"id": TEST_DOC_ID}}, status.HTTP_405_METHOD_NOT_ALLOWED)
        # opensearch_mock.return_value.create.return_value = mock_response
        # response = test_app.post(url, self.COMMON_PAYLOAD, format="json")
        # assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    @patch("geo_search_api.api.opensearch.views.OpenSearchClient")
    def test_put_negative_scenario(self, opensearch_mock, test_app):
        url = reverse("OpenSearch", (TEST_INDEX,))
        # mock_response = Response({"data": {"id": TEST_DOC_ID}}, status.HTTP_405_METHOD_NOT_ALLOWED)
        # opensearch_mock.return_value.create.return_value = mock_response
        # response = test_app.put(url, self.COMMON_PAYLOAD, format="json")
        # assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    @patch("geo_search_api.api.opensearch.views.OpenSearchClient")
    def test_delete_negative_scenario(self, opensearch_mock, test_app):
        url = reverse("OpenSearch", (TEST_INDEX,))
        # mock_response = Response({"data": {"id": TEST_DOC_ID}}, status.HTTP_405_METHOD_NOT_ALLOWED)
        # opensearch_mock.return_value.create.return_value = mock_response
        # response = test_app.delete(url, self.COMMON_PAYLOAD, format="json")
        # assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    @patch("geo_search_api.api.opensearch.views.OpenSearchClient")
    def test_get_positive_scenario_stage_env(self, opensearch_mock, test_app):
        settings.CURRENT_ENVIRONMENT = PossibleEnvironments.STAGE
        url = reverse("OpenSearch", (TEST_INDEX,))
        mock_response = Response({"data": {"id": TEST_DOC_ID}}, status.HTTP_200_OK)
        opensearch_mock.return_value.get.return_value = mock_response
        response = test_app.generic(
            method="GET",
            path=url,
            data=json.dumps(self.COMMON_PAYLOAD),
            content_type="application/json",
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["data"]["id"] == TEST_DOC_ID
