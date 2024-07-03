# Data7 ⚡ Open your data in minutes

> Pronounced data·set (**7** like **sept** in French).

![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/jmaupetit/data7/quality.yml)
![PyPI - Version](https://img.shields.io/pypi/v/data7)

## The idea 💡

**TL;DR** Data7 is a high performance web server that generates dynamic datasets
(in [CSV](https://en.wikipedia.org/wiki/Comma-separated_values) or
[Parquet](https://en.wikipedia.org/wiki/Apache_Parquet) formats) from existing
databases and streams them over HTTP 🎉

## A quick example

Let say you have a `restaurant` table in your PostgreSQL database, and you want
to make this table an always-up-to-date dataset that can be easily used by the
rest of the world.

All you have to do is to initialize your project:

```sh
data7 init
```

✍️ Edit configuration files:

```yaml
# settings.yaml
production:
  host: "https://data7.wonderful-places.org"
  port: 80

# .secrets.yaml
production:
  DATABASE_URL: "postgresql+asyncpg://user:pass@server:port/wonderful-places"

# data7.yaml
production:
  datasets:
    - basename: restaurants
      query: "SELECT * FROM restaurant"
```

🏎️ Fire up the `data7` server:

```sh
data7 run
```

💥 Your dataset is available at:

- [https://data7.wonderful-places.org/d/restaurants.csv](https://data7.wonderful-places.org/d/restaurants.csv)
  (CSV)
- [https://data7.wonderful-places.org/d/restaurants.parquet](https://data7.wonderful-places.org/d/restaurants.parquet)
  (Parquet)

## Documentation

The complete documentation of the project is avaiable at:
[https://jmaupetit.github.io/data7/](https://jmaupetit.github.io/data7/)

## License

This work is released under the MIT License.
