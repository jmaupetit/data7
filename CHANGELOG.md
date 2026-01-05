# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-01-05

### Changed 

- Update python version compatibility to >= 3.11
- Build the python package using `uv` & hatchling

## [0.13.2] - 2025-10-31

### Fixed 

- Upgrade starlette to 0.49.1

## [0.13.1] - 2025-10-31

### Changed

#### Dependencies

- Upgrade starlette to 0.49.1

## [0.13.0] - 2025-10-31

### Changed

#### Dependencies

- Upgrade dynaconf to 3.2.12
- Upgrade pandas to 2.3.3
- Upgrade pyinstrument to 5.1.1
- Upgrade sentry-sdk to 2.43.0
- Upgrade sqlalchemy to 2.0.44
- Upgrade starlette to 0.47.3
- Upgrade typer to 0.16.1

## [0.12.1] - 2025-07-24

### Changed

#### Dependencies

- Downgrade pyarrow to at least 20.0.0

## [0.12.0] - 2025-07-24

### Changed

#### Dependencies

- Upgrade pyarrow to 21.0.0
- Upgrade starlette to 0.47.2
- Upgrade typer to 0.16.0
- Upgrade uvicorn to 0.35.0

## [0.11.2] - 2025-05-16

### Changed

#### Dependencies

- Downgrade typer to at least 0.12.0

## [0.11.1] - 2025-05-16

### Changed

#### Dependencies

- Downgrade pandas to at least 2.1.4

## [0.11.0] - 2025-05-14

### Added

- Make database connection pool configurable

### Changed

#### Dependencies

- Upgrade psycopg to 3.2.9
- Upgrade sentry-sdk to 2.28.0

## [0.10.0] - 2025-05-09

### Added

- Stream datasets from the CLI using the new `stream` command

### Changed

#### Dependencies

- Upgrade dynaconf to 3.2.11
- Upgrade pandas to 2.2.3
- Upgrade pyarrow to 20.0.0
- Upgrade pyinstrument to 5.0.1
- Upgrade sentry-sdk to 2.27.0
- Upgrade sqlalchemy to 2.0.40
- Upgrade starlette to 0.46.2
- Upgrade typer to 0.15.3
- Upgrade uvicorn to 0.34.2

## [0.9.0] - 2025-01-07

### Changed

- Improve Sentry configuration (toggle tracing and configure profiling)

#### Dependencies

- Upgrade matplotlib to 3.10.0
- Upgrade pyarrow to 18.2.0
- Upgrade sentry-sdk to 2.18.0
- Upgrade starlette to 0.41.2
- Upgrade typer to 0.15.1
- Upgrade uvicorn to 0.32.1

## [0.8.0] - 2024-10-17

### Changed

#### Dependencies

- Upgrade anyio to 4.6.2.post1
- Upgrade psycopg to 3.2.3
- Upgrade pyinstrument to 5.0.0
- Upgrade sentry-sdk to 2.17.0
- Upgrade sqlalchemy to 2.0.36
- Upgrade starlette to 0.40.0
- Upgrade uvicorn to 0.31.1

## [0.7.0] - 2024-09-09

### Changed

- Recommend using psycopg3 driver for PostgreSQL

#### Dependencies

- Upgrade dynaconf to 3.2.6
- Upgrade pyarrow to 17.0.0
- Upgrade pyinstrument to 0.5.7
- Upgrade sentry-sdk to 2.13.0
- Upgrade SQLAlchemy to 2.0.32
- Upgrade starlette to 0.38.5
- Upgrade typer to 0.12.5
- Upgrade uvicorn to 0.30.6

## [0.6.0] - 2024-07-16

### Added

- Integrate pyinstrument profiler

### Changed

- Improve performances using Pandas

## [0.5.0] - 2024-07-08

### Changed

- Ignore datasets with a query returning no results instead of raising an error

### Fixed

- [CLI] `run` command `reload` option should not be enabled by default

## [0.4.1] - 2024-07-04

### Fixed

- [CLI] fix ignored `run` `--host` and `--port` options

## [0.4.0] - 2024-07-04

### Added

- Integrate Sentry

### Fixed

- Fix documentation typos

## [0.3.0] - 2024-07-03

### Added

- Add project documentation

## [0.2.0] - 2024-07-01

### Added

- Implement `data7` CLI

## [0.1.0] - 2024-06-26

### Added

- Implement CSV output format
- Implement Parquet output format

[unreleased]: https://github.com/jmaupetit/data7/compare/v1.0.0...main
[1.0.0]: https://github.com/jmaupetit/data7/compare/v0.13.2...v1.0.0
[0.13.2]: https://github.com/jmaupetit/data7/compare/v0.13.1...v0.13.2
[0.13.1]: https://github.com/jmaupetit/data7/compare/v0.13.0...v0.13.1
[0.13.0]: https://github.com/jmaupetit/data7/compare/v0.12.1...v0.13.0
[0.12.1]: https://github.com/jmaupetit/data7/compare/v0.12.0...v0.12.1
[0.12.0]: https://github.com/jmaupetit/data7/compare/v0.11.2...v0.12.0
[0.11.2]: https://github.com/jmaupetit/data7/compare/v0.11.1...v0.11.2
[0.11.1]: https://github.com/jmaupetit/data7/compare/v0.11.0...v0.11.1
[0.11.0]: https://github.com/jmaupetit/data7/compare/v0.10.0...v0.11.0
[0.10.0]: https://github.com/jmaupetit/data7/compare/v0.9.0...v0.10.0
[0.9.0]: https://github.com/jmaupetit/data7/compare/v0.8.0...v0.9.0
[0.8.0]: https://github.com/jmaupetit/data7/compare/v0.7.0...v0.8.0
[0.7.0]: https://github.com/jmaupetit/data7/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/jmaupetit/data7/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/jmaupetit/data7/compare/v0.4.1...v0.5.0
[0.4.1]: https://github.com/jmaupetit/data7/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/jmaupetit/data7/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/jmaupetit/data7/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/jmaupetit/data7/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/jmaupetit/data7/compare/27c4af8...v0.1.0
