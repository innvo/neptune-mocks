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
            'email': {'total': 0, 'valid': 0}
        },
        'edges_per_person': {},  # New field to track edges per person
        'persons_with_no_edges': 0,  # Track persons without any email edges
        'persons_with_too_many_edges': 0  # Track persons with more than 5 email edges
    }
    
    # Get sets of valid node IDs for quick lookup
    valid_node_ids = set(node_df['node_id'].values)
    person_node_ids = set(node_df[node_df['node_type'] == 'person']['node_id'].values)
    email_node_ids = set(node_df[node_df['node_type'] == 'email']['node_id'].values)
    
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
        to_node_valid = to_node in email_node_ids
        
        if from_node_valid and to_node_valid:
            validation_results['valid_edges'] += 1
            validation_results['node_type_stats']['person']['valid'] += 1
            validation_results['node_type_stats']['email']['valid'] += 1
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
        elif edge_count > 5:
            validation_results['persons_with_too_many_edges'] += 1
    
    # Update total counts
    validation_results['node_type_stats']['person']['total'] = len(person_node_ids)
    validation_results['node_type_stats']['email']['total'] = len(email_node_ids)
    
    return validation_results

def generate_person_email_edges():
    """
    Generate person-email edges with the following requirements:
    - Every person must have at least 1 email edge
    - Every person can have up to 5 email edges
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
        
        # Get email nodes and convert to list for faster access
        email_nodes = node_df[node_df['node_type'] == 'email']
        if email_nodes.empty:
            print("Warning: No email nodes found in node_data.csv")
            print("Note: You may need to add 'email' to NODE_TYPES in generate_node_data.py")
            return None
        
        print(f"\nFound {len(person_nodes)} person nodes and {len(email_nodes)} email nodes")
        
        # Check if we have enough email nodes for all persons
        if len(email_nodes) < len(person_nodes):
            print(f"\nWARNING: Only {len(email_nodes)} email nodes available for {len(person_nodes)} persons")
            print("This means some email nodes will be shared across multiple persons")
        
        # Convert to lists and sets for faster operations
        person_ids = person_nodes['node_id'].tolist()
        email_ids = email_nodes['node_id'].tolist()
        valid_node_ids = set(node_df['node_id'].values)
        
        # Pre-generate edge counts for all persons using numpy for speed
        # Email edges should be fewer than datainstance edges (1-5 instead of 1-10)
        edge_counts = np.random.choice(
            [1, 2, 3, 4, 5], 
            size=len(person_ids),
            p=[0.6, 0.25, 0.1, 0.03, 0.02]
        )
        
        # Initialize edge data and counters
        edges = []
        edge_type_count = 0
        email_type_stats = {'PRIMARY': 0, 'SECONDARY': 0, 'WORK': 0}
        
        # Track used person-email pairs to avoid duplicates
        used_pairs = set()
        
        # Generate edges for each person with progress bar
        print("\nGenerating person_email edges...")
        for i, person_id in enumerate(tqdm(person_ids, desc="Processing person nodes")):
            
            # Get available emails that haven't been used with this person
            available_emails = []
            for email_id in email_ids:
                pair_key = (person_id, email_id)
                if pair_key not in used_pairs:
                    available_emails.append(email_id)
            
            # If no available emails, we need to reuse some (this ensures every person gets at least 1 edge)
            if len(available_emails) == 0:
                print(f"\nWARNING: No available emails for person {person_id}, reusing existing emails")
                # Reset used_pairs for this person to allow reuse
                available_emails = email_ids.copy()
            
            # Use pre-generated edge count for this person
            num_email_edges = edge_counts[i]
            
            # Limit the number of edges to available emails (minimum 1, maximum 5)
            num_email_edges = max(1, min(num_email_edges, len(available_emails), 5))
            
            # Randomly select emails without replacement
            selected_emails = random.sample(available_emails, num_email_edges)
            
            for email_id in selected_emails:
                # Add to used pairs
                pair_key = (person_id, email_id)
                used_pairs.add(pair_key)
                
                # Determine email type
                email_type = random.choice(["PRIMARY", "SECONDARY", "WORK"])
                
                edges.append({
                    'edge_id': str(uuid.uuid4()),
                    'node_id_from': person_id,
                    'node_id_to': email_id,
                    'edge_type': 'person_email',
                    'edge_properties': {}
                })
                edge_type_count += 1
                email_type_stats[email_type] += 1
        
        # Save all edges as a single JSON array
        os.makedirs('src/data/output/gds', exist_ok=True)
        with open('src/data/output/gds/mock_person-email_data.json', 'w') as f:
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
        print(f"Persons with no email edges: {validation_results['persons_with_no_edges']}")
        print(f"Persons with more than 5 email edges: {validation_results['persons_with_too_many_edges']}")
        
        # Calculate and display edges per person distribution using Counter
        edges_per_person_dist = Counter(validation_results['edges_per_person'].values())
        
        print("\nDistribution of Email Edges per Person:")
        for count in range(1, 6):  # Show distribution for 1-5 edges
            count_value = edges_per_person_dist.get(count, 0)
            print(f"Persons with {count} email edges: {count_value}")
        # Show any counts beyond 5 (should be 0 with new logic)
        for count in sorted(edges_per_person_dist.keys()):
            if count > 5:
                print(f"Persons with {count} email edges: {edges_per_person_dist[count]} (EXCEEDS LIMIT)")
        
        # Verify that every person has at least 1 edge and no more than 5
        persons_with_edges = sum(1 for count in edges_per_person_dist.values() if count > 0)
        persons_within_limit = sum(1 for count in edges_per_person_dist.values() if 1 <= count <= 5)
        total_persons = len(person_nodes)
        print(f"\n✅ {persons_with_edges}/{total_persons} persons have at least 1 email edge")
        print(f"✅ {persons_within_limit}/{total_persons} persons have 1-5 email edges (within limit)")
        
        if validation_results['missing_from_nodes']:
            print(f"\nMissing or invalid person nodes: {len(validation_results['missing_from_nodes'])}")
            print("Sample of missing person nodes:", list(validation_results['missing_from_nodes'])[:5])
        
        if validation_results['missing_to_nodes']:
            print(f"\nMissing or invalid email nodes: {len(validation_results['missing_to_nodes'])}")
            print("Sample of missing email nodes:", list(validation_results['missing_to_nodes'])[:5])
        
        print("\nNode Type Statistics:")
        for node_type, stats in validation_results['node_type_stats'].items():
            print(f"\n{node_type.capitalize()} Nodes:")
            print(f"  Total: {stats['total']}")
            print(f"  Used in valid edges: {stats['valid']}")
        
        print("\nEmail Type Statistics:")
        for email_type, count in email_type_stats.items():
            print(f"{email_type}: {count} edges")
        
        print("\nEdge Generation Statistics:")
        print(f"Total number of person_email edges generated: {edge_type_count}")
        print(f"Processing time: {processing_time:.2f} seconds")
        print(f"Edges per second: {edge_type_count / processing_time:.2f}")
        
        # Read the final edge file to get the complete DataFrame
        with open('src/data/output/gds/mock_person-email_data.json', 'r') as f:
            edges_data = json.load(f)
        final_edge_df = pd.DataFrame(edges_data)
        return final_edge_df
        
    except Exception as e:
        print(f"Error generating edges: {str(e)}")
        return None

if __name__ == "__main__":
    edge_df = generate_person_email_edges()
    if edge_df is not None:
        print("\nSample of Generated Edges:")
        print(edge_df.head())
