import boto3
from botocore.client import Config
from pathlib import Path
from typing import Optional


class S3Uploader:
    def __init__(
        self,
        endpoint_url: str,
        region: str,
        bucket: str,
        logger,
        access_key_id: Optional[str] = None,
        secret_access_key: Optional[str] = None,
        session_token: Optional[str] = None,
    ):
        self.bucket = bucket
        self.logger = logger

        client_kwargs = {
            "service_name": "s3",
            "endpoint_url": endpoint_url,
            "region_name": region,
            "config": Config(signature_version="s3v4"),
        }

        if access_key_id and secret_access_key:
            client_kwargs["aws_access_key_id"] = access_key_id
            client_kwargs["aws_secret_access_key"] = secret_access_key
            if session_token:
                client_kwargs["aws_session_token"] = session_token

        self.s3 = boto3.client(**client_kwargs)

    def upload_file(self, local_path: str, s3_key: str) -> None:
        lp = Path(local_path)
        if not lp.exists():
            raise FileNotFoundError(f"Missing file: {local_path}")

        self.logger.info(f"S3 UPLOAD s3://{self.bucket}/{s3_key}")
        self.s3.upload_file(str(lp), self.bucket, s3_key)
