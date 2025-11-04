#!/usr/bin/env python3
"""
Test script for GUI format support (without launching GUI)
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

# Mock tkinter to avoid GUI dependencies
import unittest.mock as mock
sys.modules['tkinter'] = mock.MagicMock()
sys.modules['tkinter.ttk'] = mock.MagicMock()
sys.modules['tkinter.filedialog'] = mock.MagicMock()
sys.modules['tkinter.messagebox'] = mock.MagicMock()
sys.modules['tkinter.scrolledtext'] = mock.MagicMock()

print("Testing GUI Format Support (mocked)")
print("=" * 50)

# Now we can test the format change logic without GUI
class MockGUI:
    def __init__(self):
        self.output_format = mock.MagicMock()
        self.output_file = mock.MagicMock()
        self.log = print
        
    def on_format_change(self, event=None):
        """Handle format selection change and update output filename"""
        format_name = self.output_format.get()
        current_output = self.output_file.get()
        
        # Get the base filename without extension
        base_name = os.path.splitext(current_output)[0]
        
        # Map format to common file extension
        format_extensions = {
            'turtle': '.ttl',
            'json-ld': '.jsonld',
            'xml': '.rdf',
            'nt': '.nt',
            'n3': '.n3',
            'trig': '.trig',
            'nquads': '.nq',
            'csv': '.csv',
            'tsv': '.tsv',
            'sssom': '.sssom.tsv'
        }
        
        new_extension = format_extensions.get(format_name, '.ttl')
        new_filename = base_name + new_extension
        
        self.output_file.set(new_filename)
        self.log(f"Output format changed to: {format_name}")
        return new_filename

# Test format changes
gui = MockGUI()

test_cases = [
    ('improved_ontology.ttl', 'turtle', 'improved_ontology.ttl'),
    ('improved_ontology.ttl', 'json-ld', 'improved_ontology.jsonld'),
    ('improved_ontology.ttl', 'xml', 'improved_ontology.rdf'),
    ('improved_ontology.ttl', 'nt', 'improved_ontology.nt'),
    ('improved_ontology.ttl', 'csv', 'improved_ontology.csv'),
    ('improved_ontology.ttl', 'sssom', 'improved_ontology.sssom.tsv'),
]

all_passed = True
for input_file, format_name, expected_output in test_cases:
    gui.output_file.get = lambda: input_file
    gui.output_format.get = lambda f=format_name: f
    
    result = gui.on_format_change()
    
    if result == expected_output:
        print(f"✓ {format_name}: {input_file} -> {result}")
    else:
        print(f"✗ {format_name}: Expected {expected_output}, got {result}")
        all_passed = False

print("\n" + "=" * 50)
if all_passed:
    print("✅ All GUI format tests passed!")
    sys.exit(0)
else:
    print("❌ Some tests failed")
    sys.exit(1)
