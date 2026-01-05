## Install dependencies

Contributing to Data7 requires the following dependencies to be installed:

- [GNU Make](https://www.gnu.org/software/make/)
- [Curl](https://curl.se/)
- [uv](https://docs.astral.sh/uv/)

!!! Note

    Depending on your operating system, use your favorite package manager
    (`brew`, `apt`, `pacman`, ...) to install them!

## Bootstrap the project

To quickly start contributing to this project, we've got you covered! Once
you've forked/cloned the project, use GNU Make to ease your life:

```sh
# Clone the forked project somewhere on your system
git clone git@github.com:my_username/data7.git

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

## Quality checks

You can run tests and linters using dedicated GNU Make rules:

```sh
# Run the tests suite
make test

# Linters!
make lint
```

Happy hacking 😻
