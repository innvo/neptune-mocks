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

def get_subgraph(node_ids: List[str], level: int) -> List[Dict[str, Any]]:
    """Get subgraph for multiple nodes (person or address) and their connections up to specified level deep."""
    # Format the list of node IDs for the query
    node_ids_str = ', '.join([f'"{id}"' for id in node_ids])
    query = f'MATCH path = (start)-[*0..{level}]-(n) WHERE id(start) IN [{node_ids_str}] RETURN nodes(path) as nodes, relationships(path) as edges'
    result = query_neptune(query)
    return result.get('results', [])

def visualize_network(node_ids: List[str], level: int):
    """
    Visualize the network for multiple nodes (person or address) and their connections.
    
    Args:
        node_ids (List[str]): List of node IDs to visualize (can be person or address).
        level (int): The depth level to traverse in the network.
    """
    try:
        # Create a new directed graph
        G = nx.DiGraph()
        
        # Get subgraph from Neptune
        logger.info(f"Fetching subgraph for nodes {node_ids} from Neptune with level {level}...")
        subgraph_data = get_subgraph(node_ids, level)
        
        # Add nodes and edges from the subgraph
        person_count = 0
        address_count = 0
        edge_count = 0
        
        for result in subgraph_data:
            nodes = result.get('nodes', [])
            edges = result.get('edges', [])
            
            logger.info(f"Processing {len(nodes)} nodes and {len(edges)} edges")
            
            # Add nodes
            for node in nodes:
                node_id = node.get('~id')
                node_props = node.get('~properties', {})
                node_labels = node.get('~labels', [])
                
                if node_id and node_id not in G.nodes():
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
            
            # Add edges
            for edge in edges:
                logger.info(f"Processing edge: {json.dumps(edge, indent=2)}")
                edge_type = edge.get('~type')
                edge_props = edge.get('~properties', {})
                
                # Extract start and end nodes from the edge
                start_node = edge.get('~start')
                end_node = edge.get('~end')
                
                logger.info(f"Edge from {start_node} to {end_node}")
                
                if start_node and end_node and start_node in G.nodes() and end_node in G.nodes():
                    G.add_edge(start_node,
                              end_node,
                              edge_type=edge_type,
                              address_type=edge_props.get('address_type'))
                    edge_count += 1
                    logger.info(f"Added edge from {start_node} to {end_node}")
                else:
                    logger.warning(f"Could not add edge: start={start_node}, end={end_node}")
        
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
        node_edge_colors = []  # New list for node border colors
        node_edge_widths = []  # New list for node border widths
        
        for node in G.nodes():
            if G.nodes[node]['node_type'] == 'person':
                node_colors.append('lightblue')
                node_sizes.append(500)
            else:
                node_colors.append('lightgreen')
                node_sizes.append(300)
            
            # Add red border for starting nodes
            if node in node_ids:
                node_edge_colors.append('red')
                node_edge_widths.append(3)
            else:
                node_edge_colors.append('black')
                node_edge_widths.append(1)
        
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
        
        # Draw nodes with borders
        nx.draw_networkx_nodes(G, pos,
                             node_color=node_colors,
                             node_size=node_sizes,
                             edgecolors=node_edge_colors,
                             linewidths=node_edge_widths,
                             alpha=0.7)
        
        # Draw edges
        nx.draw_networkx_edges(G, pos,
                             edge_color=edge_colors,
                             arrows=True,
                             arrowsize=20,
                             width=2,
                             alpha=0.6)
        
        # Add labels
        labels = {node: f"{G.nodes[node]['label']}\n({node})" for node in G.nodes()}
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
        
        plt.title(f'Person-Address Network ({level} Levels Deep)')
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
    # Prompt user for node IDs
    print("\nEnter the node IDs to visualize their network (comma-separated)")
    print("Example person IDs: 103b8fd1-fb6a-43e9-b7ea-1ac5eee9f976, 401bc498-6092-4292-938e-73497e72276d")
    print("Example address IDs: 3cf559d0-6465-4b85-91bc-1c27f98b90cb, 1bd17f36-16b8-4b20-a6e1-ef98e1965f45")
    print("Press Enter to use the example IDs or type different IDs:")
    
    user_input = input().strip()
    if not user_input:
        node_ids = ["103b8fd1-fb6a-43e9-b7ea-1ac5eee9f976", "401bc498-6092-4292-938e-73497e72276d"]
    else:
        node_ids = [id.strip() for id in user_input.split(',')]
    
    # Prompt user for level
    print("\nEnter the level depth (1-5 recommended):")
    print("Press Enter to use default level 3 or type a different level:")
    
    level_input = input().strip()
    if not level_input:
        level = 3
    else:
        try:
            level = int(level_input)
            if level < 1:
                print("Level must be at least 1. Using level 1.")
                level = 1
            elif level > 10:
                print("Warning: High levels may result in large networks. Using level 10.")
                level = 10
        except ValueError:
            print("Invalid level input. Using default level 3.")
            level = 3
    
    print(f"\nVisualizing network for node IDs: {node_ids} with level {level}")
    visualize_network(node_ids, level) 