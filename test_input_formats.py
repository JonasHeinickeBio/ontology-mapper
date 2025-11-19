#!/usr/bin/env python3
"""
Test script for multiple input format support
"""

import sys
import os
import tempfile

# Add the project root to Python path
sys.path.insert(0, os.path.abspath('.'))

from rdflib import Graph, RDF, RDFS, OWL, SKOS, URIRef, Literal
from rdflib.namespace import DCTERMS
from core.parser import OntologyParser


def create_test_ontology_graph():
    """Create a simple test ontology"""
    graph = Graph()
    
    # Add namespace bindings
    graph.bind("", "http://example.org/test#")
    graph.bind("owl", OWL)
    graph.bind("rdfs", RDFS)
    graph.bind("skos", SKOS)
    graph.bind("dcterms", DCTERMS)
    
    # Create classes
    disease_class = URIRef("http://example.org/ontology#Disease")
    graph.add((disease_class, RDF.type, RDFS.Class))
    graph.add((disease_class, RDFS.label, Literal("Disease", lang='en')))
    
    symptom_class = URIRef("http://example.org/ontology#Symptom")
    graph.add((symptom_class, RDF.type, RDFS.Class))
    graph.add((symptom_class, RDFS.label, Literal("Symptom", lang='en')))
    
    # Create instances
    diabetes = URIRef("http://example.org/ontology#diabetes")
    graph.add((diabetes, RDF.type, disease_class))
    graph.add((diabetes, RDFS.label, Literal("Diabetes", lang='en')))
    
    fatigue = URIRef("http://example.org/ontology#fatigue")
    graph.add((fatigue, RDF.type, symptom_class))
    graph.add((fatigue, RDFS.label, Literal("Fatigue", lang='en')))
    
    return graph


def test_input_format_parsing():
    """Test parsing of different input formats"""
    print("\n  Testing input format parsing...")
    
    graph = create_test_ontology_graph()
    
    # Test formats
    test_formats = [
        ('turtle', '.ttl'),
        ('json-ld', '.jsonld'),
        ('xml', '.rdf'),
        ('nt', '.nt'),
        ('n3', '.n3'),
    ]
    
    for format_name, extension in test_formats:
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix=extension, delete=False) as f:
            temp_file = f.name
        
        try:
            # Serialize test graph to file
            graph.serialize(destination=temp_file, format=format_name)
            
            # Test explicit format specification
            parser = OntologyParser(temp_file, format_name)
            if not parser.parse():
                print(f"    ✗ {format_name}: Failed to parse with explicit format")
                return False
            
            if len(parser.graph) == 0:
                print(f"    ✗ {format_name}: Parsed graph is empty")
                return False
            
            print(f"    ✓ {format_name}: Parsed {len(parser.graph)} triples (explicit format)")
            
            # Test auto-detection from filename
            parser_auto = OntologyParser(temp_file)
            if not parser_auto.parse():
                print(f"    ✗ {format_name}: Failed to parse with auto-detection")
                return False
            
            print(f"    ✓ {format_name}: Auto-detected and parsed {len(parser_auto.graph)} triples")
            
        except Exception as e:
            print(f"    ✗ {format_name}: Error: {e}")
            return False
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    return True


def test_format_validation():
    """Test format validation"""
    print("\n  Testing format validation...")
    
    # Valid formats
    valid_formats = ['turtle', 'ttl', 'json-ld', 'xml', 'rdf', 'nt', 'n3']
    for fmt in valid_formats:
        try:
            # Create dummy file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.ttl', delete=False) as f:
                temp_file = f.name
            
            try:
                OntologyParser(temp_file, fmt)
                print(f"    ✓ Valid format accepted: {fmt}")
            finally:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
        except ValueError as e:
            print(f"    ✗ Unexpected error for valid format {fmt}: {e}")
            return False
    
    # Invalid format
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ttl', delete=False) as f:
            temp_file = f.name
        
        try:
            OntologyParser(temp_file, 'invalid_format')
            print(f"    ✗ Should have raised ValueError for invalid format")
            return False
        except ValueError:
            print(f"    ✓ Invalid format properly rejected")
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    except Exception as e:
        print(f"    ✗ Unexpected error: {e}")
        return False
    
    return True


def test_format_detection():
    """Test format detection from filename"""
    print("\n  Testing format detection from filename...")
    
    parser = OntologyParser.__new__(OntologyParser)
    
    test_cases = [
        ('ontology.ttl', 'turtle'),
        ('ontology.jsonld', 'json-ld'),
        ('ontology.rdf', 'xml'),
        ('ontology.xml', 'xml'),
        ('ontology.nt', 'nt'),
        ('ontology.n3', 'n3'),
        ('ontology.unknown', None),
    ]
    
    for filename, expected in test_cases:
        result = parser._detect_format_from_filename(filename)
        if result == expected:
            print(f"    ✓ {filename} -> {result}")
        else:
            print(f"    ✗ {filename} -> {result} (expected {expected})")
            return False
    
    return True


def test_backward_compatibility():
    """Test backward compatibility with ttl_file attribute"""
    print("\n  Testing backward compatibility...")
    
    graph = create_test_ontology_graph()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ttl', delete=False) as f:
        temp_file = f.name
    
    try:
        # Serialize test graph
        graph.serialize(destination=temp_file, format='turtle')
        
        # Test that ttl_file attribute still exists
        parser = OntologyParser(temp_file)
        if not hasattr(parser, 'ttl_file'):
            print(f"    ✗ ttl_file attribute not found (breaks backward compatibility)")
            return False
        
        if parser.ttl_file != temp_file:
            print(f"    ✗ ttl_file attribute has wrong value")
            return False
        
        print(f"    ✓ ttl_file attribute maintained for backward compatibility")
        
        # Test parsing still works
        if not parser.parse():
            print(f"    ✗ Parsing failed")
            return False
        
        print(f"    ✓ Parsing works as before")
        
    finally:
        if os.path.exists(temp_file):
            os.unlink(temp_file)
    
    return True


def main():
    """Run all input format tests"""
    print("Testing Multiple Input Format Support")
    print("=" * 50)
    
    all_passed = True
    
    # Test format validation
    if not test_format_validation():
        print("❌ Format validation test FAILED")
        all_passed = False
    
    # Test format detection
    if not test_format_detection():
        print("❌ Format detection test FAILED")
        all_passed = False
    
    # Test input format parsing
    if not test_input_format_parsing():
        print("❌ Input format parsing test FAILED")
        all_passed = False
    
    # Test backward compatibility
    if not test_backward_compatibility():
        print("❌ Backward compatibility test FAILED")
        all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✅ All input format tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
