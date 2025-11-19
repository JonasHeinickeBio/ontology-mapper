#!/usr/bin/env python3
"""
Example script demonstrating multiple output format usage

This script shows how to generate ontology mappings in different formats
programmatically using the OntologyGenerator class.
"""

import sys
import os
import tempfile

# Add the project root to Python path
sys.path.insert(0, os.path.abspath('.'))

from core.generator import OntologyGenerator


def example_1_simple_format_export():
    """Example 1: Export a simple ontology to multiple formats"""
    print("\n" + "="*60)
    print("Example 1: Export to Multiple Formats")
    print("="*60)
    
    generator = OntologyGenerator()
    
    # Create a simple concept with alignments
    concept = {
        'key': 'covid19',
        'label': 'COVID-19',
        'type': 'Disease',
        'category': 'query'
    }
    
    # Mock alignments from different ontologies
    selections = {
        'covid19': [
            {
                'uri': 'http://purl.obolibrary.org/obo/MONDO_0100096',
                'label': 'COVID-19',
                'ontology': 'MONDO',
                'description': 'A disease caused by infection with SARS-CoV-2',
                'synonyms': ['coronavirus disease 2019', '2019-nCoV disease'],
                'source': 'bioportal',
                'relationship': 'skos:exactMatch'
            },
            {
                'uri': 'http://purl.obolibrary.org/obo/DOID_0080600',
                'label': 'COVID-19',
                'ontology': 'DOID',
                'description': 'A coronavirus infectious disease',
                'synonyms': ['SARS-CoV-2 infection'],
                'source': 'ols',
                'relationship': 'skos:exactMatch'
            }
        ]
    }
    
    # Generate in different formats
    formats = ['turtle', 'json-ld', 'xml', 'nt', 'csv', 'sssom']
    
    for fmt in formats:
        # Use temporary file for demonstration
        with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{fmt}', delete=False) as f:
            output_file = f.name
        
        try:
            print(f"\n📄 Generating {fmt.upper()} format...")
            generator.generate_single_word_ontology(
                concept,
                selections,
                output_file,
                output_format=fmt
            )
            
            # Show first few lines of the output
            print(f"\n   Preview of {output_file}:")
            with open(output_file, 'r') as f:
                all_lines = f.readlines()
                preview_lines = all_lines[:10]
                for line in preview_lines:
                    print(f"   {line.rstrip()}")
                if len(all_lines) > 10:
                    print(f"   ... ({len(all_lines) - 10} more lines)")
            
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)


def example_2_format_detection():
    """Example 2: Use format auto-detection from filename"""
    print("\n" + "="*60)
    print("Example 2: Format Auto-Detection from Filename")
    print("="*60)
    
    generator = OntologyGenerator()
    
    concept = {
        'key': 'hypertension',
        'label': 'Hypertension',
        'type': 'Disease',
        'category': 'query'
    }
    
    selections = {
        'hypertension': [{
            'uri': 'http://purl.obolibrary.org/obo/HP_0000822',
            'label': 'Hypertension',
            'ontology': 'HP',
            'description': 'Abnormally high blood pressure',
            'synonyms': ['High blood pressure'],
            'source': 'bioportal',
            'relationship': 'skos:exactMatch'
        }]
    }
    
    # Test different filenames - format will be auto-detected
    test_files = [
        'hypertension.ttl',       # Will use turtle
        'hypertension.jsonld',    # Will use json-ld
        'hypertension.rdf',       # Will use xml (RDF/XML)
        'hypertension.nt',        # Will use nt
        'hypertension.csv',       # Will use csv
    ]
    
    for filename in test_files:
        output_file = os.path.join(tempfile.gettempdir(), filename)
        
        try:
            print(f"\n📁 Creating {filename}...")
            # No format parameter - will auto-detect
            generator.generate_single_word_ontology(
                concept,
                selections,
                output_file
            )
            
            size = os.path.getsize(output_file)
            print(f"   ✓ Created: {filename} ({size} bytes)")
            
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)


def example_3_sssom_mapping():
    """Example 3: Create SSSOM mapping file for interoperability"""
    print("\n" + "="*60)
    print("Example 3: SSSOM Mapping Format")
    print("="*60)
    
    generator = OntologyGenerator()
    
    # Multiple concepts with alignments
    concept = {
        'key': 'asthma',
        'label': 'Asthma',
        'type': 'Disease',
        'category': 'query'
    }
    
    selections = {
        'asthma': [
            {
                'uri': 'http://purl.obolibrary.org/obo/MONDO_0004979',
                'label': 'asthma',
                'ontology': 'MONDO',
                'description': 'A bronchial disease',
                'synonyms': ['asthma bronchiale'],
                'source': 'bioportal',
                'relationship': 'skos:exactMatch'
            },
            {
                'uri': 'http://purl.obolibrary.org/obo/HP_0002099',
                'label': 'Asthma',
                'ontology': 'HP',
                'description': 'Asthma phenotype',
                'synonyms': [],
                'source': 'ols',
                'relationship': 'skos:closeMatch'
            }
        ]
    }
    
    output_file = os.path.join(tempfile.gettempdir(), 'asthma_mappings.sssom.tsv')
    
    try:
        print(f"\n📊 Creating SSSOM mapping file...")
        generator.generate_single_word_ontology(
            concept,
            selections,
            output_file,
            output_format='sssom'
        )
        
        print(f"\n   Content of {output_file}:")
        with open(output_file, 'r') as f:
            content = f.read()
            print(f"\n{content}")
        
        print("\n   ℹ️  SSSOM format is compatible with:")
        print("      - SSSOM-py toolkit")
        print("      - OAK (Ontology Access Kit)")
        print("      - Various mapping tools")
        
    finally:
        if os.path.exists(output_file):
            os.unlink(output_file)


def example_4_csv_export():
    """Example 4: Export to CSV for spreadsheet analysis"""
    print("\n" + "="*60)
    print("Example 4: CSV Export for Spreadsheet Analysis")
    print("="*60)
    
    generator = OntologyGenerator()
    
    concept = {
        'key': 'diabetes',
        'label': 'Diabetes',
        'type': 'Disease',
        'category': 'query'
    }
    
    selections = {
        'diabetes': [{
            'uri': 'http://purl.obolibrary.org/obo/MONDO_0005015',
            'label': 'diabetes mellitus',
            'ontology': 'MONDO',
            'description': 'A metabolic disease',
            'synonyms': ['diabetes', 'DM'],
            'source': 'bioportal',
            'relationship': 'skos:exactMatch'
        }]
    }
    
    output_file = os.path.join(tempfile.gettempdir(), 'diabetes_triples.csv')
    
    try:
        print(f"\n📈 Creating CSV file...")
        generator.generate_single_word_ontology(
            concept,
            selections,
            output_file,
            output_format='csv'
        )
        
        print(f"\n   Preview of {output_file}:")
        with open(output_file, 'r') as f:
            lines = f.readlines()[:15]  # First 15 lines
            for line in lines:
                print(f"   {line.rstrip()}")
            if len(lines) >= 15:
                print(f"   ... (more lines)")
        
        print("\n   ℹ️  CSV format can be opened in:")
        print("      - Microsoft Excel")
        print("      - Google Sheets")
        print("      - LibreOffice Calc")
        print("      - Any spreadsheet software")
        
    finally:
        if os.path.exists(output_file):
            os.unlink(output_file)


def main():
    """Run all examples"""
    print("\n" + "="*60)
    print("Multiple Output Format Examples")
    print("="*60)
    
    print("\nThis script demonstrates how to use different output formats")
    print("for ontology mapping results.")
    
    # Run examples
    example_1_simple_format_export()
    example_2_format_detection()
    example_3_sssom_mapping()
    example_4_csv_export()
    
    print("\n" + "="*60)
    print("Examples completed!")
    print("="*60)
    print("\nFor more information:")
    print("  - Use 'python main.py --list-formats' to see all formats")
    print("  - Use 'python main.py --help' for CLI usage")
    print("  - Check README.md for detailed documentation")
    print()


if __name__ == '__main__':
    main()
