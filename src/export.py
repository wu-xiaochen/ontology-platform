"""
Data Export Module
Provides data export functionality in multiple formats: JSON, CSV, Turtle, JSON-LD

v1.0.0 - Initial version
"""

import csv
import json
import io
import logging
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ExportFormat(Enum):
    """Supported export formats"""
    JSON = "json"
    CSV = "csv"
    TURTLE = "turtle"
    JSONLD = "jsonld"


@dataclass
class ExportOptions:
    """Export options"""
    format: ExportFormat = ExportFormat.JSON
    include_metadata: bool = True
    include_schema: bool = True
    max_records: int = 10000
    compression: bool = False


class DataExporter:
    """Export ontology data in various formats"""
    
    def __init__(self, rdf_adapter=None, neo4j_client=None):
        self.rdf_adapter = rdf_adapter
        self.neo4j_client = neo4j_client
    
    def export_triples(
        self,
        subject: Optional[str] = None,
        predicate: Optional[str] = None,
        obj: Optional[str] = None,
        options: ExportOptions = None
    ) -> str:
        """Export triples to specified format"""
        options = options or ExportOptions()
        
        # Get triples
        triples = []
        if self.rdf_adapter:
            triples = self.rdf_adapter.query(subject, predicate, obj)
        
        # Apply limit
        triples = triples[:options.max_records]
        
        # Export based on format
        if options.format == ExportFormat.JSON:
            return self._to_json(triples, options)
        elif options.format == ExportFormat.CSV:
            return self._to_csv(triples, options)
        elif options.format == ExportFormat.TURTLE:
            return self._to_turtle(triples, options)
        elif options.format == ExportFormat.JSONLD:
            return self._to_jsonld(triples, options)
        
        raise ValueError(f"Unsupported format: {options.format}")
    
    def export_entities(
        self,
        label: Optional[str] = None,
        options: ExportOptions = None
    ) -> str:
        """Export entities to specified format"""
        options = options or ExportOptions()
        
        # Get entities
        entities = []
        if self.neo4j_client:
            if label:
                entities = self.neo4j_client.query_by_properties(label, {})
            else:
                # Get all entities - simplified
                entities = []
        
        # Apply limit
        entities = entities[:options.max_records]
        
        # Export based on format
        if options.format == ExportFormat.JSON:
            return self._entities_to_json(entities, options)
        elif options.format == ExportFormat.CSV:
            return self._entities_to_csv(entities, options)
        
        raise ValueError(f"Unsupported format for entities: {options.format}")
    
    def export_schema(
        self,
        options: ExportOptions = None
    ) -> str:
        """Export ontology schema"""
        options = options or ExportOptions()
        
        schema = {}
        if self.rdf_adapter:
            schema = self.rdf_adapter.export_schema()
        
        if options.format == ExportFormat.JSON:
            return json.dumps(schema, indent=2, ensure_ascii=False)
        elif options.format == ExportFormat.JSONLD:
            return self._schema_to_jsonld(schema, options)
        
        raise ValueError(f"Unsupported format for schema: {options.format}")
    
    def _to_json(self, triples: List, options: ExportOptions) -> str:
        """Convert triples to JSON"""
        data = {"triples": []}
        
        if options.include_metadata:
            data["metadata"] = {
                "exported_at": datetime.now().isoformat(),
                "count": len(triples),
                "format": "json"
            }
        
        for t in triples:
            data["triples"].append(t.to_dict() if hasattr(t, 'to_dict') else {
                "subject": t.subject if hasattr(t, 'subject') else str(t[0]),
                "predicate": t.predicate if hasattr(t, 'predicate') else str(t[1]),
                "object": t.object if hasattr(t, 'object') else str(t[2]),
                "confidence": t.confidence if hasattr(t, 'confidence') else 1.0
            })
        
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    def _to_csv(self, triples: List, options: ExportOptions) -> str:
        """Convert triples to CSV"""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(["subject", "predicate", "object", "confidence", "source"])
        
        # Write data
        for t in triples:
            writer.writerow([
                t.subject if hasattr(t, 'subject') else str(t[0]),
                t.predicate if hasattr(t, 'predicate') else str(t[1]),
                t.object if hasattr(t, 'object') else str(t[2]),
                t.confidence if hasattr(t, 'confidence') else 1.0,
                t.source if hasattr(t, 'source') else ""
            ])
        
        return output.getvalue()
    
    def _to_turtle(self, triples: List, options: ExportOptions) -> str:
        """Convert triples to Turtle format"""
        lines = []
        
        if options.include_metadata:
            lines.append("# Exported from Ontology Platform")
            lines.append(f"# Export time: {datetime.now().isoformat()}")
            lines.append(f"# Triple count: {len(triples)}")
            lines.append("")
        
        base_uri = "http://example.org/"
        
        for t in triples:
            s = t.subject if hasattr(t, 'subject') else str(t[0])
            p = t.predicate if hasattr(t, 'predicate') else str(t[1])
            o = t.object if hasattr(t, 'object') else str(t[2])
            
            # Format URIs
            if not s.startswith("http"):
                s = f"{base_uri}{s}"
            if not p.startswith("http"):
                p = f"{base_uri}{p}"
            
            # Handle literals
            if o.startswith("http"):
                obj = f"<{o}>"
            else:
                obj = f'"{o}"'
            
            lines.append(f"<{s}> <{p}> {obj} .")
        
        return "\n".join(lines)
    
    def _to_jsonld(self, triples: List, options: ExportOptions) -> str:
        """Convert triples to JSON-LD"""
        graph = []
        
        for t in triples:
            s = t.subject if hasattr(t, 'subject') else str(t[0])
            p = t.predicate if hasattr(t, 'predicate') else str(t[1])
            o = t.object if hasattr(t, 'object') else str(t[2])
            
            graph.append({
                "@id": s,
                "@type": p,
                "@value": o
            })
        
        doc = {
            "@context": {
                "@vocab": "http://example.org/",
                "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
            },
            "@graph": graph
        }
        
        if options.include_metadata:
            doc["metadata"] = {
                "exported_at": datetime.now().isoformat(),
                "count": len(triples)
            }
        
        return json.dumps(doc, indent=2, ensure_ascii=False)
    
    def _entities_to_json(self, entities: List, options: ExportOptions) -> str:
        """Convert entities to JSON"""
        data = {"entities": []}
        
        if options.include_metadata:
            data["metadata"] = {
                "exported_at": datetime.now().isoformat(),
                "count": len(entities)
            }
        
        for e in entities:
            data["entities"].append(e.to_dict() if hasattr(e, 'to_dict') else e)
        
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    def _entities_to_csv(self, entities: List, options: ExportOptions) -> str:
        """Convert entities to CSV"""
        output = io.StringIO()
        
        if not entities:
            return ""
        
        # Get all property keys
        all_keys = set()
        for e in entities:
            if hasattr(e, 'properties'):
                all_keys.update(e.properties.keys())
        
        fieldnames = ["name", "label"] + sorted(all_keys)
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for e in entities:
            row = {
                "name": e.name if hasattr(e, 'name') else str(e.get("name", "")),
                "label": e.label if hasattr(e, 'label') else str(e.get("label", ""))
            }
            
            if hasattr(e, 'properties'):
                for k, v in e.properties.items():
                    row[k] = str(v)
            
            writer.writerow(row)
        
        return output.getvalue()
    
    def _schema_to_jsonld(self, schema: Dict, options: ExportOptions) -> str:
        """Convert schema to JSON-LD"""
        doc = {
            "@context": {
                "@vocab": "http://example.org/",
                "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
                "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
                "owl": "http://www.w3.org/2002/07/owl#"
            },
            "@graph": []
        }
        
        # Add classes
        for cls in schema.get("classes", []):
            doc["@graph"].append({
                "@id": cls.get("uri", ""),
                "@type": "rdfs:Class",
                "rdfs:label": cls.get("label", ""),
                "rdfs:comment": cls.get("description", "")
            })
        
        # Add properties
        for prop in schema.get("properties", []):
            doc["@graph"].append({
                "@id": prop.get("uri", ""),
                "@type": "rdf:Property",
                "rdfs:label": prop.get("label", "")
            })
        
        if options.include_metadata:
            doc["metadata"] = {
                "exported_at": datetime.now().isoformat()
            }
        
        return json.dumps(doc, indent=2, ensure_ascii=False)


# Global exporter instance
data_exporter = DataExporter()
