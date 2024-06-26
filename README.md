# Data7 - Dynamic datasets the easy way

> Pronounced data·set (**7** like **sept** in French).

![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/jmaupetit/data7/quality.yml)
![PyPI - Version](https://img.shields.io/pypi/v/data7)


## The idea 💡

**TL;DR** Data7 is a high performance web server that generates dynamic datasets
(in [CSV](https://en.wikipedia.org/wiki/Comma-separated_values) or
[Parquet](https://en.wikipedia.org/wiki/Apache_Parquet) formats) from existing
databases and stream them over HTTP 🎉

### Example usage

Let say you have a `restaurant` table in your `wonderful-places` PostgreSQL
database, and you want to make this table an always-up-to-date dataset that can
be easily used by the rest of the world. All you have to do is edit Data7
configuration as follow:

```yaml
#
# Data7 configuration file
#
# config.yaml
#
datasets:
  - basename: restaurants
    query: "SELECT * FROM restaurant"
```

Fire up the `data7` server:

```
data7 start
```

And :boom: your dataset is available at:

- [https://data7.wonderful-places.org/d/restaurants.csv](https://data7.wonderful-places.org/d/restaurants.csv)
- [https://data7.wonderful-places.org/d/restaurants.parquet](https://data7.wonderful-places.org/d/restaurants.parquet)

## Getting started

To quickly start contributing to this project, we got you covered! Once you've
cloned the project, use GNU Make to ease your life (`make` and `curl` are
required).

```sh
# Clone the project somewhere on your system
git clone git@github.com:jmaupetit/data7.git

# Enter the project's root directory
cd data7

# Prepare your working environment
make bootstrap
```

You can now start the development server:

```sh
make run
```

Test development endpoints:

```sh
# CSV format (displayed in the terminal)
curl http://localhost:8000/d/invoices.csv

# Parquet format (downloaded locally)
curl -O http://localhost:8000/d/invoices.parquet

# Check that the file exists
ls invoices.parquet
```

You can run quality checks using dedicated GNU Make rules:

```sh
# Run the tests suite
make test

# Linters!
make lint
```

Happy hacking 😻

## License

This work is released under the MIT License (see [LICENSE](./LICENSE)).
