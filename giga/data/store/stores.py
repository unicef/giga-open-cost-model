
from .data_store import DataStore
from .gcs_store import GCSDataStore
from .local_fs_store import LocalFS

# Global Data Store instances. 
LOCAL_FS_STORE: DataStore = LocalFS()
GCS_BUCKET_STORE: DataStore = None  # GCSDataStore()

# Configure which storage to use for country data here.
COUNTRY_DATA_STORE: DataStore = LOCAL_FS_STORE  #  GCS_BUCKET_STORE