import re
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from drf_spectacular.utils import extend_schema_serializer

from geo_search_api.apps.ideas.models import Idea, IdeaStatuses
from geo_search_api.api.ideas.utils import get_possible_idea_statuses
from geo_search_api.api.serializers import BaseListSerializer
from geo_search_api.api.likes.serializers import LikesSumUpSerializer


@extend_schema_serializer(exclude_fields=("owner",))
class IdeaCreateSerializer(serializers.ModelSerializer):
    class Meta:
        exclude = (
            "id",
            "status",
            "is_trending",
            "engagement_rate",
            "created_at",
            "updated_at",
        )
        model = Idea


class IdeaGetSerializer(serializers.ModelSerializer):
    comments_count = serializers.IntegerField(read_only=True)
    likes_count = serializers.IntegerField(read_only=True)

    class Meta:
        fields = "__all__"
        model = Idea

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["likes"] = LikesSumUpSerializer(
            instance.get_likes_sum_up(self.context["request"].user["id"])
        ).data
        return data


class IdeaUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        exclude = (
            "id",
            "topic",
            "status",
            "owner",
            "is_trending",
            "engagement_rate",
            "created_at",
            "updated_at",
        )
        model = Idea


class IdeaDeleteSerializer(serializers.ModelSerializer):
    class Meta:
        fields = "__all__"
        model = Idea


class IdeaStatusUpdateSerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(IdeaStatuses, required=True)

    class Meta:
        fields = (
            "id",
            "status",
        )
        model = Idea

    def validate(self, attrs):
        new_status = attrs.get("status")
        status = self.instance.status
        if new_status not in get_possible_idea_statuses(status):
            raise ValidationError(
                f"Wrong status. Current idea status must be changed only "
                f"on {', '.join(get_possible_idea_statuses(status))}."
            )
        return attrs


class IdeasListSerializer(BaseListSerializer):  # pylint: disable=W0223
    results = serializers.ListSerializer(child=IdeaGetSerializer(), read_only=True)


class IdeasListQuerySerializer(serializers.Serializer):  # pylint: disable=W0223

    _sort_attributes = (
        "created_at",
        "updated_at",
        "engagement_rate",
        "is_trending",
    )

    status = serializers.ChoiceField(IdeaStatuses, required=False)
    topic = serializers.UUIDField(required=False)
    owner = serializers.CharField(required=False)
    sort = serializers.CharField(
        required=False,
        help_text=(
            "Attributes are available for sorting: `created_at`, `updated_at`, `engagement_rate`, "
            "`is_trending`. Example: *?order=-engagement_rate,is_trending* hence sorting in "
            "descending order by *engagement_rate* and ascending order by *is_trending*. Default "
            "sorting: **-is_trending,-created_at**"
        ),
    )

    def validate_sort(self, value):
        chunks = value.split(",")
        for _ in chunks:
            if re.sub(r"[^\w]", "", _) not in self._sort_attributes:
                raise ValidationError(
                    f"{_} incorrect attribute for srting. Allowed attributes: "
                    f"{', '.join(self._sort_attributes)}"
                )
        return chunks
