from rest_framework import status
from rest_framework.test import APIClient


def test_health_check(test_app):
    response = test_app.get("/api/health_check/")
    assert response.status_code == status.HTTP_200_OK
    assert response.data == {"message": "OK"}


def test_health_check_cluster():
    test_app = APIClient()
    response = test_app.get("/api/health_check/cluster")
    assert response.status_code == status.HTTP_200_OK
    assert response.data == {"message": "OK"}
