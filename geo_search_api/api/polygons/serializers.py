from rest_framework import serializers as drf_serializers

from geo_search_api.api.serializers import QuerySerializerMixin


class PolygonsGetQuerySerializer(
    drf_serializers.Serializer,
    QuerySerializerMixin,
):  # pylint: disable=W0223

    index = drf_serializers.CharField(
        required=True,
        help_text=(
            "Comma-separated list of the index names for which it requires to retrieve polygons."
        ),
    )
    include_source = drf_serializers.BooleanField(
        required=False, default=True, help_text="Defines if to return the document’s source."
    )
    size = drf_serializers.IntegerField(
        min_value=-1,
        required=False,
        help_text=(
            "How many results to include in the response. By default it returns all entries from "
            "the index."
        ),
    )

    def validate_index(self, value):
        v = super().validate_index(value)
        return [v] if isinstance(v, str) else v


class PolygonsDocumentsPostRequestSerializer(
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


class PolygonsDocumentsPostResponseSerializer(
    drf_serializers.BaseSerializer
):  # pylint: disable=W0223
    def to_representation(self, instance):

        representation = {}
        for i, index in enumerate(self.context.get("indexes")):
            representation.update({index: instance.get("responses")[i].get("hits").get("hits")})

        return representation
