import base64
import sys
import json
import typing
import abc

import stringcase
from rest_framework import serializers as drf_serializers
from django.conf import settings as dj_settings

from clients.s3client import S3Client, S3Operation
from clients.opensearch import OpenSearchClient, QueryTypeEnum
from geo_search_api.api.serializers import QuerySerializerMixin
from geo_search_api.api.search.constants import DOCUMENT_FIELD_NAME, AUTOCOMPLETE_MAP


class GPSSerializerMixin:
    @staticmethod
    def validate_coordinates(value):
        coordinates = GPSSerializerMixin._get_coordinates(value)
        if not -90 <= coordinates["lat"] <= 90:
            raise drf_serializers.ValidationError(
                "Latitude can have coordinates between -90 and 90 degrees. "
                f"Wrong value: {coordinates['lat']}"
            )
        if not -180 <= coordinates["lon"] <= 180:
            raise drf_serializers.ValidationError(
                "Longitude can have coordinates between -180 and 180 degrees. "
                f"Wrong value: {coordinates['lon']}."
            )
        return coordinates

    @staticmethod
    def _get_coordinates(value):
        coordinates = value.split(",")
        try:
            return {"lat": float(coordinates[0]), "lon": float(coordinates[1])}
        except ValueError:
            raise drf_serializers.ValidationError(
                f"Coordinates should have integer(float) type. Wrong values: {coordinates}."
            )


class PresignedUrlMixin:
    def add_presigned_url(self, hit_data):
        """
        Adds a Base64 encoded presigned URL
        """
        document_path = hit_data.get("_source", {}).get("document_path", None)
        bucket_name = hit_data.get("_source", {}).get("bucket_name", None)

        if document_path and bucket_name:
            s3_client = S3Client()
            presigned_url = s3_client.get_presigned_url(
                file_location=document_path, bucket_name=bucket_name, operation=S3Operation.GET
            )
            base64_encoded_url = base64.b64encode(presigned_url.encode()).decode()

            hit_data.get("_source", {})["encoded_presigned_url"] = base64_encoded_url


class HitsBaseSerializer(PresignedUrlMixin, drf_serializers.Serializer):  # pylint: disable=W0223
    def to_representation(self, instance):
        for hit in instance["hits"]["hits"]:
            serializer_name = "{}HitSerializer".format(
                stringcase.capitalcase(stringcase.camelcase(stringcase.snakecase(hit["_index"])))
            )
            hit_data = getattr(sys.modules[__name__], serializer_name)(
                hit, context={"load_associated_assets": True, **self.context}
            ).data
            self.add_presigned_url(hit_data)

        return instance


class HitBaseSerializer(drf_serializers.Serializer):  # pylint: disable=W0223
    _index = drf_serializers.CharField()
    _id = drf_serializers.CharField()
    _score = drf_serializers.FloatField()
    _source = drf_serializers.DictField()
    _associated = drf_serializers.DictField(required=False)

    @staticmethod
    @abc.abstractmethod
    def get_allowed_associated_with(instance: dict) -> dict:
        raise NotImplementedError

    def to_representation(self, instance):
        associated_from_client = self.context.get("associated")
        if not associated_from_client:
            return instance
        if isinstance(associated_from_client, str):
            associated_from_client = associated_from_client.split()

        allowed_associated_with = self.get_allowed_associated_with(instance)
        final_indexes = [
            _ for _ in set(associated_from_client) if _ in allowed_associated_with.keys()
        ]
        if not final_indexes:
            return instance
        final_indexes.sort()

        query_type = []
        query_parameters = []
        for _ in final_indexes:
            for keys, values in allowed_associated_with[_].items():
                query_type.append(keys)
                query_parameters.append(values)

        self._load_associated(instance, final_indexes, query_type, *query_parameters)

        return instance

    def _load_associated(
        self,
        instance: dict,
        indexes: typing.List[str],
        query_type: typing.List[QueryTypeEnum],
        *query_parameters,
    ):

        if not self.context.get("load_associated_assets", False):
            return

        _, associated = OpenSearchClient().multi_search(
            index=indexes,
            query_type=query_type,
            query_parameters=list(query_parameters),
        )

        for i, index in enumerate(indexes):
            instance.setdefault("_associated", {}).update(
                {index: associated["responses"][i]["hits"]["hits"]}
            )


class BasinShapeIndexHitSerializer(HitBaseSerializer):
    @staticmethod
    def get_allowed_associated_with(instance: dict) -> dict:
        name, allowed = instance["_source"]["Name"], {}
        # It can be `None` or empty string
        if name:
            allowed.update(
                {
                    "document_location": {
                        QueryTypeEnum.TERM: {"field": "basin.keyword", "value": name}
                    },
                    "wells_ontology": {
                        QueryTypeEnum.TERM: {"field": "basin.keyword", "value": name}
                    },
                }
            )
        return allowed


class WellsOntologyHitSerializer(HitBaseSerializer):
    @staticmethod
    def get_allowed_associated_with(instance: dict) -> dict:
        basin, well_name, allowed = (
            instance["_source"]["basin"],
            instance["_source"]["well_name"],
            {},
        )

        if basin:
            allowed.update(
                {
                    "basin-shape-index": {
                        QueryTypeEnum.TERM: {"field": "Name.keyword", "value": basin}
                    }
                }
            )

        if well_name:
            allowed.update(
                {
                    "document_location": {
                        QueryTypeEnum.TERM: {"field": "well_name.keyword", "value": well_name}
                    },
                    "las_files": {
                        QueryTypeEnum.BOOL: {
                            "should": [
                                {
                                    QueryTypeEnum.TERM: {
                                        "field": "well_name.keyword",
                                        "value": well_name,
                                    }
                                },
                                {
                                    QueryTypeEnum.TERM: {
                                        "field": "extracted_well_name.keyword",
                                        "value": {"value": well_name, "case_insensitive": True},
                                    }
                                },
                            ]
                        }
                    },
                }
            )
        return allowed


class LasFilesHitSerializer(HitBaseSerializer):
    @staticmethod
    def get_allowed_associated_with(instance: dict) -> dict:
        well_name, extracted_well_name, allowed, should = (
            instance["_source"]["well_name"],
            instance["_source"]["extracted_well_name"],
            {},
            [],
        )

        if well_name:
            should.append({QueryTypeEnum.TERM: {"field": "well_name.keyword", "value": well_name}})

        if extracted_well_name:
            should.append(
                {
                    QueryTypeEnum.TERM: {
                        "field": "well_name.keyword",
                        "value": {"value": extracted_well_name, "case_insensitive": True},
                    }
                }
            )

        if should:
            allowed.update({"wells_ontology": {QueryTypeEnum.BOOL: {"should": should}}})

        return allowed


class DocumentLocationHitSerializer(HitBaseSerializer):
    @staticmethod
    def get_allowed_associated_with(instance: dict) -> dict:
        basin, well_name, allowed = (
            instance["_source"]["basin"],
            instance["_source"]["well_name"],
            {},
        )

        if basin:
            allowed.update(
                {
                    "basin-shape-index": {
                        QueryTypeEnum.TERM: {"field": "Name.keyword", "value": basin}
                    }
                }
            )

        if well_name:
            allowed.update(
                {
                    "wells_ontology": {
                        QueryTypeEnum.TERM: {"field": "well_name.keyword", "value": well_name}
                    }
                }
            )

        return allowed


class SearchQuerySerializer(
    drf_serializers.Serializer, QuerySerializerMixin
):  # pylint: disable=W0223
    index = drf_serializers.CharField(
        required=False,
        help_text=(
            "Name of the index. *If you did not specify the name of the index, the search will "
            "be performed on all existing indexes.*"
        ),
    )
    size = drf_serializers.IntegerField(
        min_value=-1,
        required=False,
        help_text=(
            "How many results to include in the response. By default it returns all entries from "
            "the index."
        ),
    )
    query_type = drf_serializers.ChoiceField(
        QueryTypeEnum.choices(),
        required=False,
        help_text=(
            "You can find more information about query types here "
            "[Query DSL](https://opensearch.org/docs/latest/query-dsl/)."
        ),
    )
    query_parameters = drf_serializers.CharField(
        required=False,
        help_text=(
            "Each query type has its own unique set of parameters that are necessary for the "
            "successful execution of the request: "
            "[SIMPLE_QUERY_STRING](https://opensearch.org/docs/latest/query-dsl/full-text/"
            "#simple-query-string) **Note: the value should to be a valid JSON string.** "
            'Example: *?query_parameters={"query": "a", "fields": ["attr-a"]}*'
        ),
    )
    associated = drf_serializers.CharField(
        required=False,
        help_text=(
            "Comma-separated the list of index from which need to load the associated objects."
        ),
    )

    @staticmethod
    def validate_query_type(value):
        return QueryTypeEnum[value]

    @staticmethod
    def validate_query_parameters(value):
        try:
            return json.loads(value)
        except json.decoder.JSONDecodeError:
            raise drf_serializers.ValidationError("The values is not a valid JSON string.")

    def validate_associated(self, value):
        return super().validate_index(value)


class SearchDataScapeAutocompleteQuerySerializer(
    drf_serializers.Serializer
):  # pylint: disable=W0223
    query = drf_serializers.CharField(required=True, min_length=2)
    size = drf_serializers.IntegerField(
        min_value=1,
        max_value=dj_settings.MAX_SEARCHING_SIZE,
        default=3,
        help_text="The number of suggestions per index.",
    )


class SearchDataScapeAutocompleteResponseSerializer(
    drf_serializers.Serializer
):  # pylint: disable=W0223
    def to_representation(self, instance):
        representation, instance_location = {}, -1
        for index, fields in AUTOCOMPLETE_MAP.items():
            representation.setdefault(index, {"suggestions": []})
            for field in map(lambda x: x.replace(".keyword", ""), fields):
                instance_location += 1
                options = instance["responses"][instance_location]["hits"]["hits"]
                for o in options:
                    if len(representation[index]["suggestions"]) >= self.context.get(
                        "size_per_index"
                    ):
                        break

                    try:
                        if o["_source"][field] not in representation[index]["suggestions"]:
                            representation[index]["suggestions"].append(o["_source"][field])
                    except KeyError:
                        pass

        return representation


class SearchDataScapeMultiQuerySerializer(
    drf_serializers.Serializer, QuerySerializerMixin
):  # pylint: disable=W0223
    index = drf_serializers.CharField(
        required=False,
        help_text=(
            "Name of the index. *If you did not specify the name of the index, the search will "
            "be performed on all existing indexes.*"
        ),
        default="basin-shape-index,wells_ontology,las_files,document_location",
    )
    size = drf_serializers.IntegerField(
        min_value=-1,
        max_value=dj_settings.MAX_SEARCHING_SIZE,
        default=dj_settings.MAX_SEARCHING_SIZE,
        required=False,
        help_text=(
            "How many results to include in the response. By default it returns all entries from "
            "the index."
        ),
    )
    query = drf_serializers.CharField(
        required=True,
        help_text="The query to search.",
        min_length=2,
    )


class SearchDataScapeMultiResponseSerializer(
    PresignedUrlMixin, drf_serializers.Serializer
):  # pylint: disable=W0223
    def to_representation(self, instance):
        representation = {}
        indexes = self.context.get("q_params").get("index")
        for i, index in enumerate(indexes if isinstance(indexes, list) else [indexes]):
            _response = instance.get("responses")[i]
            hits = _response.get("hits").get("hits")
            for hit in hits:
                self.add_presigned_url(hit)
            representation.update({index: hits})

        return representation

    def map_document(self, document: typing.List[dict]):
        document["highlight"] = {
            name.replace(f".{DOCUMENT_FIELD_NAME}", ""): val
            for name, val in document["highlight"].items()
        }
        return document


class SearchResponseSerializer(HitsBaseSerializer):
    pass


class SearchInBoundingBoxQuerySerializer(  # pylint: disable=W0223
    drf_serializers.Serializer, QuerySerializerMixin, GPSSerializerMixin
):
    index = drf_serializers.CharField(required=True, help_text=("Name of the index."))

    top_left = drf_serializers.CharField(
        required=False,
        help_text="It allows to specify the top left bound coordinate.",
        default="90,-180",
    )
    bottom_right = drf_serializers.CharField(
        required=False,
        help_text="It allows to specify the bottom right bound coordinate.",
        default="-90,180",
    )

    def validate_index(self, value):
        return super().validate_index(value)

    @staticmethod
    def validate_top_left(value):
        return GPSSerializerMixin.validate_coordinates(value)

    @staticmethod
    def validate_bottom_right(value):
        return GPSSerializerMixin.validate_coordinates(value)


class SearchDataScapeClustersQuerySerializer(
    SearchInBoundingBoxQuerySerializer
):  # pylint: disable=W0223
    index = drf_serializers.CharField(
        required=False,
        help_text=(
            "It allows to specify the name of the index or comma-separated the name of indexes "
            "for which need to perform the search."
        ),
        default="wells_ontology,las_files,document_location",
    )
    precision = drf_serializers.IntegerField(default=1)

    def validate_index(self, value):
        value = super().validate_index(value)
        return value if isinstance(value, list) else [value]

    @staticmethod
    def validate_precision(value):
        if not 1 <= value <= 12:
            raise drf_serializers.ValidationError(
                f"precision parameter should be more than 0 and less or equals to 12. "
                f"Wrong value: {value}."
            )
        return value


class SearchDataScapeDocumentsPostSerializer(
    drf_serializers.Serializer,
    QuerySerializerMixin,
):  # pylint: disable=W0223
    index = drf_serializers.CharField(
        required=True, help_text="Index name which will be used in searching."
    )
    document_ids = drf_serializers.ListField(
        required=True,
        child=drf_serializers.CharField(),
        help_text="Array with document ids that should be found.",
    )
    associated = drf_serializers.CharField(
        required=False,
        help_text=(
            "Comma-separated the list of index from which need to load the associated objects."
        ),
    )

    def validate_associated(self, value):
        return super().validate_index(value)


class SearchDataScapeClustersSerializer(
    PresignedUrlMixin, drf_serializers.BaseSerializer
):  # pylint: disable=W0223
    @staticmethod
    def _generate_cluster_response(geo_bounding_box_response):
        return {
            "doc_count": geo_bounding_box_response["doc_count"],
            "document_ids": [
                _id["key"] for _id in geo_bounding_box_response["document_ids"]["buckets"]
            ],
            "asset_location": {
                "coordinates": [
                    geo_bounding_box_response["cluster_coordinates"]["location"]["lat"],
                    geo_bounding_box_response["cluster_coordinates"]["location"]["lon"],
                ],
                "type": "point",
            },
        }

    def to_representation(self, instance):

        representation = {}
        for count, value in enumerate(self.context["q_params"]["index"]):
            representation.update(
                {
                    value: map(
                        self._generate_cluster_response,
                        instance["responses"][count]["aggregations"]["clusters"]["buckets"],
                    ),
                }
            )
        for value in representation:
            processed_clusters = []
            for cluster in representation[value]:
                for doc in cluster.get("documents", []):
                    self.add_presigned_url(doc)
                processed_clusters.append(cluster)
            representation[value] = processed_clusters

        return representation


class SearchDataScapeDocumentsPointsSerializer(
    drf_serializers.BaseSerializer
):  # pylint: disable=W0223
    def to_representation(self, instance):
        documents = [
            {
                "document_id": document["_id"],
                "asset_location": document["_source"]["asset_location"],
            }
            for document in instance
        ]
        return {self.context["q_params"]["index"]: documents}


class SearchDataScapeDocumentsSerializer(HitsBaseSerializer):
    def to_representation(self, instance):
        representation = {}
        for count, value in enumerate(self.context["request_body"]):
            self.context.update({"associated": value.get("associated")})
            representation.update(
                {value["index"]: super().to_representation(instance[count])["hits"]["hits"]}
            )
        return representation
