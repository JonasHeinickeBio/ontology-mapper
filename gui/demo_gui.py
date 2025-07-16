#!/usr/bin/env python3
"""
BioPortal GUI Demo

Standalone demo version that includes embedded CLI functionality.
"""

from typing import Dict, List, Optional

import tkinter as tk
from tkinter import filedialog, scrolledtext, ttk


# Embedded minimal CLI classes for demo
class DemoBioPortalLookup:
    """Demo BioPortal lookup with mock data"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    def search(self, query: str, ontologies: str = "", max_results: int = 5) -> List[Dict]:
        """Return demo results"""
        return [
            {
                "uri": f"http://purl.obolibrary.org/obo/DEMO_{query.upper().replace(' ', '_')}_001",
                "label": f"Demo: {query.title()}",
                "ontology": "DEMO",
                "description": f"This is a demo description for {query}. In real usage, this would contain the actual definition from BioPortal.",
                "synonyms": [f"Demo synonym 1 for {query}", f"Demo synonym 2 for {query}"],
                "source": "bioportal_demo",
            },
            {
                "uri": f"http://purl.obolibrary.org/obo/DEMO_{query.upper().replace(' ', '_')}_002",
                "label": f"Demo Alternative: {query.title()}",
                "ontology": "DEMO_ALT",
                "description": f"This is an alternative demo description for {query}.",
                "synonyms": [f"Alternative synonym for {query}"],
                "source": "bioportal_demo",
            },
        ]


class DemoOLSLookup:
    """Demo OLS lookup with mock data"""

    def search(self, query: str, ontologies: str = "", max_results: int = 5) -> List[Dict]:
        """Return demo OLS results"""
        return [
            {
                "uri": f"http://www.ebi.ac.uk/efo/EFO_{query.upper().replace(' ', '_')}_001",
                "label": f"OLS Demo: {query.title()}",
                "ontology": "EFO_DEMO",
                "description": f"This is a demo OLS description for {query}. In real usage, this would come from the EBI OLS service.",
                "synonyms": [f"OLS synonym for {query}"],
                "source": "ols",
            }
        ]


class DemoOntologyParser:
    """Demo ontology parser"""

    def __init__(self, ttl_file: str):
        self.ttl_file = ttl_file
        self.classes = ["Disease", "Symptom", "Treatment"]
        self.instances = [
            {"name": "long_covid", "type": "Disease", "label": "Long COVID"},
            {"name": "fatigue", "type": "Symptom", "label": "Fatigue"},
        ]

    def parse(self) -> bool:
        """Demo parse"""
        return True

    def get_priority_concepts(self) -> List[Dict]:
        """Demo priority concepts"""
        concepts = []
        for instance in self.instances:
            concepts.append(
                {
                    "key": instance["name"],
                    "label": instance["label"],
                    "type": instance["type"],
                    "category": "instance",
                }
            )
        for class_name in self.classes:
            concepts.append(
                {"key": class_name, "label": class_name, "type": "Class", "category": "class"}
            )
        return concepts


class DemoConceptLookup:
    """Demo concept lookup"""

    def __init__(self, bioportal, ols):
        self.bioportal = bioportal
        self.ols = ols

    def lookup_concept(self, concept: Dict):
        """Demo lookup"""
        bp_results = self.bioportal.search(concept["label"], max_results=2)
        ols_results = self.ols.search(concept["label"], max_results=2)

        # Combine results
        combined = bp_results + ols_results

        # Demo comparison
        comparison = {
            "concept": concept["label"],
            "bioportal_count": len(bp_results),
            "ols_count": len(ols_results),
            "discrepancies": (
                ["Demo: Result count differs between services"]
                if len(bp_results) != len(ols_results)
                else []
            ),
        }

        return combined, comparison


# Simple demo GUI
class DemoBioPortalGUI:
    """Simplified demo GUI"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("BioPortal GUI Demo")
        self.root.geometry("800x600")

        self.ttl_file = tk.StringVar()
        self.setup_demo_ui()

    def setup_demo_ui(self):
        """Setup demo UI"""
        # Header
        header = ttk.Label(
            self.root,
            text="🧪 BioPortal Ontology Alignment GUI - DEMO MODE",
            font=("Arial", 16, "bold"),
        )
        header.pack(pady=10)

        # Info
        info_text = """This is a demonstration of the BioPortal GUI tool.
In demo mode, mock data is used to show the interface and workflow.
For full functionality, use the complete version with bioportal_cli.py."""

        info_label = ttk.Label(self.root, text=info_text, justify=tk.CENTER)
        info_label.pack(pady=10)

        # File selection
        file_frame = ttk.LabelFrame(self.root, text="Demo File Selection")
        file_frame.pack(fill=tk.X, padx=20, pady=10)

        ttk.Label(file_frame, text="TTL File (demo):").pack(anchor=tk.W, padx=5, pady=2)
        file_entry_frame = ttk.Frame(file_frame)
        file_entry_frame.pack(fill=tk.X, padx=5, pady=2)

        ttk.Entry(file_entry_frame, textvariable=self.ttl_file, width=50).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        ttk.Button(file_entry_frame, text="Browse", command=self.browse_file).pack(side=tk.LEFT)

        # Demo button
        demo_frame = ttk.Frame(self.root)
        demo_frame.pack(pady=20)

        ttk.Button(
            demo_frame,
            text="🚀 Start Demo Processing",
            command=self.start_demo,
            style="Accent.TButton",
        ).pack(padx=10)

        # Log area
        log_frame = ttk.LabelFrame(self.root, text="Demo Log")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Status
        self.status = ttk.Label(
            self.root, text="Demo ready - Click 'Start Demo Processing' to begin"
        )
        self.status.pack(pady=5)

        self.log("🧪 BioPortal GUI Demo initialized")
        self.log("This demo shows the interface without requiring real API connections")

    def browse_file(self):
        """Demo file browser"""
        filename = filedialog.askopenfilename(
            title="Select TTL File (Demo)",
            filetypes=[("Turtle files", "*.ttl"), ("All files", "*.*")],
        )
        if filename:
            self.ttl_file.set(filename)
            self.log(f"📁 Selected file: {filename}")

    def start_demo(self):
        """Start demo processing"""
        self.log("\n🚀 Starting demo processing...")
        self.status.config(text="Processing...")

        # Initialize demo components
        bioportal = DemoBioPortalLookup()
        ols = DemoOLSLookup()
        ontology = DemoOntologyParser(self.ttl_file.get() or "demo.ttl")
        lookup = DemoConceptLookup(bioportal, ols)

        # Demo processing
        self.log("✅ Initialized demo components")
        self.log("📊 Demo ontology: 3 classes, 2 instances")

        concepts = ontology.get_priority_concepts()
        self.log(f"🎯 Found {len(concepts)} priority concepts")

        for i, concept in enumerate(concepts, 1):
            self.log(f"\n🔍 Processing {i}/{len(concepts)}: {concept['label']}")

            # Demo lookup
            options, comparison = lookup.lookup_concept(concept)
            self.log(f"✅ Found {len(options)} standardized terms")

            if comparison["discrepancies"]:
                self.log("⚠️ Service discrepancies detected")

            # Show demo options
            self.log("Demo alignment options:")
            for j, option in enumerate(options, 1):
                source_icon = "🌐" if option["source"] == "bioportal_demo" else "🔬"
                self.log(f"  {j}. {source_icon} {option['label']} ({option['ontology']})")

            # Auto-select first option for demo
            self.log(f"🤖 Demo auto-selected: {options[0]['label']}")

        self.log("\n💾 Demo: Generated improved ontology")
        self.log("📋 Demo: Created alignment report")
        self.log("\n🎉 Demo processing completed!")
        self.log("\nThis was a demonstration. For real processing:")
        self.log("1. Use the full GUI with bioportal_cli.py")
        self.log("2. Get a BioPortal API key")
        self.log("3. Process real TTL ontology files")

        self.status.config(text="Demo completed - Ready for another run")

    def log(self, message):
        """Add to demo log"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def run(self):
        """Run demo GUI"""
        self.root.mainloop()


def main():
    """Main demo entry point"""
    try:
        app = DemoBioPortalGUI()
        app.run()
    except Exception as e:
        print(f"Demo error: {e}")


if __name__ == "__main__":
    main()
