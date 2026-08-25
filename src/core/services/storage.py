import os
import uuid
from typing import Protocol, BinaryIO

class FileStorageService(Protocol):
    def save(self, filename: str, stream: BinaryIO) -> str:
        ...
        
    def delete(self, path: str) -> None:
        ...

class LocalDiskStorage:
    def __init__(self, upload_folder: str) -> None:
        self._upload_folder = upload_folder
        os.makedirs(self._upload_folder, exist_ok=True)
        
    def save(self, filename: str, stream: BinaryIO) -> str:
        ext = os.path.splitext(filename)[1]
        safe_filename = f"{uuid.uuid4().hex}{ext}"
        file_path = os.path.join(self._upload_folder, safe_filename)
        os.makedirs(self._upload_folder, exist_ok=True)
        with open(file_path, "wb") as f:
            while chunk := stream.read(8192):
                f.write(chunk)
        return safe_filename
        
    def delete(self, path: str) -> None:
        if not path:
            return
        full_path = os.path.join(self._upload_folder, path)
        if os.path.exists(full_path):
            try:
                os.remove(full_path)
            except OSError:
                pass
