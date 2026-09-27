import pytest

from django import test as dj_test
from geo_search_api.apps.notes.management.commands import add_basin_index

from tests.test_data import TEST_GEODOC, TEST_INDEX


class TestCreateIndex:
    basin_file = "tests/test_shapefile.txt"
    bad_file = "tests/test_bad_shapefile.txt"

    @dj_test.override_settings(AWS_OPENSEARCH_HOST="http://opensearch.localhost:9200")
    def test_command_positive_scenario(self, mock_os_client_for_index_command):
        command = add_basin_index.Command()
        command.handle(TEST_INDEX, filepath=self.basin_file)
        mock_os_client_for_index_command.exists_index.assert_called_once_with(TEST_INDEX)
        mock_os_client_for_index_command.create_index.assert_not_called()
        mock_os_client_for_index_command.bulk.assert_called_once_with(TEST_GEODOC)

    @dj_test.override_settings(AWS_OPENSEARCH_HOST="http://opensearch.localhost:9200")
    def test_command_no_file_path_positive_scenario(self, mock_os_client_for_index_command):
        mock_os_client_for_index_command.exists_index.return_value = True
        command = add_basin_index.Command()
        command.handle(TEST_INDEX)
        mock_os_client_for_index_command.exists_index.assert_called_once_with(TEST_INDEX)
        mock_os_client_for_index_command.create_index.assert_not_called()
        mock_os_client_for_index_command.bulk.assert_called()

    @dj_test.override_settings(AWS_OPENSEARCH_HOST="http://opensearch.localhost:9200")
    def test_command_bad_file_path_negative_scenario(self, mock_os_client_for_index_command):
        mock_os_client_for_index_command.exists_index.return_value = True
        with pytest.raises(FileNotFoundError):
            command = add_basin_index.Command()
            command.handle(TEST_INDEX, filepath="non_existent.txt")

    @dj_test.override_settings(AWS_OPENSEARCH_HOST="http://opensearch.localhost:9200")
    def test_command_create_index_positive_scenario(self, mock_os_client_for_index_command):
        mock_os_client_for_index_command.exists_index.return_value = False
        command = add_basin_index.Command()
        command.handle(TEST_INDEX, filepath=self.basin_file)
        mock_os_client_for_index_command.exists_index.assert_called_once_with(TEST_INDEX)
        mock_os_client_for_index_command.create_index.assert_called_once_with(
            index_name=TEST_INDEX,
            index_settings={"mappings": {"properties": {"geometry": {"type": "geo_shape"}}}},
        )
        mock_os_client_for_index_command.bulk.assert_called_once_with(TEST_GEODOC)

    @dj_test.override_settings(AWS_OPENSEARCH_HOST="http://opensearch.localhost:9200")
    def test_command_negative_scenario(self, mock_os_client_for_index_command):
        mock_os_client_for_index_command.bulk.return_value = (False, {"bad": "bulk statement"})
        command = add_basin_index.Command()
        res = command.handle(TEST_INDEX)
        mock_os_client_for_index_command.exists_index.assert_called_once_with(TEST_INDEX)
        assert res == {"bad": "bulk statement"}
