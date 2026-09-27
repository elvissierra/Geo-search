from rest_framework import serializers

from geo_search_api.api.serializers import BaseListSerializer
from geo_search_api.apps.topics.models import Topic, TopicTypes, TopicTag, TopicStage


class TopicTagCreateSerializer(serializers.ModelSerializer):
    class Meta:
        exclude = ("id",)
        model = TopicTag


class TopicTagGetSerializer(serializers.ModelSerializer):
    class Meta:
        fields = "__all__"
        model = TopicTag


class TopicTagUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        exclude = ("id",)
        model = TopicTag


class TopicTagDeleteSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ("id",)
        model = TopicTag


class TopicStageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        exclude = ("id",)
        model = TopicStage


class TopicStageGetSerializer(serializers.ModelSerializer):
    class Meta:
        fields = "__all__"
        model = TopicStage


class TopicStageUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        exclude = ("id",)
        model = TopicStage


class TopicStageDeleteSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ("id",)
        model = TopicStage


class TopicCreateSerializer(serializers.ModelSerializer):
    class Meta:
        exclude = (
            "id",
            "owner",
        )
        model = Topic


class TopicGetSerializer(serializers.ModelSerializer):
    stage_name = serializers.CharField(read_only=True)
    tags = TopicTagGetSerializer(many=True)
    contributors_count = serializers.IntegerField(read_only=True)
    ideas_count = serializers.IntegerField(read_only=True)

    class Meta:
        exclude = ("stage",)
        model = Topic


class TopicUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        exclude = ("id", "owner", "created_at", "updated_at")
        model = Topic


class TopicDeleteSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ("id",)
        model = Topic


class TopicsListSerializer(BaseListSerializer):  # pylint: disable=W0223
    results = serializers.ListSerializer(child=TopicGetSerializer(), read_only=True)


class TopicsListQuerySerializer(serializers.Serializer):  # pylint: disable=W0223
    topic_type = serializers.ChoiceField(TopicTypes, required=False)


class TopicTagsListSerializer(BaseListSerializer):  # pylint: disable=W0223
    results = serializers.ListSerializer(child=TopicTagGetSerializer(), read_only=True)


class TopicStagesListSerializer(BaseListSerializer):  # pylint: disable=W0223
    results = serializers.ListSerializer(child=TopicStageGetSerializer(), read_only=True)
