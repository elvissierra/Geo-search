from django.urls import path

from geo_search_api.api.likes import views

urlpatterns = [
    path(
        "<str:object_type>/<uuid:object_id>/",
        views.LikesGetOrCreateOrDeleteView.as_view(),
        name="LikesGetOrCreateOrDelete",
    ),
    path("configuration/", views.LikesConfigurationGetView.as_view(), name="LikesConfigurationGet"),
]
