from django.urls import path, include
from django.conf import settings

from geo_search_api.api.topics import views

#  will be filled in the next tasks
urlpatterns = []

if settings.SHOW_TOPICS_MANAGEMENT_API:
    urlpatterns.extend(
        [
            path("", views.TopicsGetOrCreateView.as_view(), name="TopicsGetOrCreate"),
            path(
                "<uuid:topic_id>/",
                views.TopicGetOrUpdateOrDeleteView.as_view(),
                name="TopicGetOrUpdateOrDelete",
            ),
            path(
                "<uuid:topic_id>/contributors/", include("geo_search_api.api.contributors.urls")
            ),
            path(
                "stages/",
                views.TopicStageGetOrCreateView.as_view(),
                name="TopicStageGetOrCreate",
            ),
            path(
                "stages/<uuid:topic_stage_id>/",
                views.TopicStageGetOrUpdateOrDeleteView.as_view(),
                name="TopicStageGetOrUpdateOrDelete",
            ),
            path("tags/", views.TopicTagsGetOrCreateView.as_view(), name="TopicTagsGetOrCreate"),
            path(
                "tags/<uuid:topic_tag_id>/",
                views.TopicTagGetOrUpdateOrDeleteView.as_view(),
                name="TopicTagGetOrUpdateOrDelete",
            ),
        ]
    )
