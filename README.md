# Ontology Mapping Tool

A modular command-line interface and GUI for mapping and enriching ontologies using BioPortal and OLS APIs.

## Overview

This tool provides a simple, user-friendly interface for ontology concept lookup and mapping across multiple biomedical ontologies. It supports both command-line interface (CLI) and graphical user interface (GUI) modes.

### Key Features

- **Multi-ontology support**: 24+ ontologies including MONDO, HP, NCIT, DOID, CHEBI, GO, SNOMEDCT, and more
- **Dual API integration**: BioPortal and OLS APIs with intelligent fallback
- **Advanced error handling**: Retry mechanisms, circuit breakers, and graceful degradation
- **Multiple input formats**: Read Turtle, JSON-LD, RDF/XML, N-Triples, N3, TriG, N-Quads with auto-detection
- **Multiple output formats**: Export to Turtle, JSON-LD, RDF/XML, N-Triples, CSV, TSV, SSSOM, and more
- **Format conversion**: Convert between any supported RDF format
- **Intelligent caching**: In-memory and persistent caching for faster repeated queries
- **Interactive search**: Real-time concept lookup with user-friendly selection
- **Flexible file processing**: Parse and enrich ontology files in any supported format
- **Batch processing**: Handle multiple concepts efficiently
- **GUI interface**: User-friendly graphical interface for non-technical users with format selection
- **Result comparison**: Compare results from different ontology services
- **Comprehensive logging**: Detailed logging for debugging and monitoring

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Quick Install

```bash
# Clone the repository
git clone https://github.com/your-username/ontology-mapping-tool.git
cd ontology-mapping-tool

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

### Setup API Keys

1. Copy the environment template:
   ```bash
   cp .env.template .env
   ```

2. Edit `.env` and add your API keys:
   - Get a BioPortal API key from: https://bioportal.bioontology.org/account
   - (Optional) Get a UMLS API key from: https://uts.nlm.nih.gov/uts/profile

3. (Optional) Configure caching settings in `.env`:
   - `CACHE_ENABLED`: Enable/disable caching (default: true)
   - `CACHE_TTL`: Cache time-to-live in seconds (default: 86400 = 24 hours)
   - `CACHE_PERSISTENT`: Enable persistent file-based cache (default: true)
   - `CACHE_DIR`: Cache directory location (default: ~/.ontology_mapper_cache)
   - `CACHE_MAX_SIZE_MB`: Maximum cache size in MB (default: 100)

4. (Optional) Configure error handling and retry behavior in `.env`:
   - `ERROR_RETRY_ENABLED`: Enable automatic retry (default: true)
   - `ERROR_MAX_RETRIES`: Maximum retry attempts (default: 3)
   - `ERROR_CIRCUIT_BREAKER_ENABLED`: Enable circuit breaker (default: true)
   - See [ERROR_HANDLING.md](ERROR_HANDLING.md) for complete configuration options

## Usage

### Command Line Interface

#### Basic concept lookup:
```bash
python main.py --single-word "breast cancer"
```

#### Process ontology files:
```bash
# Process a Turtle file
python main.py ontology.ttl --output enriched_ontology.ttl

# Process a JSON-LD file
python main.py ontology.jsonld --output enriched_ontology.jsonld

# Process an RDF/XML file with explicit format
python main.py ontology.rdf --input-format xml --output enriched_ontology.ttl
```

#### Input Format Support:
```bash
# List available input formats
python main.py --list-input-formats

# Parse JSON-LD input
python main.py data.jsonld --input-format json-ld

# Parse RDF/XML input
python main.py data.rdf --input-format xml

# Auto-detect input format from extension
python main.py ontology.jsonld  # Automatically detects JSON-LD
python main.py ontology.rdf     # Automatically detects RDF/XML
```

#### Supported Input Formats:
- **turtle/ttl** (default): Turtle - Human-readable RDF format
- **json-ld**: JSON-LD - JSON format for linked data
- **xml/rdf-xml/rdf**: RDF/XML - Traditional RDF XML format
- **nt/ntriples**: N-Triples - Simple line-based RDF format
- **n3**: Notation3 - Superset of Turtle with rules
- **trig**: TriG - Turtle with named graphs
- **nquads**: N-Quads - N-Triples with named graphs

#### Output Format Selection:
```bash
# List available output formats (both input and output)
python main.py --list-formats

# Export as JSON-LD
python main.py ontology.ttl --output result.jsonld --format json-ld

# Export as RDF/XML
python main.py --single-word "diabetes" --output result.rdf --format xml

# Export as N-Triples
python main.py ontology.ttl --output result.nt --format nt

# Export as SSSOM mapping
python main.py ontology.ttl --output mappings.sssom.tsv --format sssom

# Auto-detect format from file extension
python main.py --single-word "cancer" --output result.jsonld

# Convert between formats
python main.py ontology.jsonld --input-format json-ld --output ontology.ttl --format turtle
```

#### Supported Output Formats:
- **turtle/ttl** (default): Turtle - Human-readable RDF format
- **json-ld**: JSON-LD - JSON format for linked data
- **xml/rdf-xml**: RDF/XML - Traditional RDF XML format
- **nt/ntriples**: N-Triples - Simple line-based RDF format
- **n3**: Notation3 - Superset of Turtle with rules
- **trig**: TriG - Turtle with named graphs
- **nquads**: N-Quads - N-Triples with named graphs
- **csv**: CSV - Comma-separated values (tabular export)
- **tsv**: TSV - Tab-separated values (tabular export)
- **sssom**: SSSOM TSV - Simple Standard for Sharing Ontology Mappings

#### Cache Management:
```bash
# View cache statistics
python main.py --cache-stats

# Clear all cached data
python main.py --clear-cache

# Disable cache for a single run
python main.py --single-word "diabetes" --no-cache
```

#### Batch processing:
```bash
python main.py --batch concepts.txt --output results.json
```

## Caching

The tool includes an intelligent caching mechanism to reduce API calls and improve performance:

### Features

- **In-memory caching**: Fast access to recently queried results
- **Persistent caching**: Results saved to disk and reused across sessions
- **Configurable TTL**: Set cache expiration time (default 24 hours)
- **Automatic cleanup**: Old entries are removed when size limit is reached
- **Cache statistics**: Monitor hit rates and cache performance
- **Per-service caching**: Separate caches for BioPortal and OLS

### Benefits

- 50%+ reduction in API calls for repeated queries
- Faster response times for cached results
- Reduced load on API servers
- Works seamlessly across CLI and GUI
- Respects API rate limits

### Usage

Cache is enabled by default. Configure it via environment variables in `.env`:

```bash
# Enable/disable caching
CACHE_ENABLED=true

# Cache time-to-live (24 hours)
CACHE_TTL=86400

# Enable persistent disk cache
CACHE_PERSISTENT=true

# Maximum cache size in MB
CACHE_MAX_SIZE_MB=100
```

View cache statistics:
```bash
python main.py --cache-stats
```

Clear cache:
```bash
python main.py --clear-cache
```

Disable cache for a single run:
```bash
python main.py --single-word "query" --no-cache
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

#### `OntologyGenerator`
Generator for creating ontologies with alignments. Supports multiple output formats:
- RDF formats via rdflib (Turtle, JSON-LD, RDF/XML, N-Triples, etc.)
- Custom formats (CSV, TSV, SSSOM)

## Output Format Examples

### Turtle (Default)
```bash
python main.py --single-word "diabetes" --output result.ttl
```
Produces human-readable RDF in Turtle format with prefixes and namespaces.

### JSON-LD (Web-Friendly)
```bash
python main.py --single-word "diabetes" --output result.jsonld --format json-ld
```
Produces JSON format suitable for web APIs and JavaScript applications.

### RDF/XML (Traditional)
```bash
python main.py --single-word "diabetes" --output result.rdf --format xml
```
Produces traditional RDF/XML format compatible with older tools.

### N-Triples (Simple)
```bash
python main.py --single-word "diabetes" --output result.nt --format nt
```
Produces simple line-based format, one triple per line.

### CSV/TSV (Tabular)
```bash
python main.py --single-word "diabetes" --output result.csv --format csv
```
Produces tabular format with columns: Subject, Predicate, Object, Object Type.

### SSSOM (Mapping Standard)
```bash
python main.py --single-word "diabetes" --output mappings.sssom.tsv --format sssom
```
Produces SSSOM (Simple Standard for Sharing Ontology Mappings) format for interoperability with mapping tools.

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
python -m pytest tests/
```

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

### And many more...

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
