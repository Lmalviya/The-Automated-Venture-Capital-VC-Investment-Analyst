from pathlib import Path
from urllib.parse import urlparse
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from vs_analyst.utility.storage.base import BaseStorageProvider
from vs_analyst.config import settings
from vs_analyst.utility.logs import get_logger

logger = get_logger(__name__)

class S3StorageProvider(BaseStorageProvider):
    def __init__(self):
        # Configure client connection details
        self.endpoint_url = settings.storage_config.endpoint_url
        self.aws_access_key_id = settings.storage_config.access_key
        # SecretStr requires get_secret_value()
        self.aws_secret_access_key = settings.storage_config.secret_key.get_secret_value()
        self.region_name = settings.storage_config.region_name
        self.default_bucket = settings.storage_config.bucket_name

        self.s3_client = boto3.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.region_name,
            config=Config(signature_version="s3v4"),
        )

    def _parse_url_or_key(self, file_url_or_key: str) -> tuple[str, str]:
        """
        Parses the input to determine the bucket and key.
        Supports:
          - s3://bucket-name/key/path
          - http://host:port/bucket-name/key/path
          - raw-key-path (falls back to default configured bucket)
        """
        parsed = urlparse(file_url_or_key)

        # 1. Scheme 's3' (s3://bucket/key)
        if parsed.scheme == "s3":
            bucket = parsed.netloc
            key = parsed.path.lstrip("/")
            logger.debug("Parsed S3 URI", bucket=bucket, key=key)
            return bucket, key

        # 2. HTTP/HTTPS URLs (http://host:port/bucket/key)
        elif parsed.scheme in ("http", "https"):
            path_parts = parsed.path.lstrip("/").split("/", 1)
            if len(path_parts) == 2:
                bucket, key = path_parts
                logger.debug("Parsed HTTP S3 URL", bucket=bucket, key=key)
                return bucket, key
            
        # 3. Fallback: treat as raw key in the default bucket
        if self.default_bucket:
            logger.debug("Treating input as raw key in default bucket", default_bucket=self.default_bucket, key=file_url_or_key)
            return self.default_bucket, file_url_or_key
            
        raise ValueError(f"Could not parse storage path '{file_url_or_key}' and no default bucket is configured.")

    def download_file(self, file_url_or_key: str, destination: Path) -> Path:
        bucket, key = self._parse_url_or_key(file_url_or_key)
        logger.info("Downloading file from S3", bucket=bucket, key=key, destination=str(destination))

        try:
            self.s3_client.download_file(bucket, key, str(destination))
            logger.info("File downloaded successfully", destination=str(destination))
            return destination
        except ClientError as e:
            logger.error("S3 ClientError downloading file", error=str(e), bucket=bucket, key=key)
            raise RuntimeError(f"Failed to download file from S3: {e}") from e
        except Exception as e:
            logger.error("Unexpected error downloading file", error=str(e), bucket=bucket, key=key)
            raise RuntimeError(f"Unexpected download error: {e}") from e

    def upload_file(self, local_path: Path, destination_key: str) -> str:
        if not local_path.exists():
            raise FileNotFoundError(f"Local file not found for upload: {local_path}")
            
        bucket = self.default_bucket
        if not bucket:
            raise ValueError("No default bucket configured for uploads.")
            
        logger.info("Uploading file to S3", bucket=bucket, key=destination_key, local_path=str(local_path))

        try:
            self.s3_client.upload_file(str(local_path), bucket, destination_key)
            logger.info("File uploaded successfully", bucket=bucket, key=destination_key)
            
            # Construct standard endpoint/bucket/key URL for reference
            if self.endpoint_url:
                return f"{self.endpoint_url.rstrip('/')}/{bucket}/{destination_key}"
            return f"s3://{bucket}/{destination_key}"
        except ClientError as e:
            logger.error("S3 ClientError uploading file", error=str(e), bucket=bucket, key=destination_key)
            raise RuntimeError(f"Failed to upload file to S3: {e}") from e
        except Exception as e:
            logger.error("Unexpected error uploading file", error=str(e), bucket=bucket, key=destination_key)
            raise RuntimeError(f"Unexpected upload error: {e}") from e
