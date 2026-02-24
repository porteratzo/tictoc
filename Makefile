.PHONY: test lint install example

test:
	pytest

lint:
	pre-commit run --all-files

install:
	pip install -e ".[dev]"
	pre-commit install

example:
	python example.py
	python generate_plots.py
