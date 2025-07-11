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
            'anumber': {'total': 0, 'valid': 0}
        },
        'edges_per_person': {}  # New field to track edges per person
    }
    
    # Get sets of valid node IDs for quick lookup
    valid_node_ids = set(node_df['node_id'].values)
    person_node_ids = set(node_df[node_df['node_type'] == 'person']['node_id'].values)
    anumber_node_ids = set(node_df[node_df['node_type'] == 'anumber']['node_id'].values)
    
    # Initialize edges_per_person counter
    for person_id in person_node_ids:
        validation_results['edges_per_person'][person_id] = 0
    
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
        to_node_is_anumber = to_node in anumber_node_ids
        
        if from_node_exists and to_node_exists and from_node_is_person and to_node_is_anumber:
            validation_results['valid_edges'] += 1
            validation_results['node_type_stats']['person']['valid'] += 1
            validation_results['node_type_stats']['anumber']['valid'] += 1
            validation_results['edges_per_person'][from_node] += 1
        else:
            validation_results['invalid_edges'] += 1
            if not from_node_exists or not from_node_is_person:
                validation_results['missing_from_nodes'].add(from_node)
            if not to_node_exists or not to_node_is_anumber:
                validation_results['missing_to_nodes'].add(to_node)
    
    # Update total counts
    validation_results['node_type_stats']['person']['total'] = len(person_node_ids)
    validation_results['node_type_stats']['anumber']['total'] = len(anumber_node_ids)
    
    return validation_results

def process_person_batch(batch_data):
    """Process a batch of persons to generate anumber edges"""
    person_ids, anumber_ids, batch_start_idx = batch_data
    batch_edges = []
    used_pairs = set()
    
    for i, person_id in enumerate(person_ids):
        # Get available anumbers that haven't been used with this person
        available_anumbers = [anumber_id for anumber_id in anumber_ids 
                            if (person_id, anumber_id) not in used_pairs]
        
        # If no available anumbers, reuse some (ensures every person gets at least 1 edge)
        if len(available_anumbers) == 0:
            available_anumbers = anumber_ids.copy()
        
        # Most people have 1 A-Number, some have 2 (primary and secondary)
        num_anumber_edges = random.choices([1, 2], weights=[0.8, 0.2])[0]
        num_anumber_edges = min(num_anumber_edges, len(available_anumbers))
        
        # Randomly select anumbers without replacement
        selected_anumbers = random.sample(available_anumbers, num_anumber_edges)
        
        # First anumber is always PRIMARY
        first_anumber = True
        for anumber_id in selected_anumbers:
            # Add to used pairs
            pair_key = (person_id, anumber_id)
            used_pairs.add(pair_key)
            
            # Determine anumber type
            if first_anumber:
                anumber_type = 'PRIMARY'
                first_anumber = False
            else:
                anumber_type = 'SECONDARY'
            
            batch_edges.append({
                'edge_id': str(uuid.uuid4()),
                'node_id_from': person_id,
                'node_id_to': anumber_id,
                'edge_type': 'person_anumber',
                'edge_properties': {
                    'ANUMBER_TYPE': anumber_type,
                    'ISSUE_DATE': None,  # Could be populated with realistic dates if needed
                    'STATUS': random.choice(["ACTIVE", "INACTIVE", "PENDING"])
                }
            })
    
    return batch_edges

def generate_person_anumber_edges():
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
        
        # Get person nodes and convert to list for faster access
        person_nodes = node_df[node_df['node_type'] == 'person']
        if person_nodes.empty:
            print("Warning: No person nodes found in node_data.csv")
            return None
        
        # Get anumber nodes and convert to list for faster access
        anumber_nodes = node_df[node_df['node_type'] == 'anumber']
        if anumber_nodes.empty:
            print("Warning: No anumber nodes found in node_data.csv")
            return None
        
        print(f"\nFound {len(person_nodes)} person nodes and {len(anumber_nodes)} anumber nodes")
        
        # Convert to lists and sets for faster operations
        person_ids = person_nodes['node_id'].tolist()
        anumber_ids = anumber_nodes['node_id'].tolist()
        
        # Initialize edge data and counters
        edges = []
        edge_type_count = 0
        anumber_type_stats = {'PRIMARY': 0, 'SECONDARY': 0}
        
        # Optimized batch processing with multiprocessing
        print("\nGenerating person_anumber edges with optimized processing...")
        
        # Calculate optimal batch size based on data size
        total_persons = len(person_ids)
        num_cores = mp.cpu_count()
        batch_size = max(1, total_persons // (num_cores * 2))  # Larger batches for better performance
        
        print(f"Using {num_cores} CPU cores with batch size of {batch_size}")
        
        # Create batches
        batches = []
        for i in range(0, total_persons, batch_size):
            batch_end = min(i + batch_size, total_persons)
            batch_person_ids = person_ids[i:batch_end]
            batches.append((batch_person_ids, anumber_ids, i))
        
        # Process batches in parallel
        with ThreadPoolExecutor(max_workers=num_cores) as executor:
            # Submit all batches
            future_to_batch = {executor.submit(process_person_batch, batch): batch for batch in batches}
            
            # Collect results with progress bar
            for future in tqdm(as_completed(future_to_batch), total=len(batches), desc="Processing batches"):
                batch_edges = future.result()
                edges.extend(batch_edges)
                edge_type_count += len(batch_edges)
        
        # Count anumber types for statistics
        for edge in edges:
            anumber_type = edge['edge_properties']['ANUMBER_TYPE']
            anumber_type_stats[anumber_type] += 1
        
        # Save all edges as a single JSON array
        os.makedirs('src/data/output/gds', exist_ok=True)
        with open('src/data/output/gds/mock_person-anumber_data.json', 'w') as f:
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
        
        print("\nDistribution of A-Number Edges per Person:")
        for count in sorted(edges_per_person_dist.keys()):
            print(f"Persons with {count} anumber edges: {edges_per_person_dist[count]}")
        
        # Print anumber type statistics
        print("\nA-Number Type Distribution:")
        for anumber_type, count in anumber_type_stats.items():
            print(f"{anumber_type}: {count} edges")
        
        # Print processing statistics
        print(f"\nProcessing Statistics:")
        print(f"Total processing time: {processing_time:.2f} seconds")
        print(f"Edges generated per second: {edge_type_count / processing_time:.2f}")
        print(f"Average edges per person: {edge_type_count / len(person_ids):.2f}")
        
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
        print(f"Error generating person-anumber edges: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    generate_person_anumber_edges()
