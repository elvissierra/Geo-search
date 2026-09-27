from django.urls import re_path

from .views import StorageGetView, StoragePostView

urlpatterns = [
    re_path(
        r"(?P<bucket_name>[^\/]+)/(?P<file_path>.*)\/url$",
        StorageGetView.as_view(),
        name="StorageGet",
    ),
    re_path(r"(?P<bucket_name>[^\/]+)/url$", StoragePostView.as_view(), name="StoragePost"),
]
