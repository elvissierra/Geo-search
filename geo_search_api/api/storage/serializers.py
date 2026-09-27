from rest_framework import serializers


class PresignedURLSerializer(serializers.Serializer):  # pylint: disable=W0223
    original_url = serializers.CharField()
    presigned_url = serializers.CharField()


class FilePathsSerializer(serializers.Serializer):  # pylint: disable=W0223
    file_paths = serializers.ListField(required=False)
