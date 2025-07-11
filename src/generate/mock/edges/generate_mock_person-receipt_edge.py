import pandas as pd
import uuid
import random
from tqdm import tqdm
import time
import os
import json
import platform
import numpy as np
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing as mp
import gc
import psutil

# Define role type mappings
ROLE_TYPE_MAPPINGS = {
    'PRIMARY BENEFICIARY': 'PRIMARY BENEFICIARY',
    'INCIDENT OFFICIAL': 'INCIDENT OFFICIAL',
    'SPOUSE': 'NONPRIMARY BENEFICIARY',
    'SON': 'NONPRIMARY BENEFICIARY',
    'BENEFICIARY': 'PRIMARY BENEFICIARY',
    'DERIVATIVE APPLICANT': 'NONPRIMARY BENEFICIARY',
    'STEPFATHER': 'NONPRIMARY BENEFICIARY',
    'MOTHER': 'NONPRIMARY BENEFICIARY',
    'STEPSON': 'NONPRIMARY BENEFICIARY',
    'PARENT': 'NONPRIMARY BENEFICIARY',
    'WIFE': 'NONPRIMARY BENEFICIARY',
    'ADOPTED DAUGHTER': 'NONPRIMARY BENEFICIARY',
    'BENEFICIARY\'S SPOUSE': 'NONPRIMARY BENEFICIARY',
    'APPLICANT': 'APPLICANT',
    'ADOPTED SON': 'NONPRIMARY BENEFICIARY',
    'GRANDMOTHER': 'NONPRIMARY BENEFICIARY',
    'PARENT 1': 'PRIMARY BENEFICIARY',
    'HOUSEHOLD MEMBER': 'NONPRIMARY BENEFICIARY',
    'STEPDAUGHTER': 'NONPRIMARY BENEFICIARY',
    'INTERPRETER': 'INTERPRETER',
    'FAMILY MEMBER': 'FAMILY MEMBER',
    'I130 OTHER BENEFICIARY': 'BENEFICIARY',
    'PARENT 2 NAME AT BIRTH': 'NONPRIMARY BENEFICIARY',
    'ADOPTIVE FATHER': 'NONPRIMARY BENEFICIARY',
    'BROTHER': 'NONPRIMARY BENEFICIARY',
    'PARENTS': 'NONPRIMARY BENEFICIARY',
    'PRINCIPAL ALIEN': 'PRIMARY BENEFICIARY',
    'ATTORNEY AT INTERVIEW': 'ATTORNEY',
    'SISTER': 'NONPRIMARY BENEFICIARY',
    'PARENT 2': 'PRIMARY BENEFICIARY',
    'GRANDFATHER': 'NONPRIMARY BENEFICIARY',
    'PETITIONER': 'PETITIONER',
    'ATTORNEY': 'ATTORNEY',
    'HUSBAND': 'NONPRIMARY BENEFICIARY',
    'PARENT 1 NAME AT BIRTH': 'NONPRIMARY BENEFICIARY',
    'FATHER': 'NONPRIMARY BENEFICIARY',
    'HOUSEHOLD RELATIVE': 'NONPRIMARY BENEFICIARY',
    'PRINCIPAL APPLICANT': 'PRIMARY APPLICANT',
    'INTENDING IMMIGRANT NO NEED FOR I864A': 'PRIMARY BENEFICIARY',
    'I130 OTHER BENEFICIARY': 'NONPRIMARY BENEFICIARY',
    'USCIS CIVIL SURGEON': 'CIVIL SURGEON',
    'IMPLICATED FAMILY MEMBER': 'FAMILY MEMBER',
    'FAMILY MEMBER': 'NONPRIMARY BENEFICIARY',
    'AUTHORIZED SIGNATORY': 'PETITIONER',
    'BENEFICIARY': 'BENEFICIARY',
    'PRINCIPAL APPLICANT': 'PRINCIPAL APPLICANT',
    'SPONSOR AFFIDAVIT OF SUPP': 'PETITIONER',
    'INTERPRETER IN G1256': 'INTERPRETER',
    'SPONSOR': 'PETITIONER',
    'CHILD': 'NONPRIMARY BENEFICIARY',
    'INTERPRETER AT INTERVIEW': 'INTERPRETER',
    'REPRESENTATIVE': 'REPRESENTATIVE',
    'ADOPTIVE MOTHER': 'NONPRIMARY BENEFICIARY',
    'DAUGHTER': 'NONPRIMARY BENEFICIARY',
    'BENEFICIARY, SEPARATE PETITION': 'PRIMARY BENEFICIARY',
    'FATHER': 'NONPRIMARY BENEFICIARY',
    'STUDENT': 'STUDENT',
    'PREPARER': 'PREPARER',
    'BENEFICIARY\'S FAMILY MEMBER': 'CF-BENEFICIARY\'S FAMILY MEMBER',
    'PARENT': 'CF-PARENT',
    'STEPMOTHER': 'NONPRIMARY BENEFICIARY',
    'USCIS OFFICER AS INTERPRETER': 'INTERPRETER',
    'GRANDSON': 'NONPRIMARY BENEFICIARY',
    'LANGUAGE SERVICE PROVIDER': 'INTERPRETER',
    'BENEFICIARY\'S LANGUAGE SERVICE PROVIDER': 'INTERPRETER',
    'BENEFICIARY\'S INTERPRETER IN G1256': 'INTERPRETER',
    'GRANDDAUGHTER': 'NONPRIMARY BENEFICIARY',
    'FIANCE': 'NONPRIMARY BENEFICIARY',
    'INTERPRETER VIA PHONE': 'INTERPRETER',
    'CUSTODIAN SON': 'NONPRIMARY BENEFICIARY',
    'CUSTODIAN DAUGHTER': 'NONPRIMARY BENEFICIARY',
    'LEGAL GUARDIAN': 'NONPRIMARY BENEFICIARY',
    'FOUNDLING': 'NONPRIMARY BENEFICIARY',
    'APPLICANT': 'CF-APPLICANT',
    'PARENT 2': 'PARENT',
    'BENEFICIARY': 'CF-BENEFICIARY',
    'PARENT 1 NAME AT BIRTH': 'PARENT'
}

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
            'receipt': {'total': 0, 'valid': 0}
        },
        'edges_per_person': {},  # Track edges per person
        'edges_per_receipt': {}  # Track edges per receipt
    }
    
    # Get sets of valid node IDs for quick lookup
    valid_node_ids = set(node_df['node_id'].values)
    person_node_ids = set(node_df[node_df['node_type'] == 'person']['node_id'].values)
    receipt_node_ids = set(node_df[node_df['node_type'] == 'receipt']['node_id'].values)
    
    # Initialize counters
    for person_id in person_node_ids:
        validation_results['edges_per_person'][person_id] = 0
    for receipt_id in receipt_node_ids:
        validation_results['edges_per_receipt'][receipt_id] = 0
    
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
        to_node_is_receipt = to_node in receipt_node_ids
        
        if from_node_exists and to_node_exists and from_node_is_person and to_node_is_receipt:
            validation_results['valid_edges'] += 1
            validation_results['node_type_stats']['person']['valid'] += 1
            validation_results['node_type_stats']['receipt']['valid'] += 1
            validation_results['edges_per_person'][from_node] += 1
            validation_results['edges_per_receipt'][to_node] += 1
        else:
            validation_results['invalid_edges'] += 1
            if not from_node_exists or not from_node_is_person:
                validation_results['missing_from_nodes'].add(from_node)
            if not to_node_exists or not to_node_is_receipt:
                validation_results['missing_to_nodes'].add(to_node)
    
    # Update total counts
    validation_results['node_type_stats']['person']['total'] = len(person_node_ids)
    validation_results['node_type_stats']['receipt']['total'] = len(receipt_node_ids)
    
    return validation_results

def process_person_batch(batch_data):
    """Process a batch of persons to generate receipt edges - MAXIMUM PERFORMANCE"""
    person_ids, receipt_ids, edge_counts, person_lookup, batch_start_idx = batch_data
    batch_edges = []
    used_pairs = set()
    
    # Pre-allocate memory for maximum performance
    estimated_edges = len(person_ids) * 3  # Assume average 3 edges per person for receipts
    batch_edges = []
    batch_edges.reserve(estimated_edges) if hasattr(batch_edges, 'reserve') else None
    
    for i, person_id in enumerate(person_ids):
        # Get available receipts that haven't been used with this person
        available_receipts = [receipt_id for receipt_id in receipt_ids 
                             if (person_id, receipt_id) not in used_pairs]
        
        # If no available receipts, reuse some (ensures every person gets at least 1 edge)
        if len(available_receipts) == 0:
            available_receipts = receipt_ids.copy()
        
        # Use pre-generated edge count for this person
        num_receipt_edges = edge_counts[batch_start_idx + i]
        
        # Limit the number of edges to available receipts (minimum 1, maximum 5)
        num_receipt_edges = max(1, min(num_receipt_edges, len(available_receipts), 5))
        
        # Randomly select receipts without replacement
        selected_receipts = random.sample(available_receipts, num_receipt_edges)
        
        for receipt_id in selected_receipts:
            # Add to used pairs
            pair_key = (person_id, receipt_id)
            used_pairs.add(pair_key)
            
            # Get random role type and its standardized version
            role_type = random.choice(list(ROLE_TYPE_MAPPINGS.keys()))
            role_type_std = ROLE_TYPE_MAPPINGS[role_type]
            
            # Get person's name
            name_full = person_lookup.get(person_id, "UNKNOWN")
            
            batch_edges.append({
                'edge_id': str(uuid.uuid4()),
                'node_id_from': person_id,
                'node_id_to': receipt_id,
                'edge_type': 'person_receipt',
                'edge_properties': {
                    'ROLE_TYPE': role_type,
                    'ROLE_TYPE_STD': role_type_std,
                    'NAME_FULL': name_full
                }
            })
    
    return batch_edges

def get_optimal_batch_size(total_persons, num_cores, memory_gb):
    """Calculate optimal batch size based on CPU cores and available memory"""
    # For maximum performance, use larger batches
    # Base calculation: one batch per core for maximum parallelism
    base_batch_size = max(1, total_persons // num_cores)
    
    # Adjust based on available memory (more memory = larger batches)
    memory_factor = min(4, max(1, memory_gb // 4))  # Scale up to 4x for high memory systems
    
    # For very large datasets, use even larger batches
    if total_persons > 100000:
        batch_size = max(1, total_persons // (num_cores * 1))  # One batch per core
    else:
        batch_size = max(1, total_persons // (num_cores * 2))  # Two batches per core
    
    # Apply memory factor
    batch_size = int(batch_size * memory_factor)
    
    return max(100, batch_size)  # Minimum batch size of 100

def generate_person_receipt_edges():
    """
    Generate person-receipt edges with MAXIMUM CPU and MEMORY utilization:
    - Every person must have at least 1 receipt edge
    - Every person can have up to 5 receipt edges
    - Distribution is weighted to favor fewer edges (1-3 most common)
    - Uses maximum available CPU cores and memory
    """
    try:
        clear_terminal()
        start_time = time.time()
        
        # Get system resources for optimization
        num_cores = mp.cpu_count()
        memory_gb = psutil.virtual_memory().total // (1024**3)
        
        print(f"🚀 MAXIMUM PERFORMANCE MODE")
        print(f"CPU Cores: {num_cores}")
        print(f"Available Memory: {memory_gb} GB")
        print("=" * 60)
        
        # Read node_data.csv, excluding node_name column
        print("Reading node data...")
        node_df = pd.read_csv('src/data/input/node_data.csv', usecols=['node_id', 'node_type'])
        
        # Read person data to get NAME_FULL
        print("Reading person data...")
        with open('src/data/output/gds/mock_person_data.json', 'r') as f:
            person_data = json.load(f)
        
        # Create a dictionary for quick person lookup
        person_lookup = {person['node_id']: person['node_properties']['NAME_FULL'] for person in person_data}
        
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
        
        # Get receipt nodes and convert to list for faster access
        receipt_nodes = node_df[node_df['node_type'] == 'receipt']
        if receipt_nodes.empty:
            print("Warning: No receipt nodes found in node_data.csv")
            return None
        
        print(f"\nFound {len(person_nodes)} person nodes and {len(receipt_nodes)} receipt nodes")
        
        # Check if we have enough receipt nodes for all persons
        if len(receipt_nodes) < len(person_nodes):
            print(f"\nWARNING: Only {len(receipt_nodes)} receipt nodes available for {len(person_nodes)} persons")
            print("This means some receipt nodes will be shared across multiple persons")
        
        # Convert to lists and sets for faster operations
        person_ids = person_nodes['node_id'].tolist()
        receipt_ids = receipt_nodes['node_id'].tolist()
        valid_node_ids = set(node_df['node_id'].values)
        
        # Pre-generate edge counts for all persons using numpy for speed
        edge_counts = np.random.choice(
            [1, 2, 3, 4, 5], 
            size=len(person_ids),
            p=[0.6, 0.25, 0.1, 0.03, 0.02]
        )
        
        # Initialize edge data and counters
        edges = []
        edge_type_count = 0
        role_type_stats = {role_type: 0 for role_type in set(ROLE_TYPE_MAPPINGS.values())}
        
        # MAXIMUM PERFORMANCE: Calculate optimal batch size
        batch_size = get_optimal_batch_size(len(person_ids), num_cores, memory_gb)
        
        print(f"\n🚀 MAXIMUM PERFORMANCE SETTINGS:")
        print(f"CPU Cores: {num_cores}")
        print(f"Batch Size: {batch_size:,}")
        print(f"Memory Available: {memory_gb} GB")
        print(f"Estimated batches: {len(person_ids) // batch_size + 1}")
        
        # Create batches
        batches = []
        for i in range(0, len(person_ids), batch_size):
            batch_end = min(i + batch_size, len(person_ids))
            batch_person_ids = person_ids[i:batch_end]
            batches.append((batch_person_ids, receipt_ids, edge_counts, person_lookup, i))
        
        print(f"\nGenerating person_receipt edges with MAXIMUM performance...")
        
        # Process batches in parallel with maximum workers
        max_workers = min(num_cores * 2, len(batches))  # Use up to 2x CPU cores for I/O bound tasks
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all batches
            future_to_batch = {executor.submit(process_person_batch, batch): batch for batch in batches}
            
            # Collect results with progress bar
            for future in tqdm(as_completed(future_to_batch), total=len(batches), desc="Processing batches"):
                batch_edges = future.result()
                edges.extend(batch_edges)
                edge_type_count += len(batch_edges)
                
                # Aggressive garbage collection for memory management
                if len(edges) % 5000 == 0:
                    gc.collect()
        
        # Count role types for statistics
        for edge in edges:
            role_type_std = edge['edge_properties']['ROLE_TYPE_STD']
            role_type_stats[role_type_std] += 1
        
        # Save all edges as a single JSON array
        os.makedirs('src/data/output/gds', exist_ok=True)
        with open('src/data/output/gds/mock_person-receipt_data.json', 'w') as f:
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
        
        print("\nDistribution of Receipt Edges per Person:")
        for count in sorted(edges_per_person_dist.keys()):
            print(f"Persons with {count} receipt edges: {edges_per_person_dist[count]}")
        
        # Print role type statistics
        print("\nRole Type Distribution:")
        for role_type, count in role_type_stats.items():
            if count > 0:  # Only show types that were actually used
                print(f"{role_type}: {count} edges")
        
        # Print MAXIMUM PERFORMANCE statistics
        print(f"\n🚀 MAXIMUM PERFORMANCE STATISTICS:")
        print(f"Total processing time: {processing_time:.2f} seconds")
        print(f"Edges generated per second: {edge_type_count / processing_time:.2f}")
        print(f"Average edges per person: {edge_type_count / len(person_ids):.2f}")
        print(f"CPU utilization: {num_cores} cores")
        print(f"Memory utilization: {memory_gb} GB available")
        print(f"Batch efficiency: {len(batches)} batches processed")
        
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
        print(f"Error generating person-receipt edges: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    generate_person_receipt_edges() 