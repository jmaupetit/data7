"""Tests for the data7.app module."""

from pathlib import PurePath

import pyarrow as pa
import pytest
from data7.app import (
    Dataset,
    Extension,
    app,
    get_dataset_from_url,
    get_routes_from_datasets,
    populate_datasets,
    sql2csv,
    sql2parquet,
    stream_dataset,
)
from data7.config import settings
from pyarrow import parquet
from starlette.status import HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_501_NOT_IMPLEMENTED
from starlette.testclient import TestClient


@pytest.mark.anyio
async def test_populate_datasets(monkeypatch):
    """Test the populate_datasets function."""
    employees_query = (
        "SELECT "
        "LastName as last_name, "
        "FirstName as first_name, "
        "city as city "
        "FROM Employee"
    )

    customers_query = (
        "SELECT "
        "LastName as last_name, "
        "FirstName as first_name, "
        "Company as company "
        "FROM Customer"
    )

    monkeypatch.setattr(
        settings,
        "datasets",
        [
            {
                "basename": "employees",
                "query": employees_query,
            },
            {
                "basename": "customers",
                "query": customers_query,
            },
        ],
    )
    datasets = await populate_datasets()
    assert datasets == [
        Dataset(
            basename="employees",
            query=employees_query,
            fields=["last_name", "first_name", "city"],
        ),
        Dataset(
            basename="customers",
            query=customers_query,
            fields=["last_name", "first_name", "company"],
        ),
    ]


@pytest.mark.anyio
async def test_populate_datasets_with_invalid_query(monkeypatch):
    """Test the populate_datasets function when user defined an invalid query."""
    employees_query = (
        "SELECT "
        "LastName as last_name, "
        "FirstName as first_name, "
        "city as city "
        "FROM Employee "
        "WHERE LastName = 'Doe'"
    )

    monkeypatch.setattr(
        settings,
        "datasets",
        [
            {
                "basename": "employees",
                "query": employees_query,
            },
        ],
    )

    with pytest.raises(
        ValueError, match="Dataset 'employees' query returned no result"
    ):
        await populate_datasets()

    employees_query = (
        "SELECT "
        "LastName as last_name, "
        "FirstName as first_name, "
        "city as city "
        "FROM Employe "
        "WHERE LastName = 'Doe'"
    )

    monkeypatch.setattr(
        settings,
        "datasets",
        [
            {
                "basename": "employees",
                "query": employees_query,
            },
        ],
    )

    with pytest.raises(
        ValueError, match="Dataset 'employees' query failed, maybe SQL is invalid"
    ):
        await populate_datasets()


def test_get_dataset_from_url():
    """Test the get_dataset_from_url function."""
    datasets = [
        Dataset(
            basename="employees",
            query=(
                "SELECT "
                "LastName as last_name, "
                "FirstName as first_name, "
                "city as city "
                "FROM Employee"
            ),
            fields=["last_name", "first_name", "city"],
        ),
        Dataset(
            basename="customers",
            query=(
                "SELECT "
                "LastName as last_name, "
                "FirstName as first_name, "
                "Company as company "
                "FROM Customer"
            ),
            fields=["last_name", "first_name", "company"],
        ),
    ]

    dataset, extension = get_dataset_from_url(PurePath("/d/customers.csv"), datasets)
    assert dataset.basename == "customers"
    assert extension == Extension.CSV

    dataset, extension = get_dataset_from_url(
        PurePath("/d/customers.parquet"), datasets
    )
    assert dataset.basename == "customers"
    assert extension == Extension.PARQUET

    # Unsupported extension
    with pytest.raises(ValueError, match="Data7 extension 'xls' is not supported"):
        get_dataset_from_url(PurePath("/d/customers.xls"), datasets)

    # Unknown dataset
    with pytest.raises(ValueError, match="Requested dataset is not registered"):
        get_dataset_from_url(PurePath("/d/tracks.csv"), datasets)


def test_get_routes_from_datasets():
    """Test get_routes_from_datasets utility."""
    datasets = [
        Dataset(
            basename="employees",
            query=(
                "SELECT "
                "LastName as last_name, "
                "FirstName as first_name, "
                "city as city "
                "FROM Employee"
            ),
            fields=["last_name", "first_name", "city"],
        ),
        Dataset(
            basename="customers",
            query=(
                "SELECT "
                "LastName as last_name, "
                "FirstName as first_name, "
                "Company as company "
                "FROM Customer"
            ),
            fields=["last_name", "first_name", "company"],
        ),
    ]
    routes = get_routes_from_datasets(datasets)
    assert routes[0].path == "/d/employees.csv"
    assert routes[1].path == "/d/employees.parquet"
    assert routes[2].path == "/d/customers.csv"
    assert routes[3].path == "/d/customers.parquet"


@pytest.mark.anyio
async def test_sql2csv():
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
        fields=["last_name", "first_name", "company"],
    )

    n_customers = 59
    output = [row async for row in sql2csv(dataset)]
    assert len(output) == n_customers + 1
    assert output[0] == "last_name,first_name,company\r\n"
    assert output[1] == "Almeida,Roberto,Riotur\r\n"
    assert output[-1] == "Zimmermann,Fynn,\r\n"

    # Dataset as no fields defined
    dataset.fields = None
    with pytest.raises(
        ValueError, match="Requested dataset 'customers' has no defined fields"
    ):
        async for _ in sql2csv(dataset):
            pass


@pytest.mark.anyio
async def test_sql2parquet(monkeypatch):
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
        fields=["last_name", "first_name", "company"],
    )

    monkeypatch.setattr(settings, "PARQUET_BATCH_SIZE", 10)

    n_customers = 59
    with pa.BufferReader(b"".join([b async for b in sql2parquet(dataset)])) as stream:
        customers = parquet.ParquetFile(stream)
        assert customers.metadata.num_rows == n_customers
        assert customers.metadata.num_columns == len(dataset.fields)

        table = customers.read()
        assert str(table["last_name"][0]) == "Almeida"
        assert str(table["first_name"][0]) == "Roberto"
        assert str(table["company"][0]) == "Riotur"
        assert str(table["last_name"][-1]) == "Zimmermann"
        assert str(table["first_name"][-1]) == "Fynn"
        assert str(table["company"][-1]) == "None"


def test_stream_dataset_route():
    """Test data7 application stream_dataset view."""
    app.state.datasets = [
        Dataset(
            basename="employees",
            query=(
                "SELECT "
                "LastName as last_name, "
                "FirstName as first_name, "
                "city as city "
                "FROM Employee"
            ),
            fields=["last_name", "first_name", "city"],
        ),
        Dataset(
            basename="customers",
            query=(
                "SELECT "
                "LastName as last_name, "
                "FirstName as first_name, "
                "Company as company "
                "FROM Customer"
            ),
            fields=["last_name", "first_name", "company"],
        ),
    ]
    for route in get_routes_from_datasets(app.state.datasets):
        app.add_route(route.path, route.endpoint)

    client = TestClient(app)

    # Employees - CSV
    response = client.get("/d/employees.csv")
    assert response.status_code == HTTP_200_OK
    assert response.text.startswith("last_name,first_name,city")

    # Employees - Parquet
    response = client.get("/d/employees.parquet")
    assert response.status_code == HTTP_200_OK

    # Customers - CSV
    response = client.get("/d/customers.csv")
    assert response.status_code == HTTP_200_OK
    assert response.text.startswith("last_name,first_name,company")

    # Customers - Parquet
    response = client.get("/d/customers.parquet")
    assert response.status_code == HTTP_200_OK

    # Customer - unknown format
    response = client.get("/d/customers.xls")
    assert response.status_code == HTTP_404_NOT_FOUND

    # Add a special route with unsupported extension (this cannot happen)
    app.add_route("/d/customers.xls", stream_dataset)
    response = client.get("/d/customers.xls")
    assert response.status_code == HTTP_501_NOT_IMPLEMENTED
    assert response.text == "Data7 extension 'xls' is not supported"
