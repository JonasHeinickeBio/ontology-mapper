# BioPortal Ontology Alignment GUI

A modern graphical user interface for enhancing ontologies using BioPortal and OLS (Ontology Lookup Service) standard terminologies.

## Features

- 🖥️ **Intuitive GUI**: Easy-to-use interface with tabbed layout
- 🌐 **Dual Service Support**: Integration with both BioPortal and OLS APIs
- 📊 **Service Comparison**: Compare results between services and flag discrepancies
- 🔍 **Interactive Selection**: Rich metadata display with descriptions and synonyms
- 📈 **Progress Tracking**: Real-time progress updates and detailed logging
- 📁 **File Management**: Built-in file browser and output management
- 📋 **Detailed Reports**: Comprehensive alignment reports and statistics

## Installation

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Ensure CLI Module Access**: 
   The GUI depends on the CLI module in the parent `ontology_mapping` folder.

## Usage

### Quick Start

1. **Launch the GUI**:
   ```bash
   python bioportal_gui.py
   ```

2. **Configure Input**:
   - Select your TTL ontology file
   - Optionally enter BioPortal API key (leave empty for demo mode)
   - Choose services (BioPortal and/or OLS)
   - Set output file names

3. **Process Ontology**:
   - Click "Start Processing"
   - For each concept, select appropriate alignments
   - Review service comparisons and discrepancies
   - Monitor progress in the Processing tab

4. **Review Results**:
   - Check the Results tab for statistics
   - Open generated files (enhanced ontology, reports)
   - Export or view alignment details

### GUI Components

#### Configuration Tab
- **Input File**: Browse and select TTL ontology files
- **API Configuration**: BioPortal API key settings
- **Services**: Enable/disable BioPortal and OLS lookups
- **Output Files**: Configure output file names and paths

#### Processing Tab
- **Progress Tracking**: Real-time progress bar and status
- **Processing Log**: Detailed log of all operations
- **Control Buttons**: Start, stop, and log management

#### Results Tab
- **Summary**: Processing statistics and results overview
- **Generated Files**: List of output files with descriptions
- **Actions**: Open files, folders, and export reports

### Concept Alignment Window

For each concept found in your ontology, a dedicated alignment window shows:

- **Service Indicators**: 🌐 BioPortal, 🔬 OLS
- **Comparison Alerts**: Warnings about service discrepancies
- **Rich Metadata**: Descriptions, synonyms, ontology sources
- **Multi-Selection**: Choose multiple alignments per concept
- **Details View**: Expanded information for each option

### Output Files

1. **Enhanced Ontology** (`improved_ontology.ttl`):
   - Original ontology with alignment annotations
   - Standard terminologies linked via owl:sameAs, rdfs:seeAlso
   - Rich metadata including descriptions and synonyms

2. **Alignment Report** (`alignment_report.json`):
   - Processing timestamp and statistics
   - Complete record of all selections
   - Service comparison data

3. **Service Comparison Report** (`service_comparison_report.json`):
   - Detailed comparison between BioPortal and OLS
   - Discrepancy analysis
   - Common and unique terms identified

## API Keys

### BioPortal API Key
- **Optional**: The tool works in demo mode without an API key
- **Recommended**: Get a free API key from [BioPortal](https://bioportal.bioontology.org/)
- **Setup**: Enter in GUI or set `BIOPORTAL_API_KEY` environment variable

### OLS Access
- **No API Key Required**: OLS is freely accessible
- **Rate Limits**: Reasonable usage limits apply

## Technical Details

### Supported Ontology Formats
- **Input**: Turtle (TTL) format
- **Output**: Turtle (TTL) with enhanced annotations

### Priority Concepts
The tool automatically identifies priority concepts for alignment:
- **Instances**: long_covid, fatigue, immune_dysfunction
- **Classes**: Disease, Symptom, BiologicalProcess, MolecularEntity, Treatment

### Search Strategies
Each concept type uses optimized search strategies:
- **Multiple variants** per concept for comprehensive coverage
- **Targeted ontologies** based on concept type
- **Intelligent deduplication** of results

### Alignment Relationships
- **owl:sameAs**: For exact matches (typically instances)
- **rdfs:seeAlso**: For related terms (typically classes)
- **skos:closeMatch**: For approximate matches

## Examples

### Basic Usage
```bash
# Launch GUI
python bioportal_gui.py

# Select ontology file through GUI
# Configure services and API key
# Start processing and follow prompts
```

### Demo Mode
- Leave API key empty for demonstration
- Uses mock BioPortal data
- Full OLS integration still available

## Troubleshooting

### Common Issues

1. **Import Errors**:
   - Ensure `bioportal_cli.py` is in the parent `ontology_mapping` folder
   - Install all required dependencies

2. **No Concepts Found**:
   - Check that your TTL file contains recognized concept types
   - Verify TTL syntax is valid

3. **API Timeouts**:
   - Network connectivity issues
   - API rate limiting (especially without API key)

4. **Processing Hangs**:
   - Use Stop button to interrupt
   - Check log for error messages

### Performance Tips
- Use BioPortal API key for better performance
- Enable both services for comprehensive coverage
- Process smaller ontologies first to test

## Integration

The GUI integrates seamlessly with:
- **CLI Tool**: Shares core functionality with command-line version
- **BioPortal API**: Direct integration with bioontology.org
- **OLS API**: Integration with EBI Ontology Lookup Service
- **Standard Formats**: TTL input/output for interoperability

## Contributing

To extend the GUI:
1. Core logic is in the CLI module (`bioportal_cli.py`)
2. GUI components are modular and extensible
3. Threading model separates UI from processing
4. Error handling and logging integrated throughout

## Support

For issues or questions:
- Check the built-in Help (Help button in GUI)
- Review processing logs for error details
- Ensure all dependencies are properly installed
