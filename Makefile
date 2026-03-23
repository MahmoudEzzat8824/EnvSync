PYTHON := .venv/bin/python
PIP := .venv/bin/pip

.PHONY: venv install install-dev test run-help run-compare clean

venv:
	python3 -m venv .venv

install: venv
	$(PIP) install -r requirements.txt
	$(PIP) install -e .

install-dev: venv
	$(PIP) install -r requirements.txt
	$(PIP) install -e .[dev]

test:
	$(PYTHON) -m pytest -q

run-help:
	.venv/bin/envsync --help

run-compare:
	.venv/bin/envsync compare --env dev.env --env staging.env --env prod.env

clean:
	rm -rf .pytest_cache __pycache__ .mypy_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
