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

import json
import os
import threading
import time
from datetime import datetime
from typing import Any

import tkinter as tk
from rdflib import OWL, RDF, RDFS, SKOS, Graph, Literal, URIRef
from rdflib.namespace import DCTERMS
from tkinter import filedialog, messagebox, scrolledtext, ttk

# Import the core classes from the CLI tool
from core.lookup import ConceptLookup
from core.parser import OntologyParser
from services.bioportal import BioPortalLookup
from services.ols import OLSLookup


class ConceptAlignmentWindow:
    """Window for selecting alignments for a specific concept"""

    def __init__(self, parent, concept: dict, options: list[dict], comparison: dict):
        self.parent = parent
        self.concept = concept
        self.options = options
        self.comparison = comparison
        self.selections: list[dict] = []
        self.result: list[dict] | None = None

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

        ttk.Label(
            header_frame, text=f"Concept: {self.concept['label']}", font=("Arial", 14, "bold")
        ).pack(anchor=tk.W)
        ttk.Label(
            header_frame,
            text=f"Type: {self.concept['type']} | Category: {self.concept['category']}",
            font=("Arial", 10),
        ).pack(anchor=tk.W)

        # Comparison summary
        if self.comparison.get("discrepancies"):
            alert_frame = ttk.LabelFrame(self.window, text="⚠️ Service Comparison Alert")
            alert_frame.pack(fill=tk.X, padx=10, pady=5)

            for discrepancy in self.comparison["discrepancies"]:
                ttk.Label(alert_frame, text=f"• {discrepancy}", foreground="orange").pack(
                    anchor=tk.W, padx=5
                )

            stats_text = f"BioPortal: {self.comparison['bioportal_count']} results | OLS: {self.comparison['ols_count']} results"
            ttk.Label(alert_frame, text=stats_text).pack(anchor=tk.W, padx=5)

        # Options frame
        options_frame = ttk.LabelFrame(
            self.window, text=f"✅ Found {len(self.options)} standardized terms:"
        )
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
        self.checkboxes: dict[str, dict[str, Any]] = {}
        for _i, option in enumerate(self.options):
            source_icon = "🌐" if option["source"] == "bioportal" else "🔬"
            ols_only = " (OLS-only)" if option.get("ols_only") else ""

            # Truncate long descriptions
            description = option.get("description", "")
            if len(description) > 80:
                description = description[:80] + "..."

            # Truncate long URIs
            uri = option["uri"]
            if len(uri) > 60:
                uri = uri[:60] + "..."

            item_id = self.tree.insert(
                "",
                tk.END,
                values=(
                    "☐",  # Checkbox placeholder
                    f"{source_icon} {option['source']}{ols_only}",
                    option["label"],
                    option["ontology"],
                    uri,
                    description,
                ),
            )

            self.checkboxes[item_id] = {"selected": False, "option": option}

        # Bind click event
        self.tree.bind("<Button-1>", self.on_tree_click)
        self.tree.bind("<Double-1>", self.show_details)

        # Buttons frame
        buttons_frame = ttk.Frame(self.window)
        buttons_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(buttons_frame, text="Select All", command=self.select_all).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(buttons_frame, text="Clear All", command=self.clear_all).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(buttons_frame, text="Show Details", command=self.show_details).pack(
            side=tk.LEFT, padx=5
        )

        ttk.Button(buttons_frame, text="Skip", command=self.skip).pack(side=tk.RIGHT, padx=5)
        ttk.Button(buttons_frame, text="Confirm Selection", command=self.confirm).pack(
            side=tk.RIGHT, padx=5
        )

        # Status
        self.status_label = ttk.Label(
            self.window, text="Select one or more alignments for this concept"
        )
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
        checkbox_data["selected"] = not checkbox_data["selected"]

        # Update checkbox display
        values = list(self.tree.item(item, "values"))
        values[0] = "☑" if checkbox_data["selected"] else "☐"
        self.tree.item(item, values=values)

        # Update status
        selected_count = sum(1 for cb in self.checkboxes.values() if cb["selected"])
        self.status_label.config(text=f"Selected {selected_count} alignment(s)")

    def select_all(self):
        """Select all items"""
        for item in self.checkboxes:
            if not self.checkboxes[item]["selected"]:
                self.toggle_selection(item)

    def clear_all(self):
        """Clear all selections"""
        for item in self.checkboxes:
            if self.checkboxes[item]["selected"]:
                self.toggle_selection(item)

    def show_details(self, event=None):
        """Show detailed information about selected item"""
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showinfo("No Selection", "Please select an item to view details.")
            return

        item = selected_items[0]
        option = self.checkboxes[item]["option"]

        # Create details window
        details_window = tk.Toplevel(self.window)
        details_window.title(f"Details: {option['label']}")
        details_window.geometry("600x400")

        # Add details
        text_widget = scrolledtext.ScrolledText(details_window, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        details_text = f"""Label: {option["label"]}
Source: {option["source"]}
Ontology: {option["ontology"]}
URI: {option["uri"]}

Description:
{option.get("description", "No description available")}

Synonyms:
"""
        if option.get("synonyms"):
            for synonym in option["synonyms"]:
                details_text += f"• {synonym}\n"
        else:
            details_text += "No synonyms available"

        text_widget.insert(tk.END, details_text)
        text_widget.config(state=tk.DISABLED)

        # Add URI copy button
        def copy_uri():
            details_window.clipboard_clear()
            details_window.clipboard_append(option["uri"])
            messagebox.showinfo("Copied", "URI copied to clipboard!")

        ttk.Button(details_window, text="Copy URI", command=copy_uri).pack(pady=5)

    def skip(self):
        """Skip this concept"""
        self.result = []
        self.window.destroy()

    def confirm(self):
        """Confirm selections"""
        selected_options = []
        for _item, checkbox_data in self.checkboxes.items():
            if checkbox_data["selected"]:
                option = checkbox_data["option"]
                selected_options.append(
                    {
                        "uri": option["uri"],
                        "label": option["label"],
                        "ontology": option["ontology"],
                        "description": option.get("description", ""),
                        "synonyms": option.get("synonyms", []),
                        "source": option["source"],
                        "relationship": (
                            "owl:sameAs"
                            if self.concept["category"] == "instance"
                            else "rdfs:seeAlso"
                        ),
                    }
                )

        if not selected_options:
            messagebox.showwarning(
                "No Selection", "Please select at least one alignment or skip this concept."
            )
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

        self.setup_ui()

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

        ttk.Radiobutton(
            mode_frame,
            text="📄 Process TTL File",
            variable=self.use_single_word,
            value=False,
            command=self.on_mode_change,
        ).pack(anchor=tk.W, padx=5, pady=2)
        ttk.Radiobutton(
            mode_frame,
            text="🔍 Single Word Query",
            variable=self.use_single_word,
            value=True,
            command=self.on_mode_change,
        ).pack(anchor=tk.W, padx=5, pady=2)

        # File selection
        self.file_frame = ttk.LabelFrame(parent, text="Input File")
        self.file_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(self.file_frame, text="TTL Ontology File:").pack(anchor=tk.W, padx=5, pady=2)
        file_entry_frame = ttk.Frame(self.file_frame)
        file_entry_frame.pack(fill=tk.X, padx=5, pady=2)

        ttk.Entry(file_entry_frame, textvariable=self.ttl_file, width=60).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        ttk.Button(file_entry_frame, text="Browse", command=self.browse_ttl_file).pack(side=tk.LEFT)

        # Single word query
        self.query_frame = ttk.LabelFrame(parent, text="Single Word Query")
        self.query_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(self.query_frame, text="Query Term:").pack(anchor=tk.W, padx=5, pady=2)
        ttk.Entry(self.query_frame, textvariable=self.single_word_query, width=60).pack(
            anchor=tk.W, padx=5, pady=2
        )
        ttk.Label(
            self.query_frame,
            text="Enter a single word or term to search for (e.g., 'fatigue', 'covid', 'cancer')",
            font=("Arial", 8),
            foreground="gray",
        ).pack(anchor=tk.W, padx=5)

        # Ontology selection
        ontology_frame = ttk.LabelFrame(parent, text="Ontology Selection")
        ontology_frame.pack(fill=tk.X, padx=10, pady=5)

        ont_entry_frame = ttk.Frame(ontology_frame)
        ont_entry_frame.pack(fill=tk.X, padx=5, pady=2)

        ttk.Label(ontology_frame, text="Selected Ontologies (comma-separated):").pack(
            anchor=tk.W, padx=5, pady=2
        )
        ttk.Entry(ont_entry_frame, textvariable=self.selected_ontologies, width=50).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        ttk.Button(ont_entry_frame, text="Browse Ontologies", command=self.browse_ontologies).pack(
            side=tk.LEFT
        )

        ttk.Label(
            ontology_frame,
            text="Leave empty for automatic selection, or specify like: HP,NCIT,MONDO",
            font=("Arial", 8),
            foreground="gray",
        ).pack(anchor=tk.W, padx=5)

        # Search options
        search_frame = ttk.LabelFrame(parent, text="Search Options")
        search_frame.pack(fill=tk.X, padx=10, pady=5)

        max_results_frame = ttk.Frame(search_frame)
        max_results_frame.pack(fill=tk.X, padx=5, pady=2)

        ttk.Label(max_results_frame, text="Max Results per Search:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Spinbox(max_results_frame, from_=1, to=20, textvariable=self.max_results, width=5).pack(
            side=tk.LEFT
        )

        # API Configuration
        api_frame = ttk.LabelFrame(parent, text="API Configuration")
        api_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(api_frame, text="BioPortal API Key (optional):").pack(anchor=tk.W, padx=5, pady=2)
        ttk.Entry(api_frame, textvariable=self.api_key, width=60, show="*").pack(
            anchor=tk.W, padx=5, pady=2
        )
        ttk.Label(
            api_frame,
            text="Leave empty for demo mode or set BIOPORTAL_API_KEY environment variable",
            font=("Arial", 8),
            foreground="gray",
        ).pack(anchor=tk.W, padx=5)

        # Service Selection
        service_frame = ttk.LabelFrame(parent, text="Services")
        service_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Checkbutton(service_frame, text="🌐 Use BioPortal", variable=self.use_bioportal).pack(
            anchor=tk.W, padx=5, pady=2
        )
        ttk.Checkbutton(
            service_frame, text="🔬 Use OLS (Ontology Lookup Service)", variable=self.use_ols
        ).pack(anchor=tk.W, padx=5, pady=2)

        # Output Configuration
        output_frame = ttk.LabelFrame(parent, text="Output Files")
        output_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(output_frame, text="Output Ontology File:").pack(anchor=tk.W, padx=5, pady=2)
        ttk.Entry(output_frame, textvariable=self.output_file, width=60).pack(
            anchor=tk.W, padx=5, pady=2
        )

        ttk.Label(output_frame, text="Alignment Report File:").pack(anchor=tk.W, padx=5, pady=2)
        ttk.Entry(output_frame, textvariable=self.report_file, width=60).pack(
            anchor=tk.W, padx=5, pady=2
        )

        # Action buttons
        action_frame = ttk.Frame(parent)
        action_frame.pack(fill=tk.X, padx=10, pady=20)

        self.start_button = ttk.Button(
            action_frame, text="Start Processing", command=self.start_processing
        )
        self.start_button.pack(side=tk.LEFT, padx=5)

        ttk.Button(action_frame, text="Load Example", command=self.load_example).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(action_frame, text="List Ontologies", command=self.show_ontologies).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(action_frame, text="Help", command=self.show_help).pack(side=tk.RIGHT, padx=5)

        # Initialize mode
        self.on_mode_change()

    def setup_process_tab(self, parent):
        """Setup processing tab"""
        # Progress frame
        progress_frame = ttk.LabelFrame(parent, text="Progress")
        progress_frame.pack(fill=tk.X, padx=10, pady=5)

        self.progress_label = ttk.Label(progress_frame, text="No processing started")
        self.progress_label.pack(anchor=tk.W, padx=5, pady=2)

        self.progress_bar = ttk.Progressbar(progress_frame, mode="determinate")
        self.progress_bar.pack(fill=tk.X, padx=5, pady=5)

        # Log frame
        log_frame = ttk.LabelFrame(parent, text="Processing Log")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=20)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Control buttons
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill=tk.X, padx=10, pady=5)

        self.stop_button = ttk.Button(
            control_frame, text="Stop Processing", command=self.stop_processing, state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)

        ttk.Button(control_frame, text="Clear Log", command=self.clear_log).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(control_frame, text="Save Log", command=self.save_log).pack(
            side=tk.RIGHT, padx=5
        )

    def setup_results_tab(self, parent):
        """Setup results tab"""
        # Summary frame
        summary_frame = ttk.LabelFrame(parent, text="Processing Summary")
        summary_frame.pack(fill=tk.X, padx=10, pady=5)

        self.summary_text = scrolledtext.ScrolledText(summary_frame, wrap=tk.WORD, height=8)
        self.summary_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Files frame
        files_frame = ttk.LabelFrame(parent, text="Generated Files")
        files_frame.pack(fill=tk.X, padx=10, pady=5)

        self.files_tree = ttk.Treeview(
            files_frame, columns=("File", "Size", "Description"), show="headings", height=6
        )
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

        ttk.Button(
            results_action_frame, text="Open Output Folder", command=self.open_output_folder
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(results_action_frame, text="View Ontology", command=self.view_ontology).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(results_action_frame, text="Export Report", command=self.export_report).pack(
            side=tk.RIGHT, padx=5
        )

    def browse_ttl_file(self):
        """Browse for TTL file"""
        filename = filedialog.askopenfilename(
            title="Select TTL Ontology File",
            filetypes=[("Turtle files", "*.ttl"), ("All files", "*.*")],
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
            messagebox.showwarning(
                "Example Not Found", "Example file not found. Please select a TTL file manually."
            )

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
            lookup = ConceptLookup(
                bioportal,
                ols,
                self.selected_ontologies.get() if self.selected_ontologies.get() else None,
            )

            # Show ontologies being used
            if self.selected_ontologies.get():
                self.log(f"🎯 Using ontologies: {self.selected_ontologies.get()}")
            else:
                self.log("🎯 Using default ontology selection strategy")

            # Create a mock concept for the single word
            concept = {
                "key": self.single_word_query.get().replace(" ", "_"),
                "label": self.single_word_query.get(),
                "type": "Term",
                "category": "query",
            }

            self.update_status("Searching for alignments...")

            # Perform lookup
            options, comparison = lookup.lookup_concept(concept, self.max_results.get())

            if not options:
                self.log(f"❌ No results found for '{self.single_word_query.get()}'")
                self.update_status("No results found")
                return

            # Display comparison summary
            if comparison["discrepancies"]:
                self.log("\n⚠️  Service Comparison Alert:")
                for discrepancy in comparison["discrepancies"]:
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

    def show_single_word_results(self, concept: dict, options: list[dict], comparison: dict):
        """Show single word query results for selection"""
        self.log(f"✅ Found {len(options)} standardized terms:")
        for j, result in enumerate(options, 1):
            source_indicator = (
                "🌐"
                if result["source"] == "bioportal"
                else "🔬"
                if result["source"] == "ols"
                else "🎭"
            )
            ols_only_indicator = " (OLS-only)" if result.get("ols_only") else ""

            self.log(f"{j:2d}. {source_indicator} {result['label']}{ols_only_indicator}")
            self.log(f"     Ontology: {result['ontology']} | Source: {result['source']}")
            self.log(f"     URI: {result['uri'][:70]}{'...' if len(result['uri']) > 70 else ''}")

            # Show description if available
            if result.get("description") and result["description"].strip():
                desc = (
                    result["description"][:120] + "..."
                    if len(result["description"]) > 120
                    else result["description"]
                )
                self.log(f"     Description: {desc}")

            # Show synonyms if available
            if result.get("synonyms") and len(result["synonyms"]) > 0:
                synonyms_str = ", ".join(result["synonyms"][:3])  # Show max 3 synonyms
                if len(result["synonyms"]) > 3:
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
            self.log(
                f"📊 Found {len(ontology.classes)} classes and {len(ontology.instances)} instances"
            )

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

                # Update progress bar and label
                self.progress_bar.config(value=i)
                self.progress_label.config(
                    text=f"Processing concept {i + 1}/{len(concepts)}: {concept['label']}"
                )

                self.log(
                    f"\n🔍 Step {i + 1}/{len(concepts)}: {concept['label']} ({concept['type']})"
                )

                # Perform lookup
                options, comparison = lookup.lookup_concept(concept)
                self.all_comparisons[concept["key"]] = comparison

                if not options:
                    self.log(f"❌ No results found for '{concept['label']}'")
                    continue

                # Display comparison summary
                if comparison["discrepancies"]:
                    self.log("⚠️ Service Comparison Alert:")
                    for discrepancy in comparison["discrepancies"]:
                        self.log(f"   • {discrepancy}")

                self.log(f"✅ Found {len(options)} standardized terms")

                # Show alignment window (must be done on main thread)
                self.show_alignment_window(concept, options, comparison)

                # Wait for user selection (simple polling)
                timeout_counter = 0
                while (
                    hasattr(self, "waiting_for_selection")
                    and self.waiting_for_selection
                    and self.is_processing
                    and timeout_counter < 3000  # 5 minute timeout
                ):
                    time.sleep(0.1)
                    timeout_counter += 1

                # Handle timeout or processing stop
                if timeout_counter >= 3000:
                    self.log("⏰ Timeout waiting for user selection")
                    continue  # Skip to next concept
                elif not self.is_processing:
                    return

                # Process selection result
                if self.current_selection_result is not None:
                    if self.current_selection_result:
                        self.current_selections[concept["key"]] = self.current_selection_result
                        self.log(
                            f"✅ Selected {len(self.current_selection_result)} alignment(s) for {concept['label']}"
                        )
                    else:
                        self.log(f"⏭️ Skipped {concept['label']}")
                    self.current_selection_result = None

            # Generate improved ontology if we have selections
            if self.current_selections:
                self.generate_improved_ontology(ontology)
            else:
                self.log(
                    "❌ No selections made. Process completed without generating improved ontology."
                )

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

        try:
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
                    external_uri = URIRef(alignment["uri"])

                    # Determine alignment type based on similarity
                    alignment_type = self._determine_alignment_type(alignment, concept_key)

                    # Add standardized alignment relationship
                    if alignment_type == "exact":
                        improved_graph.add((local_uri, SKOS.exactMatch, external_uri))
                    elif alignment_type == "close":
                        improved_graph.add((local_uri, SKOS.closeMatch, external_uri))
                    elif alignment_type == "related":
                        improved_graph.add((local_uri, SKOS.relatedMatch, external_uri))
                    else:
                        improved_graph.add((local_uri, RDFS.seeAlso, external_uri))

                    # Add standard metadata
                    improved_graph.add(
                        (
                            local_uri,
                            SKOS.inScheme,
                            URIRef(
                                f"http://bioportal.bioontology.org/ontologies/{alignment['ontology']}"
                            ),
                        )
                    )
                    improved_graph.add(
                        (
                            local_uri,
                            DCTERMS.source,
                            URIRef(
                                f"http://bioportal.bioontology.org/ontologies/{alignment['ontology']}"
                            ),
                        )
                    )

                    # Use standard SKOS properties for labels
                    if alignment.get("label") and alignment["label"].strip():
                        existing_labels = [
                            str(o)
                            for s, p, o in improved_graph.triples((local_uri, SKOS.prefLabel, None))
                        ]
                        if alignment["label"] not in existing_labels:
                            improved_graph.add(
                                (local_uri, SKOS.altLabel, Literal(alignment["label"], lang="en"))
                            )

                    # Add description using standard DCTERMS
                    if alignment.get("description") and alignment["description"].strip():
                        clean_description = self._clean_description(alignment["description"])
                        if clean_description:
                            improved_graph.add(
                                (
                                    local_uri,
                                    DCTERMS.description,
                                    Literal(clean_description, lang="en"),
                                )
                            )

                    # Add deduplicated synonyms
                    if alignment.get("synonyms"):
                        existing_alt_labels = {
                            str(o).lower()
                            for s, p, o in improved_graph.triples((local_uri, SKOS.altLabel, None))
                        }
                        unique_synonyms = self._deduplicate_synonyms(
                            alignment["synonyms"], existing_alt_labels
                        )

                        for synonym in unique_synonyms[:3]:
                            improved_graph.add(
                                (local_uri, SKOS.altLabel, Literal(synonym, lang="en"))
                            )

                    total_alignments += 1
                    source_icon = "🌐" if alignment["source"] == "bioportal" else "🔬"
                    self.log(
                        f"✅ {source_icon} {concept_key} → {alignment['label']} ({alignment['ontology']}) [{alignment_type}]"
                    )

            # Add enhanced provenance using PROV-O vocabulary
            prov_activity = URIRef("http://example.org/ontology#BioPortalGUIAlignment")
            improved_graph.add(
                (prov_activity, RDF.type, URIRef("http://www.w3.org/ns/prov#Activity"))
            )
            improved_graph.add(
                (prov_activity, DCTERMS.title, Literal("Ontology Alignment Activity", lang="en"))
            )
            improved_graph.add(
                (
                    prov_activity,
                    DCTERMS.description,
                    Literal(
                        "Interactive ontology alignment using BioPortal and OLS services via GUI",
                        lang="en",
                    ),
                )
            )
            improved_graph.add(
                (
                    prov_activity,
                    URIRef("http://www.w3.org/ns/prov#startedAtTime"),
                    Literal(datetime.now().isoformat()),
                )
            )

            # Add tool information
            tool_agent = URIRef("http://example.org/ontology#BioPortalGUITool")
            improved_graph.add(
                (tool_agent, RDF.type, URIRef("http://www.w3.org/ns/prov#SoftwareAgent"))
            )
            improved_graph.add(
                (tool_agent, DCTERMS.title, Literal("BioPortal GUI Alignment Tool", lang="en"))
            )
            improved_graph.add(
                (tool_agent, URIRef("http://www.w3.org/ns/prov#wasAssociatedWith"), prov_activity)
            )

            # Save improved ontology
            output_path = self.output_file.get()
            improved_graph.serialize(destination=output_path, format="turtle")

            # Generate report
            report = {
                "timestamp": datetime.now().isoformat(),
                "input_file": self.ttl_file.get(),
                "output_file": output_path,
                "original_triples": len(ontology.graph),
                "improved_triples": len(improved_graph),
                "alignments_added": total_alignments,
                "concepts_aligned": len(self.current_selections),
                "service_comparisons": self.all_comparisons,
                "selections": self.current_selections,
            }

            report_path = self.report_file.get()
            with open(report_path, "w") as f:
                json.dump(report, f, indent=2)

            # Update results tab
            self.update_results(report, output_path, report_path)

            # Log summary
            self.log("\n🎉 SUCCESS!")
            self.log(f"  Output: {output_path}")
            self.log(f"  Report: {report_path}")
            self.log(f"  Original triples: {len(ontology.graph):,}")
            self.log(f"  New triples: {len(improved_graph) - len(ontology.graph):,}")
            self.log(f"  Total triples: {len(improved_graph):,}")
            self.log(f"  Concepts aligned: {len(self.current_selections)}")
            self.log(f"  Total alignments: {total_alignments}")

        except Exception as e:
            self.log(f"❌ Error generating improved ontology: {str(e)}")

    def update_results(self, report, output_path, report_path):
        """Update the results tab with processing results"""

        def update_ui():
            # Update summary
            self.summary_text.delete(1.0, tk.END)
            summary = f"""Processing completed successfully!

Input File: {report["input_file"]}
Output File: {report["output_file"]}
Report File: {report_path}

Statistics:
• Original triples: {report["original_triples"]:,}
• New triples added: {report["improved_triples"] - report["original_triples"]:,}
• Total triples: {report["improved_triples"]:,}
• Concepts aligned: {report["concepts_aligned"]}
• Total alignments: {report["alignments_added"]}

Processing completed at: {report["timestamp"]}
"""
            self.summary_text.insert(tk.END, summary)

            # Update files tree
            for item in self.files_tree.get_children():
                self.files_tree.delete(item)

            # Add output files
            if os.path.exists(output_path):
                size = f"{os.path.getsize(output_path):,} bytes"
                self.files_tree.insert(
                    "", tk.END, values=(output_path, size, "Enhanced ontology with alignments")
                )

            if os.path.exists(report_path):
                size = f"{os.path.getsize(report_path):,} bytes"
                self.files_tree.insert(
                    "", tk.END, values=(report_path, size, "Detailed alignment report")
                )

            # Add comparison report if available
            comp_report_path = "service_comparison_report.json"
            if os.path.exists(comp_report_path):
                size = f"{os.path.getsize(comp_report_path):,} bytes"
                self.files_tree.insert(
                    "", tk.END, values=(comp_report_path, size, "Service comparison analysis")
                )

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

    def save_log(self):
        """Save log to file"""
        filename = filedialog.asksaveasfilename(
            title="Save Processing Log",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if filename:
            with open(filename, "w") as f:
                f.write(self.log_text.get(1.0, tk.END))
            messagebox.showinfo("Success", f"Log saved to {filename}")

    def update_status(self, message):
        """Update status bar"""
        self.root.after(0, lambda: self.status_bar.config(text=message))

    def open_output_folder(self):
        """Open the output folder in file manager"""
        output_dir = os.path.dirname(os.path.abspath(self.output_file.get()))
        if os.path.exists(output_dir):
            import subprocess  # nosec B404

            subprocess.run(["xdg-open", output_dir], check=False)  # nosec B603, B607
        else:
            messagebox.showwarning("Folder Not Found", "Output folder does not exist yet.")

    def view_ontology(self):
        """View the generated ontology file"""
        output_path = self.output_file.get()
        if os.path.exists(output_path):
            import subprocess  # nosec B404

            subprocess.run(["xdg-open", output_path], check=False)  # nosec B603, B607
        else:
            messagebox.showwarning("File Not Found", "Output ontology file does not exist yet.")

    def export_report(self):
        """Export detailed report"""
        report_path = self.report_file.get()
        if os.path.exists(report_path):
            import subprocess  # nosec B404

            subprocess.run(["xdg-open", report_path], check=False)  # nosec B603, B607
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

    def on_mode_change(self):
        """Handle mode change between TTL file and single word query"""
        if self.use_single_word.get():
            self.file_frame.pack_forget()
            self.query_frame.pack(fill=tk.X, padx=10, pady=5)
        else:
            self.query_frame.pack_forget()
            self.file_frame.pack(fill=tk.X, padx=10, pady=5)

    def browse_ontologies(self):
        """Browse available ontologies"""
        # This would open a window to browse available ontologies
        # For now, just show a simple dialog
        messagebox.showinfo(
            "Browse Ontologies",
            "Feature coming soon! For now, manually enter ontology codes like: HP,NCIT,MONDO",
        )

    def show_ontologies(self):
        """Show list of available ontologies"""
        ontology_list = """Common Ontologies:

HP - Human Phenotype Ontology
NCIT - NCI Thesaurus
MONDO - Monarch Disease Ontology
GO - Gene Ontology
DOID - Disease Ontology
EFO - Experimental Factor Ontology
UBERON - Uber Anatomy Ontology
CL - Cell Ontology
CHEBI - Chemical Entities of Biological Interest
"""

        ont_window = tk.Toplevel(self.root)
        ont_window.title("Available Ontologies")
        ont_window.geometry("500x400")

        text_widget = scrolledtext.ScrolledText(ont_window, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_widget.insert(tk.END, ontology_list)
        text_widget.config(state=tk.DISABLED)

    def show_concept_alignment_window(self, concept: dict, options: list[dict], comparison: dict):
        """Show concept alignment window (alias for show_alignment_window)"""
        self.show_alignment_window(concept, options, comparison)

    def processing_complete(self):
        """Handle processing completion"""
        self.update_status("Processing completed successfully")
        self.log("🎉 Processing completed successfully!")

    def _determine_alignment_type(self, alignment: dict, concept_key: str) -> str:
        """Determine the type of alignment based on concept and external term characteristics"""
        label_match = alignment.get("label", "").lower()
        concept_label = concept_key.lower().replace("_", " ")

        # Exact match criteria
        if label_match == concept_label:
            return "exact"

        # Check for exact match in synonyms
        synonyms = [s.lower() for s in alignment.get("synonyms", [])]
        if concept_label in synonyms:
            return "exact"

        # Close match criteria (similar terms)
        if concept_label in label_match or label_match in concept_label:
            return "close"

        # Check for semantic relationships
        broader_indicators = ["disease", "disorder", "condition", "syndrome"]
        narrower_indicators = ["symptom", "sign", "manifestation"]

        if any(
            indicator in label_match for indicator in broader_indicators
        ) and concept_key.lower() in ["symptom", "sign"]:
            return "broader"

        if any(
            indicator in label_match for indicator in narrower_indicators
        ) and concept_key.lower() in ["disease", "disorder"]:
            return "narrower"

        # Default to related match
        return "related"

    def _clean_description(self, description: str) -> str:
        """Clean and normalize description text"""
        if not description:
            return ""

        # Remove extra whitespace and normalize
        cleaned = " ".join(description.split())

        # Remove common prefixes that add no value
        prefixes_to_remove = [
            "A ",
            "An ",
            "The ",
            "This is a ",
            "This is an ",
            "This is the ",
            "Definition: ",
            "Description: ",
        ]

        for prefix in prefixes_to_remove:
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix) :]
                break

        # Ensure first letter is capitalized
        if cleaned:
            cleaned = cleaned[0].upper() + cleaned[1:]

        # Limit length to reasonable size
        if len(cleaned) > 200:
            cleaned = cleaned[:197] + "..."

        return cleaned

    def _deduplicate_synonyms(self, synonyms: list[str], existing_labels: set) -> list[str]:
        """Remove duplicate and low-quality synonyms"""
        if not synonyms:
            return []

        unique_synonyms = []
        seen_normalized: set[str] = set()

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


if __name__ == "__main__":
    main()
