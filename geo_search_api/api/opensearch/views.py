from urllib.parse import urlencode

from rest_framework.decorators import api_view
from drf_spectacular.utils import extend_schema
from drf_spectacular.openapi import OpenApiTypes

# from django.conf import settings
# from django.http import HttpResponseNotAllowed
#
# from geo_search_api.environments import PossibleEnvironments
from clients.opensearch import OpenSearchClient


@extend_schema(deprecated=True, responses=OpenApiTypes.OBJECT)
@api_view(["GET", "POST", "PUT", "DELETE"])
def opensearch(request, url):
    """
    Opensearch proxy requests
    """
    params = urlencode(request.GET)
    path = f"{url}?{params}" if params else url
    client = OpenSearchClient()

    # commented until UI will be ready for this changes
    # if settings.CURRENT_ENVIRONMENT in [PossibleEnvironments.PROD, PossibleEnvironments.STAGE]:
    #     if request.method != "GET":
    #         return HttpResponseNotAllowed(["POST", "PUT", "DELETE"], "Method not allowed.")
    #     return client.get(path, request.body)

    if request.method == "POST":
        return client.create(path, request.body)
    if request.method == "PUT":
        return client.update(path, request.body)
    if request.method == "DELETE":
        return client.delete(path, request.body)
    return client.get(path, request.body)
