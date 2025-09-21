PYTHON ?= python3
VENV ?= .venv
PIP := $(VENV)/bin/pip
PY := $(VENV)/bin/python

.PHONY: init install test run lint fmt clean

init:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -e .[test]

install:
	$(PIP) install -e .

fmt:
	$(PY) -m black app

lint:
	$(PY) -m ruff check app

lint-fix:
	$(PY) -m ruff check app --fix

fmt-check:
	$(PY) -m black --check app

test:
	$(PY) -m pytest

run:
	$(PY) -m uvicorn app.main:app --reload

clean:
	rm -rf $(VENV) __pycache__ .pytest_cache
