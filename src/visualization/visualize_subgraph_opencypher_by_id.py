import networkx as nx
import json
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba
import requests
from typing import Dict, List, Any, Set, Optional
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
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {"query": query}
    
    logger.info(f"Executing Neptune query: {query}")
    response = requests.post(url, headers=headers, data=data, verify=False)
    response.raise_for_status()
    result = response.json()
    logger.info(f"Neptune response: {json.dumps(result, indent=2)}")
    return result

def get_multi_level_subgraph(node_id: str) -> List[Dict[str, Any]]:
    """Get subgraph for a specific node and its connections up to 2 levels deep."""
    query = f"""
    MATCH path = (start)-[*0..2]-(n) 
    WHERE id(start) = "{node_id}" 
    RETURN nodes(path) as nodes, relationships(path) as edges
    """
    result = query_neptune(query)
    return result.get('results', [])

def visualize_network(node_id: str):
    """
    Visualize the network for a specific node and its connections up to 2 levels deep.
    
    Args:
        node_id (str): The ID of the node to visualize (can be person or address).
    """
    try:
        # Create a new directed graph
        G = nx.DiGraph()
        
        # Get subgraph from Neptune
        logger.info(f"Fetching multi-level subgraph for node {node_id} from Neptune...")
        subgraph_data = get_multi_level_subgraph(node_id)
        
        # Add nodes and edges from the subgraph
        person_count = 0
        address_count = 0
        edge_count = 0
        
        for result in subgraph_data:
            # Process nodes
            nodes = result.get('nodes', [])
            for node in nodes:
                node_id = node.get('~id')
                node_props = node.get('~properties', {})
                node_labels = node.get('~labels', [])
                
                if node_id and node_id not in G:
                    if 'person' in node_labels:
                        G.add_node(node_id,
                                  node_type='person',
                                  label=node_props.get('name_full', ''))
                        person_count += 1
                    elif 'address' in node_labels:
                        G.add_node(node_id,
                                  node_type='address',
                                  label=node_props.get('address_full', ''))
                        address_count += 1
            
            # Process edges
            edges = result.get('edges', [])
            for edge in edges:
                from_id = edge.get('~start')
                to_id = edge.get('~end')
                edge_props = edge.get('~properties', {})
                
                if from_id in G and to_id in G:
                    G.add_edge(from_id,
                              to_id,
                              edge_type=edge.get('~type'),
                              address_type=edge_props.get('address_type'))
                    edge_count += 1
        
        logger.info(f"Added {person_count} person nodes, {address_count} address nodes, and {edge_count} edges to the graph")
        
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
        
        plt.title('Multi-Level Person-Address Network')
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
    # Prompt user for node ID
    print("\nEnter the node ID to visualize its network (up to 2 levels deep)")
    print("Example person ID: 103b8fd1-fb6a-43e9-b7ea-1ac5eee9f976")
    print("Example address ID: 3cf559d0-6465-4b85-91bc-1c27f98b90cb")
    print("Press Enter to use the example person ID or type a different ID:")
    
    user_input = input().strip()
    node_id = user_input if user_input else "103b8fd1-fb6a-43e9-b7ea-1ac5eee9f976"
    
    print(f"\nVisualizing multi-level network for node ID: {node_id}")
    visualize_network(node_id) 