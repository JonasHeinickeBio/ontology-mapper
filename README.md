# Ontology Mapping Tool

A modular command-line interface and GUI for mapping and enriching ontologies using BioPortal and OLS APIs.

## Overview

This tool provides a simple, user-friendly interface for ontology concept lookup and mapping across multiple biomedical ontologies. It supports both command-line interface (CLI) and graphical user interface (GUI) modes.

### Key Features

- **Multi-ontology support**: 24+ ontologies including MONDO, HP, NCIT, DOID, CHEBI, GO, SNOMEDCT, and more
- **Dual API integration**: BioPortal and OLS APIs with intelligent fallback
- **Interactive search**: Real-time concept lookup with user-friendly selection
- **TTL file processing**: Parse and enrich existing ontology files
- **Batch processing**: Handle multiple concepts efficiently
- **GUI interface**: User-friendly graphical interface for non-technical users
- **Result comparison**: Compare results from different ontology services

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Quick Install

```bash
# Clone the repository
git clone https://github.com/JonasHeinickeBio/ontology-mapper.git
cd ontology-mapper

# Install the package with all dependencies
pip install -e .

# Or install with development dependencies
pip install -e .[dev]

# Or install with all optional dependencies
pip install -e .[all]
```

### Development Setup

For development, we recommend using the development dependencies:

```bash
# Install with development dependencies
pip install -e .[dev]

# Set up pre-commit hooks
pre-commit install

# Run tests
pytest

# Run linting
black .
isort .
flake8 .
mypy .
```

### Setup API Keys

1. Copy the environment template:

   ```bash
   cp .env.template .env
   ```

2. Edit `.env` and add your API keys:
   - Get a BioPortal API key from: <https://bioportal.bioontology.org/account>
   - (Optional) Get a UMLS API key from: <https://uts.nlm.nih.gov/uts/profile>

## Usage

### Command Line Interface

#### Basic concept lookup

```bash
python main.py --search "breast cancer"
```

#### Process a TTL file

```bash
python main.py --input ontology.ttl --output enriched_ontology.ttl
```

#### Interactive mode

```bash
python main.py --interactive
```

#### Batch processing

```bash
python main.py --batch concepts.txt --output results.json
```

### Graphical User Interface

Launch the GUI:

```bash
python gui/launch_gui.py
```

Or use the demo interface:

```bash
python gui/demo_gui.py
```

## Supported Ontologies

The tool supports lookup across 24+ major biomedical ontologies:

- **MONDO**: Monarch Disease Ontology
- **HP**: Human Phenotype Ontology
- **NCIT**: National Cancer Institute Thesaurus
- **DOID**: Disease Ontology
- **CHEBI**: Chemical Entities of Biological Interest
- **GO**: Gene Ontology
- **SNOMEDCT**: Systematized Nomenclature of Medicine Clinical Terms
- **ICD10CM**, **ICD11**: International Classification of Diseases
- **LOINC**: Logical Observation Identifiers Names and Codes
- **OMIM**: Online Mendelian Inheritance in Man
- **ORDO**: Orphanet Rare Disease Ontology
- And many more...

## Architecture

The tool is organized into modular components:

```
ontology-mapping-tool/
├── cli/                 # Command-line interface
│   ├── main.py         # Main CLI entry point
│   └── interface.py    # CLI interface logic
├── core/               # Core functionality
│   ├── parser.py       # TTL file parsing
│   ├── lookup.py       # Concept lookup orchestration
│   └── generator.py    # Output generation
├── services/           # API services
│   ├── bioportal.py    # BioPortal API client
│   ├── ols.py          # OLS API client
│   └── comparator.py   # Result comparison
├── config/             # Configuration
│   └── ontologies.py   # Ontology definitions
├── utils/              # Utilities
│   ├── helpers.py      # Helper functions
│   └── loading.py      # Loading animations
└── gui/                # Graphical interface
    ├── launch_gui.py   # GUI launcher
    ├── bioportal_gui.py # Main GUI application
    └── demo_gui.py     # Demo interface
```

## Examples

### Example 1: Simple Concept Lookup

```bash
python main.py --search "diabetes mellitus"
```

### Example 2: Processing TTL File

```bash
python main.py --input disease_ontology.ttl --output enhanced_ontology.ttl
```

### Example 3: Batch Processing

Create a file `concepts.txt`:

```
breast cancer
diabetes mellitus
hypertension
```

Then run:

```bash
python main.py --batch concepts.txt --output results.json
```

## API Reference

### Core Classes

#### `ConceptLookup`

Main class for performing concept lookups across multiple ontologies.

#### `BioPortalService`

Client for interacting with the BioPortal API.

#### `OLSService`

Client for interacting with the OLS (Ontology Lookup Service) API.

#### `OntologyParser`

Parser for TTL (Turtle) ontology files.

## Configuration

### Ontology Configuration

Edit `config/ontologies.py` to customize:

- Supported ontologies
- API endpoints
- Search strategies
- Result filtering

### Environment Variables

- `BIOPORTAL_API_KEY`: Your BioPortal API key (required)
- `UMLS_API_KEY`: Your UMLS API key (optional)

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=. --cov-report=html

# Run specific test categories
pytest -m unit
pytest -m integration

# Run tests excluding slow tests
pytest -m "not slow"
```

For development workflow, see [DEVELOPMENT.md](DEVELOPMENT.md).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For questions, issues, or contributions:

- Open an issue on GitHub
- Check the documentation in the `docs/` directory
- Review the example scripts in `examples/`

## Acknowledgments

- BioPortal team for providing the ontology API
- OLS team for the Ontology Lookup Service
- The broader biomedical ontology community

## Citation

If you use this tool in your research, please cite:

```
[Your citation information here]
```

---

**Note**: This tool is designed to complement existing ontology mapping frameworks like SSSOM-py by providing a simple, user-friendly interface for concept lookup and initial mapping tasks.

- `helpers.py`: Common helper functions (text cleaning, deduplication, etc.)

### Configuration (`config/`)

- `ontologies.py`: Ontology definitions, mappings, and search strategies

### Command Line Interface (`cli/`)

- `interface.py`: Main CLI interface and argument parsing
- `main.py`: CLI entry point and error handling

## Usage

### Quick Start

```bash
# List available ontologies
python run_cli.py --list-ontologies

# Query a single term
python run_cli.py --single-word "fatigue" --ontologies "HP,NCIT"

# Process a TTL file
python run_cli.py ontology.ttl --output improved.ttl

# Batch processing with pre-selected choices
python run_cli.py ontology.ttl --batch-mode selections.json
```

### Common Options

- `--ontologies`: Specify ontologies to search (e.g., "HP,NCIT,MONDO")
- `--max-results`: Maximum results per search (default: 5)
- `--disable-ols`: Use only BioPortal
- `--disable-bioportal`: Use only OLS
- `--comparison-only`: Run comparison without generating output
- `--terminal-only`: Print results without creating files

### Environment Setup

Set your BioPortal API key:

```bash
export BIOPORTAL_API_KEY="your_api_key_here"
```

Or use the `--api-key` argument.

## Available Ontologies

The tool supports 24+ ontologies including:

### Disease & Phenotype

- **MONDO**: Monarch Disease Ontology
- **HP**: Human Phenotype Ontology
- **DOID**: Disease Ontology
- **ORDO**: Orphanet Rare Disease Ontology

### Clinical & Medical

- **SNOMEDCT**: SNOMED Clinical Terms
- **ICD10/ICD11**: International Classification of Diseases
- **LOINC**: Logical Observation Identifiers Names and Codes
- **CPT**: Current Procedural Terminology

### Biological

- **GO**: Gene Ontology
- **CHEBI**: Chemical Entities of Biological Interest
- **PRO**: Protein Ontology
- **UBERON**: Anatomical structures

### And many more

## Example Workflows

### Disease Research

```bash
python run_cli.py --single-word "cancer" --ontologies "MONDO,HP,DOID,NCIT,ORDO"
```

### Symptom Analysis

```bash
python run_cli.py --single-word "headache" --ontologies "HP,SYMP,NCIT"
```

### Chemical/Drug Research

```bash
python run_cli.py --single-word "aspirin" --ontologies "CHEBI,RXNORM,NCIT"
```

## File Structure

```
ontology_mapping/
├── bioportal_cli.py          # Original monolithic file (kept for reference)
├── run_cli.py                # Convenient wrapper script
├── main.py                   # Main entry point
├── cli/
│   ├── __init__.py
│   ├── interface.py          # CLI interface and argument parsing
│   └── main.py               # CLI entry point
├── core/
│   ├── __init__.py
│   ├── parser.py             # TTL file parsing
│   ├── lookup.py             # Concept lookup orchestration
│   └── generator.py          # Ontology generation
├── services/
│   ├── __init__.py
│   ├── bioportal.py          # BioPortal API client
│   ├── ols.py                # OLS API client
│   └── comparator.py         # Result comparison
├── utils/
│   ├── __init__.py
│   ├── loading.py            # Loading animations
│   └── helpers.py            # Helper functions
└── config/
    ├── __init__.py
    └── ontologies.py          # Ontology configurations
```

## Dependencies

- `rdflib`: RDF graph processing
- `requests`: HTTP API calls
- `argparse`: Command-line argument parsing
- `threading`: Loading bar animations
- `json`: Configuration and batch processing

## Migration from Monolithic Version

The original `bioportal_cli.py` (1185+ lines) has been split into focused modules:

1. **Services separated**: BioPortal and OLS clients are now independent
2. **Core logic isolated**: Parsing, lookup, and generation are distinct
3. **Configuration centralized**: All ontology definitions in one place
4. **CLI decoupled**: Interface separated from business logic
5. **Utilities extracted**: Common functions in dedicated modules

This modular approach improves:

- **Maintainability**: Easier to update individual components
- **Testability**: Each module can be tested independently
- **Reusability**: Components can be imported and used elsewhere
- **Readability**: Smaller, focused files are easier to understand

## Future Enhancements

The modular structure makes it easy to add:

- New ontology services
- Additional output formats
- Enhanced comparison algorithms
- Batch processing improvements
- Web interface components
