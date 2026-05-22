from abc import ABC, abstractmethod
from pathlib import Path

class BaseStorageProvider(ABC):
    @abstractmethod
    def download_file(self, file_url_or_key: str, destination: Path) -> Path:
        """
        Downloads a file from storage to a local path.
        
        Args:
            file_url_or_key: The reference key or full URL of the object in storage.
            destination: Absolute local path to write the downloaded file to.
            
        Returns:
            Absolute path to the downloaded local file.
        """
        pass

    @abstractmethod
    def upload_file(self, local_path: Path, destination_key: str) -> str:
        """
        Uploads a local file to storage.
        
        Args:
            local_path: Absolute path to the local file to upload.
            destination_key: Remote key/path for the file in storage.
            
        Returns:
            The remote path or URL representing the stored file.
        """
        pass
