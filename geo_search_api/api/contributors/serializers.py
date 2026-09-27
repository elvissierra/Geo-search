from rest_framework import serializers
from geo_search_api.apps.contributors.models import Contributor, ContributorStatus


class ContributorCreateSerializer(serializers.ModelSerializer):
    class Meta:
        exclude = ("id",)
        model = Contributor


class ContributorsGetSerializer(serializers.ModelSerializer):
    class Meta:
        fields = "__all__"
        model = Contributor


class ContributorUpdateSerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(ContributorStatus, required=True)

    class Meta:
        fields = ("status", "prize")
        model = Contributor


class ContributorDeleteSerializer(serializers.ModelSerializer):
    class Meta:
        fields = "__all__"
        model = Contributor


class ContributorsListQuerySerializer(serializers.Serializer):  # pylint: disable=W0223
    status = serializers.ChoiceField(ContributorStatus, required=False)
