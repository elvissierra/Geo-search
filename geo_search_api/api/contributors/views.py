from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from drf_spectacular.openapi import OpenApiResponse
from django.shortcuts import get_object_or_404

from geo_search_api.apps.contributors.models import Contributor

from geo_search_api.api.contributors.serializers import (
    ContributorsGetSerializer,
    ContributorCreateSerializer,
    ContributorUpdateSerializer,
    ContributorDeleteSerializer,
    ContributorsListQuerySerializer,
)


class ContributorsGetOrCreateView(APIView):
    @extend_schema(
        parameters=[ContributorsListQuerySerializer],
        responses={
            200: ContributorsGetSerializer,
            401: OpenApiResponse(description="Unauthorized"),
        },
    )
    def get(self, request, topic_id):
        """
        Get all contributors.
        """
        params = ContributorsListQuerySerializer(data=request.query_params)
        params.is_valid(raise_exception=True)

        contributors = Contributor.objects.filter(
            **params.validated_data, topic_id=topic_id
        ).order_by("prize")
        serializer = ContributorsGetSerializer(
            contributors, many=True, context={"request": request}
        )

        return Response(serializer.data, status=status.HTTP_200_OK)

    @staticmethod
    @extend_schema(
        request=ContributorCreateSerializer,
        responses={
            201: ContributorsGetSerializer,
            400: OpenApiResponse(description="Bad Request"),
            401: OpenApiResponse(description="Unauthorized"),
        },
    )
    def post(request, topic_id):
        """
        Create a contributor.
        """
        serializer = ContributorCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        contributor = serializer.save()
        return Response(ContributorsGetSerializer(contributor).data, status=status.HTTP_201_CREATED)


class ContributorsGetUpdateDeleteView(APIView):
    @staticmethod
    @extend_schema(
        responses={
            200: ContributorsGetSerializer,
            401: OpenApiResponse(description="Unauthorized"),
            404: OpenApiResponse(description="Not Found"),
        },
    )
    def get(request, topic_id, contributor_id):
        """
        Get a specific contributor by id.
        """
        contributor = get_object_or_404(Contributor, id=contributor_id, topic_id=topic_id)
        return Response(ContributorsGetSerializer(contributor, context={"request": request}).data)

    @staticmethod
    @extend_schema(
        request=ContributorUpdateSerializer,
        responses={
            200: ContributorsGetSerializer,
            400: OpenApiResponse(description="Bad Request"),
            401: OpenApiResponse(description="Unauthorized"),
            404: OpenApiResponse(description="Not Found"),
        },
    )
    def put(request, topic_id, contributor_id):
        """
        Update a specific contributor status by id.
        """
        contributor = get_object_or_404(Contributor, id=contributor_id, topic_id=topic_id)
        serializer = ContributorUpdateSerializer(contributor, data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
        return Response(ContributorsGetSerializer(contributor, context={"request": request}).data)

    @staticmethod
    @extend_schema(
        responses={
            200: ContributorDeleteSerializer,
            401: OpenApiResponse(description="Unauthorized"),
            404: OpenApiResponse(description="Not Found"),
        },
    )
    def delete(request, topic_id, contributor_id):
        """
        Delete a specific contributor by id.
        """
        contributor = get_object_or_404(Contributor, id=contributor_id, topic_id=topic_id)
        contributor.delete()
        return Response(ContributorDeleteSerializer(contributor).data)
