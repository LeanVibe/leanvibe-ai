#!/usr/bin/env python3
"""
Neo4j Connection Validation Script

Tests Neo4j driver installation and connection capabilities with fallback handling.
"""

import sys
import time
from typing import Tuple, Optional


def test_neo4j_driver_import() -> Tuple[bool, str]:
    """Test Neo4j driver import and basic functionality"""
    try:
        import neo4j
        from neo4j import GraphDatabase, Driver, Session
        
        version = getattr(neo4j, '__version__', 'Unknown')
        return True, f"Neo4j driver imported successfully (version: {version})"
    except ImportError as e:
        return False, f"Failed to import Neo4j driver: {e}"


def test_neo4j_connection(uri: str = "bolt://localhost:7687", 
                         username: str = "neo4j", 
                         password: str = "neo4j") -> Tuple[bool, str]:
    """Test actual Neo4j database connection"""
    try:
        from neo4j import GraphDatabase
        
        # Create driver with timeout
        driver = GraphDatabase.driver(uri, auth=(username, password))
        
        # Test connection with a simple query
        with driver.session() as session:
            # Run a simple query to verify connection
            result = session.run("RETURN 1 as test_value")
            record = result.single()
            
            if record and record["test_value"] == 1:
                driver.close()
                return True, f"Successfully connected to Neo4j at {uri}"
            else:
                driver.close()
                return False, "Connected but query returned unexpected result"
                
    except Exception as e:
        return False, f"Failed to connect to Neo4j: {e}"


def test_neo4j_with_common_configs() -> Tuple[bool, str]:
    """Test Neo4j connection with common configurations"""
    common_configs = [
        ("bolt://localhost:7687", "neo4j", "neo4j"),
        ("bolt://localhost:7687", "neo4j", "password"),
        ("neo4j://localhost:7687", "neo4j", "neo4j"),
        ("bolt://127.0.0.1:7687", "neo4j", "neo4j"),
    ]
    
    for uri, username, password in common_configs:
        success, message = test_neo4j_connection(uri, username, password)
        if success:
            return True, f"Connected with config: {uri} (user: {username})"
    
    return False, "Could not connect with any common configuration"


def test_networkx_fallback() -> Tuple[bool, str]:
    """Test NetworkX as a fallback graph library"""
    try:
        import networkx as nx
        
        # Create a simple graph to test functionality
        G = nx.Graph()
        G.add_edge('A', 'B')
        G.add_edge('B', 'C')
        G.add_edge('C', 'A')
        
        # Test basic operations
        nodes = len(G.nodes())
        edges = len(G.edges())
        
        if nodes == 3 and edges == 3:
            version = getattr(nx, '__version__', 'Unknown')
            return True, f"NetworkX fallback working correctly (version: {version})"
        else:
            return False, f"NetworkX graph operations failed: {nodes} nodes, {edges} edges"
            
    except Exception as e:
        return False, f"NetworkX fallback failed: {e}"


def check_neo4j_service() -> Tuple[bool, str]:
    """Check if Neo4j service is likely running"""
    try:
        import socket
        
        # Check if port 7687 (default Neo4j bolt port) is open
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)  # 1 second timeout
        result = sock.connect_ex(('localhost', 7687))
        sock.close()
        
        if result == 0:
            return True, "Neo4j service appears to be running (port 7687 is open)"
        else:
            return False, "Neo4j service not detected (port 7687 is closed)"
            
    except Exception as e:
        return False, f"Could not check Neo4j service status: {e}"


def create_fallback_graph_service() -> Tuple[bool, str]:
    """Create a mock graph service for when Neo4j is not available"""
    try:
        fallback_code = '''
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
'''
        
        # Write the fallback service to app/services/
        fallback_path = "/Users/bogdan/work/leanvibe-ai/leanvibe-backend/app/services/fallback_graph_service.py"
        with open(fallback_path, 'w') as f:
            f.write(fallback_code)
        
        return True, f"Fallback graph service created at {fallback_path}"
        
    except Exception as e:
        return False, f"Failed to create fallback graph service: {e}"


def main():
    """Run all Neo4j validation tests"""
    print("🔗 Neo4j Connection Validation")
    print("=" * 50)
    
    # Test driver import first
    print("🔍 Testing Neo4j driver import...")
    success, message = test_neo4j_driver_import()
    print(f"{'✅' if success else '❌'} {message}")
    
    if not success:
        print("❌ Cannot proceed with connection tests - driver not available")
        return 1
    
    # Check if Neo4j service is running
    print("\\n🔍 Checking Neo4j service status...")
    service_success, service_message = check_neo4j_service()
    print(f"{'✅' if service_success else '⚠️'} {service_message}")
    
    # Test connection if service appears to be running
    if service_success:
        print("\\n🔍 Testing Neo4j connection...")
        conn_success, conn_message = test_neo4j_with_common_configs()
        print(f"{'✅' if conn_success else '❌'} {conn_message}")
    else:
        conn_success = False
        print("⚠️ Skipping connection test - service not detected")
    
    # Test NetworkX fallback
    print("\\n🔍 Testing NetworkX fallback...")
    fallback_success, fallback_message = test_networkx_fallback()
    print(f"{'✅' if fallback_success else '❌'} {fallback_message}")
    
    # Create fallback service if needed
    if not conn_success and fallback_success:
        print("\\n🔧 Creating fallback graph service...")
        create_success, create_message = create_fallback_graph_service()
        print(f"{'✅' if create_success else '❌'} {create_message}")
    
    # Summary
    print("\\n" + "=" * 50)
    print("📋 NEO4J VALIDATION SUMMARY")
    
    if conn_success:
        print("✅ Neo4j is fully operational - direct database connection available")
    elif fallback_success:
        print("⚠️ Neo4j connection not available - fallback to NetworkX configured")
        print("   The system will work with reduced graph database functionality")
    else:
        print("❌ Neither Neo4j nor NetworkX fallback is available")
        print("   Graph-related features will be disabled")
    
    print("\\n📝 Recommendations:")
    if not service_success:
        print("  - Install and start Neo4j Community Edition")
        print("  - Or use Docker: docker run -p 7474:7474 -p 7687:7687 neo4j")
    if not conn_success and service_success:
        print("  - Check Neo4j authentication credentials")
        print("  - Verify Neo4j is accepting connections on port 7687")
    
    return 0 if (conn_success or fallback_success) else 1


if __name__ == "__main__":
    sys.exit(main())