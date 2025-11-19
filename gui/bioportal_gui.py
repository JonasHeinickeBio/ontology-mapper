#!/usr/bin/env python3
"""
BioPortal Ontology Alignment GUI Tool

A graphical user interface for improving ontologies using BioPortal and OLS standard terminologies.
Provides an intuitive interface for TTL file processing, concept alignment, and ontology enhancement.

Features:
- File browser for TTL selection
- Service comparison between BioPortal and OLS
- Interactive concept alignment with metadata display
- Real-time progress tracking
- Export enhanced ontologies and reports

Usage:
    python bioportal_gui.py
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import sys
import json
import threading
from datetime import datetime
from typing import List, Dict, Optional
import webbrowser

# Import the core classes from the CLI tool
try:
    from bioportal_cli import BioPortalLookup, OLSLookup, OntologyParser, ConceptLookup, ResultComparator
except ImportError as e:
    print(f"Import error: {e}")
    print("Looking for bioportal_cli.py in current directory...")
    messagebox.showerror("Import Error", 
                        "Could not import CLI modules.\n"
                        "Please ensure bioportal_cli.py is available in this folder.")
    sys.exit(1)


class ToolTip:
    """Tooltip class for showing helpful hints on hover"""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)
    
    def show_tip(self, event=None):
        if self.tipwindow or not self.text:
            return
        x, y, _, _ = self.widget.bbox("insert") if hasattr(self.widget, 'bbox') else (0, 0, 0, 0)
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                        background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                        font=("Arial", 9))
        label.pack()
    
    def hide_tip(self, event=None):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None


class ConceptAlignmentWindow:
    """Window for selecting alignments for a specific concept"""
    
    def __init__(self, parent, concept: Dict, options: List[Dict], comparison: Dict):
        self.parent = parent
        self.concept = concept
        self.options = options
        self.comparison = comparison
        self.selections = []
        self.result = None
        
        # Create toplevel window
        self.window = tk.Toplevel(parent)
        self.window.title(f"Align Concept: {concept['label']}")
        self.window.geometry("1000x700")
        self.window.transient(parent)
        self.window.grab_set()
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the alignment window UI"""
        # Header
        header_frame = ttk.Frame(self.window)
        header_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(header_frame, text=f"Concept: {self.concept['label']}", 
                 font=("Arial", 14, "bold")).pack(anchor=tk.W)
        ttk.Label(header_frame, text=f"Type: {self.concept['type']} | Category: {self.concept['category']}", 
                 font=("Arial", 10)).pack(anchor=tk.W)
        
        # Comparison summary
        if self.comparison.get('discrepancies'):
            alert_frame = ttk.LabelFrame(self.window, text="⚠️ Service Comparison Alert")
            alert_frame.pack(fill=tk.X, padx=10, pady=5)
            
            for discrepancy in self.comparison['discrepancies']:
                ttk.Label(alert_frame, text=f"• {discrepancy}", foreground="orange").pack(anchor=tk.W, padx=5)
            
            stats_text = f"BioPortal: {self.comparison['bioportal_count']} results | OLS: {self.comparison['ols_count']} results"
            ttk.Label(alert_frame, text=stats_text).pack(anchor=tk.W, padx=5)
        
        # Options frame
        options_frame = ttk.LabelFrame(self.window, text=f"✅ Found {len(self.options)} standardized terms:")
        options_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Create treeview for options
        columns = ("Select", "Source", "Label", "Ontology", "URI", "Description")
        self.tree = ttk.Treeview(options_frame, columns=columns, show="headings", height=15)
        
        # Configure columns
        self.tree.heading("Select", text="Select")
        self.tree.heading("Source", text="Source")
        self.tree.heading("Label", text="Label")
        self.tree.heading("Ontology", text="Ontology")
        self.tree.heading("URI", text="URI")
        self.tree.heading("Description", text="Description")
        
        self.tree.column("Select", width=60, anchor=tk.CENTER)
        self.tree.column("Source", width=80, anchor=tk.CENTER)
        self.tree.column("Label", width=200)
        self.tree.column("Ontology", width=100, anchor=tk.CENTER)
        self.tree.column("URI", width=250)
        self.tree.column("Description", width=300)
        
        # Add scrollbars
        v_scrollbar = ttk.Scrollbar(options_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(options_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack tree and scrollbars
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Populate tree
        self.checkboxes = {}
        for i, option in enumerate(self.options):
            source_icon = "🌐" if option['source'] == 'bioportal' else "🔬"
            ols_only = " (OLS-only)" if option.get('ols_only') else ""
            
            # Truncate long descriptions
            description = option.get('description', '')
            if len(description) > 80:
                description = description[:80] + "..."
            
            # Truncate long URIs
            uri = option['uri']
            if len(uri) > 60:
                uri = uri[:60] + "..."
            
            item_id = self.tree.insert("", tk.END, values=(
                "☐",  # Checkbox placeholder
                f"{source_icon} {option['source']}{ols_only}",
                option['label'],
                option['ontology'],
                uri,
                description
            ))
            
            self.checkboxes[item_id] = {
                'selected': False,
                'option': option
            }
        
        # Bind click event
        self.tree.bind("<Button-1>", self.on_tree_click)
        self.tree.bind("<Double-1>", self.show_details)
        
        # Buttons frame
        buttons_frame = ttk.Frame(self.window)
        buttons_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(buttons_frame, text="Select All", command=self.select_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Clear All", command=self.clear_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Show Details", command=self.show_details).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(buttons_frame, text="Skip", command=self.skip).pack(side=tk.RIGHT, padx=5)
        ttk.Button(buttons_frame, text="Confirm Selection", command=self.confirm).pack(side=tk.RIGHT, padx=5)
        
        # Status
        self.status_label = ttk.Label(self.window, text="Select one or more alignments for this concept")
        self.status_label.pack(pady=5)
        
    def on_tree_click(self, event):
        """Handle tree item click to toggle selection"""
        region = self.tree.identify_region(event.x, event.y)
        if region == "cell":
            item = self.tree.identify_row(event.y)
            column = self.tree.identify_column(event.x)
            
            if column == "#1" and item in self.checkboxes:  # First column (Select)
                self.toggle_selection(item)
    
    def toggle_selection(self, item):
        """Toggle selection of an item"""
        checkbox_data = self.checkboxes[item]
        checkbox_data['selected'] = not checkbox_data['selected']
        
        # Update checkbox display
        values = list(self.tree.item(item, "values"))
        values[0] = "☑" if checkbox_data['selected'] else "☐"
        self.tree.item(item, values=values)
        
        # Update status
        selected_count = sum(1 for cb in self.checkboxes.values() if cb['selected'])
        self.status_label.config(text=f"Selected {selected_count} alignment(s)")
    
    def select_all(self):
        """Select all items"""
        for item in self.checkboxes:
            if not self.checkboxes[item]['selected']:
                self.toggle_selection(item)
    
    def clear_all(self):
        """Clear all selections"""
        for item in self.checkboxes:
            if self.checkboxes[item]['selected']:
                self.toggle_selection(item)
    
    def show_details(self, event=None):
        """Show detailed information about selected item"""
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showinfo("No Selection", "Please select an item to view details.")
            return
        
        item = selected_items[0]
        option = self.checkboxes[item]['option']
        
        # Create details window
        details_window = tk.Toplevel(self.window)
        details_window.title(f"Details: {option['label']}")
        details_window.geometry("600x400")
        
        # Add details
        text_widget = scrolledtext.ScrolledText(details_window, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        details_text = f"""Label: {option['label']}
Source: {option['source']}
Ontology: {option['ontology']}
URI: {option['uri']}

Description:
{option.get('description', 'No description available')}

Synonyms:
"""
        if option.get('synonyms'):
            for synonym in option['synonyms']:
                details_text += f"• {synonym}\n"
        else:
            details_text += "No synonyms available"
        
        text_widget.insert(tk.END, details_text)
        text_widget.config(state=tk.DISABLED)
        
        # Add URI copy button
        def copy_uri():
            details_window.clipboard_clear()
            details_window.clipboard_append(option['uri'])
            messagebox.showinfo("Copied", "URI copied to clipboard!")
        
        ttk.Button(details_window, text="Copy URI", command=copy_uri).pack(pady=5)
    
    def skip(self):
        """Skip this concept"""
        self.result = []
        self.window.destroy()
    
    def confirm(self):
        """Confirm selections"""
        selected_options = []
        for item, checkbox_data in self.checkboxes.items():
            if checkbox_data['selected']:
                option = checkbox_data['option']
                selected_options.append({
                    'uri': option['uri'],
                    'label': option['label'],
                    'ontology': option['ontology'],
                    'description': option.get('description', ''),
                    'synonyms': option.get('synonyms', []),
                    'source': option['source'],
                    'relationship': 'owl:sameAs' if self.concept['category'] == 'instance' else 'rdfs:seeAlso'
                })
        
        if not selected_options:
            messagebox.showwarning("No Selection", "Please select at least one alignment or skip this concept.")
            return
        
        self.result = selected_options
        self.window.destroy()


class BioPortalGUI:
    """Main GUI application for BioPortal ontology alignment"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("BioPortal Ontology Alignment GUI")
        self.root.geometry("1200x800")
        
        # Application state
        self.ttl_file = tk.StringVar()
        self.api_key = tk.StringVar()
        self.output_file = tk.StringVar(value="improved_ontology.ttl")
        self.report_file = tk.StringVar(value="alignment_report.json")
        self.output_format = tk.StringVar(value="turtle")  # Default format
        
        # Service options
        self.use_bioportal = tk.BooleanVar(value=True)
        self.use_ols = tk.BooleanVar(value=True)
        
        # New options for ontology selection and single word queries
        self.selected_ontologies = tk.StringVar()
        self.single_word_query = tk.StringVar()
        self.use_single_word = tk.BooleanVar(value=False)
        self.max_results = tk.IntVar(value=5)
        
        # Processing state
        self.is_processing = False
        self.current_concepts = []
        self.current_selections = {}
        self.all_comparisons = {}
        self.waiting_for_selection = False
        self.current_selection_result = None
        
        # Advanced features state
        self.dark_mode = tk.BooleanVar(value=False)
        self.min_confidence = tk.DoubleVar(value=0.0)
        self.search_synonyms = tk.BooleanVar(value=True)
        self.search_descriptions = tk.BooleanVar(value=False)
        self.search_history = []
        self.max_history = 10
        
        self.setup_ui()
        self.setup_keyboard_shortcuts()
        self.setup_drag_drop()
        
    def setup_ui(self):
        """Setup the main GUI"""
        # Create notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Configuration tab
        config_frame = ttk.Frame(notebook)
        notebook.add(config_frame, text="Configuration")
        self.setup_config_tab(config_frame)
        
        # Processing tab
        process_frame = ttk.Frame(notebook)
        notebook.add(process_frame, text="Processing")
        self.setup_process_tab(process_frame)
        
        # Results tab
        results_frame = ttk.Frame(notebook)
        notebook.add(results_frame, text="Results")
        self.setup_results_tab(results_frame)
        
        # Status bar
        self.status_bar = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def setup_config_tab(self, parent):
        """Setup configuration tab"""
        # Mode selection
        mode_frame = ttk.LabelFrame(parent, text="Operation Mode")
        mode_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Radiobutton(mode_frame, text="📄 Process TTL File", variable=self.use_single_word, 
                       value=False, command=self.on_mode_change).pack(anchor=tk.W, padx=5, pady=2)
        ttk.Radiobutton(mode_frame, text="🔍 Single Word Query", variable=self.use_single_word, 
                       value=True, command=self.on_mode_change).pack(anchor=tk.W, padx=5, pady=2)
        
        # File selection
        self.file_frame = ttk.LabelFrame(parent, text="Input File")
        self.file_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(self.file_frame, text="TTL Ontology File:").pack(anchor=tk.W, padx=5, pady=2)
        file_entry_frame = ttk.Frame(self.file_frame)
        file_entry_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Entry(file_entry_frame, textvariable=self.ttl_file, width=60).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(file_entry_frame, text="Browse", command=self.browse_ttl_file).pack(side=tk.LEFT)
        
        # Single word query
        self.query_frame = ttk.LabelFrame(parent, text="Single Word Query")
        self.query_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(self.query_frame, text="Query Term:").pack(anchor=tk.W, padx=5, pady=2)
        ttk.Entry(self.query_frame, textvariable=self.single_word_query, width=60).pack(anchor=tk.W, padx=5, pady=2)
        ttk.Label(self.query_frame, text="Enter a single word or term to search for (e.g., 'fatigue', 'covid', 'cancer')", 
                 font=("Arial", 8), foreground="gray").pack(anchor=tk.W, padx=5)
        
        # Ontology selection
        ontology_frame = ttk.LabelFrame(parent, text="Ontology Selection")
        ontology_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ont_entry_frame = ttk.Frame(ontology_frame)
        ont_entry_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(ontology_frame, text="Selected Ontologies (comma-separated):").pack(anchor=tk.W, padx=5, pady=2)
        ttk.Entry(ont_entry_frame, textvariable=self.selected_ontologies, width=50).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(ont_entry_frame, text="Browse Ontologies", command=self.browse_ontologies).pack(side=tk.LEFT)
        
        ttk.Label(ontology_frame, text="Leave empty for automatic selection, or specify like: HP,NCIT,MONDO", 
                 font=("Arial", 8), foreground="gray").pack(anchor=tk.W, padx=5)
        
        # Search options with advanced filters
        search_frame = ttk.LabelFrame(parent, text="Search Options & Filters")
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        
        max_results_frame = ttk.Frame(search_frame)
        max_results_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(max_results_frame, text="Max Results per Search:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Spinbox(max_results_frame, from_=1, to=20, textvariable=self.max_results, width=5).pack(side=tk.LEFT)
        
        # Advanced filters
        filters_frame = ttk.Frame(search_frame)
        filters_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Confidence filter
        conf_frame = ttk.Frame(filters_frame)
        conf_frame.pack(fill=tk.X, pady=2)
        ttk.Label(conf_frame, text="Min Confidence Score:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Scale(conf_frame, from_=0.0, to=1.0, variable=self.min_confidence, 
                 orient=tk.HORIZONTAL, length=200).pack(side=tk.LEFT, padx=(0, 5))
        self.conf_label = ttk.Label(conf_frame, text="0.0")
        self.conf_label.pack(side=tk.LEFT)
        self.min_confidence.trace_add('write', self.update_confidence_label)
        
        # Search scope checkboxes
        ttk.Checkbutton(filters_frame, text="Search in Synonyms", 
                       variable=self.search_synonyms).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(filters_frame, text="Search in Descriptions", 
                       variable=self.search_descriptions).pack(anchor=tk.W, pady=2)
        
        # API Configuration
        api_frame = ttk.LabelFrame(parent, text="API Configuration")
        api_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(api_frame, text="BioPortal API Key (optional):").pack(anchor=tk.W, padx=5, pady=2)
        ttk.Entry(api_frame, textvariable=self.api_key, width=60, show="*").pack(anchor=tk.W, padx=5, pady=2)
        ttk.Label(api_frame, text="Leave empty for demo mode or set BIOPORTAL_API_KEY environment variable", 
                 font=("Arial", 8), foreground="gray").pack(anchor=tk.W, padx=5)
        
        # Service Selection
        service_frame = ttk.LabelFrame(parent, text="Services")
        service_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Checkbutton(service_frame, text="🌐 Use BioPortal", variable=self.use_bioportal).pack(anchor=tk.W, padx=5, pady=2)
        ttk.Checkbutton(service_frame, text="🔬 Use OLS (Ontology Lookup Service)", variable=self.use_ols).pack(anchor=tk.W, padx=5, pady=2)
        
        # Output Configuration
        output_frame = ttk.LabelFrame(parent, text="Output Files")
        output_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(output_frame, text="Output Ontology File:").pack(anchor=tk.W, padx=5, pady=2)
        ttk.Entry(output_frame, textvariable=self.output_file, width=60).pack(anchor=tk.W, padx=5, pady=2)
        
        # Format selection
        format_frame = ttk.Frame(output_frame)
        format_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(format_frame, text="Output Format:").pack(side=tk.LEFT, padx=(0, 5))
        format_options = ['turtle', 'json-ld', 'xml', 'nt', 'n3', 'trig', 'nquads', 'csv', 'tsv', 'sssom']
        format_combo = ttk.Combobox(format_frame, textvariable=self.output_format, 
                                    values=format_options, state='readonly', width=15)
        format_combo.pack(side=tk.LEFT, padx=(0, 5))
        format_combo.bind('<<ComboboxSelected>>', self.on_format_change)
        
        ttk.Label(format_frame, text="(Auto-detect from filename or select manually)", 
                 font=("Arial", 8), foreground="gray").pack(side=tk.LEFT, padx=5)
        
        ttk.Label(output_frame, text="Alignment Report File:").pack(anchor=tk.W, padx=5, pady=2)
        ttk.Entry(output_frame, textvariable=self.report_file, width=60).pack(anchor=tk.W, padx=5, pady=2)
        
        # Advanced Features
        advanced_frame = ttk.LabelFrame(parent, text="Advanced Features")
        advanced_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Theme toggle
        theme_frame = ttk.Frame(advanced_frame)
        theme_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Checkbutton(theme_frame, text="🌙 Dark Mode", variable=self.dark_mode, 
                       command=self.toggle_dark_mode).pack(side=tk.LEFT, padx=5)
        
        # Search history
        history_frame = ttk.Frame(advanced_frame)
        history_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(history_frame, text="Recent Searches:").pack(side=tk.LEFT, padx=(0, 5))
        self.history_combo = ttk.Combobox(history_frame, values=[], state='readonly', width=40)
        self.history_combo.pack(side=tk.LEFT, padx=(0, 5))
        self.history_combo.bind('<<ComboboxSelected>>', self.load_from_history)
        ttk.Button(history_frame, text="Clear History", command=self.clear_history).pack(side=tk.LEFT, padx=5)
        
        # Action buttons
        action_frame = ttk.Frame(parent)
        action_frame.pack(fill=tk.X, padx=10, pady=20)
        
        self.start_button = ttk.Button(action_frame, text="▶ Start Processing", command=self.start_processing)
        self.start_button.pack(side=tk.LEFT, padx=5)
        ToolTip(self.start_button, "Start processing ontology or single word query (Ctrl+S)")
        
        load_btn = ttk.Button(action_frame, text="📁 Load Example", command=self.load_example)
        load_btn.pack(side=tk.LEFT, padx=5)
        ToolTip(load_btn, "Load an example ontology file for testing")
        
        list_btn = ttk.Button(action_frame, text="📋 List Ontologies", command=self.show_ontologies)
        list_btn.pack(side=tk.LEFT, padx=5)
        ToolTip(list_btn, "Show list of available ontologies")
        
        help_btn = ttk.Button(action_frame, text="❓ Help", command=self.show_help)
        help_btn.pack(side=tk.RIGHT, padx=5)
        ToolTip(help_btn, "Show help and keyboard shortcuts (F1)")
        
        # Initialize mode
        self.on_mode_change()
        
    def setup_process_tab(self, parent):
        """Setup processing tab"""
        # Progress frame
        progress_frame = ttk.LabelFrame(parent, text="Progress")
        progress_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.progress_label = ttk.Label(progress_frame, text="No processing started")
        self.progress_label.pack(anchor=tk.W, padx=5, pady=2)
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress_bar.pack(fill=tk.X, padx=5, pady=5)
        
        # Add detailed progress label
        self.detailed_progress = ttk.Label(progress_frame, text="", foreground="gray")
        self.detailed_progress.pack(anchor=tk.W, padx=5, pady=2)
        
        # Add indeterminate progress for network operations
        self.network_progress = ttk.Progressbar(progress_frame, mode='indeterminate', length=200)
        self.network_progress_label = ttk.Label(progress_frame, text="")
        
        # Log frame
        log_frame = ttk.LabelFrame(parent, text="Processing Log")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=20)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Control buttons
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.stop_button = ttk.Button(control_frame, text="Stop Processing", command=self.stop_processing, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_frame, text="Clear Log", command=self.clear_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Save Log", command=self.save_log).pack(side=tk.RIGHT, padx=5)
        
    def setup_results_tab(self, parent):
        """Setup results tab"""
        # Validation frame
        validation_frame = ttk.LabelFrame(parent, text="⚠️ Validation & Quality Checks")
        validation_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.validation_text = scrolledtext.ScrolledText(validation_frame, wrap=tk.WORD, height=4)
        self.validation_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.validation_text.insert(tk.END, "No validation issues detected.\n")
        self.validation_text.config(state=tk.DISABLED)
        
        # Summary frame
        summary_frame = ttk.LabelFrame(parent, text="Processing Summary")
        summary_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.summary_text = scrolledtext.ScrolledText(summary_frame, wrap=tk.WORD, height=8)
        self.summary_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Statistics visualization frame
        stats_frame = ttk.LabelFrame(parent, text="📊 Mapping Statistics")
        stats_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.stats_canvas = tk.Canvas(stats_frame, height=150, bg='white')
        self.stats_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Files frame
        files_frame = ttk.LabelFrame(parent, text="Generated Files")
        files_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.files_tree = ttk.Treeview(files_frame, columns=("File", "Size", "Description"), show="headings", height=6)
        self.files_tree.heading("File", text="File")
        self.files_tree.heading("Size", text="Size")
        self.files_tree.heading("Description", text="Description")
        
        self.files_tree.column("File", width=300)
        self.files_tree.column("Size", width=100)
        self.files_tree.column("Description", width=400)
        
        self.files_tree.pack(fill=tk.X, padx=5, pady=5)
        
        # Results actions
        results_action_frame = ttk.Frame(parent)
        results_action_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(results_action_frame, text="Open Output Folder", command=self.open_output_folder).pack(side=tk.LEFT, padx=5)
        ttk.Button(results_action_frame, text="View Ontology", command=self.view_ontology).pack(side=tk.LEFT, padx=5)
        ttk.Button(results_action_frame, text="Export Report", command=self.export_report).pack(side=tk.RIGHT, padx=5)
        
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
    
    def browse_ttl_file(self):
        """Browse for TTL file"""
        filename = filedialog.askopenfilename(
            title="Select TTL Ontology File",
            filetypes=[("Turtle files", "*.ttl"), ("All files", "*.*")]
        )
        if filename:
            self.ttl_file.set(filename)
    
    def load_example(self):
        """Load example configuration"""
        example_path = "/home/jhe24/AID-PAIS/AID-PAIS-KnowledgeGraph/hybrid_kg_prototype/ontology_mapping/test_medical_ontology.ttl"
        if os.path.exists(example_path):
            self.ttl_file.set(example_path)
            self.log("Loaded example configuration")
        else:
            messagebox.showwarning("Example Not Found", "Example file not found. Please select a TTL file manually.")
    
    def start_processing(self):
        """Start the ontology processing"""
        # Validate inputs based on mode
        if self.use_single_word.get():
            # Single word mode validation
            if not self.single_word_query.get().strip():
                messagebox.showerror("Error", "Please enter a query term")
                return
        else:
            # TTL file mode validation
            if not self.ttl_file.get():
                messagebox.showerror("Error", "Please select a TTL file")
                return
            
            if not os.path.exists(self.ttl_file.get()):
                messagebox.showerror("Error", "Selected TTL file does not exist")
                return
        
        if not self.use_bioportal.get() and not self.use_ols.get():
            messagebox.showerror("Error", "Please select at least one service (BioPortal or OLS)")
            return
        
        # Disable start button and enable stop button
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.is_processing = True
        
        # Clear previous results
        self.clear_log()
        self.current_selections = {}
        self.all_comparisons = {}
        
        # Start processing in a separate thread
        if self.use_single_word.get():
            threading.Thread(target=self.process_single_word, daemon=True).start()
        else:
            threading.Thread(target=self.process_ontology, daemon=True).start()

    def process_single_word(self):
        """Process single word query (runs in separate thread)"""
        try:
            self.update_status("Starting single word query...")
            self.log("🔍 Single Word Query Mode")
            self.log(f"Query: '{self.single_word_query.get()}'")
            self.log("=" * 40)
            
            # Initialize components
            bioportal = BioPortalLookup(self.api_key.get() if self.api_key.get() else None)
            ols = OLSLookup()
            lookup = ConceptLookup(bioportal, ols, self.selected_ontologies.get() if self.selected_ontologies.get() else None)
            
            # Show ontologies being used
            if self.selected_ontologies.get():
                self.log(f"🎯 Using ontologies: {self.selected_ontologies.get()}")
            else:
                self.log("🎯 Using default ontology selection strategy")
            
            # Create a mock concept for the single word
            concept = {
                'key': self.single_word_query.get().replace(' ', '_'),
                'label': self.single_word_query.get(),
                'type': 'Term',
                'category': 'query'
            }
            
            self.update_status("Searching for alignments...")
            self.show_network_progress(True, "🌐 Querying BioPortal and OLS APIs...")
            
            # Perform lookup
            options, comparison = lookup.lookup_concept(concept, self.max_results.get())
            
            self.show_network_progress(False)
            
            if not options:
                self.log(f"❌ No results found for '{self.single_word_query.get()}'")
                self.update_status("No results found")
                return
            
            # Display comparison summary
            if comparison['discrepancies']:
                self.log(f"\n⚠️  Service Comparison Alert:")
                for discrepancy in comparison['discrepancies']:
                    self.log(f"   • {discrepancy}")
                self.log(f"   BioPortal: {comparison['bioportal_count']} results")
                self.log(f"   OLS: {comparison['ols_count']} results")
                self.log("")
            
            # Store current concept for selection
            self.current_concepts = [concept]
            self.current_options = options
            self.current_comparison = comparison
            
            # Switch to processing tab and show results
            self.root.after(0, lambda: self.show_single_word_results(concept, options, comparison))
            
        except Exception as e:
            self.log(f"❌ Error: {e}")
            self.update_status(f"Error: {e}")
        finally:
            self.root.after(0, self.processing_complete)

    def show_single_word_results(self, concept: Dict, options: List[Dict], comparison: Dict):
        """Show single word query results for selection"""
        self.log(f"✅ Found {len(options)} standardized terms:")
        for j, result in enumerate(options, 1):
            source_indicator = "🌐" if result['source'] == 'bioportal' else "🔬" if result['source'] == 'ols' else "🎭"
            ols_only_indicator = " (OLS-only)" if result.get('ols_only') else ""
            
            self.log(f"{j:2d}. {source_indicator} {result['label']}{ols_only_indicator}")
            self.log(f"     Ontology: {result['ontology']} | Source: {result['source']}")
            self.log(f"     URI: {result['uri'][:70]}{'...' if len(result['uri']) > 70 else ''}")
            
            # Show description if available
            if result.get('description') and result['description'].strip():
                desc = result['description'][:120] + "..." if len(result['description']) > 120 else result['description']
                self.log(f"     Description: {desc}")
            
            # Show synonyms if available
            if result.get('synonyms') and len(result['synonyms']) > 0:
                synonyms_str = ", ".join(result['synonyms'][:3])  # Show max 3 synonyms
                if len(result['synonyms']) > 3:
                    synonyms_str += f" (+ {len(result['synonyms']) - 3} more)"
                self.log(f"     Synonyms: {synonyms_str}")
            
            self.log("")
        
        # Open alignment window for selection
        self.show_concept_alignment_window(concept, options, comparison)
    
    def process_ontology(self):
        """Process the ontology (runs in separate thread)"""
        try:
            self.update_status("Starting ontology processing...")
            self.log("🔧 BioPortal & OLS Ontology Alignment GUI")
            self.log("=" * 45)
            
            # Initialize components
            bioportal = BioPortalLookup(self.api_key.get() if self.api_key.get() else None)
            ols = OLSLookup()
            ontology = OntologyParser(self.ttl_file.get())
            lookup = ConceptLookup(bioportal, ols)
            
            # Parse ontology
            self.log(f"Loading ontology from {self.ttl_file.get()}...")
            if not ontology.parse():
                self.log("❌ Failed to parse ontology")
                return
            
            self.log(f"✅ Loaded {len(ontology.graph)} triples")
            self.log(f"📊 Found {len(ontology.classes)} classes and {len(ontology.instances)} instances")
            
            # Get concepts to improve
            concepts = ontology.get_priority_concepts()
            if not concepts:
                self.log("❌ No priority concepts found in ontology")
                return
            
            self.current_concepts = concepts
            self.log(f"🎯 Found {len(concepts)} priority concepts to improve")
            
            # Update progress bar
            self.root.after(0, lambda: self.progress_bar.config(maximum=len(concepts)))
            
            # Process each concept
            for i, concept in enumerate(concepts):
                if not self.is_processing:
                    self.log("⏹️ Processing stopped by user")
                    return
                
                self.root.after(0, lambda i=i: self.progress_bar.config(value=i))
                self.root.after(0, lambda i=i, concept=concept: self.progress_label.config(
                    text=f"Processing concept {i+1}/{len(concepts)}: {concept['label']}"
                ))
                
                self.log(f"\n🔍 Step {i+1}/{len(concepts)}: {concept['label']} ({concept['type']})")
                self.show_network_progress(True, f"🌐 Querying APIs for '{concept['label']}'...")
                
                # Perform lookup
                options, comparison = lookup.lookup_concept(concept)
                self.all_comparisons[concept['key']] = comparison
                
                self.show_network_progress(False)
                
                if not options:
                    self.log(f"❌ No results found for '{concept['label']}'")
                    continue
                
                # Display comparison summary
                if comparison['discrepancies']:
                    self.log("⚠️ Service Comparison Alert:")
                    for discrepancy in comparison['discrepancies']:
                        self.log(f"   • {discrepancy}")
                
                self.log(f"✅ Found {len(options)} standardized terms")
                
                # Show alignment window (must be done on main thread)
                alignment_window = None
                self.root.after(0, lambda: self.show_alignment_window(concept, options, comparison))
                
                # Wait for user selection (simple polling)
                while hasattr(self, 'waiting_for_selection') and self.waiting_for_selection and self.is_processing:
                    threading.Event().wait(0.1)
                
                if not self.is_processing:
                    return
                
                # Process selection result
                if self.current_selection_result is not None:
                    if self.current_selection_result:
                        self.current_selections[concept['key']] = self.current_selection_result
                        self.log(f"✅ Selected {len(self.current_selection_result)} alignment(s) for {concept['label']}")
                    else:
                        self.log(f"⏭️ Skipped {concept['label']}")
                    self.current_selection_result = None
            
            # Generate improved ontology if we have selections
            if self.current_selections:
                self.generate_improved_ontology(ontology)
            else:
                self.log("❌ No selections made. Process completed without generating improved ontology.")
            
            self.log("\n🎉 Processing completed!")
            
        except Exception as e:
            self.log(f"❌ Error during processing: {str(e)}")
        finally:
            # Re-enable controls
            self.root.after(0, lambda: self.start_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.stop_button.config(state=tk.DISABLED))
            self.root.after(0, lambda: self.progress_label.config(text="Processing completed"))
            self.is_processing = False
    
    def show_alignment_window(self, concept, options, comparison):
        """Show alignment selection window on main thread"""
        self.waiting_for_selection = True
        
        def on_window_close():
            self.current_selection_result = alignment_window.result
            self.waiting_for_selection = False
        
        alignment_window = ConceptAlignmentWindow(self.root, concept, options, comparison)
        alignment_window.window.protocol("WM_DELETE_WINDOW", on_window_close)
        self.root.wait_window(alignment_window.window)
        on_window_close()
    
    def generate_improved_ontology(self, ontology):
        """Generate the improved ontology with alignments"""
        self.log("\n💾 Generating Improved Ontology")
        self.log("=" * 35)
        
        # Validate mappings first
        self.validate_mappings(self.current_selections)
        
        try:
            # Import rdflib components
            from rdflib import Graph, RDF, RDFS, OWL, SKOS, URIRef, Literal
            from rdflib.namespace import DCTERMS
            
            # Create enhanced graph
            improved_graph = Graph()
            
            # Copy original ontology
            for s, p, o in ontology.graph:
                improved_graph.add((s, p, o))
            
            # Add namespace bindings - using standard vocabularies
            improved_graph.bind("", "http://example.org/ontology#")
            improved_graph.bind("owl", OWL)
            improved_graph.bind("skos", SKOS)
            improved_graph.bind("dcterms", DCTERMS)
            improved_graph.bind("prov", "http://www.w3.org/ns/prov#")
            improved_graph.bind("mondo", "http://purl.obolibrary.org/obo/MONDO_")
            improved_graph.bind("hp", "http://purl.obolibrary.org/obo/HP_")
            improved_graph.bind("go", "http://purl.obolibrary.org/obo/GO_")
            improved_graph.bind("ncit", "http://purl.obolibrary.org/obo/NCIT_")
            improved_graph.bind("efo", "http://www.ebi.ac.uk/efo/EFO_")
            improved_graph.bind("doid", "http://purl.obolibrary.org/obo/DOID_")
            
            # Add alignments with standardized properties
            total_alignments = 0
            for concept_key, alignments in self.current_selections.items():
                local_uri = URIRef(f"http://example.org/ontology#{concept_key}")
                
                for alignment in alignments:
                    external_uri = URIRef(alignment['uri'])
                    
                    # Determine alignment type based on similarity
                    alignment_type = self._determine_alignment_type(alignment, concept_key)
                    
                    # Add standardized alignment relationship
                    if alignment_type == 'exact':
                        improved_graph.add((local_uri, SKOS.exactMatch, external_uri))
                    elif alignment_type == 'close':
                        improved_graph.add((local_uri, SKOS.closeMatch, external_uri))
                    elif alignment_type == 'related':
                        improved_graph.add((local_uri, SKOS.relatedMatch, external_uri))
                    else:
                        improved_graph.add((local_uri, RDFS.seeAlso, external_uri))
                    
                    # Add standard metadata
                    improved_graph.add((local_uri, SKOS.inScheme, URIRef(f"http://bioportal.bioontology.org/ontologies/{alignment['ontology']}")))
                    improved_graph.add((local_uri, DCTERMS.source, URIRef(f"http://bioportal.bioontology.org/ontologies/{alignment['ontology']}")))
                    
                    # Use standard SKOS properties for labels
                    if alignment.get('label') and alignment['label'].strip():
                        existing_labels = [str(o) for s, p, o in improved_graph.triples((local_uri, SKOS.prefLabel, None))]
                        if alignment['label'] not in existing_labels:
                            improved_graph.add((local_uri, SKOS.altLabel, Literal(alignment['label'], lang='en')))
                    
                    # Add description using standard DCTERMS
                    if alignment.get('description') and alignment['description'].strip():
                        clean_description = self._clean_description(alignment['description'])
                        if clean_description:
                            improved_graph.add((local_uri, DCTERMS.description, Literal(clean_description, lang='en')))
                    
                    # Add deduplicated synonyms
                    if alignment.get('synonyms'):
                        existing_alt_labels = set(str(o).lower() for s, p, o in improved_graph.triples((local_uri, SKOS.altLabel, None)))
                        unique_synonyms = self._deduplicate_synonyms(alignment['synonyms'], existing_alt_labels)
                        
                        for synonym in unique_synonyms[:3]:
                            improved_graph.add((local_uri, SKOS.altLabel, Literal(synonym, lang='en')))
                    
                    total_alignments += 1
                    source_icon = "🌐" if alignment['source'] == 'bioportal' else "🔬"
                    self.log(f"✅ {source_icon} {concept_key} → {alignment['label']} ({alignment['ontology']}) [{alignment_type}]")
            
            # Add enhanced provenance using PROV-O vocabulary
            prov_activity = URIRef("http://example.org/ontology#BioPortalGUIAlignment")
            improved_graph.add((prov_activity, RDF.type, URIRef("http://www.w3.org/ns/prov#Activity")))
            improved_graph.add((prov_activity, DCTERMS.title, Literal("Ontology Alignment Activity", lang='en')))
            improved_graph.add((prov_activity, DCTERMS.description, 
                             Literal("Interactive ontology alignment using BioPortal and OLS services via GUI", lang='en')))
            improved_graph.add((prov_activity, URIRef("http://www.w3.org/ns/prov#startedAtTime"), 
                             Literal(datetime.now().isoformat())))
            
            # Add tool information
            tool_agent = URIRef("http://example.org/ontology#BioPortalGUITool")
            improved_graph.add((tool_agent, RDF.type, URIRef("http://www.w3.org/ns/prov#SoftwareAgent")))
            improved_graph.add((tool_agent, DCTERMS.title, Literal("BioPortal GUI Alignment Tool", lang='en')))
            improved_graph.add((tool_agent, URIRef("http://www.w3.org/ns/prov#wasAssociatedWith"), prov_activity))
            
            # Save improved ontology using selected format
            output_path = self.output_file.get()
            format_name = self.output_format.get()
            
            # Import and use OntologyGenerator for serialization
            from core.generator import OntologyGenerator
            generator = OntologyGenerator()
            generator._serialize_graph(improved_graph, output_path, format_name)
            
            self.log(f"  Saved as {format_name} format")
            
            # Generate report
            report = {
                'timestamp': datetime.now().isoformat(),
                'input_file': self.ttl_file.get(),
                'output_file': output_path,
                'output_format': format_name,
                'original_triples': len(ontology.graph),
                'improved_triples': len(improved_graph),
                'alignments_added': total_alignments,
                'concepts_aligned': len(self.current_selections),
                'service_comparisons': self.all_comparisons,
                'selections': self.current_selections
            }
            
            report_path = self.report_file.get()
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            # Update results tab
            self.update_results(report, output_path, report_path)
            
            # Log summary
            self.log(f"\n🎉 SUCCESS!")
            self.log(f"  Output: {output_path}")
            self.log(f"  Report: {report_path}")
            self.log(f"  Original triples: {len(ontology.graph):,}")
            self.log(f"  New triples: {len(improved_graph) - len(ontology.graph):,}")
            self.log(f"  Total triples: {len(improved_graph):,}")
            self.log(f"  Concepts aligned: {len(self.current_selections)}")
            self.log(f"  Total alignments: {total_alignments}")
            
        except Exception as e:
            self.log(f"❌ Error generating improved ontology: {str(e)}")
    
    def validate_mappings(self, selections):
        """Validate mappings and detect potential issues"""
        issues = []
        
        # Check for duplicate mappings
        uri_counts = {}
        for concept_key, alignments in selections.items():
            for alignment in alignments:
                uri = alignment['uri']
                if uri in uri_counts:
                    uri_counts[uri].append(concept_key)
                else:
                    uri_counts[uri] = [concept_key]
        
        duplicates = {uri: concepts for uri, concepts in uri_counts.items() if len(concepts) > 1}
        if duplicates:
            issues.append("⚠️ DUPLICATE MAPPINGS:")
            for uri, concepts in duplicates.items():
                issues.append(f"  • {uri[:60]}... mapped by: {', '.join(concepts)}")
        
        # Check for concepts with many mappings
        multi_mapped = {k: v for k, v in selections.items() if len(v) > 5}
        if multi_mapped:
            issues.append("\n⚠️ CONCEPTS WITH MANY MAPPINGS:")
            for concept, alignments in multi_mapped.items():
                issues.append(f"  • {concept}: {len(alignments)} mappings (may need review)")
        
        # Check for low confidence if available
        low_conf = []
        for concept_key, alignments in selections.items():
            for alignment in alignments:
                if 'confidence' in alignment and alignment['confidence'] < 0.5:
                    low_conf.append(f"  • {concept_key} → {alignment['label']} (confidence: {alignment['confidence']:.2f})")
        
        if low_conf:
            issues.append("\n⚠️ LOW CONFIDENCE MAPPINGS:")
            issues.extend(low_conf)
        
        # Update validation panel
        self.validation_text.config(state=tk.NORMAL)
        self.validation_text.delete(1.0, tk.END)
        
        if issues:
            self.validation_text.insert(tk.END, "\n".join(issues))
            self.log(f"\n⚠️ Validation detected {len(issues)} potential issues")
        else:
            self.validation_text.insert(tk.END, "✅ No validation issues detected.\n")
            self.log("✅ Validation passed - no issues detected")
        
        self.validation_text.config(state=tk.DISABLED)
        return len(issues) == 0
    
    def update_results(self, report, output_path, report_path):
        """Update the results tab with processing results"""
        def update_ui():
            # Update summary
            self.summary_text.delete(1.0, tk.END)
            summary = f"""Processing completed successfully!

Input File: {report['input_file']}
Output File: {report['output_file']}
Report File: {report_path}

Statistics:
• Original triples: {report['original_triples']:,}
• New triples added: {report['improved_triples'] - report['original_triples']:,}
• Total triples: {report['improved_triples']:,}
• Concepts aligned: {report['concepts_aligned']}
• Total alignments: {report['alignments_added']}

Processing completed at: {report['timestamp']}
"""
            self.summary_text.insert(tk.END, summary)
            
            # Update files tree
            for item in self.files_tree.get_children():
                self.files_tree.delete(item)
            
            # Add output files
            if os.path.exists(output_path):
                size = f"{os.path.getsize(output_path):,} bytes"
                self.files_tree.insert("", tk.END, values=(output_path, size, "Enhanced ontology with alignments"))
            
            if os.path.exists(report_path):
                size = f"{os.path.getsize(report_path):,} bytes"
                self.files_tree.insert("", tk.END, values=(report_path, size, "Detailed alignment report"))
            
            # Add comparison report if available
            comp_report_path = "service_comparison_report.json"
            if os.path.exists(comp_report_path):
                size = f"{os.path.getsize(comp_report_path):,} bytes"
                self.files_tree.insert("", tk.END, values=(comp_report_path, size, "Service comparison analysis"))
            
            # Draw statistics visualization
            self.draw_statistics(report)
        
        self.root.after(0, update_ui)
    
    def stop_processing(self):
        """Stop the processing"""
        self.is_processing = False
        self.update_status("Stopping processing...")
    
    def log(self, message):
        """Add message to log"""
        def update_log():
            self.log_text.insert(tk.END, message + "\n")
            self.log_text.see(tk.END)
            self.root.update_idletasks()
        
        self.root.after(0, update_log)
    
    def clear_log(self):
        """Clear the processing log"""
        self.log_text.delete(1.0, tk.END)
    
    def draw_statistics(self, report):
        """Draw simple bar chart statistics on canvas"""
        canvas = self.stats_canvas
        canvas.delete("all")
        
        # Get canvas dimensions
        width = canvas.winfo_width() if canvas.winfo_width() > 1 else 800
        height = canvas.winfo_height() if canvas.winfo_height() > 1 else 150
        
        # Calculate statistics by ontology
        ontology_counts = {}
        for concept_key, alignments in report.get('selections', {}).items():
            for alignment in alignments:
                ont = alignment.get('ontology', 'Unknown')
                ontology_counts[ont] = ontology_counts.get(ont, 0) + 1
        
        if not ontology_counts:
            canvas.create_text(width//2, height//2, text="No data to display", 
                             font=("Arial", 12), fill="gray")
            return
        
        # Sort by count
        sorted_onts = sorted(ontology_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Draw bar chart
        max_count = max(count for _, count in sorted_onts) if sorted_onts else 1
        bar_width = (width - 200) // len(sorted_onts) if sorted_onts else 50
        bar_spacing = 10
        
        x_offset = 100
        y_offset = 20
        chart_height = height - 40
        
        colors = ['#4CAF50', '#2196F3', '#FF9800', '#9C27B0', '#F44336', 
                 '#00BCD4', '#FFEB3B', '#795548', '#607D8B', '#E91E63']
        
        for i, (ont, count) in enumerate(sorted_onts):
            # Calculate bar dimensions
            bar_height = (count / max_count) * (chart_height - 20)
            x1 = x_offset + i * (bar_width + bar_spacing)
            y1 = y_offset + chart_height - bar_height
            x2 = x1 + bar_width - bar_spacing
            y2 = y_offset + chart_height
            
            # Draw bar
            color = colors[i % len(colors)]
            canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="black")
            
            # Draw count on top of bar
            canvas.create_text((x1 + x2) // 2, y1 - 10, text=str(count), 
                             font=("Arial", 10, "bold"))
            
            # Draw ontology label (rotated if needed)
            label = ont[:8] if len(ont) > 8 else ont
            canvas.create_text((x1 + x2) // 2, y2 + 15, text=label, 
                             font=("Arial", 9), angle=0)
        
        # Draw title
        canvas.create_text(width // 2, 10, text="Mappings by Ontology", 
                         font=("Arial", 12, "bold"))
    
    def save_log(self):
        """Save log to file"""
        filename = filedialog.asksaveasfilename(
            title="Save Processing Log",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            with open(filename, 'w') as f:
                f.write(self.log_text.get(1.0, tk.END))
            messagebox.showinfo("Success", f"Log saved to {filename}")
    
    def update_status(self, message):
        """Update status bar"""
        self.root.after(0, lambda: self.status_bar.config(text=message))
    
    def show_network_progress(self, show=True, message=""):
        """Show/hide network activity indicator"""
        def update():
            if show:
                self.network_progress.pack(anchor=tk.W, padx=5, pady=2)
                self.network_progress.start(10)
                self.network_progress_label.config(text=message)
                self.network_progress_label.pack(anchor=tk.W, padx=5, pady=2)
            else:
                self.network_progress.stop()
                self.network_progress.pack_forget()
                self.network_progress_label.pack_forget()
        
        self.root.after(0, update)
    
    def open_output_folder(self):
        """Open the output folder in file manager"""
        output_dir = os.path.dirname(os.path.abspath(self.output_file.get()))
        if os.path.exists(output_dir):
            os.system(f"xdg-open '{output_dir}'")
        else:
            messagebox.showwarning("Folder Not Found", "Output folder does not exist yet.")
    
    def view_ontology(self):
        """View the generated ontology file"""
        output_path = self.output_file.get()
        if os.path.exists(output_path):
            os.system(f"xdg-open '{output_path}'")
        else:
            messagebox.showwarning("File Not Found", "Output ontology file does not exist yet.")
    
    def export_report(self):
        """Export detailed report"""
        report_path = self.report_file.get()
        if os.path.exists(report_path):
            os.system(f"xdg-open '{report_path}'")
        else:
            messagebox.showwarning("File Not Found", "Report file does not exist yet.")
    
    def show_help(self):
        """Show help information"""
        help_text = """BioPortal Ontology Alignment GUI Help

This tool helps you enhance your ontologies by aligning concepts with standardized terminologies from BioPortal and OLS (Ontology Lookup Service).

Getting Started:
1. Select a TTL ontology file in the Configuration tab
2. Optionally enter your BioPortal API key (or leave empty for demo mode)
3. Choose which services to use (BioPortal and/or OLS)
4. Configure output file names
5. Click "Start Processing"

Processing:
- The tool will parse your ontology and identify priority concepts
- For each concept, it searches both BioPortal and OLS for standardized terms
- You'll be presented with alignment options and can select the best matches
- The tool compares results between services and flags discrepancies

Results:
- An enhanced ontology file with alignment annotations
- A detailed report of all alignments and comparisons
- Service comparison analysis showing differences between BioPortal and OLS

Tips:
- Use demo mode to test the tool without an API key
- Select multiple alignments for a concept if appropriate
- Review the service comparison alerts to understand differences
- Check the Results tab for generated files and statistics

For more information, visit:
- BioPortal: https://bioportal.bioontology.org/
- OLS: https://www.ebi.ac.uk/ols/
"""
        
        help_window = tk.Toplevel(self.root)
        help_window.title("Help")
        help_window.geometry("600x500")
        
        text_widget = scrolledtext.ScrolledText(help_window, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_widget.insert(tk.END, help_text)
        text_widget.config(state=tk.DISABLED)
    
    def setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts for improved accessibility"""
        self.root.bind('<Control-s>', lambda e: self.start_processing())
        self.root.bind('<Control-o>', lambda e: self.browse_ttl_file())
        self.root.bind('<Control-h>', lambda e: self.show_help())
        self.root.bind('<Control-d>', lambda e: self.toggle_dark_mode())
        self.root.bind('<F1>', lambda e: self.show_help())
        self.root.bind('<Escape>', lambda e: self.stop_processing() if self.is_processing else None)
    
    def setup_drag_drop(self):
        """Setup drag and drop file handling (requires tkinterdnd2)"""
        try:
            self.root.drop_target_register('DND_Files')
            self.root.dnd_bind('<<Drop>>', self.handle_drop)
        except:
            pass  # Silently skip if tkinterdnd2 not available
    
    def handle_drop(self, event):
        """Handle dropped files"""
        try:
            files = self.root.tk.splitlist(event.data)
            if files and files[0].endswith('.ttl'):
                self.ttl_file.set(files[0])
                self.log(f"📁 File loaded via drag & drop: {files[0]}")
        except:
            pass
    
    def update_confidence_label(self, *args):
        """Update confidence score label"""
        score = self.min_confidence.get()
        self.conf_label.config(text=f"{score:.2f}")
    
    def toggle_dark_mode(self):
        """Toggle between light and dark mode"""
        if self.dark_mode.get():
            style = ttk.Style()
            style.theme_use('clam')
            
            bg_color = '#2b2b2b'
            fg_color = '#ffffff'
            select_bg = '#404040'
            
            self.root.configure(bg=bg_color)
            style.configure('TFrame', background=bg_color)
            style.configure('TLabel', background=bg_color, foreground=fg_color)
            style.configure('TLabelframe', background=bg_color, foreground=fg_color)
            style.configure('TLabelframe.Label', background=bg_color, foreground=fg_color)
            style.configure('TButton', background=select_bg, foreground=fg_color)
            style.configure('TCheckbutton', background=bg_color, foreground=fg_color)
            style.configure('TRadiobutton', background=bg_color, foreground=fg_color)
            
            self.log_text.config(bg='#1e1e1e', fg=fg_color, insertbackground=fg_color)
            self.summary_text.config(bg='#1e1e1e', fg=fg_color, insertbackground=fg_color)
            
            self.log("🌙 Dark mode enabled")
        else:
            style = ttk.Style()
            style.theme_use('default')
            
            self.root.configure(bg='SystemButtonFace')
            self.log_text.config(bg='white', fg='black', insertbackground='black')
            self.summary_text.config(bg='white', fg='black', insertbackground='black')
            
            self.log("☀️ Light mode enabled")
    
    def add_to_history(self, query):
        """Add a search to history"""
        if query and query not in self.search_history:
            self.search_history.insert(0, query)
            if len(self.search_history) > self.max_history:
                self.search_history.pop()
            self.history_combo['values'] = self.search_history
    
    def load_from_history(self, event=None):
        """Load a search from history"""
        selection = self.history_combo.get()
        if selection:
            self.single_word_query.set(selection)
            self.log(f"📜 Loaded from history: {selection}")
    
    def clear_history(self):
        """Clear search history"""
        self.search_history = []
        self.history_combo['values'] = []
        self.log("🗑️ Search history cleared")
    
    def browse_ontologies(self):
        """Show ontology selection dialog"""
        ontologies = [
            "MONDO - Monarch Disease Ontology",
            "HP - Human Phenotype Ontology",
            "NCIT - National Cancer Institute Thesaurus",
            "DOID - Disease Ontology",
            "CHEBI - Chemical Entities of Biological Interest",
            "GO - Gene Ontology",
            "SNOMEDCT - SNOMED Clinical Terms",
            "ICD10CM - ICD-10 Clinical Modification",
            "ICD11 - ICD-11",
            "LOINC - Logical Observation Identifiers",
            "OMIM - Online Mendelian Inheritance in Man",
            "ORDO - Orphanet Rare Disease Ontology",
            "EFO - Experimental Factor Ontology",
            "UBERON - Uber Anatomy Ontology"
        ]
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Ontologies")
        dialog.geometry("500x600")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Select ontologies to search:", 
                 font=("Arial", 12, "bold")).pack(padx=10, pady=10)
        
        canvas = tk.Canvas(dialog)
        scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        selections = {}
        for ont in ontologies:
            code = ont.split(' - ')[0]
            var = tk.BooleanVar()
            selections[code] = var
            ttk.Checkbutton(scrollable_frame, text=ont, variable=var).pack(anchor=tk.W, padx=5, pady=2)
        
        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y", pady=10)
        
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def apply_selection():
            selected = [code for code, var in selections.items() if var.get()]
            self.selected_ontologies.set(','.join(selected))
            dialog.destroy()
        
        def select_all():
            for var in selections.values():
                var.set(True)
        
        def clear_all():
            for var in selections.values():
                var.set(False)
        
        ttk.Button(button_frame, text="Select All", command=select_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear All", command=clear_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Apply", command=apply_selection).pack(side=tk.RIGHT, padx=5)
    
    def on_mode_change(self):
        """Handle mode change between file and single word"""
        if self.use_single_word.get():
            self.file_frame.pack_forget()
        else:
            self.query_frame.pack_forget()
    
    def show_ontologies(self):
        """Show list of available ontologies"""
        ontology_info = """Available Ontologies

Disease & Phenotype:
• MONDO - Monarch Disease Ontology
• HP - Human Phenotype Ontology  
• DOID - Disease Ontology
• ORDO - Orphanet Rare Disease Ontology
• OMIM - Online Mendelian Inheritance in Man

Clinical & Medical:
• SNOMEDCT - SNOMED Clinical Terms
• ICD10CM, ICD11 - International Classification of Diseases
• LOINC - Logical Observation Identifiers
• CPT - Current Procedural Terminology

Biological:
• GO - Gene Ontology
• CHEBI - Chemical Entities of Biological Interest
• PRO - Protein Ontology
• UBERON - Uber Anatomy Ontology

And many more...

Use the "Browse Ontologies" button to select specific ontologies,
or leave empty for automatic ontology selection.
"""
        
        info_window = tk.Toplevel(self.root)
        info_window.title("Available Ontologies")
        info_window.geometry("600x500")
        
        text_widget = scrolledtext.ScrolledText(info_window, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_widget.insert(tk.END, ontology_info)
        text_widget.config(state=tk.DISABLED)
    
    def show_concept_alignment_window(self, concept: Dict, options: List[Dict], comparison: Dict):
        """Show concept alignment window for single word queries"""
        alignment_window = ConceptAlignmentWindow(self.root, concept, options, comparison)
        
        def on_close():
            self.current_selection_result = alignment_window.result
            if alignment_window.result:
                self.add_to_history(concept['label'])
                self.log(f"\n✅ Selected {len(alignment_window.result)} alignment(s):")
                for sel in alignment_window.result:
                    self.log(f"   • {sel['label']} ({sel['ontology']}) - {sel['uri']}")
        
        alignment_window.window.protocol("WM_DELETE_WINDOW", on_close)
        self.root.wait_window(alignment_window.window)
        on_close()
    
    def processing_complete(self):
        """Handle completion of processing"""
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.is_processing = False
        self.update_status("Processing complete")
    
    def run(self):
        """Start the GUI application"""
        self.root.mainloop()


def main():
    """Main entry point"""
    try:
        app = BioPortalGUI()
        app.run()
    except KeyboardInterrupt:
        print("Application interrupted by user")
    except Exception as e:
        messagebox.showerror("Error", f"Application error: {str(e)}")


if __name__ == '__main__':
    main()

    def _determine_alignment_type(self, alignment: Dict, concept_key: str) -> str:
        """Determine the type of alignment based on concept and external term characteristics"""
        label_match = alignment.get('label', '').lower()
        concept_label = concept_key.lower().replace('_', ' ')
        
        # Exact match criteria
        if label_match == concept_label:
            return 'exact'
        
        # Check for exact match in synonyms
        synonyms = [s.lower() for s in alignment.get('synonyms', [])]
        if concept_label in synonyms:
            return 'exact'
        
        # Close match criteria (similar terms)
        if concept_label in label_match or label_match in concept_label:
            return 'close'
        
        # Check for semantic relationships
        broader_indicators = ['disease', 'disorder', 'condition', 'syndrome']
        narrower_indicators = ['symptom', 'sign', 'manifestation']
        
        if any(indicator in label_match for indicator in broader_indicators) and concept_key.lower() in ['symptom', 'sign']:
            return 'broader'
        
        if any(indicator in label_match for indicator in narrower_indicators) and concept_key.lower() in ['disease', 'disorder']:
            return 'narrower'
        
        # Default to related match
        return 'related'
    
    def _clean_description(self, description: str) -> str:
        """Clean and normalize description text"""
        if not description:
            return ""
        
        # Remove extra whitespace and normalize
        cleaned = ' '.join(description.split())
        
        # Remove common prefixes that add no value
        prefixes_to_remove = [
            "A ", "An ", "The ",
            "This is a ", "This is an ", "This is the ",
            "Definition: ", "Description: "
        ]
        
        for prefix in prefixes_to_remove:
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):]
                break
        
        # Ensure first letter is capitalized
        if cleaned:
            cleaned = cleaned[0].upper() + cleaned[1:]
        
        # Limit length to reasonable size
        if len(cleaned) > 200:
            cleaned = cleaned[:197] + "..."
        
        return cleaned
    
    def _deduplicate_synonyms(self, synonyms: List[str], existing_labels: set) -> List[str]:
        """Remove duplicate and low-quality synonyms"""
        if not synonyms:
            return []
        
        unique_synonyms = []
        seen_normalized = set()
        
        for synonym in synonyms:
            if not synonym or not synonym.strip():
                continue
            
            # Normalize for comparison
            normalized = synonym.lower().strip()
            
            # Skip if already seen or in existing labels
            if normalized in seen_normalized or normalized in existing_labels:
                continue
            
            # Skip very short synonyms (likely not meaningful)
            if len(normalized) < 3:
                continue
            
            # Skip synonyms that are just case variations
            if any(normalized == existing.lower() for existing in seen_normalized):
                continue
            
            # Add to unique list
            unique_synonyms.append(synonym.strip())
            seen_normalized.add(normalized)
        
        # Sort by length and relevance (shorter, more specific terms first)
        unique_synonyms.sort(key=lambda x: (len(x), x.lower()))
        
        return unique_synonyms
