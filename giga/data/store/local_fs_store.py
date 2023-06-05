import os
from typing import Any, List, Generator, IO
from .data_store import DataStore


class LocalFS(DataStore):
    """
    An implementation of DataStore for the local file system.
    This allows local configuration files to be deployed with
    the application.
    """

    def read_file(self, path: str) -> Any:
        with open(path, "r") as f:
            return f.read()

    def write_file(self, path: str, data: Any) -> None:
        with open(path, "w") as f:
            f.write(data)

    def file_exists(self, path: str) -> bool:
        return os.path.isfile(path)
    
    def list_files(self, path: str) -> List[str]:
        return [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
    
    def walk(self, top: str) -> Generator:
        return os.walk(top)
    
    def open(self, file: str, mode: str='r') -> IO:
        return open(file, mode)
    
    def is_file(self, path: str) -> bool:
        return os.path.isfile(path)
    
    def is_dir(self, path: str) -> bool:
        return os.path.isdir(path)
    
    def rmdir(self, path: str) -> None:
        os.rmdir(path)

    def remove(self, path: str) -> None:
        os.remove(path)