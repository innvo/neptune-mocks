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

def validate_referential_integrity(edges, node_df):
    """Validate referential integrity of edges against node data"""
    validation_results = {
        'total_edges': len(edges),
        'valid_edges': 0,
        'invalid_edges': 0,
        'missing_from_nodes': set(),
        'missing_to_nodes': set(),
        'edge_type_stats': {},
        'node_type_stats': {
            'person': {'total': 0, 'valid': 0},
            'name': {'total': 0, 'valid': 0}
        }
    }
    
    # Get sets of valid node IDs for quick lookup
    valid_node_ids = set(node_df['node_id'].values)
    person_node_ids = set(node_df[node_df['node_type'] == 'person']['node_id'].values)
    name_node_ids = set(node_df[node_df['node_type'] == 'name']['node_id'].values)
    
    for edge in edges:
        from_node = edge['node_id_from']
        to_node = edge['node_id_to']
        edge_type = edge['edge_type']
        
        # Count edge types
        validation_results['edge_type_stats'][edge_type] = validation_results['edge_type_stats'].get(edge_type, 0) + 1
        
        # Validate node existence
        from_node_exists = from_node in valid_node_ids
        to_node_exists = to_node in valid_node_ids
        
        # Validate node types
        from_node_is_person = from_node in person_node_ids
        to_node_is_name = to_node in name_node_ids
        
        if from_node_exists and to_node_exists and from_node_is_person and to_node_is_name:
            validation_results['valid_edges'] += 1
            validation_results['node_type_stats']['person']['valid'] += 1
            validation_results['node_type_stats']['name']['valid'] += 1
        else:
            validation_results['invalid_edges'] += 1
            if not from_node_exists or not from_node_is_person:
                validation_results['missing_from_nodes'].add(from_node)
            if not to_node_exists or not to_node_is_name:
                validation_results['missing_to_nodes'].add(to_node)
    
    # Update total counts
    validation_results['node_type_stats']['person']['total'] = len(person_node_ids)
    validation_results['node_type_stats']['name']['total'] = len(name_node_ids)
    
    return validation_results

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
        name_type_stats = {'PRIMARY': 0, 'OTHER': 0, 'ALIAS': 0}
        
        # Generate edges for each person with progress bar
        print("\nGenerating person_name edges...")
        for _, person in tqdm(person_nodes.iterrows(), total=len(person_nodes), desc="Processing person nodes"):
            person_id = person['node_id']
            
            # Ensure each person has at least 1 name edge
            num_name_edges = random.randint(1, min(3, len(name_nodes)))
            selected_names = name_nodes.sample(n=num_name_edges)
            
            # First name is always PRIMARY
            first_name = True
            for _, name in selected_names.iterrows():
                name_id = name['node_id']
                if validate_node_existence(node_df, name_id):
                    # Determine name type
                    if first_name:
                        name_type = 'PRIMARY'
                        first_name = False
                    else:
                        name_type = random.choice(['OTHER', 'ALIAS'])
                    
                    edges.append({
                        'edge_id': str(uuid.uuid4()),
                        'node_id_from': person_id,
                        'node_id_to': name_id,
                        'edge_type': 'person_name',
                        'edge_properties': {
                            'NAME_TYPE': name_type
                        }
                    })
                    edge_type_count += 1
                    name_type_stats[name_type] += 1
                else:
                    missing_nodes.add(name_id)
        
        # Save all edges as a single JSON array
        os.makedirs('src/data/output/gds', exist_ok=True)
        with open('src/data/output/gds/mock_person-name_data.json', 'w') as f:
            json.dump(edges, f, indent=2)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Validate referential integrity
        validation_results = validate_referential_integrity(edges, node_df)
        
        # Print validation results
        print("\nReferential Integrity Validation Results:")
        print(f"Total edges generated: {validation_results['total_edges']}")
        print(f"Valid edges: {validation_results['valid_edges']}")
        print(f"Invalid edges: {validation_results['invalid_edges']}")
        
        if validation_results['missing_from_nodes']:
            print(f"\nMissing or invalid person nodes: {len(validation_results['missing_from_nodes'])}")
            print("Sample of missing person nodes:", list(validation_results['missing_from_nodes'])[:5])
        
        if validation_results['missing_to_nodes']:
            print(f"\nMissing or invalid name nodes: {len(validation_results['missing_to_nodes'])}")
            print("Sample of missing name nodes:", list(validation_results['missing_to_nodes'])[:5])
        
        print("\nNode Type Statistics:")
        for node_type, stats in validation_results['node_type_stats'].items():
            print(f"\n{node_type.capitalize()} Nodes:")
            print(f"  Total: {stats['total']}")
            print(f"  Used in valid edges: {stats['valid']}")
        
        print("\nName Type Statistics:")
        for name_type, count in name_type_stats.items():
            print(f"{name_type}: {count} edges")
        
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