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
            'organization': {'total': 0, 'valid': 0}
        },
        'edges_per_person': {},  # Track edges per person
        'edges_per_organization': {}  # Track edges per organization
    }
    
    # Get sets of valid node IDs for quick lookup
    valid_node_ids = set(node_df['node_id'].values)
    person_node_ids = set(node_df[node_df['node_type'] == 'person']['node_id'].values)
    organization_node_ids = set(node_df[node_df['node_type'] == 'organization']['node_id'].values)
    
    # Initialize counters
    for person_id in person_node_ids:
        validation_results['edges_per_person'][person_id] = 0
    for org_id in organization_node_ids:
        validation_results['edges_per_organization'][org_id] = 0
    
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
        to_node_is_organization = to_node in organization_node_ids
        
        if from_node_exists and to_node_exists and from_node_is_person and to_node_is_organization:
            validation_results['valid_edges'] += 1
            validation_results['node_type_stats']['person']['valid'] += 1
            validation_results['node_type_stats']['organization']['valid'] += 1
            validation_results['edges_per_person'][from_node] += 1
            validation_results['edges_per_organization'][to_node] += 1
        else:
            validation_results['invalid_edges'] += 1
            if not from_node_exists or not from_node_is_person:
                validation_results['missing_from_nodes'].add(from_node)
            if not to_node_exists or not to_node_is_organization:
                validation_results['missing_to_nodes'].add(to_node)
    
    # Update total counts
    validation_results['node_type_stats']['person']['total'] = len(person_node_ids)
    validation_results['node_type_stats']['organization']['total'] = len(organization_node_ids)
    
    return validation_results

def process_person_batch(batch_data):
    """Process a batch of persons to generate organization edges"""
    person_ids, organization_ids, batch_start_idx = batch_data
    batch_edges = []
    used_pairs = set()
    
    # Configuration for edge generation
    person_has_org_probability = 0.7  # 70% of persons will have organization edges
    max_orgs_per_person = 3
    
    for i, person_id in enumerate(person_ids):
        # Determine if this person will have organization edges
        if random.random() < person_has_org_probability:
            # Get available organizations that haven't been used with this person
            available_organizations = [org_id for org_id in organization_ids 
                                     if (person_id, org_id) not in used_pairs]
            
            # If no available organizations, reuse some
            if len(available_organizations) == 0:
                available_organizations = organization_ids.copy()
            
            # Random number of organizations (1 to max_orgs_per_person)
            num_org_edges = random.randint(1, min(max_orgs_per_person, len(available_organizations)))
            
            # Randomly select organizations without replacement
            selected_organizations = random.sample(available_organizations, num_org_edges)
            
            for org_id in selected_organizations:
                # Add to used pairs
                pair_key = (person_id, org_id)
                used_pairs.add(pair_key)
                
                batch_edges.append({
                    'edge_id': str(uuid.uuid4()),
                    'node_id_from': person_id,
                    'node_id_to': org_id,
                    'edge_type': 'person_organization',
                    'edge_name': 'workAt',
                    'edge_properties': {
                        'ORG_TYPE': 'EMPLOYER',
                        'ADDR_FROM_DATE': f"{random.randint(2010, 2024)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
                        'ADDR_THRU_DATE': f"{random.randint(2010, 2024)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
                        'EMPLOYMENT_START_DATE': f"{random.randint(2010, 2024)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
                        'EMPLOYMENT_END_DATE': f"{random.randint(2010, 2024)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
                    }
                })
    
    return batch_edges

def generate_person_organization_edges():
    try:
        clear_terminal()
        start_time = time.time()
        
        # Read person data from mock_person_data.json to ensure consistency
        print("Reading person data from mock_person_data.json...")
        with open('src/data/output/gds/mock_person_data.json', 'r') as f:
            person_data = json.load(f)
        
        # Extract person IDs from the JSON data
        person_ids = [person['node_id'] for person in person_data]
        print(f"Found {len(person_ids)} person IDs from mock_person_data.json")
        
        # Read organization data from node_data.csv
        print("Reading organization data from node_data.csv...")
        node_df = pd.read_csv('src/data/input/node_data.csv', usecols=['node_id', 'node_type'])
        
        # Get organization nodes and convert to list for faster access
        organization_nodes = node_df[node_df['node_type'] == 'organization']
        if organization_nodes.empty:
            print("Warning: No organization nodes found in node_data.csv")
            return None
        
        print(f"Found {len(organization_nodes)} organization nodes")
        
        # Convert to lists and sets for faster operations
        organization_ids = organization_nodes['node_id'].tolist()
        
        # Initialize edge data and counters
        edges = []
        edge_type_count = 0
        
        # Optimized batch processing with multiprocessing
        print("\nGenerating person_organization edges with optimized processing...")
        
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
            batches.append((batch_person_ids, organization_ids, i))
        
        # Process batches in parallel
        with ThreadPoolExecutor(max_workers=num_cores) as executor:
            # Submit all batches
            future_to_batch = {executor.submit(process_person_batch, batch): batch for batch in batches}
            
            # Collect results with progress bar
            for future in tqdm(as_completed(future_to_batch), total=len(batches), desc="Processing batches"):
                batch_edges = future.result()
                edges.extend(batch_edges)
                edge_type_count += len(batch_edges)
        
        # Save all edges as a single JSON array
        os.makedirs('src/data/output/gds', exist_ok=True)
        with open('src/data/output/gds/mock_person-organization_data.json', 'w') as f:
            json.dump(edges, f, indent=2)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Create a combined node dataframe for validation
        # Create person nodes dataframe from mock_person_data.json
        person_nodes_data = []
        for person in person_data:
            person_nodes_data.append({
                'node_id': person['node_id'],
                'node_type': 'person'
            })
        person_nodes_df = pd.DataFrame(person_nodes_data)
        
        # Combine person and organization nodes for validation
        combined_node_df = pd.concat([person_nodes_df, organization_nodes], ignore_index=True)
        
        # Validate referential integrity
        validation_results = validate_referential_integrity(edges, combined_node_df)
        
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
        
        print("\nDistribution of Organization Edges per Person:")
        for count in sorted(edges_per_person_dist.keys()):
            print(f"Persons with {count} organization edges: {edges_per_person_dist[count]}")
        
        # Calculate and display edges per organization distribution
        edges_per_org_dist = {}
        for org_id, count in validation_results['edges_per_organization'].items():
            edges_per_org_dist[count] = edges_per_org_dist.get(count, 0) + 1
        
        print("\nDistribution of Person Edges per Organization:")
        for count in sorted(edges_per_org_dist.keys()):
            print(f"Organizations with {count} person edges: {edges_per_org_dist[count]}")
        
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
        print(f"Error generating person-organization edges: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    generate_person_organization_edges()
