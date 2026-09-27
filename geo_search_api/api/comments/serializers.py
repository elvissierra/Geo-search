import stringcase
from rest_framework import serializers as drf_serializers
from rest_framework import exceptions as drf_exceptions
from drf_spectacular.utils import extend_schema_serializer

from django import conf
from django.utils import module_loading

from geo_search_api.api.serializers import BaseListSerializer
from geo_search_api.api.likes.serializers import LikesSumUpSerializer
from geo_search_api.apps.comments.models import Comment
from geo_search_api.api.comments.swagger_examples import comment_example


class CommentsConfigurationSerializers(drf_serializers.Serializer):  # pylint: disable=W0223
    object_types = drf_serializers.ListSerializer(child=drf_serializers.CharField())


class CommentObjectSpecificationSerializer(drf_serializers.Serializer):  # pylint: disable=W0223

    object_id = drf_serializers.UUIDField(required=True)
    object_type = drf_serializers.CharField(required=True)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        try:
            attrs["object_type"] = self._to_capitalcase(attrs["object_type"])
            object_type = conf.settings.COMMENTS_OBJECT_TYPES[attrs["object_type"]]
            # Check if the object type is importable
            module_loading.import_string(object_type)
        except KeyError as exc:
            raise drf_serializers.ValidationError(
                {"object_type": "Unsupported the object type"}
            ) from exc
        except ImportError as exc:
            raise drf_serializers.ValidationError(
                {"object_type": "Wrong the object import path"}
            ) from exc
        return attrs

    def _to_capitalcase(self, string: str):
        return stringcase.capitalcase(stringcase.camelcase(string.replace("-", "_")))


@extend_schema_serializer(examples=[comment_example])
class CommentGetSerializer(drf_serializers.ModelSerializer):
    class Meta:
        fields = "__all__"
        model = Comment

    def validate(self, attrs):
        parent_comment = attrs.get("parent_id")
        if parent_comment:
            if parent_comment.object_id != attrs["object_id"]:
                raise drf_exceptions.ValidationError(
                    {"object_id": "Parent comment and reply should have the same object id."}
                )
        return attrs

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["likes"] = LikesSumUpSerializer(
            instance.get_likes_sum_up(self.context["request"].user["id"])
        ).data
        if data["id"] is not None:
            replies = Comment.objects.filter(parent_id=data["id"]).all()
            data["replies"] = CommentGetSerializer(replies, many=True, context=self.context).data
        return data


class CommentUpdateSerializer(drf_serializers.ModelSerializer):
    class Meta:
        exclude = ("id", "owner", "parent_id", "object_id", "object_type")
        model = Comment


class CommentCreateSerializer(drf_serializers.ModelSerializer):
    class Meta:
        fields = (
            "parent_id",
            "content",
        )
        model = Comment


class CommentDeleteSerializer(drf_serializers.ModelSerializer):
    class Meta:
        fields = ("id",)
        model = Comment


class CommentListSerializer(BaseListSerializer):  # pylint: disable=W0223
    results = drf_serializers.ListSerializer(child=CommentGetSerializer(), read_only=True)
