import json

from django.core.management.base import BaseCommand

from clients.opensearch import OpenSearchClient


class Command(BaseCommand):
    help = "Create Basin Index in Opensearch, Upload Shape file"

    def add_arguments(self, parser):
        parser.add_argument(
            "indexname",
            type=str,
            help="Name to assign to Index.",
        )
        # Optional argument
        parser.add_argument(
            "-f",
            "--filepath",
            type=str,
            help="Option to define path to the Shapefile which will be indexed.",
        )

    def handle(self, *args, **kwargs):

        opensearch_client = OpenSearchClient()  # noqa

        # the file to be converted to json format
        default_index_name = "basin-shape-index"
        default_filepath = "geo_search_api/api/opensearch/data/Global_Basins_Shapefile_052023.txt"
        filepath = kwargs.get("filepath", default_filepath)
        index_name = args[0] if args else default_index_name

        # creating dictionary
        with open(filepath) as fh:
            data = json.load(fh)

        index_body = {
            "mappings": {
                "properties": {
                    "geometry": {"type": "geo_shape"},
                }
            }
        }

        if not opensearch_client.exists_index(index_name):
            opensearch_client.create_index(index_name=index_name, index_settings=index_body)
            self.stdout.write(f"\nindex created: {index_name}\n")
        else:
            self.stdout.write("\nindex already exists\n")

        # make entries to index
        bulk_data = []
        feature_entries = map(adjust_dict, data["features"])

        for i, feature in enumerate(feature_entries):
            bulk_action = {
                "index": {
                    "_index": index_name,
                    "_id": int(i),
                }
            }
            bulk_data.append(bulk_action)
            bulk_data.append(feature)

        # bulk upload formatted items from document
        is_success, response = opensearch_client.bulk(bulk_data)
        if is_success:
            return "Bulk index operation completed successfully."
        return response


def adjust_dict(feature_entry):
    document = feature_entry["properties"]
    del document["layer"], document["Province"]
    document["geometry"] = feature_entry["geometry"]
    return document
