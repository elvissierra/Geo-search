from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckView(APIView):
    """
    .. todo:: Create and apply a serializer for this view. We get an error
              `Error [HealthCheckView]: unable to guess serializer` on view
              the swagger.
    """

    @staticmethod
    def get(request):
        """
        Get request to check connection
        """
        return Response(data={"message": "OK"}, status=status.HTTP_200_OK)


class HealthCheckClusterView(APIView):
    """
    .. todo:: Create and apply a serializer for this view. We get an error
              `Error [HealthCheckView]: unable to guess serializer` on view
              the swagger.
    """

    authentication_classes = []  # disables authentication

    @staticmethod
    def get(request):
        """
        Get request to check connection
        """
        return Response(data={"message": "OK"}, status=status.HTTP_200_OK)
