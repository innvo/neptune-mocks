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

def validate_referential_integrity(edges, building_df, address_df):
    """Validate referential integrity of edges against building and address data"""
    validation_results = {
        'total_edges': len(edges),
        'valid_edges': 0,
        'invalid_edges': 0,
        'missing_from_nodes': set(),
        'missing_to_nodes': set(),
        'edge_type_stats': {},
        'node_type_stats': {
            'building': {'total': 0, 'valid': 0},
            'address': {'total': 0, 'valid': 0}
        },
        'edges_per_building': {},  # Track edges per building
        'address_hash_matches': 0,
        'address_hash_mismatches': 0
    }
    
    # Get sets of valid node IDs for quick lookup
    valid_building_ids = set(building_df['node_id'].values)
    valid_address_ids = set(address_df['node_id'].values)
    
    # Create address hash mapping for validation
    building_address_hashes = {}
    for _, building in building_df.iterrows():
        building_id = building['node_id']
        address_hash = building['node_properties']['ADDRESS_HASH']
        building_address_hashes[building_id] = address_hash
        validation_results['edges_per_building'][building_id] = 0
    
    address_hash_to_id = {}
    for _, address in address_df.iterrows():
        address_id = address['node_id']
        address_hash = address['node_properties']['ADDRESS_HASH']
        address_hash_to_id[address_hash] = address_id
    
    # Update total counts
    validation_results['node_type_stats']['building']['total'] = len(valid_building_ids)
    validation_results['node_type_stats']['address']['total'] = len(valid_address_ids)
    
    for edge in edges:
        from_node = edge['node_id_from']
        to_node = edge['node_id_to']
        edge_type = edge['edge_type']
        
        # Count edge types
        validation_results['edge_type_stats'][edge_type] = validation_results['edge_type_stats'].get(edge_type, 0) + 1
        
        # Validate node existence
        from_node_exists = from_node in valid_building_ids
        to_node_exists = to_node in valid_address_ids
        
        # Validate address hash match
        address_hash_match = False
        if from_node_exists and to_node_exists:
            building_hash = building_address_hashes.get(from_node)
            address_hash = None
            for _, address in address_df.iterrows():
                if address['node_id'] == to_node:
                    address_hash = address['node_properties']['ADDRESS_HASH']
                    break
            
            if building_hash and address_hash and building_hash == address_hash:
                address_hash_match = True
                validation_results['address_hash_matches'] += 1
            else:
                validation_results['address_hash_mismatches'] += 1
        
        if from_node_exists and to_node_exists and address_hash_match:
            validation_results['valid_edges'] += 1
            validation_results['node_type_stats']['building']['valid'] += 1
            validation_results['node_type_stats']['address']['valid'] += 1
            validation_results['edges_per_building'][from_node] += 1
        else:
            validation_results['invalid_edges'] += 1
            if not from_node_exists:
                validation_results['missing_from_nodes'].add(from_node)
            if not to_node_exists:
                validation_results['missing_to_nodes'].add(to_node)
    
    return validation_results

def generate_building_address_edges():
    try:
        clear_terminal()
        start_time = time.time()
        
        # Read building and address data
        print("Reading building and address data...")
        with open('src/data/output/gds/mock_building_data.json', 'r') as f:
            building_data = json.load(f)
        
        with open('src/data/output/gds/mock_address_data.json', 'r') as f:
            address_data = json.load(f)
        
        building_df = pd.DataFrame(building_data)
        address_df = pd.DataFrame(address_data)
        
        # Print data statistics
        print(f"\nData Statistics:")
        print(f"Total number of buildings: {len(building_df)}")
        print(f"Total number of addresses: {len(address_df)}")
        
        # Create address hash mapping for quick lookup
        print("\nCreating address hash mapping...")
        address_hash_to_ids = {}
        for _, address in address_df.iterrows():
            address_hash = address['node_properties']['ADDRESS_HASH']
            if address_hash not in address_hash_to_ids:
                address_hash_to_ids[address_hash] = []
            address_hash_to_ids[address_hash].append(address['node_id'])
        
        print(f"Unique address hashes: {len(address_hash_to_ids)}")
        
        # Initialize edge data and counters
        edges = []
        missing_address_hashes = set()
        edge_type_count = 0
        
        # Generate edges for each building with progress bar
        print("\nGenerating building_address edges...")
        for _, building in tqdm(building_df.iterrows(), total=len(building_df), desc="Processing building nodes"):
            building_id = building['node_id']
            building_address_hash = building['node_properties']['ADDRESS_HASH']
            
            # Find matching addresses by ADDRESS_HASH
            matching_address_ids = address_hash_to_ids.get(building_address_hash, [])
            
            if matching_address_ids:
                # Each building can have multiple addresses (e.g., unit numbers, suites)
                for address_id in matching_address_ids:
                    edges.append({
                        'edge_id': str(uuid.uuid4()),
                        'node_id_from': building_id,
                        'node_id_to': address_id,
                        'edge_type': 'building_address',
                        'edge_properties': {}
                    })
                    edge_type_count += 1
            else:
                missing_address_hashes.add(building_address_hash)
        
        # Save all edges as a single JSON array
        os.makedirs('src/data/output/gds', exist_ok=True)
        with open('src/data/output/gds/mock_building-address_data.json', 'w') as f:
            json.dump(edges, f, indent=2)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Validate referential integrity
        validation_results = validate_referential_integrity(edges, building_df, address_df)
        
        clear_terminal()
        # Print validation results
        print("\nReferential Integrity Validation Results:")
        print(f"Total edges generated: {validation_results['total_edges']}")
        print(f"Valid edges: {validation_results['valid_edges']}")
        print(f"Invalid edges: {validation_results['invalid_edges']}")
        print(f"Address hash matches: {validation_results['address_hash_matches']}")
        print(f"Address hash mismatches: {validation_results['address_hash_mismatches']}")
        
        # Calculate and display edges per building distribution
        edges_per_building_dist = {}
        for building_id, count in validation_results['edges_per_building'].items():
            edges_per_building_dist[count] = edges_per_building_dist.get(count, 0) + 1
        
        print("\nDistribution of Address Edges per Building:")
        for count in sorted(edges_per_building_dist.keys()):
            print(f"Buildings with {count} address edges: {edges_per_building_dist[count]}")
        
        if validation_results['missing_from_nodes']:
            print(f"\nMissing or invalid building nodes: {len(validation_results['missing_from_nodes'])}")
            print("Sample of missing building nodes:", list(validation_results['missing_from_nodes'])[:5])
        
        if validation_results['missing_to_nodes']:
            print(f"\nMissing or invalid address nodes: {len(validation_results['missing_to_nodes'])}")
            print("Sample of missing address nodes:", list(validation_results['missing_to_nodes'])[:5])
        
        if missing_address_hashes:
            print(f"\nBuildings with missing address hash matches: {len(missing_address_hashes)}")
            print("Sample of missing address hashes:", list(missing_address_hashes)[:5])
        
        print("\nNode Type Statistics:")
        for node_type, stats in validation_results['node_type_stats'].items():
            print(f"\n{node_type.capitalize()} Nodes:")
            print(f"  Total: {stats['total']}")
            print(f"  Used in valid edges: {stats['valid']}")
        
        print("\nEdge Generation Statistics:")
        print(f"Total number of building_address edges generated: {edge_type_count}")
        print(f"Processing time: {processing_time:.2f} seconds")
        print(f"Edges per second: {edge_type_count / processing_time:.2f}")
        
        # Read the final edge file to get the complete DataFrame
        with open('src/data/output/gds/mock_building-address_data.json', 'r') as f:
            edges_data = json.load(f)
        final_edge_df = pd.DataFrame(edges_data)
        return final_edge_df
        
    except Exception as e:
        print(f"Error generating edges: {str(e)}")
        return None

if __name__ == "__main__":
    edge_df = generate_building_address_edges()
    if edge_df is not None:
        print("\nSample of Generated Edges:")
        print(edge_df.head())
