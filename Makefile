.PHONY: help install install-dev test test-cov lint format type-check security clean build publish docs pre-commit-install pre-commit-run

# Default target
help:
	@echo "Available targets:"
	@echo "  install          Install the package"
	@echo "  install-dev      Install with development dependencies"
	@echo "  test             Run tests"
	@echo "  test-cov         Run tests with coverage"
	@echo "  lint             Run linting checks"
	@echo "  format           Format code"
	@echo "  type-check       Run type checking"
	@echo "  security         Run security checks"
	@echo "  clean            Clean build artifacts"
	@echo "  build            Build the package"
	@echo "  publish          Publish to PyPI"
	@echo "  docs             Build documentation"
	@echo "  pre-commit-install  Install pre-commit hooks"
	@echo "  pre-commit-run   Run pre-commit hooks"

# Installation
install:
	pip install -e .

install-dev:
	pip install -e .[dev]

# Testing
test:
	pytest

test-cov:
	pytest --cov=. --cov-report=html --cov-report=term-missing

test-integration:
	pytest -m integration

# Code quality
lint:
	flake8 .
	ruff check .

format:
	black .
	isort .

type-check:
	mypy .

security:
	bandit -r . -c pyproject.toml
	safety check

# Development workflow
pre-commit-install:
	pre-commit install

pre-commit-run:
	pre-commit run --all-files

# Build and publish
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: clean
	python -m build

publish: build
	python -m twine upload dist/*

# Documentation
docs:
	@echo "Documentation target not implemented yet"

# All-in-one development setup
dev-setup: install-dev pre-commit-install
	@echo "Development environment setup complete!"

# Run all checks
check: format lint type-check security test
	@echo "All checks passed!"

# Quick development cycle
dev: format lint test
	@echo "Development cycle complete!"
