# Data7 - Dynamic datasets the easy way

> Pronounced data·set (7 like _sept_ in French).

## The idea :bulb:

**TL;DR** Data7 is a high performance web server that generates dynamic datasets
(in [CSV](https://en.wikipedia.org/wiki/Comma-separated_values) or [Parquet](https://en.wikipedia.org/wiki/Apache_Parquet) formats) from existing databases and stream them over HTTP
:tada:

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
    database: postgresql://user@host:port/wonderful-places
    query: "SELECT * FROM restaurant"
```

Fire up the `data7` server:

```
data7 start
```

And :boom: your dataset is available at:

- [https://data7.wonderful-places.org/d/restaurants.csv](https://data7.wonderful-places.org/d/restaurants.csv)
- [https://data7.wonderful-places.org/d/restaurants.parquet](https://data7.wonderful-places.org/d/restaurants.parquet)

## License

This work is released under the MIT License (see [LICENSE](./LICENSE)).
