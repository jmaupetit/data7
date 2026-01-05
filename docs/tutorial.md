In this tutorial, you will learn how to set up a Data7 project using the
[Chinook database](https://github.com/lerocha/chinook-database/). Your project
will be named `open-chinook`.

## Install Data7

Data7 is a pure Python package hosted in
[PyPI](https://pypi.org/project/data7/). It can be installed using your favorite
package manager.

=== "Pip"

    ```sh
    # Create a directory for our new project
    mkdir open-chinook
    cd open-chinook

    # Create a virtual environment to work with
    python -m venv venv
    source venv/bin/activate

    # Install data7 with pip (in the active virtual environment)
    pip install data7
    ```

=== "Pipenv"

    ```sh
    # Create a directory for our new project
    mkdir open-chinook
    cd open-chinook

    # Set python release and create a virtual environment
    pipenv --python 3.11

    # Add data7 as a project dependency
    pipenv add data7
    ```

=== "Poetry"

    ```sh
    # Create a directory for our new project
    mkdir open-chinook
    cd open-chinook

    # Set up a new poetry project
    poetry init

    # Add data7 as a project dependency
    poetry add data7
    ```

=== "uv"

    ```sh
    # Create a directory for our new project
    mkdir open-chinook
    cd open-chinook

    # Set up a new uv project
    uv init

    # Add data7 as a project dependency
    uv add data7
    ```

Once installed, it comes with a
[CLI](https://en.wikipedia.org/wiki/Command-line_interface). As long as the
installation directory is in your `PATH`, the `data7` command can be invoked as
follow:

=== "Pip"

    ```sh
    data7 --help
    ```

=== "Pipenv"

    ```sh
    pipenv run data7 --help
    ```

=== "Poetry"

    ```sh
    poetry run data7 --help
    ```

=== "uv"

    ```sh
    uv run data7 --help
    ```

Expected command usage output should look like the following:

```
 Usage: data7 [OPTIONS] COMMAND [ARGS]...

╭─ Options ───────────────────────────────────────────────────────────────╮
│ --install-completion          Install completion for the current shell. │
│ --show-completion             Show completion for the current shell, to │
│                               copy it or customize the installation.    │
│ --help                        Show this message and exit.               │
╰─────────────────────────────────────────────────────────────────────────╯
╭─ Commands ──────────────────────────────────────────────────────────────╮
│ check   Check data7 project configuration.                              │
│ init    Initialize a data7 project.                                     │
│ run     Run data7 web server.                                           │
╰─────────────────────────────────────────────────────────────────────────╯
```

## Download the Chinook database

As we need data to expose in this tutorial, we will download the excellent
[Chinook database](https://github.com/lerocha/chinook-database/) in
[SQLite](https://www.sqlite.org/index.html) format using your favorite tool to
do so:

=== "Curl"

    ```sh
    curl -Lo chinook.db \
      https://github.com/lerocha/chinook-database/releases/download/v1.4.5/Chinook_Sqlite.sqlite
    ```

=== "Wget"

    ```sh
    wget -O chinook.db \
      https://github.com/lerocha/chinook-database/releases/download/v1.4.5/Chinook_Sqlite.sqlite
    ```

Make sure downloaded databases exists and is not empty (expected size should be
approximatively 1Mo):

```sh
du -sh chinook.db
```

Chinook
[database schema](https://github.com/lerocha/chinook-database/tree/master/ChinookDatabase/DataModel)
is available from the
[project's repository](https://github.com/lerocha/chinook-database):

![Chinook database schema](https://github.com/lerocha/chinook-database/assets/135025/cea7a05a-5c36-40cd-84c7-488307a123f4 "A diagram representation of the Chinook database")

## Initialize the project

Data7 requires few configuration files to be created before firing up the web
server. Those can be created using the `data7 init` command.

=== "Pip"

    ```sh
    data7 init
    ```

=== "Pipenv"

    ```sh
    pipenv run data7 init
    ```

=== "Poetry"

    ```sh
    poetry run data7 init
    ```

=== "uv"

    ```sh
    uv run data7 init
    ```

Three configuration files should have been created:

- `settings.yaml`: general application settings
- `data7.yaml`: exposed datasets configuration
- `.secrets.yaml`: private credentials such as the database connection URL

=== "settings.yaml"

    ```yaml
    #
    # Data7 application general settings
    #

    # ---- GLOBAL ----------------------------------
    global:
      # The base url path for dataset urls
      datasets_root_url: "/d"

      # Pandas chunks
      chunk_size: 5000
      schema_sniffer_size: 1000
      default_dtype_backend: pyarrow

      # Pyinstrument
      profiler_interval: 0.001
      profiler_async_mode: enabled

    # ---- DEFAULT ---------------------------------
    default:
      # Set debug to true for development, never for production!
      debug: false

      # Server
      # host:
      # port:

      # Sentry
      sentry_dsn: null
      sentry_traces_sample_rate: 1.0

      # Pyinstrument
      profiling: false

    # ---- PRODUCTION ------------------------------
    production:
      execution_environment: production

      # Set debug to true for development, never for production!
      debug: false

      # Server
      # host: data7.example.com
      # port: 8080

      # Sentry
      # sentry_dsn:
      # sentry_traces_sample_rate: 1.0

      # Pyinstrument
      profiling: false

    #
    # /!\ FEEL FREE TO REMOVE ENVIRONMENTS BELOW /!\
    #
    # ---- DEVELOPMENT -----------------------------
    development:
      execution_environment: development
      debug: true

      # Server
      host: "127.0.0.1"
      port: 8000

      # Pyinstrument
      profiling: true

    # ---- TESTING ---------------------------------
    testing:
      execution_environment: testing
    ```

=== ".secrets.yaml"

    ```yaml
    #
    # Data7 secrets.
    #
    # Feel free to adapt this file given your needs and environment.
    #

    # ---- DEFAULT ---------------------------------
    default:
      # DATABASE_URL: "sqlite:///example.db"

    # ---- PRODUCTION ------------------------------
    production:
      # DATABASE_URL: "sqlite:///example.db"

    #
    # /!\ FEEL FREE TO REMOVE ENVIRONMENTS BELOW /!\
    #
    # ---- DEVELOPMENT -----------------------------
    development:
      DATABASE_URL: "sqlite:///db/development.db"

    # ---- TESTING ---------------------------------
    testing:
      DATABASE_URL: "sqlite:///db/tests.db"
    ```

=== "data7.yaml"

    ```yaml
    #
    # Data7 datasets definition.
    #
    # Feel free to adapt this file given your needs and environment.
    #

    # ---- DEFAULT ---------------------------------
    default:
      datasets: []

    # ---- PRODUCTION ------------------------------
    production:
      datasets: []

    #
    # /!\ FEEL FREE TO REMOVE ENVIRONMENTS BELOW /!\
    #
    # ---- DEVELOPMENT -----------------------------
    development:
      datasets:
        - basename: invoices
          query: "SELECT * FROM Invoice"
        - basename: tracks
          query: >-
            SELECT Artist.Name as artist, Album.Title as title, Track.Name as track
            FROM Artist
            INNER JOIN Album ON Artist.ArtistId = Album.ArtistId
            INNER JOIN Track ON Album.AlbumId = Track.AlbumId
            ORDER BY Artist.Name, Album.Title

    # ---- TESTING ---------------------------------
    testing:
      datasets:
        - basename: dummy
          query: "SELECT 1"
    ```

!!! Tip

    As you may have noticed, Data7 supports configuring your application for
    multiple environments (_e.g._ development, testing, staging, production, etc.).
    In the following example, we will set up our environment as `development` by
    creating a `.env` file at the project root as follow:

    ```sh
    echo "ENV_FOR_DYNACONF=development" > .env
    ```

## Configure Data7

Before running our application, we need to set/check default example settings
for the development environment. First make sure that the development
`DATABASE_URL` points to downloaded Chinook database in the `.secrets.yaml`
file:

```yaml
# .secrets.yaml
development:
  DATABASE_URL: "sqlite:///chinook.db"
```

And check what datasets are defined in the `data7.yaml` file:

```yaml
# data7.yaml
development:
  datasets:
    - basename: invoices
      query: "SELECT * FROM Invoice"
    - basename: tracks
      query: >-
        SELECT Artist.Name as artist, Album.Title as title, Track.Name as track
        FROM Artist
        INNER JOIN Album ON Artist.ArtistId = Album.ArtistId
        INNER JOIN Track ON Album.AlbumId = Track.AlbumId
        ORDER BY Artist.Name, Album.Title
```

With this configuration, we expect to expose two datasets (`invoices` and
`tracks`). The `invoices` dataset is a pretty simple SQL table export while the
`tracks` dataset corresponds to a more complex query involving multiple SQL
tables.

!!! Warning

    The default configuration (`settings.yaml`) used to develop the Data7 project has
    been left untouched as it is perfectly fine for this tutorial. For a production
    environment, we invite you to properly set the `host` and `port` definitions.

## Validate configuration

To verify that your configuration respects project's requirements, Data7 comes
with a `data7 check` command. It can be handy to debug common issues you may
have while setting up your project.

=== "Pip"

    ```sh
    data7 check
    ```

=== "Pipenv"

    ```sh
    pipenv run data7 check
    ```

=== "Poetry"

    ```sh
    poetry run data7 check
    ```

=== "uv"

    ```sh
    uv run data7 check
    ```

If things are not properly configured, the command output will let you know what
seems buggy.

## Run the server

Now that everything is perfectly configured, you can run the Data7 server using
the `run` command:

=== "Pip"

    ```sh
    data7 run
    ```

=== "Pipenv"

    ```sh
    pipenv run data7 run
    ```

=== "Poetry"

    ```sh
    poetry run data7 run
    ```

=== "uv"

    ```sh
    uv run data7 run
    ```

And 💥 your Data7 server is running at: [localhost:8000](http://localhost:8000)

!!! Tip

    The development server listen to the `8000` port, if it's already in use, you
    may want to change the `port` setting (for the `development` environment) in
    the `settings.yaml` file or run the above command using another port:

    === "Pip"

        ```sh
        data7 run --port 8080
        ```

    === "Pipenv"

        ```sh
        pipenv run data7 run --port 8080
        ```

    === "Poetry"

        ```sh
        poetry run data7 run --port 8080
        ```

    === "uv"

        ```sh
        uv run data7 run --port 8080
        ```

If you are curious and test the root URL of your server, it should respond with
a 404 HTTP code (not found). This is perfectly expected as Data7 only serves
configured datasets following this pattern:
`/d/<dataset basename>.<dataset extension>`. For the `invoices` dataset (see
configuration above), it means that the two following endpoints should respond
properly:

- [localhost:8000/d/invoices.csv](http://localhost:8000/d/invoices.csv)
- [localhost:8000/d/invoices.parquet](http://localhost:8000/d/invoices.parquet)

You can test those using your favorite tool:

=== "Curl"

    The following command should display a CSV file in your terminal:

    ```sh
    curl localhost:8000/d/invoices.csv
    ```

    Or download it in Parquet format:


    ```sh
    curl -O localhost:8000/d/invoices.parquet
    ```

=== "Wget"

    The following command should download an `invoices.csv` file locally:

    ```sh
    wget localhost:8000/d/invoices.csv
    ```

    You can also test with the Parquet format:

    ```sh
    wget localhost:8000/d/invoices.parquet
    ```

!!! Question

    As you may have noticed, we've also defined a `tracks` dataset. We invite you
    to also test it following the previously defined URL pattern. And if you are
    curious, explore the Chinook database schema and be creative: create new
    datasets using more complex SQL queries. 💪

## Wrap up

In this tutorial, you have learned to create a new Data7 project from scratch.
The next step for real life usage is to connect Data7 with your production
database (PostgreSQL, MariaDB, etc.) and define your own datasets.

Keep it up!
