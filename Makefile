.PHONY: install install-dev test lint typecheck audit coverage run seed migrate bench

install:
	pip install -r requirements.lock
	pip install -e . --no-deps

install-dev:
	pip install -r requirements-dev.lock
	pip install -e . --no-deps
	playwright install chromium

test:
	python -m pytest

lint:
	ruff check .
	ruff format --check .

typecheck:
	mypy autocomplete

audit:
	pip-audit -r requirements-dev.lock

coverage:
	python -m pytest --cov --cov-report=term-missing

run:
	python manage.py runserver

seed:
	python manage.py seed_corpus data/words.csv

migrate:
	python manage.py migrate

bench:
	python scripts/benchmark_suggest.py
