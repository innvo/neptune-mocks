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

def validate_node_existence(valid_node_ids, node_id):
    """Validate that a node exists in the node_data.csv"""
    return node_id in valid_node_ids

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
            'datainstance': {'total': 0, 'valid': 0}
        },
        'edges_per_person': {},  # New field to track edges per person
        'persons_with_no_edges': 0,  # Track persons without any datainstance edges
        'persons_with_too_many_edges': 0  # Track persons with more than 10 datainstance edges
    }
    
    # Get sets of valid node IDs for quick lookup
    valid_node_ids = set(node_df['node_id'].values)
    person_node_ids = set(node_df[node_df['node_type'] == 'person']['node_id'].values)
    datainstance_node_ids = set(node_df[node_df['node_type'] == 'datainstance']['node_id'].values)
    
    # Initialize edges_per_person counter
    for person_id in person_node_ids:
        validation_results['edges_per_person'][person_id] = 0
    
    # Use Counter for faster edge type counting
    edge_type_counter = Counter()
    
    for edge in edges:
        from_node = edge['node_id_from']
        to_node = edge['node_id_to']
        edge_type = edge['edge_type']
        
        # Count edge types
        edge_type_counter[edge_type] += 1
        
        # Validate node existence and types in one check
        from_node_valid = from_node in person_node_ids
        to_node_valid = to_node in datainstance_node_ids
        
        if from_node_valid and to_node_valid:
            validation_results['valid_edges'] += 1
            validation_results['node_type_stats']['person']['valid'] += 1
            validation_results['node_type_stats']['datainstance']['valid'] += 1
            validation_results['edges_per_person'][from_node] += 1
        else:
            validation_results['invalid_edges'] += 1
            if not from_node_valid:
                validation_results['missing_from_nodes'].add(from_node)
            if not to_node_valid:
                validation_results['missing_to_nodes'].add(to_node)
    
    # Convert Counter to dict for compatibility
    validation_results['edge_type_stats'] = dict(edge_type_counter)
    
    # Count persons with no edges and too many edges
    for person_id in person_node_ids:
        edge_count = validation_results['edges_per_person'][person_id]
        if edge_count == 0:
            validation_results['persons_with_no_edges'] += 1
        elif edge_count > 10:
            validation_results['persons_with_too_many_edges'] += 1
    
    # Update total counts
    validation_results['node_type_stats']['person']['total'] = len(person_node_ids)
    validation_results['node_type_stats']['datainstance']['total'] = len(datainstance_node_ids)
    
    return validation_results

def process_person_batch(batch_data):
    """Process a batch of persons to generate datainstance edges"""
    person_ids, datainstance_ids, edge_counts, batch_start_idx = batch_data
    batch_edges = []
    used_pairs = set()
    
    for i, person_id in enumerate(person_ids):
        # Get available datainstances that haven't been used with this person
        available_datainstances = [datainstance_id for datainstance_id in datainstance_ids 
                                 if (person_id, datainstance_id) not in used_pairs]
        
        # If no available datainstances, reuse some (ensures every person gets at least 1 edge)
        if len(available_datainstances) == 0:
            available_datainstances = datainstance_ids.copy()
        
        # Use pre-generated edge count for this person
        num_datainstance_edges = edge_counts[batch_start_idx + i]
        
        # Limit the number of edges to available datainstances (minimum 1, maximum 10)
        num_datainstance_edges = max(1, min(num_datainstance_edges, len(available_datainstances), 10))
        
        # Randomly select datainstances without replacement
        selected_datainstances = random.sample(available_datainstances, num_datainstance_edges)
        
        for datainstance_id in selected_datainstances:
            # Add to used pairs
            pair_key = (person_id, datainstance_id)
            used_pairs.add(pair_key)
            
            # Determine datainstance type
            datainstance_type = random.choice(["SERVICEPROVIDER", "STAKEHOLDER"])
            
            batch_edges.append({
                'edge_id': str(uuid.uuid4()),
                'node_id_from': person_id,
                'node_id_to': datainstance_id,
                'edge_type': 'person_datainstance',
                'edge_properties': {
                    'CONFIDENCE_SCORE': round(random.uniform(0.1, 1.0), 2)
                }
            })
    
    return batch_edges

def generate_person_datainstance_edges():
    """
    Generate person-datainstance edges with the following requirements:
    - Every person must have at least 1 datainstance edge
    - Every person can have up to 10 datainstance edges
    - Distribution is weighted to favor fewer edges (1-3 most common)
    """
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
        
        # Get datainstance nodes and convert to list for faster access
        datainstance_nodes = node_df[node_df['node_type'] == 'datainstance']
        if datainstance_nodes.empty:
            print("Warning: No datainstance nodes found in node_data.csv")
            print("Note: You may need to add 'datainstance' to NODE_TYPES in generate_node_data.py")
            return None
        
        print(f"\nFound {len(person_nodes)} person nodes and {len(datainstance_nodes)} datainstance nodes")
        
        # Check if we have enough datainstance nodes for all persons
        if len(datainstance_nodes) < len(person_nodes):
            print(f"\nWARNING: Only {len(datainstance_nodes)} datainstance nodes available for {len(person_nodes)} persons")
            print("This means some datainstance nodes will be shared across multiple persons")
        
        # Convert to lists and sets for faster operations
        person_ids = person_nodes['node_id'].tolist()
        datainstance_ids = datainstance_nodes['node_id'].tolist()
        valid_node_ids = set(node_df['node_id'].values)
        
        # Pre-generate edge counts for all persons using numpy for speed
        edge_counts = np.random.choice(
            [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 
            size=len(person_ids),
            p=[0.4, 0.25, 0.15, 0.1, 0.05, 0.02, 0.01, 0.01, 0.005, 0.005]
        )
        
        # Initialize edge data and counters
        edges = []
        edge_type_count = 0
        datainstance_type_stats = {'SERVICEPROVIDER': 0, 'STAKEHOLDER': 0}
        
        # Optimized batch processing with multiprocessing
        print("\nGenerating person_datainstance edges with optimized processing...")
        
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
            batches.append((batch_person_ids, datainstance_ids, edge_counts, i))
        
        # Process batches in parallel
        with ThreadPoolExecutor(max_workers=num_cores) as executor:
            # Submit all batches
            future_to_batch = {executor.submit(process_person_batch, batch): batch for batch in batches}
            
            # Collect results with progress bar
            for future in tqdm(as_completed(future_to_batch), total=len(batches), desc="Processing batches"):
                batch_edges = future.result()
                edges.extend(batch_edges)
                edge_type_count += len(batch_edges)
        
        # Count datainstance types for statistics
        for edge in edges:
            datainstance_type = random.choice(["SERVICEPROVIDER", "STAKEHOLDER"])
            datainstance_type_stats[datainstance_type] += 1
        
        # Save all edges as a single JSON array
        os.makedirs('src/data/output/gds', exist_ok=True)
        with open('src/data/output/gds/mock_person-datainstance_data.json', 'w') as f:
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
        
        print("\nDistribution of Datainstance Edges per Person:")
        for count in sorted(edges_per_person_dist.keys()):
            print(f"Persons with {count} datainstance edges: {edges_per_person_dist[count]}")
        
        # Print datainstance type statistics
        print("\nDatainstance Type Distribution:")
        for datainstance_type, count in datainstance_type_stats.items():
            print(f"{datainstance_type}: {count} edges")
        
        # Print processing statistics
        print(f"\nProcessing Statistics:")
        print(f"Total processing time: {processing_time:.2f} seconds")
        print(f"Edges generated per second: {edge_type_count / processing_time:.2f}")
        print(f"Average edges per person: {edge_type_count / len(person_ids):.2f}")
        
        # Print validation summary
        print(f"\nValidation Summary:")
        print(f"Persons with no datainstance edges: {validation_results['persons_with_no_edges']}")
        print(f"Persons with too many datainstance edges (>10): {validation_results['persons_with_too_many_edges']}")
        
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
        print(f"Error generating person-datainstance edges: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    generate_person_datainstance_edges()
