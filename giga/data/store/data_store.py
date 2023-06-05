from abc import ABC, abstractmethod
from typing import Any, List, Generator, IO


class DataStore(ABC):
    """
    Abstract base class for a data store. This can be a local filesystem,
    Google Cloud Storage, or any other system where you can store data.
    """

    @abstractmethod
    def read_file(self, path: str) -> Any:
        """
        Read a file from the data store.
        :param path: Path to the file in the data store.
        :return: The content of the file.
        """
        pass

    @abstractmethod
    def write_file(self, path: str, data: Any) -> None:
        """
        Write data to a file in the data store.
        :param path: Path to the file in the data store.
        :param data: The data to write.
        """
        pass

    @abstractmethod
    def file_exists(self, path: str) -> bool:
        """
        Check if a file exists in the data store.
        :param path: Path to the file in the data store.
        :return: True if the file exists, False otherwise.
        """
        pass

    @abstractmethod
    def list_files(self, path: str) -> List[str]:
        """
        Lists all files in a given directory path.
        :param path: The directory path.
        :return: A list of file names.
        """
        pass

    @abstractmethod
    def walk(self, top: str) -> Generator:
        """
        Generate the file names in a directory tree by walking the tree either top-down or bottom-up.
        For each directory in the tree rooted at directory top, it yields a 3-tuple: (dirpath, dirnames, filenames).
        :param top: The root directory path.
        """
        pass

    @abstractmethod
    def open(self, file: str, mode: str='r') -> IO:
        """
        Open a file.
        :param file: The file path.
        :param mode: The mode in which the file is opened.
        :return: a file object.
        """
        pass

    @abstractmethod
    def is_file(self, path: str) -> bool:
        """
        Check if the path points to a file.
        :param path: The file path.
        :return: True if the path points to a file, False otherwise.
        """
        pass

    @abstractmethod
    def is_dir(self, path: str) -> bool:
        """
        Check if the path points to a directory.
        :param path: The path to check.
        :return: True if the path is a directory, False otherwise.
        """
        pass

    @abstractmethod
    def remove(self, path: str) -> None:
        """
        Attempts to remove a file
        """
        pass

    @abstractmethod
    def rmdir(self, dir: str) -> None:
        """
        Attempts to remove a directory and its contents
        """
        pass