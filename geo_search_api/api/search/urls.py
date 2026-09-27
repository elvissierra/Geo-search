from django.urls import path

from geo_search_api.api.search import views

urlpatterns = [
    path("", views.SearchGetView.as_view(), name="SearchGet"),
    path(
        "data-scape/",
        views.SearchDataScapeClustersGetView.as_view(),
        name="SearchDataScapeClustersGet",
    ),
    path(
        "data-scape/autocomplete/",
        views.SearchDataScapeAutocompleteGetView.as_view(),
        name="SearchDataScapeAutocompleteGet",
    ),
    path(
        "data-scape/multi/",
        views.SearchDataScapeMultiGetView.as_view(),
        name="SearchDataScapeMultiGet",
    ),
    path(
        "data-scape/documents",
        views.SearchDataScapeDocumentsPostView.as_view(),
        name="SearchDataScapeDocumentsPost",
    ),
    path(
        "data-scape/points/",
        views.SearchDataScapeDocumentsPointsGetView.as_view(),
        name="SearchDataScapeDocumentsPointsGet",
    ),
]
