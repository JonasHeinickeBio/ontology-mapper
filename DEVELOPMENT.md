# Development Guide

This guide explains how to set up the development environment and contribute to the ontology-mapper project.

## Development Setup

### Prerequisites

- Python 3.8 or higher
- Git
- Make (optional, for using Makefile commands)

### Quick Setup

```bash
# Clone the repository
git clone https://github.com/JonasHeinickeBio/ontology-mapper.git
cd ontology-mapper

# Set up development environment
make dev-setup

# Or manually:
pip install -e .[dev]
pre-commit install
```

## Project Structure

```Markdown
ontology-mapper/
├── .github/workflows/     # GitHub Actions CI/CD
├── cli/                   # Command-line interface
├── core/                  # Core functionality
├── services/              # API services
├── utils/                 # Utility functions
├── config/                # Configuration
├── gui/                   # Graphical interface
├── tests/                 # Test suite
├── examples/              # Example scripts
├── pyproject.toml         # Project configuration
├── setup.cfg              # Additional setup configuration
├── Makefile              # Development commands
└── README.md             # Main documentation
```

## Development Workflow

### 1. Code Formatting

We use `black` for code formatting and `isort` for import sorting:

```bash
# Format code
make format

# Or manually:
black .
isort .
```

### 2. Linting

We use `flake8` and `ruff` for linting:

```bash
# Run linting
make lint

# Or manually:
flake8 .
ruff check .
```

### 3. Type Checking

We use `mypy` for type checking:

```bash
# Run type checking
make type-check

# Or manually:
mypy .
```

### 4. Testing

We use `pytest` for testing:

```bash
# Run tests
make test

# Run tests with coverage
make test-cov

# Run integration tests
make test-integration
```

### 5. Security Checks

We use `bandit` and `safety` for security checks:

```bash
# Run security checks
make security

# Or manually:
bandit -r . -c pyproject.toml
safety check
```

### 6. Pre-commit Hooks

We use pre-commit hooks to ensure code quality:

```bash
# Install pre-commit hooks
make pre-commit-install

# Run pre-commit hooks manually
make pre-commit-run
```

## Testing

### Test Structure

- `tests/` - Main test directory
- `tests/test_*.py` - Test files
- `tests/conftest.py` - Test configuration and fixtures

### Test Categories

We use pytest markers to categorize tests:

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.gui` - GUI tests
- `@pytest.mark.api` - Tests requiring API access
- `@pytest.mark.slow` - Slow-running tests

### Running Tests

```bash
# Run all tests
pytest

# Run specific test category
pytest -m unit
pytest -m integration

# Run tests with coverage
pytest --cov=. --cov-report=html

# Run tests excluding slow tests
pytest -m "not slow"
```

## Code Style

### Python Style Guide

We follow PEP 8 with some modifications:

- Line length: 100 characters
- Use double quotes for strings
- Use type hints where appropriate

### Import Order

We use `isort` with the `black` profile:

1. Standard library imports
2. Third-party imports
3. Local imports

Example:

```python
import os
import sys
from typing import Dict, List

import requests
from rdflib import Graph

from core.lookup import ConceptLookup
from services.bioportal import BioPortalLookup
```

### Documentation

- Use docstrings for all public functions and classes
- Follow Google docstring format
- Include type hints in function signatures

Example:

```python
def search_concept(query: str, ontologies: List[str]) -> Dict[str, Any]:
    """Search for a concept across multiple ontologies.

    Args:
        query: The search query string
        ontologies: List of ontology names to search

    Returns:
        Dictionary containing search results

    Raises:
        ValueError: If query is empty
        APIError: If API request fails
    """
```

## Contributing

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

- Write code following the style guide
- Add tests for new functionality
- Update documentation if needed

### 3. Run Quality Checks

```bash
# Run all checks
make check

# Or step by step:
make format
make lint
make type-check
make security
make test
```

### 4. Commit Changes

```bash
git add .
git commit -m "Add your feature description"
```

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub.

## Build and Release

### Building the Package

```bash
# Clean and build
make build

# Or manually:
make clean
python -m build
```

### Publishing to PyPI

```bash
# Build and publish
make publish

# Or manually:
make build
python -m twine upload dist/*
```

## Troubleshooting

### Common Issues

1. **Import errors**: Make sure you've installed the package in development mode (`pip install -e .`)

2. **Pre-commit hooks failing**: Run `make format` to fix formatting issues

3. **Test failures**: Check if you have the required test dependencies (`pip install -e .[test]`)

4. **Type checking errors**: Install type stubs or add `# type: ignore` comments where appropriate

### Getting Help

- Check the [GitHub Issues](https://github.com/JonasHeinickeBio/ontology-mapper/issues)
- Read the main [README.md](README.md)
- Review the test files for examples

## IDE Configuration

### VS Code

Recommended extensions:

- Python
- Black Formatter
- isort
- Pylance
- Test Explorer

### PyCharm

Configure:

- Code style: Black
- Import optimization: isort
- Type checker: mypy

## Performance Considerations

- Use caching for expensive operations
- Avoid blocking the main thread in GUI applications
- Use appropriate data structures for large datasets
- Profile code when performance is critical

## Security Guidelines

- Never commit API keys or secrets
- Use environment variables for sensitive configuration
- Validate all user inputs
- Use HTTPS for all API calls
- Keep dependencies updated
