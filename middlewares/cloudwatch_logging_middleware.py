import logging
import traceback
from utils import ExceptionLogMessage
import dataclasses
import json
import uuid
from rest_framework import status

IGNORE_ENDPOINTS = {"/health_check"}
JSON_HEADER = "application/json"


class CloudwatchLoggingMiddleware:
    def __init__(self, get_response):
        self._get_response = get_response
        self._logger = logging.getLogger("watchtower")
        self._log_message = None
        self._last_error_name = ""

    def process_exception(self, request, exception):
        tb = [
            msg.strip()
            for msg in traceback.format_exception(
                type(exception), value=exception, tb=exception.__traceback__
            )
        ]
        query_params = request.META.get("QUERY_STRING")
        url = f"{request.method} {request.path_info}{'?' + query_params if len(query_params) > 0 else ''}"  # noqa
        self._log_message = ExceptionLogMessage(
            str(uuid.uuid4()), "geo-search", url, self.body, str(exception), tb
        )

    def __call__(self, request):

        try:
            self.body = json.loads(request.body) if request.method != "GET" and request.body else {}
        except ValueError:
            self.body = {}
        response = self._get_response(request)
        if response.status_code < status.HTTP_500_INTERNAL_SERVER_ERROR:
            if request.path not in IGNORE_ENDPOINTS:
                if JSON_HEADER in response.headers["content-type"]:
                    self._logger.debug(response.data)
                else:
                    self._logger.debug(f"{request.method} {request.path} {response.status_code}")
        else:
            if (
                self._log_message is not None
                and self._last_error_name != self._log_message.error_name
            ):
                self._logger.error(dataclasses.asdict(self._log_message))
                self._last_error_name = self._log_message.error_name
            else:
                if JSON_HEADER in response.headers["content-type"]:
                    self._logger.error(response.data)
                    self._last_error_name = response.data.get("detail")
                else:
                    error_message = (
                        f"{request.method} {request.path} "
                        f"{response.status_code} {response.reason_phrase}"
                    )
                    self._logger.error(error_message)
                    self._last_error_name = error_message
        return response
