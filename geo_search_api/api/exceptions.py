from rest_framework.exceptions import APIException


class InvalidTokenException(APIException):
    status_code = 401
    default_detail = "You do not have permission to perform this action."
    default_code = "Invalid Token"
