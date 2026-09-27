from rest_framework import serializers as drf_serializers
from clients.opensearch import OpenSearchClient


class QuerySerializerMixin:
    def validate_index(self, value):

        v = value.split(",")
        opensearch = OpenSearchClient()

        for _ in v:
            if not opensearch.exists_index(_):
                raise drf_serializers.ValidationError(f"The index `{_}` does not exists.")

        return value if len(v) == 1 else v


class BaseListSerializer(drf_serializers.Serializer):  # pylint: disable=W0223

    next = drf_serializers.BooleanField(read_only=True)
    previous = drf_serializers.BooleanField(read_only=True)
    count = drf_serializers.IntegerField(read_only=True)
    total_pages = drf_serializers.IntegerField(read_only=True)


class BasePaginationQuerySerializer(drf_serializers.Serializer):  # pylint: disable=W0223
    page_size = drf_serializers.IntegerField(required=False, min_value=1)
    page = drf_serializers.IntegerField(required=False, min_value=1)
