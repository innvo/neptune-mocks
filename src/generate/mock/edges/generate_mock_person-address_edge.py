import pandas as pd
import uuid
import random
from tqdm import tqdm
import time
import os
import json
import platform
import subprocess

def clear_terminal():
    """Clear the terminal screen based on the operating system"""
    if platform.system() == 'Windows':
        os.system('cls')
    else:
        os.system('clear')

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
            'address': {'total': 0, 'valid': 0}
        },
        'edges_per_person': {},  # Track edges per person
        'edges_per_address': {}  # Track edges per address
    }
    
    # Get sets of valid node IDs for quick lookup
    valid_node_ids = set(node_df['node_id'].values)
    person_node_ids = set(node_df[node_df['node_type'] == 'person']['node_id'].values)
    address_node_ids = set(node_df[node_df['node_type'] == 'address']['node_id'].values)
    
    # Initialize counters
    for person_id in person_node_ids:
        validation_results['edges_per_person'][person_id] = 0
    for address_id in address_node_ids:
        validation_results['edges_per_address'][address_id] = 0
    
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
        to_node_is_address = to_node in address_node_ids
        
        if from_node_exists and to_node_exists and from_node_is_person and to_node_is_address:
            validation_results['valid_edges'] += 1
            validation_results['node_type_stats']['person']['valid'] += 1
            validation_results['node_type_stats']['address']['valid'] += 1
            validation_results['edges_per_person'][from_node] += 1
            validation_results['edges_per_address'][to_node] += 1
        else:
            validation_results['invalid_edges'] += 1
            if not from_node_exists or not from_node_is_person:
                validation_results['missing_from_nodes'].add(from_node)
            if not to_node_exists or not to_node_is_address:
                validation_results['missing_to_nodes'].add(to_node)
    
    # Update total counts
    validation_results['node_type_stats']['person']['total'] = len(person_node_ids)
    validation_results['node_type_stats']['address']['total'] = len(address_node_ids)
    
    return validation_results

def generate_person_address_edges():
    try:
        clear_terminal()
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
        
        # Get address nodes
        address_nodes = node_df[node_df['node_type'] == 'address']
        if address_nodes.empty:
            print("Warning: No address nodes found in node_data.csv")
            return None
        
        # Initialize edge data and counters
        edges = []
        missing_nodes = set()
        edge_type_count = 0
        address_type_stats = {'PRIMARY': 0, 'SECONDARY': 0, 'TERTIARY': 0}
        
        # Track address usage to ensure we don't exceed the 1-3 people per address limit
        address_usage = {addr_id: 0 for addr_id in address_nodes['node_id']}
        
        # Generate edges for each person with progress bar
        print("\nGenerating person_address edges...")
        for _, person in tqdm(person_nodes.iterrows(), total=len(person_nodes), desc="Processing person nodes"):
            person_id = person['node_id']
            
            # Filter addresses that haven't reached their maximum usage
            available_addresses = address_nodes[address_nodes['node_id'].apply(lambda x: address_usage[x] < 3)]
            
            if len(available_addresses) == 0:
                print(f"Warning: No available addresses for person {person_id}")
                continue
            
            # Ensure each person has 1-3 address edges
            num_address_edges = random.randint(1, min(3, len(available_addresses)))
            selected_addresses = available_addresses.sample(n=num_address_edges)
            
            # First address is always PRIMARY
            first_address = True
            for _, address in selected_addresses.iterrows():
                address_id = address['node_id']
                if validate_node_existence(node_df, address_id):
                    # Determine address type
                    if first_address:
                        address_type = 'PRIMARY'
                        first_address = False
                    else:
                        address_type = random.choice(['SECONDARY', 'TERTIARY'])
                    
                    edges.append({
                        'edge_id': str(uuid.uuid4()),
                        'node_id_from': person_id,
                        'node_id_to': address_id,
                        'edge_type': 'person_address',
                        'edge_properties': {
                            'ADDRESS_TYPE': address_type
                        }
                    })
                    edge_type_count += 1
                    address_type_stats[address_type] += 1
                    address_usage[address_id] += 1
                else:
                    missing_nodes.add(address_id)
        
        # Save all edges as a single JSON array
        os.makedirs('src/data/output/gds', exist_ok=True)
        with open('src/data/output/gds/mock_person-address_data.json', 'w') as f:
            json.dump(edges, f, indent=2)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Validate referential integrity
        validation_results = validate_referential_integrity(edges, node_df)
        
        clear_terminal()
        # Print validation results
        print("\nReferential Integrity Validation Results:")
        print(f"Total edges generated: {validation_results['total_edges']}")
        print(f"Valid edges: {validation_results['valid_edges']}")
        print(f"Invalid edges: {validation_results['invalid_edges']}")
        
        # Calculate and display edges per person distribution
        edges_per_person_dist = {}
        for person_id, count in validation_results['edges_per_person'].items():
            edges_per_person_dist[count] = edges_per_person_dist.get(count, 0) + 1
        
        print("\nDistribution of Address Edges per Person:")
        for count in sorted(edges_per_person_dist.keys()):
            print(f"Persons with {count} address edges: {edges_per_person_dist[count]}")
        
        # Calculate and display edges per address distribution
        edges_per_address_dist = {}
        for address_id, count in validation_results['edges_per_address'].items():
            edges_per_address_dist[count] = edges_per_address_dist.get(count, 0) + 1
        
        print("\nDistribution of People per Address:")
        for count in sorted(edges_per_address_dist.keys()):
            print(f"Addresses with {count} people: {edges_per_address_dist[count]}")
        
        if validation_results['missing_from_nodes']:
            print(f"\nMissing or invalid person nodes: {len(validation_results['missing_from_nodes'])}")
            print("Sample of missing person nodes:", list(validation_results['missing_from_nodes'])[:5])
        
        if validation_results['missing_to_nodes']:
            print(f"\nMissing or invalid address nodes: {len(validation_results['missing_to_nodes'])}")
            print("Sample of missing address nodes:", list(validation_results['missing_to_nodes'])[:5])
        
        print("\nNode Type Statistics:")
        for node_type, stats in validation_results['node_type_stats'].items():
            print(f"\n{node_type.capitalize()} Nodes:")
            print(f"  Total: {stats['total']}")
            print(f"  Used in valid edges: {stats['valid']}")
        
        print("\nAddress Type Statistics:")
        for address_type, count in address_type_stats.items():
            print(f"{address_type}: {count} edges")
        
        print("\nEdge Generation Statistics:")
        print(f"Total number of person_address edges generated: {edge_type_count}")
        print(f"Processing time: {processing_time:.2f} seconds")
        print(f"Edges per second: {edge_type_count / processing_time:.2f}")
        
        # Read the final edge file to get the complete DataFrame
        with open('src/data/output/gds/mock_person-address_data.json', 'r') as f:
            edges_data = json.load(f)
        final_edge_df = pd.DataFrame(edges_data)
        return final_edge_df
        
    except Exception as e:
        print(f"Error generating edges: {str(e)}")
        return None

if __name__ == "__main__":
    edge_df = generate_person_address_edges()
    if edge_df is not None:
        print("\nSample of Generated Edges:")
        print(edge_df.head()) 