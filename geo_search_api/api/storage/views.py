from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from botocore.exceptions import BotoCoreError
from drf_spectacular.utils import extend_schema
from drf_spectacular.openapi import OpenApiResponse
from geo_search_api.api.storage.serializers import (
    FilePathsSerializer,
    PresignedURLSerializer,
)
from geo_search_api.api.storage.swagger_examples import post_presigned_url_example
from clients.s3client import S3Client


class StorageGetView(APIView):
    @staticmethod
    def get(request, bucket_name: str, file_path: str):
        """
        Get request to check connection
        """

        storage_client = S3Client()
        try:
            url = storage_client.get_presigned_url(file_location=file_path, bucket_name=bucket_name)
        except BotoCoreError:
            return Response({"errors": "Bad request"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"data": dict(url=url)}, status=status.HTTP_200_OK)


class StoragePostView(APIView):
    @staticmethod
    @extend_schema(
        parameters=[FilePathsSerializer],
        request=FilePathsSerializer,
        responses={
            201: "Ok",
            400: OpenApiResponse(description="Bad Request"),
            401: OpenApiResponse(description="Unauthorized"),
        },
        examples=[post_presigned_url_example],
    )
    def post(request, bucket_name: str):
        """
        Post request for batch presigned urls
        """
        storage_client = S3Client()
        serializer = FilePathsSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        file_paths = serializer.validated_data.get("file_paths", [])
        urls = []
        for file_path in file_paths:
            try:
                url = storage_client.get_presigned_url(
                    file_location=file_path, bucket_name=bucket_name
                )
                urls.append(
                    {
                        "original_url": file_path,
                        "presigned_url": url,
                    }
                )
            except BotoCoreError:
                return Response({"error": "Bad request"}, status=status.HTTP_400_BAD_REQUEST)

        response_data = PresignedURLSerializer(urls, many=True).data
        return Response({"data": response_data}, status=status.HTTP_200_OK)
