from rest_framework import status as drf_status
from rest_framework import response as drf_response
from rest_framework import views as drf_views
from drf_spectacular.utils import extend_schema
from drf_spectacular.openapi import OpenApiResponse

from clients.opensearch import OpenSearchClient, QueryTypeEnum

from geo_search_api.api.polygons.constants import PolygonApiConfig
from geo_search_api.api.polygons.serializers import (
    PolygonsGetQuerySerializer,
    PolygonsDocumentsPostRequestSerializer,
    PolygonsDocumentsPostResponseSerializer,
)


class PolygonsRegistryGetView(drf_views.APIView):
    @extend_schema(
        responses={
            401: OpenApiResponse(description="Unauthorized"),
        },
    )
    def get(self, request):
        """
        Get the metadata of polygons indexes
        """

        _, response = OpenSearchClient().search(
            index=PolygonApiConfig.registry_opensearch_index_name
        )
        return drf_response.Response(data=response, status=drf_status.HTTP_200_OK)


class PolygonsGetView(drf_views.APIView):
    @extend_schema(
        parameters=[PolygonsGetQuerySerializer],
        responses={
            400: OpenApiResponse(description="Bad Request"),
            401: OpenApiResponse(description="Unauthorized"),
        },
    )
    def get(self, request):
        """
        Get the polygons of the specific index/es
        """

        q_params = PolygonsGetQuerySerializer(data=request.query_params)
        q_params.is_valid(raise_exception=True)

        validated_index, validated_include_source = map(
            q_params.validated_data.get,
            ["index", "include_source"],
        )

        okay, response = OpenSearchClient().multi_search(
            index=validated_index,
            query_type=[QueryTypeEnum.MATCH_ALL for _ in range(len(validated_index))],
            query_parameters=[
                {"kwargs": {"_source": validated_include_source}}
                for _ in range(len(validated_index))
            ],
        )

        if not okay:
            return drf_response.Response(
                {"detail": response}, status=drf_status.HTTP_400_BAD_REQUEST
            )

        return drf_response.Response(data=response, status=drf_status.HTTP_200_OK)


class PolygonsDocumentsPostView(drf_views.APIView):
    @extend_schema(
        request=PolygonsDocumentsPostRequestSerializer(many=True),
        responses={
            200: "Ok",
            400: OpenApiResponse(description="Bad Request"),
            401: OpenApiResponse(description="Unauthorized"),
        },
        # examples=[search_data_scape_documents_example],
    )
    def post(self, request):
        """
        Search the data scape documents through the opensearch specific index(es)
        """
        request_body = PolygonsDocumentsPostRequestSerializer(data=request.data, many=True)
        request_body.is_valid(raise_exception=True)

        arg_index, arg_query_type, args_query_parameters = [], [], []
        for _ in request_body.validated_data:
            arg_index.append(_.get("index"))
            arg_query_type.append(QueryTypeEnum.IDS)
            args_query_parameters.append({"values": _.get("document_ids")})

        okay, response = OpenSearchClient().multi_search(
            index=arg_index,
            query_type=arg_query_type,
            query_parameters=args_query_parameters,
        )

        if not okay:
            return drf_response.Response(
                {"detail": response}, status=drf_status.HTTP_400_BAD_REQUEST
            )

        return drf_response.Response(
            data=PolygonsDocumentsPostResponseSerializer(
                instance=response, context={"indexes": arg_index}
            ).data,
            status=drf_status.HTTP_200_OK,
        )
