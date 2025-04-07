import pandas as pd
import uuid
import random
from tqdm import tqdm

def validate_node_existence(node_df, node_id):
    """Validate that a node exists in the node_data.csv"""
    return node_id in node_df['node_id'].values

def generate_edges_for_person(person_id, node_df, node_sets, batch_size=1000):
    """Generate edges for a single person in batches"""
    edges = []
    missing_nodes = set()
    
    # Generate edges for each node type
    for node_type, nodes in node_sets.items():
        if not nodes.empty:
            # Determine number of edges based on node type
            if node_type == 'name':
                num_edges = random.randint(1, min(3, len(nodes)))
            else:
                num_edges = random.randint(1, min(2, len(nodes)))
            
            selected_nodes = nodes.sample(n=num_edges)
            for _, node in selected_nodes.iterrows():
                node_id = node['node_id']
                if validate_node_existence(node_df, node_id):
                    edges.append({
                        'edge_id': str(uuid.uuid4()),
                        'node_id_from': person_id,
                        'node_id_to': node_id,
                        'edge_type': f'person_{node_type}'
                    })
                else:
                    missing_nodes.add(node_id)
                
                # Process in batches
                if len(edges) >= batch_size:
                    yield edges, missing_nodes
                    edges = []
                    missing_nodes = set()
    
    if edges:
        yield edges, missing_nodes

def generate_person_edges():
    try:
        # Read node_data.csv, excluding node_name column
        print("Reading node data...")
        node_df = pd.read_csv('node_data.csv', usecols=['node_id', 'node_type'])
        
        # Print node type statistics
        print("\nNode Type Statistics:")
        print(f"Total number of nodes: {len(node_df)}")
        node_counts = node_df['node_type'].value_counts()
        for node_type, count in node_counts.items():
            print(f"{node_type}: {count} nodes")
        
        # Get person nodes
        person_nodes = node_df[node_df['node_type'] == 'person']
        if person_nodes.empty:
            print("Warning: No person nodes found in node_data.csv")
            return None
        
        # Get other node types
        node_sets = {
            'name': node_df[node_df['node_type'] == 'name'],
            'address': node_df[node_df['node_type'] == 'address'],
            'form': node_df[node_df['node_type'] == 'form'],
            'phone': node_df[node_df['node_type'] == 'phone'],
            'email': node_df[node_df['node_type'] == 'email'],
            'anumber': node_df[node_df['node_type'] == 'anumber']
        }
        
        # Initialize edge data and counters
        all_edges = []
        all_missing_nodes = set()
        total_edges = 0
        
        # Process person nodes with progress bar
        print("\nGenerating edges...")
        for _, person in tqdm(person_nodes.iterrows(), total=len(person_nodes)):
            person_id = person['node_id']
            
            # Generate edges for this person
            for edges_batch, missing_nodes in generate_edges_for_person(person_id, node_df, node_sets):
                all_edges.extend(edges_batch)
                all_missing_nodes.update(missing_nodes)
                total_edges += len(edges_batch)
                
                # Save progress periodically
                if len(all_edges) >= 10000:
                    # Create DataFrame and save
                    edge_df = pd.DataFrame(all_edges)
                    edge_df.to_csv('person_edges.csv', mode='a', header=not total_edges, index=False)
                    all_edges = []  # Clear the list after saving
        
        # Save any remaining edges
        if all_edges:
            edge_df = pd.DataFrame(all_edges)
            edge_df.to_csv('person_edges.csv', mode='a', header=not total_edges, index=False)
        
        # Print warning if any missing nodes were found
        if all_missing_nodes:
            print(f"\nWarning: Found {len(all_missing_nodes)} nodes referenced in edges that don't exist in node_data.csv")
            print("These edges were not created to maintain referential integrity.")
        
        # Print final statistics
        print("\nEdge Generation Statistics:")
        print(f"Total number of edges generated: {total_edges}")
        
        # Read the final edge file to get edge type distribution
        final_edge_df = pd.read_csv('person_edges.csv')
        print("\nEdge Types Distribution:")
        edge_counts = final_edge_df['edge_type'].value_counts()
        for edge_type, count in edge_counts.items():
            print(f"{edge_type}: {count} edges")
        
        return final_edge_df
        
    except Exception as e:
        print(f"Error generating edges: {str(e)}")
        return None

if __name__ == "__main__":
    edge_df = generate_person_edges()
    if edge_df is not None:
        print("\nSample of Generated Edges:")
        print(edge_df.head()) 