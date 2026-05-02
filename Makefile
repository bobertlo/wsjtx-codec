.PHONY: install fmt lint test check

install:
	pip install -e ".[dev]"

fmt:
	ruff format wsjtx_codec tests

lint:
	ruff check wsjtx_codec tests

test:
	pytest --cov=wsjtx_codec --cov-report=term-missing

check: fmt lint test

