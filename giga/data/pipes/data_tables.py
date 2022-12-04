import os
import io
from typing import Literal, Union, Any
from pydantic import BaseModel, validator

from giga.schemas.geo import UniqueCoordinateTable
from giga.schemas.school import GigaSchoolTable

"""
The pydantic below provide pipelines that can be used to load
tabular data into the modeling application.
These pipelines can be configured to implement that aggregates this data
"""


class LocalTablePipeline(BaseModel):

    file_path: str
    table_type: Literal["school", "coordinate-map"]

    @validator("file_path")
    def must_be_valid_path(cls, v):
        if not os.path.isfile(v):
            raise ValueError(f"Invalid path to local data table {v}")
        return v

    @validator("file_path")
    def must_be_valid_table(cls, v):
        if not v.endswith(".csv"):
            raise ValueError(f"Invalid file table type, must be csv")
        return v

    def load(self):
        if self.table_type == "school":
            return GigaSchoolTable.from_csv(self.file_path)
        else:
            return UniqueCoordinateTable.from_csv(self.file_path)


class UploadedTablePipeline(BaseModel):

    uploaded_content: Any
    table_type: Literal["school", "coordinate-map"]

    def load(self):
        stream = io.BytesIO(self.uploaded_content)
        if self.table_type == "school":
            return GigaSchoolTable.from_csv(stream)
        else:
            return UniqueCoordinateTable.from_csv(stream)
