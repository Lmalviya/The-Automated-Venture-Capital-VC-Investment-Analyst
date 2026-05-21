from pathlib import Path
from urllib.parse import urlparse

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from vs_analyst.config import settings

def download_object(
    file_url: str,
    local_dir: str = "downloads",
    filename: str | None = None,
    log
) -> str:
    """
    Download object from:
    - AWS S3
    - MinIO
    - Any S3-compatible storage

    Examples:
    ---------
    s3://bucket/file.pdf

    https://bucket.s3.amazonaws.com/file.pdf

    http://localhost:9000/my-bucket/file.pdf

    https://minio.example.com/my-bucket/file.pdf
    """

    log.info("Parse file url")
    parsed = urlparse(file_url)

    bucket = None
    key = None

    # s3://bucket/key
    if parsed.scheme == "s3":
        bucket = parsed.netloc
        key = parsed.path.lstrip("/")
        log.info("file path is aws s3 url", bucket=bucket, key=key)
        
    else:
        path_parts = parsed.path.lstrip("/").split("/", 1)

        if len(path_parts) != 2:
            log.error("minio file is invalid url formate", url=file_url, path_parts=path_parts)
            raise ValueError("Invalid object URL format")

        bucket, key = path_parts
        log.info("file path is minio url", bucket=bucket, key=key)

    # Create local directory
    local_path = Path(local_dir)
    local_path.mkdir(parents=True, exist_ok=True)

    # Filename
    if filename is None:
        filename = Path(key).name

    destination = local_path / filename
    log.info(f"local directory path to store file: {destination}")

    # S3-compatible client
    s3_client = boto3.client(
        "s3",
        endpoint_url=settings.Object_db.endpoint_url,
        aws_access_key_id=settings.Object_db.aws_access_key_id,
        aws_secret_access_key=settings.Object_db.aws_secret_access_key,
        region_name=settings.Object_db.region_name,
        config=Config(signature_version="s3v4"),
    )

    try:
        s3_client.download_file(bucket, key, str(destination) )
        log.info(f"file download successfully at {destination}")
    except ClientError as e:
        log.error(f"Failed to download file, error: {e}", error=str(e))
        raise RuntimeError(f"Download failed: {e}") from e

    return str(destination)