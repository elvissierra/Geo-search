from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from drf_spectacular.openapi import OpenApiResponse
from django.shortcuts import get_object_or_404

from geo_search_api.api.serializers import BasePaginationQuerySerializer
from geo_search_api.apps.topics.models import Topic, TopicTag, TopicStage
from geo_search_api.api.topics.paginators import (
    TopicsPagination,
    TopicTagsPagination,
    TopicStagesPagination,
)
from geo_search_api.api.topics.serializers import (
    TopicsListQuerySerializer,
    TopicsListSerializer,
    TopicGetSerializer,
    TopicCreateSerializer,
    TopicUpdateSerializer,
    TopicDeleteSerializer,
    TopicTagsListSerializer,
    TopicTagGetSerializer,
    TopicTagCreateSerializer,
    TopicTagUpdateSerializer,
    TopicTagDeleteSerializer,
    TopicStagesListSerializer,
    TopicStageGetSerializer,
    TopicStageCreateSerializer,
    TopicStageUpdateSerializer,
    TopicStageDeleteSerializer,
)


class TopicsGetOrCreateView(APIView):
    paginator = TopicsPagination()

    @extend_schema(
        parameters=[BasePaginationQuerySerializer, TopicsListQuerySerializer],
        responses={
            200: TopicsListSerializer,
            401: OpenApiResponse(description="Unauthorized"),
            404: OpenApiResponse(description="Invalid page or page size"),
        },
    )
    def get(self, request):
        """
        Retrieve the list of topics.
        """

        q_param = TopicsListQuerySerializer(data=request.query_params)
        q_param.is_valid(raise_exception=True)

        topics = Topic.objects.filter(**q_param.validated_data).all()
        result_page = self.paginator.paginate_queryset(topics, request)
        serializer = TopicGetSerializer(result_page, many=True)
        return self.paginator.get_paginated_response(serializer.data)

    @staticmethod
    @extend_schema(
        request=TopicCreateSerializer,
        responses={
            201: TopicGetSerializer,
            400: OpenApiResponse(description="Bad Request"),
            401: OpenApiResponse(description="Unauthorized"),
        },
    )
    def post(request):
        """
        Create new topic.
        """
        serializer = TopicCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        topic = serializer.save(owner=request.user["id"])
        return Response(TopicGetSerializer(topic).data, status=status.HTTP_201_CREATED)


class TopicGetOrUpdateOrDeleteView(APIView):
    @staticmethod
    @extend_schema(
        responses={
            200: TopicGetSerializer,
            401: OpenApiResponse(description="Unauthorized"),
            404: OpenApiResponse(description="Not Found"),
        },
    )
    def get(request, topic_id):
        """
        Get a specific topic by id.
        """
        topic = get_object_or_404(Topic, id=topic_id)
        return Response(TopicGetSerializer(topic).data)

    @staticmethod
    @extend_schema(
        request=TopicUpdateSerializer,
        responses={
            200: TopicGetSerializer,
            400: OpenApiResponse(description="Bad Request"),
            401: OpenApiResponse(description="Unauthorized"),
            404: OpenApiResponse(description="Not Found"),
        },
    )
    def put(request, topic_id):
        """
        Update a specific topic by id.
        """
        topic = get_object_or_404(Topic, id=topic_id)
        serializer = TopicUpdateSerializer(topic, data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
        return Response(TopicGetSerializer(topic).data)

    @staticmethod
    @extend_schema(
        responses={
            200: TopicDeleteSerializer,
            401: OpenApiResponse(description="Unauthorized"),
            404: OpenApiResponse(description="Not Found"),
        },
    )
    def delete(request, topic_id):
        """
        Delete a specific topic by id.
        """
        topic = get_object_or_404(Topic, id=topic_id)
        topic.delete()
        return Response(TopicDeleteSerializer(topic).data)


class TopicTagsGetOrCreateView(APIView):
    paginator = TopicTagsPagination()

    @extend_schema(
        parameters=[BasePaginationQuerySerializer],
        responses={
            200: TopicTagsListSerializer,
            401: OpenApiResponse(description="Unauthorized"),
            404: OpenApiResponse(description="Invalid page or page size"),
        },
    )
    def get(self, request):
        """
        Retrieve the list of topic tags.
        """
        topic_tags = TopicTag.objects.all()
        result_page = self.paginator.paginate_queryset(topic_tags, request)
        serializer = TopicTagGetSerializer(result_page, many=True)
        return self.paginator.get_paginated_response(serializer.data)

    @staticmethod
    @extend_schema(
        request=TopicTagCreateSerializer,
        responses={
            201: TopicTagGetSerializer,
            400: OpenApiResponse(description="Bad Request"),
            401: OpenApiResponse(description="Unauthorized"),
        },
    )
    def post(request):
        """
        Create new topic tag.
        """
        serializer = TopicTagCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        topic_tag = serializer.save()
        return Response(TopicTagGetSerializer(topic_tag).data, status=status.HTTP_201_CREATED)


class TopicTagGetOrUpdateOrDeleteView(APIView):
    @staticmethod
    @extend_schema(
        responses={
            200: TopicTagGetSerializer,
            401: OpenApiResponse(description="Unauthorized"),
            404: OpenApiResponse(description="Not Found"),
        },
    )
    def get(request, topic_tag_id):
        """
        Get a specific topic tag by id.
        """
        topic_tag = get_object_or_404(TopicTag, id=topic_tag_id)
        return Response(TopicTagGetSerializer(topic_tag).data)

    @staticmethod
    @extend_schema(
        request=TopicTagUpdateSerializer,
        responses={
            200: TopicTagGetSerializer,
            400: OpenApiResponse(description="Bad Request"),
            401: OpenApiResponse(description="Unauthorized"),
            404: OpenApiResponse(description="Not Found"),
        },
    )
    def put(request, topic_tag_id):
        """
        Update a specific topic tag by id.
        """
        topic_tag = get_object_or_404(TopicTag, id=topic_tag_id)
        serializer = TopicTagUpdateSerializer(topic_tag, data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
        return Response(TopicTagGetSerializer(topic_tag).data)

    @staticmethod
    @extend_schema(
        responses={
            200: TopicTagDeleteSerializer,
            401: OpenApiResponse(description="Unauthorized"),
            404: OpenApiResponse(description="Not Found"),
        },
    )
    def delete(request, topic_tag_id):
        """
        Delete a specific topic tag by id.
        """
        topic_tag = get_object_or_404(TopicTag, id=topic_tag_id)
        topic_tag.delete()
        return Response(TopicTagDeleteSerializer(topic_tag).data)


class TopicStageGetOrCreateView(APIView):
    paginator = TopicStagesPagination()

    @extend_schema(
        parameters=[BasePaginationQuerySerializer],
        responses={
            200: TopicStagesListSerializer,
            401: OpenApiResponse(description="Unauthorized"),
            404: OpenApiResponse(description="Invalid page or page size"),
        },
    )
    def get(self, request):
        """
        Retrieve the list of topic stages.
        """

        topic_stages = TopicStage.objects.all()
        result_page = self.paginator.paginate_queryset(topic_stages, request)
        serializer = TopicStageGetSerializer(result_page, many=True)
        return self.paginator.get_paginated_response(serializer.data)

    @staticmethod
    @extend_schema(
        request=TopicStageCreateSerializer,
        responses={
            201: TopicStageGetSerializer,
            400: OpenApiResponse(description="Bad Request"),
            401: OpenApiResponse(description="Unauthorized"),
        },
    )
    def post(request):
        """
        Create new topic stage.
        """
        serializer = TopicStageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        topic_stage = serializer.save()
        return Response(TopicStageGetSerializer(topic_stage).data, status=status.HTTP_201_CREATED)


class TopicStageGetOrUpdateOrDeleteView(APIView):
    @staticmethod
    @extend_schema(
        responses={
            200: TopicStageGetSerializer,
            401: OpenApiResponse(description="Unauthorized"),
            404: OpenApiResponse(description="Not Found"),
        },
    )
    def get(request, topic_stage_id):
        """
        Get a specific topic stage by id.
        """
        topic_stage = get_object_or_404(TopicStage, id=topic_stage_id)
        return Response(TopicStageGetSerializer(topic_stage).data)

    @staticmethod
    @extend_schema(
        request=TopicStageUpdateSerializer,
        responses={
            200: TopicStageGetSerializer,
            400: OpenApiResponse(description="Bad Request"),
            401: OpenApiResponse(description="Unauthorized"),
            404: OpenApiResponse(description="Not Found"),
        },
    )
    def put(request, topic_stage_id):
        """
        Update a specific topic stage by id.
        """
        topic_stage = get_object_or_404(TopicStage, id=topic_stage_id)
        serializer = TopicStageUpdateSerializer(topic_stage, data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
        return Response(TopicStageGetSerializer(topic_stage).data)

    @staticmethod
    @extend_schema(
        responses={
            200: TopicStageDeleteSerializer,
            401: OpenApiResponse(description="Unauthorized"),
            403: OpenApiResponse(description="It returns when the stage cannot be deleted."),
            404: OpenApiResponse(description="Not Found"),
        },
    )
    def delete(request, topic_stage_id):
        """
        Delete a specific topic stage by id.
        """
        topic_stage = get_object_or_404(TopicStage, id=topic_stage_id)

        if topic_stage.topic_set.exists():
            # The error message describe this logic very well.
            return Response(
                {
                    "detail": f"The stage cannot be delete, it has a reference to the topic/s "
                    f"of {', '.join([t.title for t in topic_stage.topic_set.all()])}"
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        topic_stage.delete()
        return Response(TopicStageDeleteSerializer(topic_stage).data)
