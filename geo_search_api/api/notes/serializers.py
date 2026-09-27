from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer

from geo_search_api.api.likes.serializers import LikesSumUpSerializer
from geo_search_api.apps.notes.models import Note, NoteTypes
from geo_search_api.api.notes.swagger_examples import note_example


@extend_schema_serializer(examples=[note_example])
class NoteSerializer(serializers.ModelSerializer):
    comments_count = serializers.IntegerField(read_only=True)

    class Meta:
        fields = "__all__"
        model = Note

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["likes"] = LikesSumUpSerializer(
            instance.get_likes_sum_up(self.context["request"].user["id"])
        ).data
        return data


class NoteUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        exclude = ("id", "owner", "category")
        model = Note


class CreateNoteSerializer(serializers.Serializer):  # pylint: disable=W0223
    category = serializers.ChoiceField(NoteTypes.choices)
    content = serializers.CharField()


class PaginationQuerySerializer(serializers.Serializer):  # pylint: disable=W0223
    page_size = serializers.IntegerField(required=False)
    page = serializers.IntegerField(required=False)


class GetNotesQuerySerializer(serializers.Serializer):  # pylint: disable=W0223
    category = serializers.CharField(required=False)
    owner = serializers.CharField(required=False)
