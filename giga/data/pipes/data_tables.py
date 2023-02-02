import os
import io
from typing import Literal
from pydantic import BaseModel, validator

from giga.schemas.geo import UniqueCoordinateTable
from giga.schemas.school import GigaSchoolTable
from giga.schemas.cellular import CellTowerTable
from giga.schemas.distance_cache import (
    SingleLookupDistanceCache,
    MultiLookupDistanceCache,
    GreedyConnectCache,
)

"""
The pydantic below provide pipelines that can be used to load
tabular data into the modeling application.
These pipelines can be configured to implement that aggregates this data
"""


class LocalTablePipeline(BaseModel):

    file_path: str
    table_type: Literal["school", "cell-towers", "coordinate-map"]

    @validator("file_path")
    def must_be_valid_path(cls, v):
        if not os.path.isfile(v):
            raise ValueError(f"Invalid path to local data table {v}")
        return v

    @validator("file_path")
    def must_be_valid_table(cls, v):
        if not v.endswith(".csv"):
            raise ValueError("Invalid file table type, must be csv")
        return v

    def load(self):
        if self.table_type == "school":
            return GigaSchoolTable.from_csv(self.file_path)
        if self.table_type == "cell-towers":
            return CellTowerTable.from_csv(self.file_path)
        else:
            return UniqueCoordinateTable.from_csv(self.file_path)


class LocalJSONPipeline(BaseModel):

    file_path: str
    data_type: Literal["cellular-distance", "school-distance"]

    @validator("file_path")
    def must_be_valid_path(cls, v):
        if not os.path.isfile(v):
            raise ValueError(f"Invalid path to local data table {v}")
        return v

    @validator("file_path")
    def must_be_valid_table(cls, v):
        if not v.endswith(".json"):
            raise ValueError("Invalid file table type, must be json")
        return v

    def load(self):
        return SingleLookupDistanceCache.from_json(self.file_path)


class LocalConnectCachePipeline(BaseModel):

    workspace: str

    @validator("workspace")
    def must_be_valid_dir(cls, v):
        if not os.path.isdir(v):
            raise ValueError(f"Invalid workspace {v}")
        return v

    def load(self, **kwargs):
        return GreedyConnectCache.from_workspace(self.workspace, **kwargs)


class UploadedTablePipeline(BaseModel):

    uploaded_content: memoryview
    table_type: Literal["school", "coordinate-map"]

    class Config:
        arbitrary_types_allowed = True

    def load(self):
        stream = io.BytesIO(self.uploaded_content)
        if self.table_type == "school":
            return GigaSchoolTable.from_csv(stream)
        else:
            return UniqueCoordinateTable.from_csv(stream)
