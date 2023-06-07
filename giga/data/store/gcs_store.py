from typing import Any, List, Generator, IO
from google.cloud import storage
from .data_store import DataStore
import os
import gcsfs
import json
import urllib.parse

from giga.utils.globals import COUNTRY_DEFAULT_RELATIVE_DIR

COUNTRY_DATA_DIR = "workspace"

# Configure the Google Cloud Storage bucket and JSON authentication.
GCS_BUCKET_NAME = 'giga-hosted-country-data'
# Configure the Google Cloud project this bucket lives in
GCS_PROJECT = 'actual-common'
# Configured for deployment in prod.yaml
GCS_CRED_DATA = os.environ.get("OBJSTORE_GCS_CREDS", "{}")

class GCSDataStore(DataStore):
    """
    An implementation of DataStore for Google Cloud Storage.
    """

    def __init__(self):
        """
        Create a new instance of GCSDataStore.
        :param bucket_name: The name of the bucket in GCS to interact with.
        :param service_account_key_file: The path to the service account key file.
        """
        cred_data = json.loads(GCS_CRED_DATA)
        self.client = storage.Client.from_service_account_info(cred_data)
        self.bucket = self.client.get_bucket(GCS_BUCKET_NAME)
        self.fs = gcsfs.GCSFileSystem(project=GCS_PROJECT, token=cred_data)
    
    def _gcs_path(self, path: str) -> str:
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
            raise ValueError(f"Path {path} is not configured to be stored in GCS.")
        return path

    def read_file(self, path: str) -> Any:
        blob = self.bucket.blob(self._gcs_path(path))
        return blob.download_as_text()

    def write_file(self, path: str, data: Any) -> None:
        blob = self.bucket.blob(self._gcs_path(path))
        blob.upload_from_string(data)

    def file_exists(self, path: str) -> bool:
        blob = self.bucket.blob(self._gcs_path(path))
        return blob.exists()
    
    def list_files(self, path: str) -> List[str]:
        blobs = self.client.list_blobs(self.bucket, prefix=self._gcs_path(path))
        return [blob.name for blob in blobs if not blob.name.endswith('/')]
    
    def walk(self, top: str) -> Generator:
        top = self._gcs_path(top)
        top = top.rstrip('/') + '/'
        blobs = self.client.list_blobs(self.bucket, prefix=top)
        for blob in blobs:
            dirpath, filename = os.path.split(blob.name)
            yield (dirpath, [], [filename])

    def open(self, file: str, mode: str='r') -> IO:
        fs_path = f"{GCS_BUCKET_NAME}/{self._gcs_path(file)}"
        return self.fs.open(fs_path, mode)
    
    def is_file(self, path: str) -> bool:
        return self.file_exists(path)
    
    def is_dir(self, path: str) -> bool:
        blobs = self.client.list_blobs(self.bucket, prefix=self._gcs_path(path))
        for blob in blobs:
            if blob.name != path:
                return True
        return False
    
    def rmdir(self, dir: str) -> None:
        blobs = self.client.list_blobs(self.bucket, prefix=self._gcs_path(dir))
        for blob in blobs:
            blob.delete()

    def remove(self, path: str) -> None:
        blob = self.bucket.blob(self._gcs_path(path))
        if blob.exists():
            blob.delete()