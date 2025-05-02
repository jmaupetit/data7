"""Tests for the data7.streamers module."""

import pyarrow as pa
from pyarrow import parquet

from data7.models import Dataset
from data7.streamers import sql2csv, sql2parquet


def test_sql2csv(db_engine):
    """Test sql2csv function."""
    dataset = Dataset(
        basename="customers",
        query=(
            "SELECT "
            "LastName as last_name, "
            "FirstName as first_name, "
            "Company as company "
            "FROM Customer "
            "ORDER BY last_name, first_name"
        ),
    )

    n_customers = 59
    output = list(
        filter(lambda x: len(x), "".join(sql2csv(db_engine, dataset)).split("\n"))
    )
    assert len(output) == n_customers + 1
    assert output[0] == "last_name,first_name,company"
    assert output[1] == "Almeida,Roberto,Riotur"
    assert output[-1] == "Zimmermann,Fynn,"


def test_sql2parquet(db_engine):
    """Test sql2parquet function."""
    dataset = Dataset(
        basename="customers",
        query=(
            "SELECT "
            "LastName as last_name, "
            "FirstName as first_name, "
            "Company as company "
            "FROM Customer "
            "ORDER BY last_name, first_name"
        ),
    )

    n_customers = 59
    with pa.BufferReader(
        b"".join(sql2parquet(db_engine, dataset, chunksize=10))
    ) as stream:
        customers = parquet.ParquetFile(stream)
        assert customers.metadata.num_rows == n_customers

        table = customers.read()
        assert str(table["last_name"][0]) == "Almeida"
        assert str(table["first_name"][0]) == "Roberto"
        assert str(table["company"][0]) == "Riotur"
        assert str(table["last_name"][-1]) == "Zimmermann"
        assert str(table["first_name"][-1]) == "Fynn"
        assert str(table["company"][-1]) == "None"
