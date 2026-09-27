from django.urls import path

from geo_search_api.api.contributors import views

urlpatterns = [
    path("", views.ContributorsGetOrCreateView.as_view(), name="ContributorsGetOrCreate"),
    path(
        "<uuid:contributor_id>/",
        views.ContributorsGetUpdateDeleteView.as_view(),
        name="ContributorsGetUpdateDelete",
    ),
]
