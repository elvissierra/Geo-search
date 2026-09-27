from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r"(?P<url>.*)$", views.opensearch, name="OpenSearch"),
]
