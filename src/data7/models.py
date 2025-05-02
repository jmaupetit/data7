"""Data7 models module."""

import logging
from dataclasses import dataclass
from enum import StrEnum
from typing import List, Optional

logger = logging.getLogger(__name__)


class Extension(StrEnum):
    """Supported formats extensions."""

    CSV = "csv"
    PARQUET = "parquet"


class MimeType(StrEnum):
    """MimeTypes for supported formats."""

    CSV = "text/csv"
    PARQUET = "application/vnd.apache.parquet"


@dataclass
class Dataset:
    """Dataset model."""

    basename: str
    query: str
    # Indexes can be defined for a dataset query
    indexes: Optional[List[str]] = None
