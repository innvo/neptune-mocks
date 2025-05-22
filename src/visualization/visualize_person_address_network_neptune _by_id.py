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
    headers = {"Content-Type": "application/json"}
    data = {"query": query}
    
    logger.info(f"Executing Neptune query: {query}")
    response = requests.post(url, headers=headers, json=data, verify=False)
    response.raise_for_status()
    result = response.json()
    logger.info(f"Neptune response: {json.dumps(result, indent=2)}")
    return result

def get_subgraph(person_id: str) -> List[Dict[str, Any]]:
    """Get subgraph for a specific person and their connected addresses."""
    query = f"""
    MATCH (n) WHERE id(n) IN ["{person_id}"] 
    OPTIONAL MATCH (n)-[r]-(m) 
    RETURN n, r, m
    """
    result = query_neptune(query)
    return result.get('results', [])

def visualize_person_address_network(person_id: str):
    """
    Visualize the person-address network for a specific person.
    
    Args:
        person_id (str): The ID of the person node to visualize.
    """
    try:
        # Create a new directed graph
        G = nx.DiGraph()
        
        # Get subgraph from Neptune
        logger.info(f"Fetching subgraph for person {person_id} from Neptune...")
        subgraph_data = get_subgraph(person_id)
        
        # Add nodes and edges from the subgraph
        person_count = 0
        address_count = 0
        edge_count = 0
        
        for result in subgraph_data:
            # Add person node
            person_data = result.get('n', {})
            person_id = person_data.get('~id')
            person_props = person_data.get('~properties', {})
            
            if person_id and 'person' in person_data.get('~labels', []):
                G.add_node(person_id,
                          node_type='person',
                          label=person_props.get('name_full', ''))
                person_count += 1
            
            # Add connected address node and edge
            address_data = result.get('m', {})
            edge_data = result.get('r', {})
            
            if address_data and edge_data:
                address_id = address_data.get('~id')
                address_props = address_data.get('~properties', {})
                edge_props = edge_data.get('~properties', {})
                
                if address_id and 'address' in address_data.get('~labels', []):
                    G.add_node(address_id,
                              node_type='address',
                              label=address_props.get('address_full', ''))
                    address_count += 1
                    
                    G.add_edge(person_id,
                              address_id,
                              edge_type=edge_data.get('~type'),
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
    # Example usage with a specific person ID:
    person_id = "103b8fd1-fb6a-43e9-b7ea-1ac5eee9f976"
    visualize_person_address_network(person_id) 