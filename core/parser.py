"""
Ontology parser for TTL files.
"""

from rdflib import OWL, RDF, RDFS, Graph

from config.logging_config import get_logger

logger = get_logger(__name__)


class OntologyParser:
    """Parses and analyzes TTL ontology files"""

    def __init__(self, ttl_file: str):
        self.ttl_file = ttl_file
        self.graph = Graph()
        self.classes: list[str] = []
        self.instances: list[dict] = []
        self.properties: list[dict] = []
        self.relationships: list[dict] = []

    def parse(self) -> bool:
        """Parse the TTL file and extract concepts"""
        try:
            self.graph.parse(self.ttl_file, format="turtle")
            logger.info(f"Loaded {len(self.graph)} triples from {self.ttl_file}")

            # --- Extract Classes (owl:Class and rdfs:Class, any prefix) ---
            class_uris = {OWL.Class, RDFS.Class}
            for s, _p, o in self.graph.triples((None, RDF.type, None)):
                if o in class_uris or str(o).endswith("Class"):
                    # Accept both full URI and prefixed
                    class_name = str(s).split("#")[-1] if "#" in str(s) else str(s).split("/")[-1]
                    if class_name != "Entity" and class_name not in self.classes:
                        self.classes.append(class_name)

            # --- Extract Instances (flexible, any class) ---
            for s, _p, o in self.graph.triples((None, RDF.type, None)):
                class_name = str(o).split("#")[-1] if "#" in str(o) else str(o).split("/")[-1]
                if class_name in self.classes:
                    instance_name = (
                        str(s).split("#")[-1] if "#" in str(s) else str(s).split("/")[-1]
                    )
                    self.instances.append(
                        {
                            "name": instance_name,
                            "type": class_name,
                            "label": instance_name.replace("_", " "),
                        }
                    )

            # --- Extract Properties (Object and Datatype) ---
            property_types = [OWL.ObjectProperty, OWL.DatatypeProperty]
            for s, _p, o in self.graph.triples((None, RDF.type, None)):
                if o in property_types or str(o).endswith("Property"):
                    prop_name = str(s).split("#")[-1] if "#" in str(s) else str(s).split("/")[-1]
                    label = None
                    for _ss, _pp, label_val in self.graph.triples((s, RDFS.label, None)):
                        label = str(label_val)
                    self.properties.append({"name": prop_name, "label": label})

            # --- Extract Relationships (domain/range) ---
            for prop in self.properties:
                prop_uri = None
                # Find the URI for this property
                for s, _p, _o in self.graph.triples((None, RDFS.label, None)):
                    if str(_o) == prop["label"]:
                        prop_uri = s
                        break
                if prop_uri:
                    domain = None
                    range_ = None
                    for _s, _p, val in self.graph.triples((prop_uri, RDFS.domain, None)):
                        domain = (
                            str(val).split("#")[-1] if "#" in str(val) else str(val).split("/")[-1]
                        )
                    for _s, _p, val in self.graph.triples((prop_uri, RDFS.range, None)):
                        range_ = (
                            str(val).split("#")[-1] if "#" in str(val) else str(val).split("/")[-1]
                        )
                    if domain and range_:
                        self.relationships.append(
                            {"property": prop["name"], "domain": domain, "range": range_}
                        )

            logger.info(
                f"Found {len(self.classes)} classes, {len(self.instances)} instances, {len(self.properties)} properties, {len(self.relationships)} relationships"
            )
            return True

        except Exception as e:
            logger.error(f"Error parsing {self.ttl_file}: {e}")
            return False

    def get_priority_concepts(self) -> list[dict]:
        """Get priority classes, instances, and all relationships for BioPortal lookup"""
        concepts = []

        # Define priority classes
        priority_classes = {"Disease", "Symptom", "Treatment"}

        # Add instances whose type is a priority class
        for instance in self.instances:
            if instance["type"] in priority_classes:
                concepts.append(
                    {
                        "key": instance["name"],
                        "label": instance["label"],
                        "type": instance["type"],
                        "category": "instance",
                    }
                )

        # Add all priority classes
        for class_name in self.classes:
            if class_name in priority_classes:
                concepts.append(
                    {
                        "key": class_name,
                        "label": class_name,
                        "type": "Class",
                        "category": "class",
                    }
                )

        # Add all relationships (as concepts for lookup)
        for rel in self.relationships:
            concepts.append(
                {
                    "key": rel["property"],
                    "label": rel["property"],
                    "type": "Relationship",
                    "category": "relationship",
                    "domain": rel["domain"],
                    "range": rel["range"],
                }
            )

        return concepts
