
from .data_store import DataStore
from .gcs_store import GCSDataStore
from .adls_store import ADLSDataStore
from .local_fs_store import LocalFS

# Global Data Store instances. 
LOCAL_FS_STORE: DataStore = LocalFS()
GCS_BUCKET_STORE: DataStore = None  # GCSDataStore()
ADLS_CONTAINER_STORE: DataStore = ADLSDataStore()

# Configure which storage to use for country data here.
COUNTRY_DATA_STORE: DataStore = ADLS_CONTAINER_STORE  # LOCAL_FS_STORE  #  GCS_BUCKET_STORE

# Storge for schools and costs for now
SCHOOLS_DATA_STORE: DataStore = ADLSDataStore(container="giga")
