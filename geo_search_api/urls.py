from django.urls import path, include
from django.conf import settings

from geo_search_api.environments import PossibleEnvironments
from geo_search_api import swagger


urlpatterns = [
    # Temporary comment this line.
    # path("api/admin/", admin.site.urls),
    path("api/topics/", include("geo_search_api.api.topics.urls")),
    path("api/notes/", include("geo_search_api.api.notes.urls")),
    path("api/likes/", include("geo_search_api.api.likes.urls")),
    path("api/comments/", include("geo_search_api.api.comments.urls")),
    path("api/ideas/", include("geo_search_api.api.ideas.urls")),
    path("api/storage/", include("geo_search_api.api.storage.urls")),
    path("api/opensearch/", include("geo_search_api.api.opensearch.urls")),
    path("api/search/", include("geo_search_api.api.search.urls")),
    path("api/health_check/", include("geo_search_api.api.health_check.urls")),
    path("api/polygons/", include("geo_search_api.api.polygons.urls")),
]


if settings.CURRENT_ENVIRONMENT != PossibleEnvironments.PROD:
    urlpatterns.extend(swagger.urlpatterns)
