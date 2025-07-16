"""
Ontology parser for TTL files.
"""

from rdflib import RDF, RDFS, Graph


class OntologyParser:
    """Parses and analyzes TTL ontology files"""

    def __init__(self, ttl_file: str):
        self.ttl_file = ttl_file
        self.graph = Graph()
        self.classes: list[str] = []
        self.instances: list[dict] = []

    def parse(self) -> bool:
        """Parse the TTL file and extract concepts"""
        try:
            self.graph.parse(self.ttl_file, format="turtle")
            print(f"✅ Loaded {len(self.graph)} triples from {self.ttl_file}")

            # Extract classes
            for s, _p, _o in self.graph.triples((None, RDF.type, RDFS.Class)):
                class_name = str(s).split("#")[-1]
                if class_name != "Entity":  # Skip base class
                    self.classes.append(class_name)

            # Extract instances
            for s, _p, o in self.graph.triples((None, RDF.type, None)):
                if (
                    str(o).startswith("http://example.org/ontology#")
                    and str(o).split("#")[-1] in self.classes
                ):
                    instance_name = str(s).split("#")[-1]
                    class_type = str(o).split("#")[-1]
                    self.instances.append(
                        {
                            "name": instance_name,
                            "type": class_type,
                            "label": instance_name.replace("_", " "),
                        }
                    )

            print(f"📊 Found {len(self.classes)} classes and {len(self.instances)} instances")
            return True

        except Exception as e:
            print(f"❌ Error parsing {self.ttl_file}: {e}")
            return False

    def get_priority_concepts(self) -> list[dict]:
        """Get priority concepts for BioPortal lookup"""
        concepts = []

        # Add priority instances
        priority_instances = ["long_covid", "fatigue", "immune_dysfunction"]
        for instance in self.instances:
            if instance["name"] in priority_instances:
                concepts.append(
                    {
                        "key": instance["name"],
                        "label": instance["label"],
                        "type": instance["type"],
                        "category": "instance",
                    }
                )

        # Add core classes
        priority_classes = [
            "Disease",
            "Symptom",
            "BiologicalProcess",
            "MolecularEntity",
            "Treatment",
        ]
        for class_name in self.classes:
            if class_name in priority_classes:
                concepts.append(
                    {"key": class_name, "label": class_name, "type": "Class", "category": "class"}
                )

        return concepts
