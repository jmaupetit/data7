# -- General
SHELL := /bin/bash
CHINOOK_DB_URL = https://github.com/lerocha/chinook-database/releases/download/v1.4.5/Chinook_Sqlite.sqlite

# ==============================================================================
# RULES

default: help

# -- Files
db/development.db:
	mkdir -p db
	curl -Ls -o db/development.db $(CHINOOK_DB_URL)

db/tests.db: db/development.db
	cd db && ln -s development.db tests.db

data7.yaml:
	ln -s src/data7/data7.yaml.dist data7.yaml

.secrets.yaml:
	ln -s src/data7/.secrets.yaml.dist .secrets.yaml

settings.yaml:
	ln -s src/data7/settings.yaml.dist settings.yaml

# -- Docker/compose
bootstrap: ## bootstrap the project for development
bootstrap: \
	data7.yaml \
	.secrets.yaml \
	settings.yaml \
	db/tests.db \
	build
.PHONY: bootstrap

build: ## install project
	poetry install
.PHONY: build

check: ## check data7 configuration
	poetry run data7 check
.PHONY: check


docs: ## build Data7 documentation
	poetry run mkdocs build
.PHONY: docs

docs-publish: ## publish Data7 documentation
	poetry run mkdocs gh-deploy --force
.PHONY: docs-publish

docs-serve: ## run Data7 documentation server
	poetry run mkdocs serve -a localhost:8888
.PHONY: docs-serve

run: ## run the api server
	poetry run data7 run --log-level debug --reload
.PHONY: run

# -- API
lint: ## lint all sources
lint: \
	lint-black \
	lint-ruff \
  lint-mypy
.PHONY: lint

lint-black: ## lint python sources with black
	@echo 'lint:black started…'
	poetry run black src/data7 tests scripts
.PHONY: lint-black

lint-black-check: ## check python sources with black
	@echo 'lint:black check started…'
	poetry run black --check src/data7 tests scripts
.PHONY: lint-black-check

lint-ruff: ## lint python sources with ruff
	@echo 'lint:ruff started…'
	poetry run ruff check src/data7 tests scripts
.PHONY: lint-ruff

lint-ruff-fix: ## lint and fix python sources with ruff
	@echo 'lint:ruff-fix started…'
	poetry run ruff check --fix src/data7 tests scripts
.PHONY: lint-ruff-fix

lint-mypy: ## lint python sources with mypy
	@echo 'lint:mypy started…'
	poetry run mypy src/data7 tests scripts
.PHONY: lint-mypy


test: ## run tests
	poetry run pytest
.PHONY: test

# -- Misc
help:
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
.PHONY: help
