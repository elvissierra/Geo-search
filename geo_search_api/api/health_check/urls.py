from django.urls import path

from .views import HealthCheckView, HealthCheckClusterView

urlpatterns = [
    path("", HealthCheckView.as_view()),
    path("cluster", HealthCheckClusterView.as_view()),
]
