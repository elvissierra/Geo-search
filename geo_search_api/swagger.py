from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView


class SwaggerYamlView(SpectacularAPIView):
    authentication_classes = []


class SwaggerView(SpectacularSwaggerView):
    authentication_classes = []


class RedocView(SpectacularRedocView):
    authentication_classes = []


urlpatterns = [
    path("api/schema/", SwaggerYamlView.as_view(), name="schema"),
    path("api/schema/swagger-ui/", SwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/schema/redoc/", RedocView.as_view(url_name="schema"), name="redoc"),
]
