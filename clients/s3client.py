import json
from enum import Enum

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError


class S3Operation(Enum):
    PUT = "put_object"
    GET = "get_object"


class S3Client:
    def __init__(self):
        self.client = boto3.client("s3", config=Config(signature_version="s3v4"))
        self.presigned_url_expiration_time_put_object = 5 * 60
        self.presigned_url_expiration_time_get_object = 60 * 60

    def list_file_names(self, prefix, bucket_name):
        """
        List file names in given bucket under prefix directory
        :param prefix: directory to check
        :param bucket_name: bucket name to get files from
        :return: List with file names in bucket inside prefix directory
        """
        response = self.client.list_objects(Bucket=bucket_name, Prefix=prefix)
        return [content.get("Key") for content in response.get("Contents", [])]

    def read_file(self, file_location, bucket_name):
        """
        Download file from s3
        :param file_location: location of file in bucket
        :param bucket_name: name of bucket to get file from
        :return: True
        """
        try:
            result = json.loads(
                self.client.get_object(Bucket=bucket_name, Key=file_location)["Body"]
                .read()
                .decode()
            )
        except ClientError as exc:
            raise exc
        return result

    def get_presigned_url(
        self, file_location, bucket_name, operation: S3Operation = S3Operation.GET
    ):
        """
        Get presigned url to download/upload files to s3
        :param file_location: Exact location of file in s3
        :param bucket_name: Bucket name to get url for
        :param operation: get_object, put_object
        :return: presigned url
        """
        params = {
            "Bucket": bucket_name,
            "Key": file_location,
        }
        expiration_time = self.presigned_url_expiration_time_get_object
        if operation == S3Operation.PUT:
            expiration_time = self.presigned_url_expiration_time_put_object
            params.update({"ServerSideEncryption": "AES256"})
        url = self.client.generate_presigned_url(
            ClientMethod=operation.value,
            Params=params,
            ExpiresIn=expiration_time,
        )
        return url
