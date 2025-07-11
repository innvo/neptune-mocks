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
            'phone': {'total': 0, 'valid': 0}
        },
        'edges_per_person': {},  # New field to track edges per person
        'persons_with_no_edges': 0,  # Track persons without any phone edges
        'persons_with_too_many_edges': 0  # Track persons with more than 3 phone edges
    }
    
    # Get sets of valid node IDs for quick lookup
    valid_node_ids = set(node_df['node_id'].values)
    person_node_ids = set(node_df[node_df['node_type'] == 'person']['node_id'].values)
    phone_node_ids = set(node_df[node_df['node_type'] == 'phone']['node_id'].values)
    
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
        to_node_valid = to_node in phone_node_ids
        
        if from_node_valid and to_node_valid:
            validation_results['valid_edges'] += 1
            validation_results['node_type_stats']['person']['valid'] += 1
            validation_results['node_type_stats']['phone']['valid'] += 1
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
        elif edge_count > 3:
            validation_results['persons_with_too_many_edges'] += 1
    
    # Update total counts
    validation_results['node_type_stats']['person']['total'] = len(person_node_ids)
    validation_results['node_type_stats']['phone']['total'] = len(phone_node_ids)
    
    return validation_results

def generate_person_phone_edges():
    """
    Generate person-phone edges with the following requirements:
    - Every person must have at least 1 phone edge
    - Every person can have up to 3 phone edges
    - Distribution is weighted to favor fewer edges (1-2 most common)
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
        
        # Get phone nodes and convert to list for faster access
        phone_nodes = node_df[node_df['node_type'] == 'phone']
        if phone_nodes.empty:
            print("Warning: No phone nodes found in node_data.csv")
            print("Note: You may need to add 'phone' to NODE_TYPES in generate_node_data.py")
            return None
        
        print(f"\nFound {len(person_nodes)} person nodes and {len(phone_nodes)} phone nodes")
        
        # Check if we have enough phone nodes for all persons
        if len(phone_nodes) < len(person_nodes):
            print(f"\nWARNING: Only {len(phone_nodes)} phone nodes available for {len(person_nodes)} persons")
            print("This means some phone nodes will be shared across multiple persons")
        
        # Convert to lists and sets for faster operations
        person_ids = person_nodes['node_id'].tolist()
        phone_ids = phone_nodes['node_id'].tolist()
        valid_node_ids = set(node_df['node_id'].values)
        
        # Pre-generate edge counts for all persons using numpy for speed
        # Phone edges should be fewer than email edges (1-3 instead of 1-5)
        edge_counts = np.random.choice(
            [1, 2, 3], 
            size=len(person_ids),
            p=[0.7, 0.25, 0.05]
        )
        
        # Initialize edge data and counters
        edges = []
        edge_type_count = 0
        phone_type_stats = {'MOBILE': 0, 'HOME': 0, 'WORK': 0}
        
        # Track used person-phone pairs to avoid duplicates
        used_pairs = set()
        
        # Generate edges for each person with progress bar
        print("\nGenerating person_phone edges...")
        for i, person_id in enumerate(tqdm(person_ids, desc="Processing person nodes")):
            
            # Get available phones that haven't been used with this person
            available_phones = []
            for phone_id in phone_ids:
                pair_key = (person_id, phone_id)
                if pair_key not in used_pairs:
                    available_phones.append(phone_id)
            
            # If no available phones, we need to reuse some (this ensures every person gets at least 1 edge)
            if len(available_phones) == 0:
                print(f"\nWARNING: No available phones for person {person_id}, reusing existing phones")
                # Reset used_pairs for this person to allow reuse
                available_phones = phone_ids.copy()
            
            # Use pre-generated edge count for this person
            num_phone_edges = edge_counts[i]
            
            # Limit the number of edges to available phones (minimum 1, maximum 3)
            num_phone_edges = max(1, min(num_phone_edges, len(available_phones), 3))
            
            # Randomly select phones without replacement
            selected_phones = random.sample(available_phones, num_phone_edges)
            
            for phone_id in selected_phones:
                # Add to used pairs
                pair_key = (person_id, phone_id)
                used_pairs.add(pair_key)
                
                # Determine phone type
                phone_type = random.choice(["MOBILE", "HOME", "WORK"])
                
                edges.append({
                    'edge_id': str(uuid.uuid4()),
                    'node_id_from': person_id,
                    'node_id_to': phone_id,
                    'edge_type': 'person_phone',
                    'edge_properties': {}
                })
                edge_type_count += 1
                phone_type_stats[phone_type] += 1
        
        # Save to JSON
        output_path = os.path.join('src', 'data', 'output', 'gds', 'mock_person-phone_data.json')
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
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
            print(f"\nMissing from nodes: {len(validation_results['missing_from_nodes'])}")
            print("Sample of missing from nodes:", list(validation_results['missing_from_nodes'])[:5])
        
        if validation_results['missing_to_nodes']:
            print(f"\nMissing to nodes: {len(validation_results['missing_to_nodes'])}")
            print("Sample of missing to nodes:", list(validation_results['missing_to_nodes'])[:5])
        
        print("\nNode Type Statistics:")
        for node_type, stats in validation_results['node_type_stats'].items():
            print(f"\n{node_type.capitalize()} Nodes:")
            print(f"  Total: {stats['total']}")
            print(f"  Used in valid edges: {stats['valid']}")
        
        print("\nEdge Type Statistics:")
        for edge_type, count in validation_results['edge_type_stats'].items():
            print(f"  {edge_type}: {count} edges")
        
        print("\nPerson Edge Distribution:")
        print(f"  Persons with no phone edges: {validation_results['persons_with_no_edges']}")
        print(f"  Persons with too many phone edges (>3): {validation_results['persons_with_too_many_edges']}")
        
        print("\nPhone Type Distribution:")
        for phone_type, count in phone_type_stats.items():
            print(f"  {phone_type}: {count} edges")
        
        print("\nEdge Generation Statistics:")
        print(f"Total number of edges generated: {len(edges)}")
        print(f"Processing time: {processing_time:.2f} seconds")
        print(f"Edges per second: {len(edges) / processing_time:.2f}")
        print(f"Data saved to: {output_path}")
        
        return edges
        
    except Exception as e:
        print(f"Error generating person-phone edges: {str(e)}")
        return None

if __name__ == "__main__":
    edges = generate_person_phone_edges()
    if edges is not None:
        print("\nSample of Generated Person-Phone Edges:")
        print(json.dumps(edges[:5], indent=2)) 