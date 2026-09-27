import stringcase
from rest_framework import views as drf_views
from rest_framework import response as drf_response
from rest_framework import status as drf_status
from drf_spectacular.utils import extend_schema
from drf_spectacular.openapi import OpenApiResponse

from django import conf
from django.db import transaction
from django.utils import module_loading
from django.shortcuts import get_object_or_404
from geo_search_api.apps.comments.models import Comment
from geo_search_api.api.permissions import IsCommentOwner, RESTRICTED_STAGES
from geo_search_api.api.serializers import BasePaginationQuerySerializer
from geo_search_api.api.comments import serializers
from geo_search_api.api.comments import paginators
from geo_search_api.api.comments.swagger_examples import paginated_comments_example


class CommentAPIView(drf_views.APIView):
    """
    Base Comment API view
    """

    def __init__(self, **kwargs):
        """
        Initialization of CommentAPIView
        """
        super().__init__(**kwargs)
        self._object = None
        self._object_specification = None

    def method(self, request, object_type, object_id):
        """
        Handler of requests
        """
        self._load_object(object_type, object_id)

    def _load_object(self, object_type, object_id):
        """
        Load the object based ob the incoming specification
        """
        serializer = serializers.CommentObjectSpecificationSerializer(
            data={"object_type": object_type, "object_id": object_id}
        )
        serializer.is_valid(raise_exception=True)
        self._object_specification = serializer.validated_data

        object_type_module_path = conf.settings.COMMENTS_OBJECT_TYPES[
            self._object_specification["object_type"]
        ]
        self._object = get_object_or_404(
            module_loading.import_string(object_type_module_path),
            id=self._object_specification["object_id"],
        )


class CommentsConfigurationGetView(drf_views.APIView):
    @extend_schema(
        responses={
            200: OpenApiResponse(serializers.CommentsConfigurationSerializers, description=""),
            401: OpenApiResponse(description="Unauthorized"),
        },
    )
    def get(self, request):
        """
        Get the comments' configuration.
        """
        return drf_response.Response(
            serializers.CommentsConfigurationSerializers(
                {
                    "object_types": map(
                        stringcase.spinalcase,
                        conf.settings.COMMENTS_OBJECT_TYPES.keys(),
                    )
                }
            ).data,
            status=drf_status.HTTP_200_OK,
        )


class CommentsGetOrCreateView(CommentAPIView):
    paginator = paginators.CommentsPagination()

    @extend_schema(
        parameters=[BasePaginationQuerySerializer],
        responses={
            200: OpenApiResponse(
                serializers.CommentListSerializer, description="The list of comments"
            ),
            400: OpenApiResponse(
                description="Unsupported the object type or wrong the object import path"
            ),
            401: OpenApiResponse(description="Unauthorized"),
            404: OpenApiResponse(description="Returns when the object does not exists"),
        },
        examples=[paginated_comments_example],
    )
    def get(self, request, object_type, object_id):
        """
        Retrieve all comments of the specific object.
        """
        super().method(request, object_type, object_id)
        comments = self._object.comments.filter(parent_id=None).all()

        result_page = self.paginator.paginate_queryset(comments, request)
        serializer = serializers.CommentGetSerializer(
            result_page, many=True, context={"request": request}
        )
        return self.paginator.get_paginated_response(serializer.data)

    @extend_schema(
        request=serializers.CommentCreateSerializer,
        responses={
            201: OpenApiResponse(
                serializers.CommentGetSerializer,
                description="Returns when the comment is successfully created",
            ),
            400: OpenApiResponse(
                description="Unsupported the object type or wrong the object import path"
            ),
            401: OpenApiResponse(description="Unauthorized"),
            404: OpenApiResponse(description="Returns when the object does not exists"),
        },
    )
    def post(self, request, object_type, object_id):
        """
        Create a comment for the specific object.
        """
        super().method(request, object_type, object_id)

        if object_type == "idea" and self._object.topic.stage.name in RESTRICTED_STAGES:
            return drf_response.Response(
                {"detail": f"This topic is {self._object.topic.stage.name}, action not permitted."},
                status=drf_status.HTTP_400_BAD_REQUEST,
            )

        serializer = serializers.CommentCreateSerializer(
            data=request.data, context={"request": request}
        )

        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            comment = self._object.comments.create(
                owner=request.user["id"], **serializer.validated_data
            )

        return drf_response.Response(
            serializers.CommentGetSerializer(comment, context={"request": request}).data,
            status=drf_status.HTTP_201_CREATED,
        )


class CommentGetOrUpdateOrDeleteView(CommentAPIView):
    permission_classes = [IsCommentOwner]

    def get_permissions(self):
        if self.request.method == "GET":
            return []
        return super().get_permissions()

    @extend_schema(
        responses={
            200: serializers.CommentGetSerializer,
            400: OpenApiResponse(
                description="Unsupported the object type or wrong the object import path"
            ),
            401: OpenApiResponse(description="Unauthorized"),
            404: OpenApiResponse(
                description="Returns when the object ot the comment does not exists"
            ),
        },
    )
    def get(self, request, object_type, object_id, comment_id):
        """
        Get a specific comment by id.
        """
        super().method(request, object_type, object_id)
        try:
            comment = self._object.comments.get(id=comment_id)
        except Comment.DoesNotExist:
            return drf_response.Response(
                {"detail": "The comment does not exists."}, status=drf_status.HTTP_404_NOT_FOUND
            )

        response_data = serializers.CommentGetSerializer(comment, context={"request": request}).data
        return drf_response.Response(response_data)

    @extend_schema(
        request=serializers.CommentUpdateSerializer,
        responses={
            200: serializers.CommentGetSerializer,
            400: OpenApiResponse(
                description="Unsupported the object type or wrong the object import path"
            ),
            401: OpenApiResponse(description="Unauthorized"),
            403: OpenApiResponse(description="Forbidden"),
            404: OpenApiResponse(
                description="Returns when the object ot the comment does not exists"
            ),
        },
    )
    def put(self, request, object_type, object_id, comment_id):
        """
        Update a specific comment or reply by id.
        """
        super().method(request, object_type, object_id)
        try:
            comment = self._object.comments.get(id=comment_id)
        except Comment.DoesNotExist:
            return drf_response.Response(
                {"detail": "The comment does not exists."}, status=drf_status.HTTP_404_NOT_FOUND
            )

        serializer = serializers.CommentUpdateSerializer(comment, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return drf_response.Response(
            serializers.CommentGetSerializer(comment, context={"request": request}).data
        )

    @extend_schema(
        responses={
            200: serializers.CommentDeleteSerializer,
            400: OpenApiResponse(
                description="Unsupported the object type or wrong the object import path"
            ),
            401: OpenApiResponse(description="Unauthorized"),
            403: OpenApiResponse(description="Forbidden"),
            404: OpenApiResponse(description="Not Found"),
        },
    )
    def delete(self, request, object_type, object_id, comment_id):
        """
        Delete a specific comment by id.
        """
        super().method(request, object_type, object_id)

        try:
            comment = self._object.comments.get(id=comment_id)
            comment.delete()
        except Comment.DoesNotExist:
            return drf_response.Response(
                {"detail": "The comment does not exists."}, status=drf_status.HTTP_404_NOT_FOUND
            )

        return drf_response.Response(serializers.CommentDeleteSerializer(comment).data)
