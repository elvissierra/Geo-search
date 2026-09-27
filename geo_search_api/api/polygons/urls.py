from django.urls import path
from geo_search_api.api.polygons import views

urlpatterns = [
    path("", views.PolygonsGetView.as_view(), name="PolygonsGet"),
    path("registry/", views.PolygonsRegistryGetView.as_view(), name="PolygonsRegistryGet"),
    path("documents/", views.PolygonsDocumentsPostView.as_view(), name="PolygonsDocumentsPost"),
]
