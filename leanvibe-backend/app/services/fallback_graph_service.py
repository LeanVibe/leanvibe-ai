
"""
Fallback Graph Service for when Neo4j is not available
Uses NetworkX as an in-memory graph database alternative.
"""

import networkx as nx
from typing import Dict, List, Any, Optional


class FallbackGraphService:
    """NetworkX-based fallback for graph operations when Neo4j is unavailable"""
    
    def __init__(self):
        self.graph = nx.MultiDiGraph()  # Directed graph allowing multiple edges
        self.node_properties = {}
        self.edge_properties = {}
    
    def add_node(self, node_id: str, properties: Dict[str, Any] = None):
        """Add a node with properties"""
        self.graph.add_node(node_id)
        if properties:
            self.node_properties[node_id] = properties
    
    def add_relationship(self, source: str, target: str, 
                        relationship_type: str, properties: Dict[str, Any] = None):
        """Add a relationship between nodes"""
        edge_id = self.graph.add_edge(source, target, key=relationship_type)
        if properties:
            self.edge_properties[(source, target, relationship_type)] = properties
    
    def find_nodes(self, label: str = None, properties: Dict[str, Any] = None) -> List[str]:
        """Find nodes matching criteria"""
        matching_nodes = []
        
        for node_id in self.graph.nodes():
            if node_id in self.node_properties:
                node_props = self.node_properties[node_id]
                
                # Check if all required properties match
                if properties:
                    if all(node_props.get(k) == v for k, v in properties.items()):
                        matching_nodes.append(node_id)
                else:
                    matching_nodes.append(node_id)
        
        return matching_nodes
    
    def get_relationships(self, node_id: str, direction: str = "both") -> List[Dict]:
        """Get relationships for a node"""
        relationships = []
        
        if direction in ["outgoing", "both"]:
            for target in self.graph.successors(node_id):
                for rel_type in self.graph[node_id][target]:
                    relationships.append({
                        "source": node_id,
                        "target": target,
                        "type": rel_type,
                        "direction": "outgoing"
                    })
        
        if direction in ["incoming", "both"]:
            for source in self.graph.predecessors(node_id):
                for rel_type in self.graph[source][node_id]:
                    relationships.append({
                        "source": source,
                        "target": node_id,
                        "type": rel_type,
                        "direction": "incoming"
                    })
        
        return relationships
    
    def run_cypher_equivalent(self, pattern: str) -> List[Dict]:
        """Simple pattern matching (very basic Cypher-like functionality)"""
        # This is a simplified implementation
        # In practice, you'd need a more sophisticated query parser
        return []
    
    def close(self):
        """Close the service (no-op for NetworkX)"""
        pass
        
    def is_connected(self) -> bool:
        """Always return True for fallback service"""
        return True


# Global fallback instance
fallback_graph_service = FallbackGraphService()
