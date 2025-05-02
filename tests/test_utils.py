"""Tests for the data7.utils module."""

import pytest

from data7.config import settings
from data7.models import Dataset
from data7.utils import populate_datasets


def test_populate_datasets(db_engine, monkeypatch):
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
    datasets = populate_datasets(db_engine)
    assert datasets == [
        Dataset(
            basename="employees",
            query=employees_query,
        ),
        Dataset(
            basename="customers",
            query=customers_query,
        ),
    ]


def test_populate_datasets_with_invalid_query(db_engine, monkeypatch):
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

    datasets = populate_datasets(db_engine)
    assert len(datasets) == 0

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
        populate_datasets(db_engine)
