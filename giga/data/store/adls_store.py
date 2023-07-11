import contextlib
import io
import logging
from typing import Any, List, Generator, IO
from azure.storage.blob import BlobServiceClient
from .data_store import DataStore
import os

from giga.utils.globals import COUNTRY_DEFAULT_RELATIVE_DIR

COUNTRY_DATA_DIR = "workspace"

# Configure the ADLS container and connection string for authentication
ADLS_CONNECTION_STRING = os.environ.get("ADLS_CONNECTION_STRING", "")
ADLS_CONTAINER = "cost-model"

# We use this logger to disable logs from the blob storage module
logger = logging.getLogger("adls_custom_logger")
logger.disabled = True


class ADLSDataStore(DataStore):
    """
    An implementation of DataStore for Azure Data Lake Storage.
    """

    def __init__(self, container=ADLS_CONTAINER):
        """
        Create a new instance of ADLSDataStore
        :param container: The name of the container in ADLS to interact with.
        """
        self.blob_service_client = BlobServiceClient.from_connection_string(ADLS_CONNECTION_STRING, logger=logger)
        self.container_client = self.blob_service_client.get_container_client(container=container)
        self.container = container

    def _adls_path(self, path: str) -> str:
        """
        Internally, we remap absolute filepaths to nicer-looking GCS buckets
        under /conf and /data directories. This also helps enforce the upload
        interface as we fail when encountering unexpected paths.
        """
        if COUNTRY_DEFAULT_RELATIVE_DIR in path:
            start_idx = path.index(COUNTRY_DEFAULT_RELATIVE_DIR) + len(COUNTRY_DEFAULT_RELATIVE_DIR)
            path = f"/conf/countries{path[start_idx:]}"
        elif COUNTRY_DATA_DIR in path:
            start_idx = path.index(COUNTRY_DATA_DIR) + len(COUNTRY_DATA_DIR)
            path = f"/data{path[start_idx:]}"
        else:
            raise ValueError(f"Path {path} is not configured to be stored in ADLS.")
        return path

    def read_file(self, path: str) -> Any:
        # blob = self.bucket.blob(self._adls_path(path))
        blob_file_path = self._adls_path(path)
        blob_client = self.blob_service_client.get_blob_client(container=self.container, blob=blob_file_path,
                                                               snapshot=None)
        return blob_client.download_blob(encoding='UTF-8').readall()

    def write_file(self, path: str, data: Any) -> None:
        # blob = self.bucket.blob(self._adls_path(path))
        blob_file_path = self._adls_path(path)
        blob_client = self.blob_service_client.get_blob_client(container=self.container, blob=blob_file_path,
                                                               snapshot=None)
        # blob.upload_from_string(data)
        binary_data = data.encode()
        blob_client.upload_blob(binary_data, overwrite=True)

    def file_exists(self, path: str) -> bool:
        blob_file_path = self._adls_path(path)
        blob_client = self.blob_service_client.get_blob_client(container=self.container, blob=blob_file_path,
                                                               snapshot=None)
        return blob_client.exists()

    def list_files(self, path: str) -> List[str]:
        blob_items = self.container_client.list_blobs(name_starts_with=self._adls_path(path))
        return [item['name'] for item in blob_items]

    def walk(self, top: str) -> Generator:
        top = self._adls_path(top)
        top = top.rstrip('/') + '/'
        blob_items = self.container_client.list_blobs(name_starts_with=top)
        blobs = [item['name'] for item in blob_items]
        for blob in blobs:
            dirpath, filename = os.path.split(blob)
            yield (dirpath, [], [filename])

    @contextlib.contextmanager
    def open(self, path: str, mode: str = 'r') -> IO:
        # read or write depending on operation
        if mode == 'w':
            # create file object that will be written to
            file = io.StringIO()
            yield file

            # save the data from the file object to blob storage
            data = file.getvalue()
            self.write_file(path, data)

        elif mode == 'r':
            # download the data from blob storage
            data = self.read_file(path)

            # add data to the file object so that it can be read
            file = io.StringIO(data)
            yield file

    def is_file(self, path: str) -> bool:
        return self.file_exists(path)

    def is_dir(self, path: str) -> bool:
        blobs = self.list_files(path=path)
        for blob in blobs:
            if blob != path:
                return True
        return False

    def rmdir(self, dir: str) -> None:
        blobs = self.list_files(dir)
        self.container_client.delete_blobs(*blobs)

    def remove(self, path: str) -> None:
        blob_file_path = self._adls_path(path)
        blob_client = self.blob_service_client.get_blob_client(container=self.container, blob=blob_file_path,
                                                               snapshot=None)
        if blob_client.exists():
            blob_client.delete_blob()
