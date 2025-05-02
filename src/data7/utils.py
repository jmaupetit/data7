"""Data7 utils module."""

import logging
from typing import List

from sqlalchemy import Engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.sql import text

from .config import settings
from .models import Dataset

logger = logging.getLogger(__name__)


def populate_datasets(engine: Engine) -> List[Dataset]:
    """Validate configured datasets and get sql query expected field names."""
    logging.debug("Will populate datasets given configuration...")
    datasets = []

    with engine.connect() as conn:
        for raw_dataset in settings.datasets:
            dataset = Dataset(**raw_dataset)

            # Validate database query and get expected field names
            try:
                result = conn.execute(text(dataset.query))
            except OperationalError as exc:
                raise ValueError(
                    f"Dataset '{dataset.basename}' query failed, maybe SQL is invalid"
                ) from exc

            # Query returns no result, we cannot set fields.
            if result.scalar() is None:
                logger.warning(
                    "'%s' query returned no result, dataset will be ignored",
                    dataset.basename,
                )
                continue

            datasets.append(dataset)

    logger.info("Active datasets: %s", ", ".join(d.basename for d in datasets))
    return datasets
