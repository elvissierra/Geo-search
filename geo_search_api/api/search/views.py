import copy

from rest_framework import views as drf_views
from rest_framework import response as drf_response
from rest_framework import status as drf_status
from drf_spectacular.utils import extend_schema
from drf_spectacular.openapi import OpenApiResponse

from clients.opensearch import OpenSearchClient, QueryTypeEnum
from geo_search_api.api.search.constants import (
    DOCUMENT_FIELD_NAME,
    AUTOCOMPLETE_MAP,
    SEARCH_MULTI_MAP,
)
from geo_search_api.api.search.serializers import (
    SearchQuerySerializer,
    SearchResponseSerializer,
    SearchDataScapeAutocompleteQuerySerializer,
    SearchDataScapeAutocompleteResponseSerializer,
    SearchDataScapeMultiQuerySerializer,
    SearchDataScapeMultiResponseSerializer,
    SearchDataScapeClustersQuerySerializer,
    SearchDataScapeClustersSerializer,
    SearchDataScapeDocumentsPostSerializer,
    SearchDataScapeDocumentsSerializer,
    SearchInBoundingBoxQuerySerializer,
    SearchDataScapeDocumentsPointsSerializer,
)
from geo_search_api.api.search.swagger_examples import search_example
from geo_search_api.api.search.swagger_examples import (
    search_data_scape_example,
    search_data_scape_points_example,
    search_data_scape_documents_example,
    search_autocomplete_example,
    search_multi_example,
)


class SearchViewMixin:
    @staticmethod
    def _prepare_query(query: str) -> str:
        """
        Split the query by whitespace and add an operator OR
        """
        _ = query.strip()
        return " OR ".join([f"*{_}*"] + [f"{_}*" for _ in _.split(" ")]) if " " in _ else f"{_}*"


class SearchGetView(drf_views.APIView):
    @extend_schema(
        parameters=[SearchQuerySerializer],
        responses={
            200: "Ok",
            400: OpenApiResponse(description="Bad Request"),
            401: OpenApiResponse(description="Unauthorized"),
        },
        examples=[search_example],
    )
    def get(self, request):
        """
        Search through the OpenSearch specific index or all indexes
        """
        q_param = SearchQuerySerializer(data=request.query_params)
        q_param.is_valid(raise_exception=True)

        # Extract the associated data from the query parameters.
        q_associated = q_param.validated_data.pop("associated", None)

        ok, response = OpenSearchClient().search(**q_param.validated_data)
        if not ok:
            return drf_response.Response(
                {"detail": response}, status=drf_status.HTTP_400_BAD_REQUEST
            )

        return drf_response.Response(
            SearchResponseSerializer(response, context={"associated": q_associated}).data,
            status=drf_status.HTTP_200_OK,
        )


class SearchDataScapeAutocompleteGetView(drf_views.APIView, SearchViewMixin):
    @extend_schema(
        parameters=[SearchDataScapeAutocompleteQuerySerializer],
        responses={
            200: "Ok",
            400: OpenApiResponse(description="Bad Request"),
            401: OpenApiResponse(description="Unauthorized"),
        },
        examples=[search_autocomplete_example],
    )
    def get(self, request):
        """
        Search through the OpenSearch specific index or all indexes
        """
        q_param = SearchDataScapeAutocompleteQuerySerializer(data=request.query_params)
        q_param.is_valid(raise_exception=True)

        arg_index, arg_query_type, args_query_parameters = [], [], []
        for index, fields in AUTOCOMPLETE_MAP.items():
            for field in fields:
                arg_index.append(index)
                arg_query_type.append(QueryTypeEnum.QUERY_STRING)
                args_query_parameters.append(
                    {
                        "fields": [f"{field}.{DOCUMENT_FIELD_NAME}"],
                        "query": self._prepare_query(query=q_param.validated_data.get("query")),
                        "kwargs": {"_source": [field]},
                    }
                )

        ok, response = OpenSearchClient().multi_search(
            index=arg_index,
            query_type=arg_query_type,
            query_parameters=args_query_parameters,
            size=q_param.validated_data.get("size"),
        )
        if not ok:
            return drf_response.Response(
                {"detail": response}, status=drf_status.HTTP_400_BAD_REQUEST
            )

        return drf_response.Response(
            SearchDataScapeAutocompleteResponseSerializer(
                response,
                context={
                    "size_per_index": int(q_param.validated_data.get("size")),
                },
            ).data,
            status=drf_status.HTTP_200_OK,
        )


class SearchDataScapeMultiGetView(drf_views.APIView, SearchViewMixin):
    @extend_schema(
        parameters=[SearchDataScapeMultiQuerySerializer],
        responses={
            200: "Ok",
            400: OpenApiResponse(description="Bad Request"),
            401: OpenApiResponse(description="Unauthorized"),
        },
        examples=[search_multi_example],
    )
    def get(self, request):
        """
        Search through the OpenSearch specific index or all indexes
        """
        q_params = SearchDataScapeMultiQuerySerializer(data=request.query_params)
        q_params.is_valid(raise_exception=True)

        indexes = q_params.validated_data.get("index")
        arg_index, arg_query_type, args_query_parameters, arg_highlight = [], [], [], []
        for index in indexes if isinstance(indexes, list) else [indexes]:
            arg_index.append(index)
            arg_query_type.append(QueryTypeEnum.QUERY_STRING)
            args_query_parameters.append(
                {
                    "query": self._prepare_query(query=q_params.validated_data.get("query")),
                    "fields": SEARCH_MULTI_MAP.get(index).get("fields"),
                }
            )
            arg_highlight.append(SEARCH_MULTI_MAP.get(index).get("highlight"))

        ok, response = OpenSearchClient().multi_search(
            index=arg_index,
            query_type=arg_query_type,
            query_parameters=args_query_parameters,
            size=q_params.validated_data.get("size"),
            highlight=arg_highlight,
        )
        if not ok:
            return drf_response.Response(
                {"detail": response}, status=drf_status.HTTP_400_BAD_REQUEST
            )

        return drf_response.Response(
            SearchDataScapeMultiResponseSerializer(
                response, context={"q_params": q_params.validated_data}
            ).data,
            status=drf_status.HTTP_200_OK,
        )


class SearchDataScapeClustersGetView(drf_views.APIView):
    @extend_schema(
        parameters=[SearchDataScapeClustersQuerySerializer],
        responses={
            200: "Ok",
            400: OpenApiResponse(description="Bad Request"),
            401: OpenApiResponse(description="Unauthorized"),
        },
        examples=[search_data_scape_example],
    )
    def get(self, request):
        """
        Search the data scape through the opensearch specific index(es)
        """
        q_params = SearchDataScapeClustersQuerySerializer(data=request.query_params)
        q_params.is_valid(raise_exception=True)

        ok, response = OpenSearchClient().get_geo_bounding_box_clusters(**q_params.validated_data)
        if not ok:
            return drf_response.Response(
                {"detail": response}, status=drf_status.HTTP_400_BAD_REQUEST
            )

        return drf_response.Response(
            SearchDataScapeClustersSerializer(
                response, context={"q_params": q_params.validated_data}
            ).data,
            status=drf_status.HTTP_200_OK,
        )


class SearchDataScapeDocumentsPostView(drf_views.APIView):
    @extend_schema(
        request=SearchDataScapeDocumentsPostSerializer(many=True),
        responses={
            200: "Ok",
            400: OpenApiResponse(description="Bad Request"),
            401: OpenApiResponse(description="Unauthorized"),
        },
        examples=[search_data_scape_documents_example],
    )
    def post(self, request):
        """
        Search the data scape documents through the opensearch specific index(es)
        """
        documents_data = SearchDataScapeDocumentsPostSerializer(data=request.data, many=True)
        documents_data.is_valid(raise_exception=True)

        opensearch_responses = []
        for _ in documents_data.validated_data:
            data = copy.deepcopy(_)
            data.pop("associated", None)
            ok, response = OpenSearchClient().get_documents(**data)
            if not ok:
                return drf_response.Response(
                    {"detail": response}, status=drf_status.HTTP_400_BAD_REQUEST
                )
            opensearch_responses.append(response)

        return drf_response.Response(
            SearchDataScapeDocumentsSerializer(
                opensearch_responses, context={"request_body": documents_data.validated_data}
            ).data,
            status=drf_status.HTTP_200_OK,
        )


class SearchDataScapeDocumentsPointsGetView(drf_views.APIView):
    @extend_schema(
        parameters=[SearchInBoundingBoxQuerySerializer],
        responses={
            200: "Ok",
            400: OpenApiResponse(description="Bad Request"),
            401: OpenApiResponse(description="Unauthorized"),
        },
        examples=[search_data_scape_points_example],
    )
    def get(self, request):
        """
        Search the data scape through the opensearch specific index(es)
        """
        q_params = SearchInBoundingBoxQuerySerializer(data=request.query_params)
        q_params.is_valid(raise_exception=True)

        ok, response = OpenSearchClient().get_documents_in_bounding_box(**q_params.validated_data)
        if not ok:
            return drf_response.Response(
                {"detail": response}, status=drf_status.HTTP_400_BAD_REQUEST
            )

        return drf_response.Response(
            SearchDataScapeDocumentsPointsSerializer(
                response, context={"q_params": q_params.validated_data}
            ).data,
            status=drf_status.HTTP_200_OK,
        )
