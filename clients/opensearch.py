import json
import typing
import requests
import warnings
import enum

import opensearchpy
from opensearchpy.helpers import update_by_query, scan
from opensearchpy.helpers.query import (
    SimpleQueryString,
    QueryString,
    MatchAll,
    MultiMatch,
    Term,
    Terms,
    Bool,
    Ids,
    Wildcard,
)
from django.conf import settings as dj_settings
from rest_framework.response import Response


class IndexEnum(enum.Enum):

    BASINS = "basin-shape-index"
    WELLS = "wells_ontology"
    DOCUMENTS = "document_location"
    LAS_FILES = "las_files"

    @classmethod
    def as_string(cls, get: str = "value", delimiter: str = ","):
        return delimiter.join([getattr(e, get) for e in cls])


class QueryTypeEnum(enum.Enum):
    SIMPLE_QUERY_STRING = "simple_query_string"
    QUERY_STRING = "query_string"
    MATCH_ALL = "match_all"
    MULTI_MATCH = "multi_match"
    TERM = "term"
    TERMS = "terms"
    BOOL = "bool"
    SUGGEST = "suggest"
    IDS = "ids"
    WILDCARD = "wildcard"

    @classmethod
    def choices(cls):
        return tuple((i.name, i.value) for i in cls)


class QueryBuilderError(BaseException):
    pass


class QueryBuilder:
    @classmethod
    def build(cls, query_type: QueryTypeEnum, parameters: typing.Dict, **kwargs) -> typing.Dict:
        try:
            _ = getattr(cls, f"_{query_type.value}")(**parameters)
            if query_type in [QueryTypeEnum.SUGGEST]:
                return _

            _query = {"query": _}
            if "size" in kwargs:
                _query.update({"from": kwargs.pop("from_", 0), "size": kwargs.pop("size")})
            if "_source" in kwargs:
                _query.update({"_source": kwargs.pop("_source")})

            _query.update(kwargs)
            return _query
        except TypeError as exc:
            raise QueryBuilderError(exc.args[0]) from exc

    @classmethod
    def _simple_query_string(cls, query: str, fields: typing.List[str] = None) -> typing.Dict:
        return SimpleQueryString(query=query, fields=fields or []).to_dict()

    @classmethod
    def _query_string(cls, query: str, fields: typing.List[str] = None) -> typing.Dict:
        return QueryString(query=query, fields=fields or []).to_dict()

    @classmethod
    def _match_all(cls) -> typing.Dict:
        return MatchAll().to_dict()

    @classmethod
    def _multi_match(cls, query: str, fields: typing.Union[list, tuple]):
        return MultiMatch(query=query, fields=fields).to_dict()

    @classmethod
    def _term(cls, field: str, value: typing.Any) -> typing.Dict:
        return Term(**{field: value}).to_dict()

    @classmethod
    def _terms(cls, field: str, value: typing.List[typing.Any]):
        return Terms(**{field: value}).to_dict()

    @classmethod
    def _ids(cls, values: typing.List[typing.AnyStr]):
        return Ids(values=values).to_dict()

    @classmethod
    def _wildcard(cls, field: str, value: typing.List[typing.Any], case_insensitive: bool = True):
        return Wildcard(**{field: {"value": value, "case_insensitive": case_insensitive}}).to_dict()

    @classmethod
    def _suggest(cls, prefix: str, field: str, size: int, source: typing.List[str] = None):
        return {
            "_source": [] if source is None else source,
            "suggest": {
                "autocomplete": {"prefix": prefix, "completion": {"field": field, "size": size}}
            },
        }

    @classmethod
    def _bool(
        cls, must: typing.List = None, must_not: typing.List = None, should: typing.List = None
    ):

        clauses = {}
        for key, value in {"must": must, "must_not": must_not, "should": should}.items():
            if value is None:
                continue
            clauses.update({key: list(map(cls.__build_boolean_query, value))})

        return Bool(**clauses).to_dict()

    @classmethod
    def __build_boolean_query(cls, query: dict):
        for query_type, parameters in query.items():
            return cls.build(query_type, parameters).get("query")


class GeoBoundingBoxAggregation:
    key_fields = ["top_left", "bottom_right", "precision"]
    aggregated_field = "_id"
    coordinates_field = "asset_location.coordinates"

    def generate_aggregation(
        self, top_left: typing.Dict, bottom_right: typing.Dict, precision: int
    ) -> typing.Dict:
        return {
            "clusters": {
                "geohash_grid": {
                    "field": self.coordinates_field,
                    "precision": precision,
                    "bounds": {
                        "top_left": {**top_left},
                        "bottom_right": {**bottom_right},
                    },
                    "size": dj_settings.MAX_BUCKETS_AGGREGATION_SIZE,
                },
                "aggregations": {
                    "cluster_coordinates": {"geo_centroid": {"field": self.coordinates_field}},
                    "document_ids": {
                        "terms": {
                            "size": dj_settings.MAX_TERMS_AGGREGATION_CLUSTERS,
                            "field": self.aggregated_field,
                        }
                    },
                },
            },
        }

    @staticmethod
    def generate_search_filter(top_left: typing.Dict, bottom_right: typing.Dict) -> typing.Dict:
        return {
            "filter": {
                "geo_bounding_box": {
                    "asset_location.coordinates": {
                        "top_left": {**top_left},
                        "bottom_right": {**bottom_right},
                    }
                }
            }
        }


class AggregationsBuilder:
    geo_bounding_box = GeoBoundingBoxAggregation()

    def build(self, aggregation_parameters: typing.Dict) -> typing.Dict:
        if list(set(self.geo_bounding_box.key_fields) & set(aggregation_parameters)):
            return {
                "aggregations": self.geo_bounding_box.generate_aggregation(**aggregation_parameters)
            }

        # Will be modified in future when another aggregations should be supported
        return {}


def search_all_documents(func):
    def wrap(*args, **kwargs):
        status, result = func(*args, **kwargs)
        if result["hits"]["total"]["value"] > dj_settings.MAX_SEARCHING_SIZE and not kwargs.get(
            "size"
        ):
            from_ = dj_settings.MAX_SEARCHING_SIZE
            for n in range(result["hits"]["total"]["value"] // dj_settings.MAX_SEARCHING_SIZE - 1):
                kwargs["size"] = dj_settings.MAX_SEARCHING_SIZE
                kwargs["from_"] = from_
                status, new_chunk = func(*args, **kwargs)
                if status is False:
                    return status, new_chunk
                result["hits"]["hits"].extend(new_chunk["hits"]["hits"])
                from_ += dj_settings.MAX_SEARCHING_SIZE
        return status, result

    return wrap


def msearch_all_documents(func):
    def wrap(*args, **kwargs):
        status, responses = func(*args, **kwargs)

        biggest_number_documents = -1
        for _ in responses["responses"]:
            hits_total = _["hits"]["total"]["value"]
            if (
                hits_total > dj_settings.MAX_SEARCHING_SIZE
                and hits_total > biggest_number_documents
            ):
                biggest_number_documents = hits_total

        if biggest_number_documents > 0 and not kwargs.get("size"):
            from_ = dj_settings.MAX_SEARCHING_SIZE
            for _ in range(biggest_number_documents // dj_settings.MAX_SEARCHING_SIZE):
                kwargs["size"] = dj_settings.MAX_SEARCHING_SIZE
                kwargs["from_"] = from_
                status, new_chunk = func(*args, **kwargs)
                if status is False:
                    return status, new_chunk

                for index, chunk in enumerate(new_chunk["responses"]):
                    responses["responses"][index]["hits"]["hits"].extend(chunk["hits"]["hits"])

                from_ += dj_settings.MAX_SEARCHING_SIZE

        return status, responses

    return wrap


class OpenSearchClient:
    def __init__(self):
        self.__host = dj_settings.AWS_OPENSEARCH_HOST
        self.__client = opensearchpy.OpenSearch(
            hosts=[self.__host],
            use_ss=True,
            verify_certs=False,
            ssl_assert_hostname=False,
            ssl_show_warn=False,
        )

    def create_index(
        self, index_name: str, index_settings: typing.Dict = None
    ) -> typing.Tuple[bool, dict]:
        """
        Create the opensearch index.

        See https://opensearch.org/docs/latest/api-reference/index-apis/create-index/
        """
        try:
            _ = self.__client.indices.create(index_name, body=index_settings or {})
            return _.get("acknowledged", False), _
        except opensearchpy.exceptions.RequestError as exc:
            return False, exc.info

    def exists_index(self, index_name: str) -> bool:
        """
        The index exists API operation returns whether or not an index already exists.

        See https://opensearch.org/docs/latest/api-reference/index-apis/exists/
        """
        return self.__client.indices.exists(index_name)

    def delete_index(self, index_name: str) -> typing.Tuple[bool, dict]:
        """
        Delete the opensearch index.

        See https://opensearch.org/docs/latest/api-reference/index-apis/delete-index/
        """
        try:
            _ = self.__client.indices.delete(index=index_name)
            return _.get("acknowledged", False), _
        except opensearchpy.exceptions.NotFoundError as exc:
            return False, exc.info

    def get_index(self, index_name: str) -> typing.Any:
        """
        You can use the get index API operation to return information about an index.

        See https://opensearch.org/docs/latest/api-reference/index-apis/get-index/
        """
        try:
            return True, self.__client.indices.get(index=index_name).get(index_name)
        except opensearchpy.exceptions.NotFoundError as exc:
            return False, exc.info

    def close_index(self, index_name: str) -> typing.Any:
        """
        The close index API operation closes an index.

        See https://opensearch.org/docs/latest/api-reference/index-apis/close-index/
        """
        raise NotImplemented

    def open_index(self, index_name: str) -> typing.Any:
        """
        The open index API operation opens a closed index

        See https://opensearch.org/docs/latest/api-reference/index-apis/open-index/
        """
        raise NotImplemented

    def clone_index(self, source_index_name: str, target_index_name: str) -> typing.Any:
        """
        The clone index API operation clones all data in an existing read-only index into
        a new index

        See https://opensearch.org/docs/latest/api-reference/index-apis/clone/
        """
        try:
            _ = self.__client.indices.clone(index=source_index_name, target=target_index_name)
            return _.get("acknowledged", False), _
        except opensearchpy.exceptions.TransportError as exc:
            return False, exc.info

    def update_settings(self, index_name: str, settings: typing.Dict) -> typing.Any:
        """
        You can use the update settings API operation to update index-level settings.

        See https://opensearch.org/docs/latest/api-reference/index-apis/update-settings/
        """
        try:
            _ = self.__client.indices.put_settings(body=settings, index=index_name)
            return _.get("acknowledged", False), _
        except opensearchpy.exceptions.TransportError as exc:
            return False, exc.info

    def update_mapping(self, index_name: str, mapping: typing.Dict) -> typing.Any:
        """
        This operation to update mappings that already map to existing data in the index.

        See https://opensearch.org/docs/latest/api-reference/index-apis/put-mapping/
        """
        try:
            _ = self.__client.indices.put_mapping(body=mapping, index=index_name)
            return _.get("acknowledged", False), _
        except opensearchpy.exceptions.TransportError as exc:
            return False, exc.info

    def reindex(self, source_index_name: str, target_index_name: str) -> typing.Any:
        """
        The reindex operation copy all or a subset of documents that you select through a query to
        another index.

        See https://opensearch.org/docs/1.0/opensearch/reindex-data/
        """
        try:
            return True, self.__client.reindex(
                body={"source": {"index": source_index_name}, "dest": {"index": target_index_name}}
            )
        except opensearchpy.exceptions.TransportError as exc:
            return False, exc.info

    def count(
        self,
        index_name: str,
        query_type: QueryTypeEnum = None,
        query_parameters: typing.Dict = None,
    ) -> typing.Any:
        """
        The count API gives you quick access to the number of documents that match a query.

        See https://opensearch.org/docs/latest/api-reference/count/
        """
        try:
            return True, self.__client.count(
                index=index_name, body=QueryBuilder.build(query_type, query_parameters or {})
            )
        except opensearchpy.exceptions.TransportError as exc:
            return False, exc.info

    def update_by_query(
        self,
        index_name: str,
        painless_script: str,
        query_type: QueryTypeEnum = None,
        query_parameters: typing.Dict = None,
    ) -> typing.Any:
        ubq = update_by_query.UpdateByQuery(using=self.__client, index=index_name).script(
            **{"lang": "painless", "source": painless_script}
        )
        ubq = (
            ubq.filter(query_type.value, **query_parameters)
            if query_parameters is not None
            else ubq.filter(query_type.value)
        )

        try:
            return True, self.__client.update_by_query(index=index_name, body=ubq.to_dict())
        except opensearchpy.exceptions.TransportError as exc:
            return False, exc.info

    def index_document(
        self, index_name: str, document_body: typing.Dict, **kwargs
    ) -> typing.Tuple[bool, dict]:
        """
        Before you can search for data, you must first add documents. This operation adds a
        single document to your index.

        See https://opensearch.org/docs/latest/api-reference/document-apis/index-document/
        """
        return True, self.__client.index(index=index_name, body=document_body, **kwargs)

    def get_document(self, index_name: str, document_id: str) -> typing.Any:
        """
        The get document API operation to retrieve the document’s information and data

        See https://opensearch.org/docs/latest/api-reference/document-apis/get-documents/
        """
        raise NotImplemented

    @search_all_documents
    def get_documents(
        self,
        index: str,
        document_ids: typing.List,
        size: int = dj_settings.MAX_SEARCHING_SIZE,
        from_: int = 0,
        **kwargs,
    ) -> typing.Any:
        """
        The get document API operation to retrieve the document’s information and data

        See https://opensearch.org/docs/latest/api-reference/document-apis/get-documents/
        """
        query = {
            "query": {
                "ids": {"values": document_ids},
            }
        }
        try:
            return True, self.__client.search(
                body=query, index=index, size=size, from_=from_, **kwargs
            )
        except opensearchpy.exceptions.RequestError as exc:
            return False, exc.info

    def get_geo_bounding_box_clusters(
        self,
        index: typing.List[str],
        top_left: typing.Dict,
        bottom_right: typing.Dict,
        precision: int,
        query_type: QueryTypeEnum = QueryTypeEnum.MATCH_ALL,
        query_parameters: typing.Dict = None,
    ) -> typing.Tuple[bool, dict]:

        body = ""
        for idx in index:
            body += json.dumps({"index": idx}) + "\n"
            query = QueryBuilder.build(query_type, query_parameters or {})
            query["aggregations"] = GeoBoundingBoxAggregation().generate_aggregation(
                top_left=top_left, bottom_right=bottom_right, precision=precision
            )
            body += json.dumps(query) + "\n"

        return True, self.__client.msearch(body=body)

    def get_documents_in_bounding_box(
        self, index: typing.List[str], top_left: typing.Dict, bottom_right: typing.Dict
    ) -> typing.Tuple[bool, typing.Generator]:
        try:
            query = QueryBuilder.build(
                QueryTypeEnum.BOOL, {"must": [{QueryTypeEnum.MATCH_ALL: {}}]}
            )
            query["query"]["bool"].update(
                GeoBoundingBoxAggregation().generate_search_filter(top_left, bottom_right)
            )
            response = scan(self.__client, query=query, index=index)
            return True, response
        except opensearchpy.exceptions.RequestError as exc:
            return False, exc.info

    def update_document(
        self, index_name: str, document_id: str, document_body: typing.Dict
    ) -> typing.Any:
        """
        The update document API operation

        See https://opensearch.org/docs/latest/api-reference/document-apis/update-document/
        """
        raise NotImplemented

    def delete_document(self, index_name: str, document_id: str) -> typing.Any:
        """
        The delete document API operation

        See https://opensearch.org/docs/latest/api-reference/document-apis/delete-document/
        """
        raise NotImplemented

    def bulk(self, bulk_format_body: typing.List[typing.Dict]) -> typing.Tuple[bool, dict]:
        """
        This bulk operator allows you to carryout multiple document actions, on multiple document
        in one bulk operation. See the documentation for proper formatting. Each item in the
        bulk object contains an index name, operation, and document parts.

        See https://opensearch.org/docs/latest/api-reference/document-apis/bulk/
        """
        return True, self.__client.bulk(bulk_format_body)

    @search_all_documents
    def search(
        self,
        index: str = None,
        size: int = dj_settings.MAX_SEARCHING_SIZE,
        from_: int = 0,
        query_type: QueryTypeEnum = None,
        query_parameters: typing.Dict = None,
        **kwargs,
    ) -> typing.Tuple[bool, dict]:
        """
        The Search API operation lets you execute a search request to search your cluster for data.

        See https://opensearch.org/docs/latest/api-reference/search/
        """
        try:
            query = QueryBuilder.build(query_type, query_parameters or {}) if query_type else None

            response = self.__client.search(
                body=query, index=index, size=size, from_=from_, **kwargs
            )

            return True, response

        except QueryBuilderError as exc:
            return False, exc.args[0]
        except opensearchpy.exceptions.RequestError as exc:
            return False, exc.info

    @msearch_all_documents
    def multi_search(
        self,
        index: typing.List[str],
        query_type: typing.List[QueryTypeEnum],
        query_parameters: typing.List[dict],
        size: int = dj_settings.MAX_SEARCHING_SIZE,
        from_: int = 0,
        **kwargs,
    ) -> typing.Tuple[bool, dict]:
        """
        Multi-search
        See https://opensearch.org/docs/latest/api-reference/multi-search/

        :param index: A list of index names to be searched
        :param query_type: This parameter contains the type of queries for each index
        :param query_parameters: A list of query parameters for each index
        :param size:
        :param from_:
        """

        body = ""
        for i, idx in enumerate(index):
            body += json.dumps({"index": idx}) + "\n"
            parameters = query_parameters[i]
            parameters_kwargs = parameters.pop("kwargs", {})
            query = QueryBuilder.build(
                query_type[i],
                parameters,
                size=size,
                from_=from_,
                **parameters_kwargs,
            )

            if kwargs.get("highlight", []):
                query.update({"highlight": kwargs.get("highlight")[i]})

            body += json.dumps(query) + "\n"

        return True, self.__client.msearch(body=body)

    def get(self, path, payload):
        """
        Make proxy GET request
        """
        warnings.warn(
            "get will be removed in the next releases, please use some specific function "
            "instead.",
            DeprecationWarning,
        )
        return self.__make_request(requests.get, path, payload)

    def create(self, path, payload):
        """
        Make proxy POST request
        """
        warnings.warn(
            "create will be removed in the next releases, please use some specific function "
            "instead.",
            DeprecationWarning,
        )
        return self.__make_request(requests.post, path, payload)

    def update(self, path, payload):
        """
        Make proxy PUT request
        """
        warnings.warn(
            "update will be removed in the next releases, please use some specific function "
            "instead.",
            DeprecationWarning,
        )
        return self.__make_request(requests.put, path, payload)

    def delete(self, path, payload):
        """
        Make proxy DELETE request
        """
        warnings.warn(
            "delete will be removed in the next releases, please use some specific function "
            "instead.",
            DeprecationWarning,
        )
        return self.__make_request(requests.delete, path, payload)

    def __make_request(self, method, path, payload):
        url = f"{self.__host}/{path}"
        headers = {"Content-Type": "application/json"}
        response = method(url, headers=headers, data=payload)
        return Response(
            data={"data": response.json()},
            status=response.status_code,
        )
