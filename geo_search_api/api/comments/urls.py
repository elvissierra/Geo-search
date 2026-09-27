from django.urls import path

from geo_search_api.api.comments import views

urlpatterns = [
    path(
        "<str:object_type>/<uuid:object_id>/<uuid:comment_id>/",
        views.CommentGetOrUpdateOrDeleteView.as_view(),
        name="CommentGetOrUpdateOrDelete",
    ),
    path(
        "<str:object_type>/<uuid:object_id>/",
        views.CommentsGetOrCreateView.as_view(),
        name="CommentsGetOrCreate",
    ),
    path(
        "configuration/",
        views.CommentsConfigurationGetView.as_view(),
        name="CommentsConfigurationGet",
    ),
]
