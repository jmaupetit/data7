Data7 configuration is splitted over three different files:

1. `settings.yaml`: general server configuration
2. `.secrets.yaml`: all sensible settings or credentials for Data7
3. `data7.yaml`: the datasets definition

All configuraiton files respect general and specific rules that we will describe
in detail in the following sections.

## General rules

### Settings can be defined for multiple environments

Data7 configuration management is based on the
[Dynaconf library](https://www.dynaconf.com). It supports defining settings
given a particular environment. Meaning that you can define different values for
the same setting depending on the environment your instance is associated with.
By environment we mean, `development`, `testing`, `staging`, `production` to
name a few.

You can define as many environments as you need. If none is active for the
current instance (more on this later), Data7 will look for a `default`
configuration.

```yaml
# settings.yaml
default:
  # The default value if no other environment is defined or active
  debug: false

development:
  debug: true

testing:
  # Speed up tests
  debug: false

staging:
  # Better not expose logs publicly
  debug: false

production:
  # Strongly recommended
  debug: false
```

To **activate** a particular environment for your instance, you have two
options:

1. Define the `ENV_FOR_DYNACONF` environment variable with the environment name
   you want to activate, _e.g._ `ENV_FOR_DYNACONF=staging`.
2. Set the `ENV_FOR_DYNACONF` value in a `.env` file:

```env
ENV_FOR_DYNACONF=development
```

### Setting names are case-insensitive

This is an important rule: each setting can be define in upper or lower case,
_e.g._ `debug` and `DEBUG` are the same setting.

!!! Tip "Tip for contributors"

    As a consequence, you can define your settings in lower case because it's
    more readable in your YAML configuration:

    ```yaml
    debug: true
    ```

    And use the upper case form in the code:

    ```python
    from data7.conf import settings


    print(f"{settings.DEBUG=}")
    ```

### Settings can be overridden using environment variables

Every setting can be overridden by defining the corresponding environment
variable (in uppercase) prefixed by `DATA7_`, _e.g._ for the `debug` setting,
you can define the `DATA7_DEBUG=false` environment variable to override the
value defined in the `settings.yaml` file.

### Use `data7 init` to boostrap your configuration

Data7 comes with a CLI that can help you boostraping your project (see the
[tutorial](./tutorial.md)). Remember that the `data7 init` command will generate
the three required configuration files for you. Once generated it's up to you to
define your own environments and change setting values to suit your needs.

## Configuration details

### `settings.yaml`

---

#### `DATASETS_ROOT_URL`

The root URL that will prefix dataset URLs (_e.g._ the `/d` in `/d/invoices.csv`
for the `invoices` dataset.)

Default: `/d`

---

#### `CHUNK_SIZE`

Size of batches to process, _i.e._ the number of SQL query result rows to
process at each iteration.

Default: `5000`

---

#### `SCHEMA_SNIFFER_SIZE`

The number of SQL query result rows used to infer a table schema (data types).

Default: `1000`

---

#### `DEFAULT_DTYPE_BACKEND`

The backend used to infer data types while fetching data from the database.
Possible values are: `numpy_nullable` or `pyarrow` (see
[Pandas documentation](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.convert_dtypes.html)).

Default: `pyarrow`

---

#### `PROFILER_INTERVAL`

From
[pyinstrument's](https://pyinstrument.readthedocs.io/en/latest/reference.html#pyinstrument.Profiler.interval)
documentation:

> The minimum time, in seconds, between each stack sample. This translates into
> the resolution of the sampling.

Default: `0.001`

---

#### `PROFILER_ASYNC_MODE`

From
[pyinstrument's](https://pyinstrument.readthedocs.io/en/latest/reference.html#pyinstrument.Profiler.async_mode)
documentation:

> Configures how this Profiler tracks time in a program that uses async/await.

Default: `enabled`

---

#### `DEBUG`

Set to `true` to enable debugging mode, logs and server response will be more
explicit.

Default: `false`

!!! Warning

    We strongly recommend to keep default `false` value when running Data7 in production.

---

#### `PROFILING`

(De)Activate server request profiling. If set to `True`, adding the `?profile=1`
argument to HTTP requests returns the profiling analysis instead of the expected
requested dataset.

Example query:
[http://localhost:8000/d/invoices.csv?profile=1](http://localhost:8000/d/invoices.csv?profile=1)

Default: `false`

---

#### `HOST`

This is the host socket will be bind to. It can be an IPv4 or IPv6 address, or a
fully qualified domain name (_e.g._ `data7.example.org`). Set this to `0.0.0.0`
if you want your application to be available from your local network.

Default: `None` (required)

---

#### `PORT`

This the host port the socket will be bind to. It is classicaly set to `8000`
for a Python application.

Default: `None` (required)

---

#### `EXECUTION_ENVIRONMENT`

Used by [Sentry](https://sentry.io/) to track the environment of raised issue.

Default: `None`

---

#### `SENTRY_DSN`

The DSN of your Sentry project, _e.g._ `https://account@sentry.io/project_id`.
When not set, Sentry integration is not active.

Default: `None`

---

#### `SENTRY_ENABLE_TRACING`

Toggle Sentry performance tracking feature.

Default: `True`

---

#### `SENTRY_TRACES_SAMPLE_RATE`

The sample rate of traces sent to sentry: 1.0 means 100% while 0.1 means 10%. It
should be adapted for production.

Default: `1.0`

---

#### `SENTRY_PROFILES_SAMPLE_RATE`

The sample rate of profiles sent to sentry: 1.0 means 100% while 0.1 means 10%.
It should be adapted for production.

Default: `1.0`

---

### `.secrets.yaml`

---

#### `DATABASE_URL`

The URL that will be used by Data7 for database connections. It uses the
classical pattern:

`<database engine>://<user>:<password>@<host>:<port>/<database name>`

!!! Info

    Data7 supports all asynchronous database engines supported by the
    [databases library](https://www.encode.io/databases/). Depending on
    your database engine, you may need to **add the related database driver
    to your project dependencies**.

Supposing your database user is `data7`, its password is `secret` and the
database name you will query is `chinook`, depending on the database engine and
driver you want to use, here is a table that summarizes dependencies you need to
install and `DATABASE_URL` example values.

| Database   | Dependency             | Example value                                              |
| ---------- | ---------------------- | ---------------------------------------------------------- |
| PostgreSQL | `psycopg[binary,pool]` | `postgresql+psycopg://data7:secret@localhost:5432/chinook` |
| MySQL      | `mariadb-connector`    | `mysql://data7:secret@localhost:3306/chinook`              |
| SQLite     | -                      | `sqlite:///chinook.db`                                     |

---

### `data7.yaml`

---

#### `DATASETS`

This is the core setting of your Data7 instance. `DATASETS` is a list of dataset
definitions. Each dataset is defined by:

- a `basename`: the base name of your dataset will be used in its URL (_e.g._
  `/d/invoices.csv` for the `invoices` basename) and thus the corresponding file
  name when you will fetch its content.
- a `query`: the SQL query that will be executed to fetch data.

You will find example definitions for the `development` environment:

```yaml
datasets:
  # Base dataset exposing all table records
  #
  - basename: invoices
    query: "SELECT * FROM Invoice"

  # A more complex dataset using related tables
  #
  - basename: tracks
    query: >-
      SELECT Artist.Name as artist, Album.Title as title, Track.Name as track
      FROM Artist
      INNER JOIN Album ON Artist.ArtistId = Album.ArtistId
      INNER JOIN Track ON Album.AlbumId = Track.AlbumId
      ORDER BY Artist.Name, Album.Title
```

!!! Tip

    Remember that this file's syntax should be validity
    [YAML](https://en.wikipedia.org/wiki/YAML). Each database query should also
    be valid. You can check both YAML and SQL validity using the `data7 check`
    command.
