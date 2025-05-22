import networkx as nx
import json
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba
import requests
from typing import Dict, List, Any
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def query_neptune(query: str) -> Dict[str, Any]:
    """Execute a query against Neptune and return the results."""
    url = "https://localhost:8182/openCypher"
    headers = {"Content-Type": "application/json"}
    data = {"query": query}
    
    logger.info(f"Executing Neptune query: {query}")
    response = requests.post(url, headers=headers, json=data, verify=False)
    response.raise_for_status()
    result = response.json()
    logger.info(f"Neptune response: {json.dumps(result, indent=2)}")
    return result

def get_all_nodes() -> List[Dict[str, Any]]:
    """Get all nodes from Neptune."""
    query = """
    MATCH (n)
    RETURN n
    """
    result = query_neptune(query)
    nodes = result.get('results', [])
    logger.info(f"Retrieved {len(nodes)} nodes from Neptune")
    return nodes

def get_all_edges() -> List[Dict[str, Any]]:
    """Get all edges from Neptune."""
    query = """
    MATCH ()-[r]->()
    RETURN r
    """
    result = query_neptune(query)
    edges = result.get('results', [])
    logger.info(f"Retrieved {len(edges)} edges from Neptune")
    return edges

def visualize_person_address_network():
    try:
        # Create a new directed graph
        G = nx.DiGraph()
        
        # Get nodes and edges from Neptune
        logger.info("Fetching nodes from Neptune...")
        nodes = get_all_nodes()
        
        logger.info("Fetching edges from Neptune...")
        edges = get_all_edges()
        
        # Add nodes
        person_count = 0
        address_count = 0
        for node in nodes:
            node_data = node.get('n', {})
            node_id = node_data.get('~id')
            properties = node_data.get('~properties', {})
            labels = node_data.get('~labels', [])
            
            logger.debug(f"Processing node: {json.dumps(node_data, indent=2)}")
            
            if 'person' in labels:  # Person node
                G.add_node(node_id,
                          node_type='person',
                          label=properties.get('name_full', ''))
                person_count += 1
            elif 'address' in labels:  # Address node
                G.add_node(node_id,
                          node_type='address',
                          label=properties.get('address_full', ''))
                address_count += 1
        
        logger.info(f"Added {person_count} person nodes and {address_count} address nodes to the graph")
        
        # Add edges
        edge_count = 0
        for edge in edges:
            edge_data = edge.get('r', {})
            from_id = edge_data.get('~start')
            to_id = edge_data.get('~end')
            properties = edge_data.get('~properties', {})
            
            logger.debug(f"Processing edge: {json.dumps(edge_data, indent=2)}")
            
            if from_id and to_id:
                G.add_edge(from_id,
                          to_id,
                          edge_type=edge_data.get('~type'),
                          address_type=properties.get('address_type'))
                edge_count += 1
        
        logger.info(f"Added {edge_count} edges to the graph")
        
        if len(G.nodes()) == 0:
            logger.error("No nodes were added to the graph. Check the Neptune response format.")
            return
            
        if len(G.edges()) == 0:
            logger.warning("No edges were added to the graph. Check the Neptune response format.")
        
        # Create the plot
        plt.figure(figsize=(15, 10))
        
        # Set up node colors and sizes
        node_colors = []
        node_sizes = []
        for node in G.nodes():
            if G.nodes[node]['node_type'] == 'person':
                node_colors.append('lightblue')
                node_sizes.append(500)
            else:
                node_colors.append('lightgreen')
                node_sizes.append(300)
        
        # Set up edge colors based on address type
        edge_colors = []
        for u, v in G.edges():
            edge_type = G.edges[u, v]['address_type']
            if edge_type == 'PRIMARY':
                edge_colors.append('red')
            elif edge_type == 'SECONDARY':
                edge_colors.append('blue')
            else:  # TERTIARY
                edge_colors.append('gray')
        
        logger.info(f"Drawing graph with {len(G.nodes())} nodes and {len(G.edges())} edges")
        
        # Draw the graph
        pos = nx.spring_layout(G, k=1, iterations=50)
        
        # Draw nodes
        nx.draw_networkx_nodes(G, pos,
                             node_color=node_colors,
                             node_size=node_sizes,
                             alpha=0.7)
        
        # Draw edges
        nx.draw_networkx_edges(G, pos,
                             edge_color=edge_colors,
                             arrows=True,
                             arrowsize=20,
                             width=2,
                             alpha=0.6)
        
        # Add labels
        labels = {node: G.nodes[node]['label'] for node in G.nodes()}
        nx.draw_networkx_labels(G, pos, labels, font_size=8)
        
        # Add legend
        from matplotlib.lines import Line2D
        legend_elements = [
            Line2D([0], [0], marker='o', color='w', label='Person',
                  markerfacecolor='lightblue', markersize=15),
            Line2D([0], [0], marker='o', color='w', label='Address',
                  markerfacecolor='lightgreen', markersize=15),
            Line2D([0], [0], color='red', label='Primary Address',
                  linewidth=2),
            Line2D([0], [0], color='blue', label='Secondary Address',
                  linewidth=2),
            Line2D([0], [0], color='gray', label='Tertiary Address',
                  linewidth=2)
        ]
        plt.legend(handles=legend_elements, loc='upper right')
        
        plt.title('Person-Address Network')
        plt.axis('off')
        
        # Save the plot
        plt.savefig('src/data/output/visualization/person_address_network.png', 
                   dpi=300, 
                   bbox_inches='tight')
        logger.info("Network visualization saved to src/data/output/visualization/person_address_network.png")
        
        # Show the plot
        plt.show()
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error connecting to Neptune: {str(e)}")
    except Exception as e:
        logger.error(f"Error during visualization: {str(e)}", exc_info=True)

if __name__ == "__main__":
    visualize_person_address_network() 