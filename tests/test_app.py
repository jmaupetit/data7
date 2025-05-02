"""Tests for the data7.app module."""

from pathlib import PurePath

import pytest
from starlette.status import HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_501_NOT_IMPLEMENTED
from starlette.testclient import TestClient

from data7.app import (
    app,
    get_dataset_from_url,
    get_routes_from_datasets,
    stream_dataset,
)
from data7.models import Dataset, Extension


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
        ),
    ]
    routes = get_routes_from_datasets(datasets)
    assert routes[0].path == "/d/employees.csv"
    assert routes[1].path == "/d/employees.parquet"
    assert routes[2].path == "/d/customers.csv"
    assert routes[3].path == "/d/customers.parquet"


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


def test_profiling_middleware():
    """Test the profiling middleware."""
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
        ),
    ]
    for route in get_routes_from_datasets(app.state.datasets):
        app.add_route(route.path, route.endpoint)

    client = TestClient(app)

    response = client.get("/d/employees.csv?profile=1")
    assert response.status_code == HTTP_200_OK
    assert "pyinstrumentHTMLRenderer" in response.text

    # Even with a random value, profiling is activated
    response = client.get("/d/employees.csv?profile=0")
    assert response.status_code == HTTP_200_OK
    assert "pyinstrumentHTMLRenderer" in response.text

    # `profile` query parameter should be associated with a value
    response = client.get("/d/employees.csv?profile")
    assert response.status_code == HTTP_200_OK
    assert response.text.startswith("last_name,first_name,city")
