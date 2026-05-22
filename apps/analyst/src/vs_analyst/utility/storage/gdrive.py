from pathlib import Path
from vs_analyst.utility.storage.base import BaseStorageProvider

class GDriveStorageProvider(BaseStorageProvider):
    """
    Placeholder provider for Google Drive storage integration.
    Google Drive API setup requires OAuth2 / Service Account credentials.
    To be fully implemented in a future phase.
    """
    def __init__(self):
        pass

    def download_file(self, file_url_or_key: str, destination: Path) -> Path:
        raise NotImplementedError(
            "Google Drive storage provider is not implemented yet. "
            "Please configure the application to use S3StorageProvider."
        )

    def upload_file(self, local_path: Path, destination_key: str) -> str:
        raise NotImplementedError(
            "Google Drive storage provider is not implemented yet. "
            "Please configure the application to use S3StorageProvider."
        )
