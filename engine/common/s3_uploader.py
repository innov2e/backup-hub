import boto3
from botocore.client import Config
from pathlib import Path

class S3Uploader:
    def __init__(self, endpoint_url: str, region: str, bucket: str, logger):
        self.bucket = bucket
        self.logger = logger
        self.s3 = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            region_name=region,
            config=Config(signature_version="s3v4"),
        )

    def upload_file(self, local_path: str, s3_key: str) -> None:
        lp = Path(local_path)
        if not lp.exists():
            raise FileNotFoundError(f"Missing file: {local_path}")

        self.logger.info(f"S3 UPLOAD s3://{self.bucket}/{s3_key}")
        self.s3.upload_file(str(lp), self.bucket, s3_key)
