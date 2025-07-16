# Package Manager Support

This project supports both **Poetry** and **uv** package managers, using the modern PEP 621 project configuration format.

## Poetry

Poetry is fully supported with all dependency groups and scripts.

### Poetry Installation

```bash
# Install Poetry if not already installed
curl -sSL https://install.python-poetry.org | python3 -

# Install project dependencies
poetry install

# Install with specific groups
poetry install --with dev,test,docs

# Run the application
poetry run ontology-mapping
poetry run ontology-gui
```

### Poetry Development

```bash
# Add a new dependency
poetry add requests

# Add a development dependency
poetry add --group dev pytest

# Update dependencies
poetry update

# Build the project
poetry build

# Publish to PyPI
poetry publish
```

## uv

uv is fully supported with fast dependency resolution and installation.

### uv Installation

```bash
# Install uv if not already installed
pip install uv

# Install project dependencies
uv sync

# Install project in development mode
uv sync --dev

# Run the application
uv run ontology-mapping
uv run ontology-gui
```

### uv Development

```bash
# Add a new dependency
uv add requests

# Add a development dependency
uv add --dev pytest

# Update dependencies
uv sync --upgrade

# Build the project
uv build

# Run tests
uv run pytest
```

## Project Configuration

The project uses modern PEP 621 configuration in `pyproject.toml`:

- **Main dependencies**: Listed in `[project.dependencies]`
- **Optional dependencies**: Listed in `[project.optional-dependencies]`
- **Scripts**: Listed in `[project.scripts]`
- **Poetry-specific**: Listed in `[tool.poetry]` sections

## Available Dependency Groups

- **gui**: GUI-related dependencies (tkinter)
- **dev**: Development tools (pytest, black, flake8, mypy, etc.)
- **test**: Testing-specific dependencies (pytest, pytest-cov, responses)
- **docs**: Documentation tools (sphinx, themes)
- **performance**: Performance optimization tools (orjson, lxml)

## Scripts

Both package managers support the following scripts:

- `ontology-mapping`: Main CLI tool
- `ontology-gui`: GUI application launcher

## Compatibility

- **Python**: >=3.8.1
- **Poetry**: >=1.2.0
- **uv**: >=0.1.0

Both tools can coexist in the same project and will use the same dependency specifications from `pyproject.toml`.
