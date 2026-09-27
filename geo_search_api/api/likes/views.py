import stringcase
from rest_framework import views as drf_views
from rest_framework import response as drf_response
from rest_framework import status as drf_status
from drf_spectacular.utils import extend_schema
from drf_spectacular.openapi import OpenApiResponse

from django import conf
from django.db import transaction, IntegrityError
from django.utils import module_loading
from django.shortcuts import get_object_or_404
from geo_search_api.api.permissions import RESTRICTED_STAGES
from geo_search_api.api.likes import serializers
from geo_search_api.api.likes import paginators
from geo_search_api.api.serializers import BasePaginationQuerySerializer


class LikeAPIView(drf_views.APIView):
    """
    Base like API view
    """

    def __init__(self, **kwargs):
        """
        Initialization of LikeAPIView
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

        serializer = serializers.LikeObjectSpecificationSerializer(
            data={"object_type": object_type, "object_id": object_id}
        )
        serializer.is_valid(raise_exception=True)
        self._object_specification = serializer.validated_data

        object_type_module_path = conf.settings.LIKES_OBJECT_TYPES[
            self._object_specification["object_type"]
        ]
        self._object = get_object_or_404(
            module_loading.import_string(object_type_module_path),
            id=self._object_specification["object_id"],
        )


class LikesConfigurationGetView(drf_views.APIView):
    @extend_schema(
        responses={
            200: OpenApiResponse(serializers.LikesConfigurationSerializers, description=""),
            401: OpenApiResponse(description="Unauthorized"),
        },
    )
    def get(self, request):
        """
        Get the likes configuration.
        """
        return drf_response.Response(
            serializers.LikesConfigurationSerializers(
                {
                    "object_types": map(
                        stringcase.spinalcase, conf.settings.LIKES_OBJECT_TYPES.keys()
                    )
                }
            ).data,
            status=drf_status.HTTP_200_OK,
        )


class LikesGetOrCreateOrDeleteView(LikeAPIView):
    paginator = paginators.LikesPagination()

    @extend_schema(
        parameters=[BasePaginationQuerySerializer],
        responses={
            200: OpenApiResponse(serializers.LikesListSerializer, description="The list of likes"),
            400: OpenApiResponse(
                description="Unsupported the object type or wrong the object import path"
            ),
            401: OpenApiResponse(description="Unauthorized"),
            404: OpenApiResponse(description="Returns when the object does not exists"),
        },
    )
    def get(self, request, object_type, object_id):
        """
        Retrieve all likes of the specific object.
        """

        super().method(request, object_type, object_id)
        likes = self._object.likes.all()

        result_page = self.paginator.paginate_queryset(likes, request)
        serializer = serializers.LikeGetSerializer(result_page, many=True)
        return self.paginator.get_paginated_response(
            {
                "results": serializer.data,
                "is_current_user_liked": self._object.does_the_user_liked(request.user["id"]),
            }
        )

    @extend_schema(
        responses={
            201: OpenApiResponse(
                serializers.LikesSumUpSerializer,
                description="Returns when the like is successfully created",
            ),
            400: OpenApiResponse(
                description="Unsupported the object type or wrong the object import path"
            ),
            401: OpenApiResponse(description="Unauthorized"),
            403: OpenApiResponse(
                description="Returns when the user tries to like the object again"
            ),
            404: OpenApiResponse(description="Returns when the object does not exists"),
        },
    )
    def post(self, request, object_type, object_id):
        """
        Create a like for the specific object.
        """

        super().method(request, object_type, object_id)

        if object_type == "idea" and self._object.topic.stage.name in RESTRICTED_STAGES:
            return drf_response.Response(
                {"detail": f"This topic is {self._object.topic.stage.name}, action not permitted."},
                status=drf_status.HTTP_400_BAD_REQUEST,
            )

        try:
            with transaction.atomic():
                self._object.likes.create(user_id=request.user["id"])
        except IntegrityError as exc:
            # If we catch the exception related to unique constraint of `Like` model, handle it and
            # return an appropriate response to the client.
            if "unique_type_id_user" in exc.args[0]:
                return drf_response.Response(
                    {"detail": "You have already liked this object."},
                    status=drf_status.HTTP_403_FORBIDDEN,
                )

        return drf_response.Response(
            serializers.LikesSumUpSerializer(
                self._object.get_likes_sum_up(request.user["id"])
            ).data,
            status=drf_status.HTTP_201_CREATED,
        )

    @extend_schema(
        responses={
            200: OpenApiResponse(
                serializers.LikesSumUpSerializer,
                description="Returns when the like is successfully deleted",
            ),
            400: OpenApiResponse(
                description="Unsupported the object type or wrong the object import path"
            ),
            401: OpenApiResponse(description="Unauthorized"),
            403: OpenApiResponse(
                description="Returns when the like does not exists for the object"
            ),
            404: OpenApiResponse(description="Returns when the object does not exists"),
        },
    )
    def delete(self, request, object_type, object_id):
        """
        Delete a like from the specific object.
        """

        super().method(request, object_type, object_id)
        like = self._object.likes.filter(user_id=request.user["id"]).first()

        if like is None:
            return drf_response.Response(
                {"detail": "Your like does not exist for this object."},
                status=drf_status.HTTP_403_FORBIDDEN,
            )

        self._object.likes.remove(like)

        return drf_response.Response(
            serializers.LikesSumUpSerializer(
                self._object.get_likes_sum_up(request.user["id"])
            ).data,
            status=drf_status.HTTP_200_OK,
        )
