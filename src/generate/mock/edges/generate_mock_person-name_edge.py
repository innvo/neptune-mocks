import pandas as pd
import uuid
import random
from tqdm import tqdm
import time
import os
import json

def validate_node_existence(node_df, node_id):
    """Validate that a node exists in the node_data.csv"""
    return node_id in node_df['node_id'].values

def generate_person_name_edges():
    try:
        start_time = time.time()
        
        # Read node_data.csv, excluding node_name column
        print("Reading node data...")
        node_df = pd.read_csv('src/data/input/node_data.csv', usecols=['node_id', 'node_type'])
        
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
        
        # Get name nodes
        name_nodes = node_df[node_df['node_type'] == 'name']
        if name_nodes.empty:
            print("Warning: No name nodes found in node_data.csv")
            return None
        
        # Initialize edge data and counters
        edges = []
        missing_nodes = set()
        edge_type_count = 0
        
        # Generate edges for each person with progress bar
        print("\nGenerating person_name edges...")
        for _, person in tqdm(person_nodes.iterrows(), total=len(person_nodes), desc="Processing person nodes"):
            person_id = person['node_id']
            
            # Ensure each person has at least 1 name edge
            num_name_edges = random.randint(1, min(3, len(name_nodes)))
            selected_names = name_nodes.sample(n=num_name_edges)
            
            for _, name in selected_names.iterrows():
                name_id = name['node_id']
                if validate_node_existence(node_df, name_id):
                    edges.append({
                        'edge_id': str(uuid.uuid4()),
                        'node_id_from': person_id,
                        'node_id_to': name_id,
                        'edge_type': 'person_name'
                    })
                    edge_type_count += 1
                else:
                    missing_nodes.add(name_id)
        
        # Save all edges as a single JSON array
        os.makedirs('src/data/output/gds', exist_ok=True)
        with open('src/data/output/gds/mock_person-name_data.json', 'w') as f:
            json.dump(edges, f, indent=2)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Print warning if any missing nodes were found
        if missing_nodes:
            print(f"\nWarning: Found {len(missing_nodes)} nodes referenced in edges that don't exist in node_data.csv")
            print("These edges were not created to maintain referential integrity.")
        
        # Print detailed edge statistics
        print("\nEdge Generation Statistics:")
        print(f"Total number of person_name edges generated: {edge_type_count}")
        print(f"Processing time: {processing_time:.2f} seconds")
        print(f"Edges per second: {edge_type_count / processing_time:.2f}")
        
        # Read the final edge file to get the complete DataFrame
        with open('src/data/output/gds/mock_person-name_data.json', 'r') as f:
            edges_data = json.load(f)
        final_edge_df = pd.DataFrame(edges_data)
        return final_edge_df
        
    except Exception as e:
        print(f"Error generating edges: {str(e)}")
        return None

if __name__ == "__main__":
    edge_df = generate_person_name_edges()
    if edge_df is not None:
        print("\nSample of Generated Edges:")
        print(edge_df.head()) 