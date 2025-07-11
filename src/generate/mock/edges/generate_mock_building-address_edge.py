import pandas as pd
import uuid
import random
from tqdm import tqdm
import time
import os
import json
import platform
import subprocess
import numpy as np
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing as mp
from functools import partial

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
    
    # Create address hash mapping for validation
    address_id_to_hash = {}
    for _, address in address_df.iterrows():
        address_id = address['node_id']
        address_hash = address['node_properties']['ADDRESS_HASH']
        address_id_to_hash[address_id] = address_hash
    
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
            address_hash = address_id_to_hash.get(to_node)
            
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

def process_building_batch(batch_data):
    """Process a batch of buildings to generate address edges"""
    building_ids, building_hashes, address_hash_to_ids, batch_start_idx = batch_data
    batch_edges = []
    missing_address_hashes = set()
    
    for i, building_id in enumerate(building_ids):
        building_address_hash = building_hashes[i]
        
        # Find matching addresses by ADDRESS_HASH
        matching_address_ids = address_hash_to_ids.get(building_address_hash, [])
        
        if matching_address_ids:
            # Each building can have multiple addresses (e.g., unit numbers, suites)
            for address_id in matching_address_ids:
                batch_edges.append({
                    'edge_id': str(uuid.uuid4()),
                    'node_id_from': building_id,
                    'node_id_to': address_id,
                    'edge_type': 'building_address',
                    'edge_properties': {}
                })
        else:
            missing_address_hashes.add(building_address_hash)
    
    return batch_edges, missing_address_hashes

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
        
        # Convert to lists for faster access
        building_ids = building_df['node_id'].tolist()
        building_hashes = [building['node_properties']['ADDRESS_HASH'] for building in building_data]
        
        # Initialize edge data and counters
        edges = []
        missing_address_hashes = set()
        edge_type_count = 0
        
        # Optimized batch processing with multiprocessing
        print("\nGenerating building_address edges with optimized processing...")
        
        # Calculate optimal batch size based on data size
        total_buildings = len(building_ids)
        num_cores = mp.cpu_count()
        batch_size = max(1, total_buildings // (num_cores * 2))  # Larger batches for better performance
        
        print(f"Using {num_cores} CPU cores with batch size of {batch_size}")
        
        # Create batches
        batches = []
        for i in range(0, total_buildings, batch_size):
            batch_end = min(i + batch_size, total_buildings)
            batch_building_ids = building_ids[i:batch_end]
            batch_building_hashes = building_hashes[i:batch_end]
            batches.append((batch_building_ids, batch_building_hashes, address_hash_to_ids, i))
        
        # Process batches in parallel
        with ThreadPoolExecutor(max_workers=num_cores) as executor:
            # Submit all batches
            future_to_batch = {executor.submit(process_building_batch, batch): batch for batch in batches}
            
            # Collect results with progress bar
            for future in tqdm(as_completed(future_to_batch), total=len(batches), desc="Processing batches"):
                batch_edges, batch_missing_hashes = future.result()
                edges.extend(batch_edges)
                edge_type_count += len(batch_edges)
                missing_address_hashes.update(batch_missing_hashes)
        
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
        
        # Print processing statistics
        print(f"\nProcessing Statistics:")
        print(f"Total processing time: {processing_time:.2f} seconds")
        print(f"Edges generated per second: {edge_type_count / processing_time:.2f}")
        print(f"Average edges per building: {edge_type_count / len(building_ids):.2f}")
        
        if missing_address_hashes:
            print(f"\nBuildings with missing address hash matches: {len(missing_address_hashes)}")
            print("Sample of missing address hashes:", list(missing_address_hashes)[:5])
        
        if validation_results['invalid_edges'] > 0:
            print(f"\nWARNING: {validation_results['invalid_edges']} invalid edges detected!")
            if validation_results['missing_from_nodes']:
                print(f"Missing from nodes: {len(validation_results['missing_from_nodes'])}")
            if validation_results['missing_to_nodes']:
                print(f"Missing to nodes: {len(validation_results['missing_to_nodes'])}")
        else:
            print("\n✓ All edges are valid!")
        
        return edges
        
    except Exception as e:
        print(f"Error generating building-address edges: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    generate_building_address_edges()
