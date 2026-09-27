from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from drf_spectacular.openapi import OpenApiResponse
from django.shortcuts import get_object_or_404

from geo_search_api.apps.ideas.models import Idea, IdeaStatuses
from geo_search_api.api.ideas.swagger_examples import (
    idea_example,
    idea_post_status_example,
)
from geo_search_api.api.ideas.serializers import (
    IdeaCreateSerializer,
    IdeaGetSerializer,
    IdeaUpdateSerializer,
    IdeaDeleteSerializer,
    IdeasListSerializer,
    IdeasListQuerySerializer,
    IdeaStatusUpdateSerializer,
)
from geo_search_api.api.ideas.paginators import IdeasPagination
from geo_search_api.api.serializers import BasePaginationQuerySerializer
from geo_search_api.api.permissions import RESTRICTED_STAGES, IsIdeaOwner

TRENDING_IDEAS_NUM = 5


class IdeasGetOrCreateView(APIView):
    paginator = IdeasPagination()

    @extend_schema(
        parameters=[BasePaginationQuerySerializer, IdeasListQuerySerializer],
        responses={
            200: IdeasListSerializer,
            401: OpenApiResponse(description="Unauthorized"),
            404: OpenApiResponse(description="Invalid page or page size"),
        },
    )
    def get(self, request):
        """
        Retrieve the list of ideas.
        """
        query_params = IdeasListQuerySerializer(data=request.query_params)
        query_params.is_valid(raise_exception=True)

        _query = IdeasListQuerySerializer(data=request.query_params)
        _query.is_valid(raise_exception=True)

        ideas = Idea.objects
        if "sort" in _query.validated_data:
            ideas = ideas.order_by(*_query.validated_data.pop("sort"))
        ideas = ideas.filter(**_query.validated_data)

        result_page = self.paginator.paginate_queryset(ideas, request)
        serializer = IdeaGetSerializer(result_page, many=True, context={"request": request})

        return self.paginator.get_paginated_response(serializer.data)

    @staticmethod
    @extend_schema(
        request=IdeaCreateSerializer,
        responses={
            200: OpenApiResponse(IdeaCreateSerializer),
            201: OpenApiResponse(IdeaGetSerializer),
            400: OpenApiResponse(description="Bad Request"),
            401: OpenApiResponse(description="Unauthorized"),
        },
        # examples=[idea_example, idea_post_example],
    )
    def post(request):
        """
        Create an Idea  under a Topic.
        """
        request.data["owner"] = request.user["id"]

        serializer = IdeaCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        topic = serializer.validated_data.get("topic")

        if topic.stage.name in RESTRICTED_STAGES:
            return Response(
                {"detail": f"This topic is {topic.stage.name}, action not permitted."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        idea = serializer.save(owner=request.user["id"], status=IdeaStatuses.ACTIVE)

        idea.create_contributor(request.user["id"])

        return Response(
            IdeaGetSerializer(idea, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class IdeaGetOrUpdateOrDeleteView(APIView):
    permission_classes = [IsIdeaOwner]

    def get_permissions(self):
        if self.request.method == "GET":
            return []
        return super().get_permissions()

    @staticmethod
    @extend_schema(
        responses={
            200: IdeaGetSerializer,
            401: OpenApiResponse(description="Unauthorized"),
            404: OpenApiResponse(description="Not Found"),
        },
    )
    def get(request, idea_id):
        """
        Get a specific idea by id.
        """
        idea = get_object_or_404(Idea, id=idea_id)
        return Response(IdeaGetSerializer(idea, context={"request": request}).data)

    @staticmethod
    @extend_schema(
        request=IdeaUpdateSerializer,
        responses={
            200: IdeaGetSerializer,
            400: OpenApiResponse(description="Bad Request"),
            401: OpenApiResponse(description="Unauthorized"),
            403: OpenApiResponse(description="Forbidden"),
            404: OpenApiResponse(description="Not Found"),
        },
    )
    def put(request, idea_id):
        """
        Update a specific idea by id.
        """
        idea = get_object_or_404(Idea, id=idea_id)
        serializer = IdeaUpdateSerializer(idea, data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
        return Response(IdeaGetSerializer(idea, context={"request": request}).data)

    @staticmethod
    @extend_schema(
        responses={
            200: IdeaDeleteSerializer,
            401: OpenApiResponse(description="Unauthorized"),
            403: OpenApiResponse(description="Forbidden"),
            404: OpenApiResponse(description="Not Found"),
        },
    )
    def delete(request, idea_id):
        """
        Delete a specific idea by id.
        """
        idea = get_object_or_404(Idea, id=idea_id)
        idea.delete()
        return Response(IdeaDeleteSerializer(idea).data)


class IdeaStatusUpdateView(APIView):
    @staticmethod
    @extend_schema(
        request=IdeaStatusUpdateSerializer,
        responses={
            200: OpenApiResponse(IdeaGetSerializer),
            400: OpenApiResponse(description="Bad Request"),
            401: OpenApiResponse(description="Unauthorized"),
        },
        examples=[idea_example, idea_post_status_example],
    )
    def post(request):
        """Update Ideas status."""
        idea = get_object_or_404(Idea, id=request.data.get("id"))
        serializer = IdeaStatusUpdateSerializer(idea, data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
        return Response(IdeaGetSerializer(idea, context={"request": request}).data)


class IdeasTrendingGetView(APIView):
    @extend_schema(
        responses={
            200: IdeaGetSerializer,
            401: OpenApiResponse(description="Unauthorized"),
        },
    )
    def get(self, request):
        """Retrieve top trending ideas"""

        top_ideas = Idea.objects.filter(engagement_rate__isnull=False, is_trending=True).order_by(
            "-engagement_rate"
        )

        if not top_ideas.exists():
            return Response({"detail": "No trending ideas at the moment."})

        unique_idea_topics = []
        seen_topics = {}

        for idea in top_ideas:
            if idea.topic not in seen_topics:
                unique_idea_topics.append(idea)
                seen_topics[idea.topic] = [idea]
            elif (
                idea not in seen_topics[idea.topic] and len(unique_idea_topics) < TRENDING_IDEAS_NUM
            ):
                unique_idea_topics.append(idea)
                seen_topics[idea.topic].append(idea)

            if len(unique_idea_topics) >= TRENDING_IDEAS_NUM:
                break

        serializer = IdeaGetSerializer(unique_idea_topics, many=True, context={"request": request})
        return Response(serializer.data)
