import stringcase
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer

from django import conf
from django.utils import module_loading

from geo_search_api.api.serializers import BaseListSerializer
from geo_search_api.apps.likes.models import Like
from geo_search_api.api.notes.swagger_examples import paginated_likes_sum_up_example


class LikesConfigurationSerializers(serializers.Serializer):  # pylint: disable=W0223
    object_types = serializers.ListSerializer(child=serializers.CharField())


class LikeObjectSpecificationSerializer(serializers.Serializer):  # pylint: disable=W0223

    object_id = serializers.UUIDField(required=True)
    object_type = serializers.CharField(required=True)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        try:
            attrs["object_type"] = self._to_capitalcase(attrs["object_type"])
            object_type = conf.settings.LIKES_OBJECT_TYPES[attrs["object_type"]]
            # Check if the object type is importable
            module_loading.import_string(object_type)
        except KeyError as exc:
            raise serializers.ValidationError(
                {"object_type": "Unsupported the object type"}
            ) from exc
        except ImportError as exc:
            raise serializers.ValidationError(
                {"object_type": "Wrong the object import path"}
            ) from exc
        return attrs

    def _to_capitalcase(self, string: str):
        return stringcase.capitalcase(stringcase.camelcase(string.replace("-", "_")))


class LikeGetSerializer(serializers.ModelSerializer):
    class Meta:
        fields = (
            "user_id",
            "created_at",
        )
        model = Like


class LikesListSerializer(BaseListSerializer):  # pylint: disable=W0223
    results = serializers.ListSerializer(child=LikeGetSerializer(), read_only=True)
    is_current_user_liked = serializers.BooleanField(read_only=True)


@extend_schema_serializer(examples=[paginated_likes_sum_up_example])
class LikesSumUpSerializer(serializers.Serializer):  # pylint: disable=W0223
    count = serializers.IntegerField(read_only=True, help_text="The total number of the likes.")
    is_current_user_liked = serializers.BooleanField(read_only=True)
    results = LikeGetSerializer(
        many=True, read_only=True, allow_null=True, help_text="The most recent like of the object."
    )
