import networkx as nx
import json
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba

def visualize_person_address_network():
    try:
        # Create a new directed graph
        G = nx.DiGraph()
        
        # Read person nodes
        print("Reading person nodes...")
        with open('src/data/output/gds/mock_person_data.json', 'r') as f:
            person_data = json.load(f)
        
        # Read address nodes
        print("Reading address nodes...")
        with open('src/data/output/gds/mock_address_data.json', 'r') as f:
            address_data = json.load(f)
        
        # Read edges
        print("Reading edges...")
        with open('src/data/output/gds/mock_person-address_data.json', 'r') as f:
            edge_data = json.load(f)
        
        # Add person nodes
        for person in person_data:
            G.add_node(person['node_id'], 
                      node_type='person',
                      label=person.get('properties', {}).get('FIRST_NAME', '') + ' ' + 
                            person.get('properties', {}).get('LAST_NAME', ''))
        
        # Add address nodes
        for address in address_data:
            G.add_node(address['node_id'],
                      node_type='address',
                      label=address.get('properties', {}).get('STREET_ADDRESS', ''))
        
        # Add edges
        for edge in edge_data:
            G.add_edge(edge['node_id_from'],
                      edge['node_id_to'],
                      edge_type=edge['edge_type'],
                      address_type=edge['edge_properties']['ADDRESS_TYPE'])
        
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
        print("\nNetwork visualization saved to src/data/output/visualization/person_address_network.png")
        
        # Show the plot
        plt.show()
        
    except FileNotFoundError as e:
        print(f"Error: Required file not found - {str(e)}")
    except Exception as e:
        print(f"Error during visualization: {str(e)}")

if __name__ == "__main__":
    visualize_person_address_network() 