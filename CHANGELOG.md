# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Upgrade anyio to 4.6.2.post1
- Upgrade psycopg to 3.2.3
- Upgrade pyinstrument to 5.0.0
- Upgrade sentry-sdk to 2.17.0
- Upgrade sqlalchemy to 2.0.36
- Upgrade starlette to 0.40.0
- Upgrade uvicorn to 0.31.1

## [0.7.0] - 2024-09-09

### Changed

- Upgrade dynaconf to 3.2.6
- Upgrade pyarrow to 17.0.0
- Upgrade pyinstrument to 0.5.7
- Upgrade sentry-sdk to 2.13.0
- Upgrade SQLAlchemy to 2.0.32
- Upgrade starlette to 0.38.5
- Upgrade typer to 0.12.5
- Upgrade uvicorn to 0.30.6
- Recommend using psycopg3 driver for PostgreSQL

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

[unreleased]: https://github.com/jmaupetit/data7/compare/v0.7.0...main
[0.7.0]: https://github.com/jmaupetit/data7/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/jmaupetit/data7/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/jmaupetit/data7/compare/v0.4.1...v0.5.0
[0.4.1]: https://github.com/jmaupetit/data7/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/jmaupetit/data7/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/jmaupetit/data7/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/jmaupetit/data7/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/jmaupetit/data7/compare/27c4af8...v0.1.0
