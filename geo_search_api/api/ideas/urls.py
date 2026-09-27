from django.urls import path

from geo_search_api.api.ideas import views

urlpatterns = [
    path(
        "",
        views.IdeasGetOrCreateView.as_view(),
        name="IdeasGetOrCreateView",
    ),
    path(
        "<uuid:idea_id>/",
        views.IdeaGetOrUpdateOrDeleteView.as_view(),
        name="IdeaGetOrUpdateOrDelete",
    ),
    path("status/", views.IdeaStatusUpdateView.as_view(), name="IdeaStatusUpdate"),
    path("trending/", views.IdeasTrendingGetView.as_view(), name="IdeasTrendingGet"),
]
