from unittest.mock import call, patch, Mock
import json

from botocore.exceptions import BotoCoreError
from rest_framework import status
from rest_framework.reverse import reverse

from tests.test_data import (
    TEST_URL,
    TEST_FILE_PATH,
    TEST_FILE_PATHS,
    TEST_BUCKET_NAME,
    TEST_URLS,
)


class TestGetUrl:
    @staticmethod
    @patch(
        "geo_search_api.api.storage.views.S3Client",
        **{"return_value.get_presigned_url.return_value": TEST_URL}
    )
    def test_positive_scenario_for_get(s3_mock, test_app):
        url = reverse(
            "StorageGet",
            (
                TEST_BUCKET_NAME,
                TEST_FILE_PATH,
            ),
        )
        response = test_app.get(url, {"bucket_name": TEST_BUCKET_NAME, "file_path": TEST_FILE_PATH})
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["data"]["url"] == TEST_URL
        s3_mock.assert_called_once()

    @staticmethod
    @patch("geo_search_api.api.storage.views.S3Client")
    def test_negative_scenario_for_get(s3_mock, test_app):
        s3_mock.return_value.get_presigned_url.side_effect = Mock(side_effect=BotoCoreError())
        url = reverse(
            "StorageGet",
            (
                TEST_BUCKET_NAME,
                TEST_FILE_PATH,
            ),
        )
        response = test_app.get(url, {"bucket_name": TEST_BUCKET_NAME, "file_path": TEST_FILE_PATH})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["errors"] == "Bad request"
        s3_mock.assert_called_once()

    @staticmethod
    @patch(
        "geo_search_api.api.storage.views.S3Client",
        **{"return_value.get_presigned_url.side_effect": TEST_URLS}
    )
    def test_positive_scenario_for_post(s3_client, test_app):
        url = reverse(
            "StoragePost",
            args=[TEST_BUCKET_NAME],
        )
        response = test_app.post(
            url,
            data=json.dumps({"file_paths": TEST_FILE_PATHS}),
            content_type="application/json",
        )
        assert response.status_code == status.HTTP_200_OK

        response_urls = [obj["presigned_url"] for obj in response.json()["data"]]
        assert response_urls == TEST_URLS

        assert s3_client.return_value.get_presigned_url.call_count == len(TEST_FILE_PATHS)
        s3_client.return_value.get_presigned_url.assert_has_calls(
            [
                call(file_location=file_path, bucket_name=TEST_BUCKET_NAME)
                for file_path in TEST_FILE_PATHS
            ]
        )

    @staticmethod
    @patch("geo_search_api.api.storage.views.S3Client")
    def test_negative_scenario_for_post(s3_mock, test_app):
        s3_mock.return_value.get_presigned_url.side_effect = BotoCoreError()
        url = reverse("StoragePost", args=[TEST_BUCKET_NAME])
        response = test_app.post(
            url,
            data=json.dumps({"file_paths": TEST_FILE_PATHS}),
            content_type="application/json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        error_message = response.json().get("error")
        assert error_message == "Bad request"
        assert s3_mock.return_value.get_presigned_url.call_count == 1
        s3_mock.return_value.get_presigned_url.assert_called_once_with(
            file_location="data_science/test_file1.las", bucket_name=TEST_BUCKET_NAME
        )
