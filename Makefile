# Makefile for common development tasks.

APP_NAME := volt

# Latest version of supported Python.
PYTHON_VERSION := 3.10.4

# Name of virtualenv for development.
ENV_NAME ?= $(APP_NAME)-dev

# Non-pyproject.toml dependencies.
PIP_DEPS := poetry poetry-dynamic-versioning pre-commit

## Toggle for dev setup with pyenv.
WITH_PYENV ?= 1

# Cross-platform adjustments.
SYS := $(shell uname 2> /dev/null)
ifeq ($(SYS),Linux)
GREP_EXE := grep
else ifeq ($(SYS),Darwin)
GREP_EXE := ggrep
else
$(error Unsupported development platform)
endif

# Docker image name.
GIT_TAG    := $(shell git describe --tags --always --dirty 2> /dev/null || echo "untagged")
GIT_COMMIT := $(shell git rev-parse --quiet --verify HEAD || echo "?")
GIT_DIRTY  := $(shell test -n "`git status --porcelain`" && echo "-dirty" || true)
BUILD_TIME := $(shell date -u '+%Y-%m-%dT%H:%M:%SZ')
IMG_NAME   := ghcr.io/bow/$(APP_NAME)

IS_RELEASE := $(shell ((echo "${GIT_TAG}" | $(GREP_EXE) -qE "^v?[0-9]+\.[0-9]+\.[0-9]+$$") && echo '1') || true)
ifeq ($(IS_RELEASE),1)
IMG_TAG    := $(GIT_TAG)
else
IMG_TAG    := latest
endif

## Rules ##

all: help


.PHONY: build
build:  ## Build wheel and source dist.
	poetry build
	twine check dist/*


.PHONY: clean
clean:  ## Remove build artifacts, including built Docker images.
	rm -rf build/ dist/ && (docker rmi $(IMG_NAME) 2> /dev/null || true)


.PHONY: help
help:  ## Show this help.
	$(eval PADLEN=$(shell $(GREP_EXE) -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| cut -d':' -f1 \
		| awk '{cur = length($$0); lengths[cur] = lengths[cur] $$0 ORS; max=(cur > max ? cur : max)} END {printf "%s", max}' \
		|| (true && echo 0)))
	@($(GREP_EXE) --version > /dev/null 2>&1 || (>&2 "error: GNU grep not installed"; exit 1)) \
		&& printf "\033[36m◉ %s dev console\033[0m\n" "$(APP_NAME)" >&2 \
		&& $(GREP_EXE) -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
			| awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m» \033[33m%*-s\033[0m \033[36m· \033[0m%s\n", $(PADLEN), $$1, $$2}' \
			| sort


.PHONY: img
img:  ## Build and tag the Docker container.
	docker build --build-arg REVISION=$(GIT_COMMIT)$(GIT_DIRTY) --build-arg BUILD_TIME=$(BUILD_TIME) --tag $(IMG_NAME):$(IMG_TAG) .


.PHONY: install-dev
install-dev:  ## Configure a local development setup.
	@if command -v pyenv virtualenv > /dev/null 2>&1 && [ "$(WITH_PYENV)" == "1" ]; then \
		printf "Configuring a local dev environment using pyenv ...\n" >&2 \
			&& pyenv install -s "$(PYTHON_VERSION)" \
			&& pyenv virtualenv -f "$(PYTHON_VERSION)" "$(ENV_NAME)" \
			&& printf "%s\n%s" "$(ENV_NAME)" "$(PYTHON_VERSION)" > .python-version \
			&& source "$(shell pyenv root)/versions/$(ENV_NAME)/bin/activate" \
			&& pip install --upgrade pip && pyenv rehash \
			&& pip install $(PIP_DEPS) && pyenv rehash \
			&& poetry config experimental.new-installer false \
			&& poetry config virtualenvs.in-project true \
			&& poetry install && pyenv rehash \
			&& pre-commit install && pyenv rehash \
			&& printf "Done.\n" >&2; \
	else \
		printf "Configuring a local, bare dev environment ...\n" >&2 \
			&& pip install $(PIP_DEPS) && pyenv rehash \
			&& poetry config experimental.new-installer false \
			&& poetry config virtualenvs.in-project true \
			&& poetry install && pyenv rehash \
			&& pre-commit install && pyenv rehash \
			&& printf "Done.\n" >&2; \
	fi


.PHONY: lint
lint:  lint-types lint-style lint-metrics lint-sec  ## Lint the code.


.PHONY: lint-types
lint-types:  ## Lint the type hints.
	poetry run mypy volt tests


.PHONY: lint-style
lint-style:  ## Lint style conventions.
	poetry run flake8 --statistics volt tests && poetry run black -t py310 --check .


.PHONY: lint-metrics
lint-metrics:  ## Lint various metrics.
	poetry run radon cc --total-average --show-closures --show-complexity --min C volt


.PHONY: lint-sec
lint-sec:  ## Lint security.
	poetry run bandit -r volt


.PHONY: test
test:  ## Run the test suite.
	poetry run py.test --cov=volt --cov-config=.coveragerc --cov-report=term-missing --cov-report=xml:.coverage.xml volt tests
