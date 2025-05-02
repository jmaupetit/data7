"""Data7 models module."""

import logging
from dataclasses import dataclass
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class Dataset:
    """Dataset model."""

    basename: str
    query: str
    # Indexes can be defined for a dataset query
    indexes: Optional[List[str]] = None
