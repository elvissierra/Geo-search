from dataclasses import dataclass
import time
import json
import boto3
import botocore
import base64


@dataclass
class ExceptionLogMessage:
    """Structure for logging exceptions"""

    cloudwatch_id: str
    application_name: str
    url: str
    body: str
    error_name: str
    error_traceback: str


class SecretManager:
    class DataAboutSecret:
        def __init__(self, secret_arn: str):
            self.secret_arn = secret_arn
            self.last_refresh_timestamp = 0
            self.data = {}

    __refresh_time_sec: int = 3 * 60 * 60  # every 3 hours
    __secrets: dict[str, DataAboutSecret] = {}
    aws_region: str = "us-east-1"

    def add_secret(self, name: str, data_about_secret: DataAboutSecret):
        self.__secrets[name] = data_about_secret

    def get_secret(self, name: str):
        if name not in self.__secrets:
            return None

        secret = self.__secrets[name]
        if time.time() - secret.last_refresh_timestamp < self.__refresh_time_sec:
            return secret.data

        secret = self.__get_secret(secret)
        self.__secrets[name] = secret
        return secret.data

    def __get_secret(self, secret: DataAboutSecret):

        session = boto3.session.Session()
        client = session.client(service_name="secretsmanager", region_name=self.aws_region)
        try:
            get_secret_value_response = client.get_secret_value(SecretId=secret.secret_arn)
        except botocore.exceptions.ClientError as e:
            raise e
        else:
            secret_string = (
                get_secret_value_response["SecretString"]
                if "SecretString" in get_secret_value_response
                else base64.b64decode(get_secret_value_response["SecretBinary"])
            )
            try:
                secret.data = json.loads(secret_string)
            except json.decoder.JSONDecodeError:
                secret.data = secret_string
            secret.last_refresh_timestamp = time.time()
        return secret
