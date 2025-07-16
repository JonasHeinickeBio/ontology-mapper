# Installation Guide

## Quick Start

1. **Clone or download the repository**
   ```bash
   git clone https://github.com/your-username/ontology-mapping-tool.git
   cd ontology-mapping-tool
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.template .env
   ```
   Edit `.env` and add your BioPortal API key:
   ```
   BIOPORTAL_API_KEY=your_api_key_here
   ```

4. **Test the installation**
   ```bash
   python test_install.py
   ```

5. **Run the tool**

   Command line interface:
   ```bash
   python main.py
   ```

   Graphical interface:
   ```bash
   python gui/launch_gui.py
   ```

## Getting API Keys

### BioPortal API Key (Required)
1. Go to https://bioportal.bioontology.org/
2. Create a free account
3. Go to your account page
4. Copy your API key
5. Add it to your `.env` file

### UMLS API Key (Optional)
1. Go to https://uts.nlm.nih.gov/uts/
2. Create a free account
3. Generate an API key
4. Add it to your `.env` file

## Troubleshooting

### Common Issues

**ImportError: No module named 'rdflib'**
```bash
pip install rdflib
```

**API Key errors**
- Make sure your `.env` file exists
- Check that your API key is correct
- Verify you have internet connectivity

**Permission errors**
```bash
pip install --user -r requirements.txt
```

### Testing

Run the test script to verify everything works:
```bash
python test_install.py
```

This will check:
- All modules can be imported
- Configuration files are valid
- Basic functionality works

## Next Steps

See the main README.md for usage examples and documentation.
