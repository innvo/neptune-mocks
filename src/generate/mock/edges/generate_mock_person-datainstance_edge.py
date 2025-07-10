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
        
        # Track used person-datainstance pairs to avoid duplicates
        used_pairs = set()
        
        # Generate edges for each person with progress bar
        print("\nGenerating person_datainstance edges...")
        for i, person_id in enumerate(tqdm(person_ids, desc="Processing person nodes")):
            
            # Get available datainstances that haven't been used with this person
            available_datainstances = []
            for datainstance_id in datainstance_ids:
                pair_key = (person_id, datainstance_id)
                if pair_key not in used_pairs:
                    available_datainstances.append(datainstance_id)
            
            # If no available datainstances, we need to reuse some (this ensures every person gets at least 1 edge)
            if len(available_datainstances) == 0:
                print(f"\nWARNING: No available datainstances for person {person_id}, reusing existing datainstances")
                # Reset used_pairs for this person to allow reuse
                available_datainstances = datainstance_ids.copy()
            
            # Use pre-generated edge count for this person
            num_datainstance_edges = edge_counts[i]
            
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
                
                edges.append({
                    'edge_id': str(uuid.uuid4()),
                    'node_id_from': person_id,
                    'node_id_to': datainstance_id,
                    'edge_type': 'person_datainstance',
                    'edge_properties': {
                        'CONFIDENCE_SCORE': round(random.uniform(0.1, 1.0), 2)
                    }
                })
                edge_type_count += 1
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
        print(f"Persons with no datainstance edges: {validation_results['persons_with_no_edges']}")
        print(f"Persons with more than 10 datainstance edges: {validation_results['persons_with_too_many_edges']}")
        
        # Calculate and display edges per person distribution using Counter
        edges_per_person_dist = Counter(validation_results['edges_per_person'].values())
        
        print("\nDistribution of DataInstance Edges per Person:")
        for count in range(1, 11):  # Show distribution for 1-10 edges
            count_value = edges_per_person_dist.get(count, 0)
            print(f"Persons with {count} datainstance edges: {count_value}")
        # Show any counts beyond 10 (should be 0 with new logic)
        for count in sorted(edges_per_person_dist.keys()):
            if count > 10:
                print(f"Persons with {count} datainstance edges: {edges_per_person_dist[count]} (EXCEEDS LIMIT)")
        
        # Verify that every person has at least 1 edge and no more than 10
        persons_with_edges = sum(1 for count in edges_per_person_dist.values() if count > 0)
        persons_within_limit = sum(1 for count in edges_per_person_dist.values() if 1 <= count <= 10)
        total_persons = len(person_nodes)
        print(f"\n✅ {persons_with_edges}/{total_persons} persons have at least 1 datainstance edge")
        print(f"✅ {persons_within_limit}/{total_persons} persons have 1-10 datainstance edges (within limit)")
        
        if validation_results['missing_from_nodes']:
            print(f"\nMissing or invalid person nodes: {len(validation_results['missing_from_nodes'])}")
            print("Sample of missing person nodes:", list(validation_results['missing_from_nodes'])[:5])
        
        if validation_results['missing_to_nodes']:
            print(f"\nMissing or invalid datainstance nodes: {len(validation_results['missing_to_nodes'])}")
            print("Sample of missing datainstance nodes:", list(validation_results['missing_to_nodes'])[:5])
        
        print("\nNode Type Statistics:")
        for node_type, stats in validation_results['node_type_stats'].items():
            print(f"\n{node_type.capitalize()} Nodes:")
            print(f"  Total: {stats['total']}")
            print(f"  Used in valid edges: {stats['valid']}")
        
        print("\nDataInstance Type Statistics:")
        for datainstance_type, count in datainstance_type_stats.items():
            print(f"{datainstance_type}: {count} edges")
        
        print("\nEdge Generation Statistics:")
        print(f"Total number of person_datainstance edges generated: {edge_type_count}")
        print(f"Processing time: {processing_time:.2f} seconds")
        print(f"Edges per second: {edge_type_count / processing_time:.2f}")
        
        # Read the final edge file to get the complete DataFrame
        with open('src/data/output/gds/mock_person-datainstance_data.json', 'r') as f:
            edges_data = json.load(f)
        final_edge_df = pd.DataFrame(edges_data)
        return final_edge_df
        
    except Exception as e:
        print(f"Error generating edges: {str(e)}")
        return None

if __name__ == "__main__":
    edge_df = generate_person_datainstance_edges()
    if edge_df is not None:
        print("\nSample of Generated Edges:")
        print(edge_df.head())
