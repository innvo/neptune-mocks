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

def validate_referential_integrity(edges, organization_df, address_df):
    """Validate referential integrity of edges against organization and address data"""
    validation_results = {
        'total_edges': len(edges),
        'valid_edges': 0,
        'invalid_edges': 0,
        'missing_from_nodes': set(),
        'missing_to_nodes': set(),
        'edge_type_stats': {},
        'node_type_stats': {
            'organization': {'total': 0, 'valid': 0},
            'address': {'total': 0, 'valid': 0}
        },
        'edges_per_organization': {},  # Track edges per organization
        'addresses_per_organization': {},  # Track unique addresses per organization
        'organizations_per_address': {}  # Track unique organizations per address
    }
    
    # Get sets of valid node IDs for quick lookup
    valid_organization_ids = set(organization_df['node_id'].values)
    valid_address_ids = set(address_df['node_id'].values)
    
    # Initialize tracking dictionaries
    for org_id in valid_organization_ids:
        validation_results['edges_per_organization'][org_id] = 0
        validation_results['addresses_per_organization'][org_id] = set()
    
    for addr_id in valid_address_ids:
        validation_results['organizations_per_address'][addr_id] = set()
    
    # Update total counts
    validation_results['node_type_stats']['organization']['total'] = len(valid_organization_ids)
    validation_results['node_type_stats']['address']['total'] = len(valid_address_ids)
    
    for edge in edges:
        from_node = edge['node_id_from']
        to_node = edge['node_id_to']
        edge_type = edge['edge_type']
        
        # Count edge types
        validation_results['edge_type_stats'][edge_type] = validation_results['edge_type_stats'].get(edge_type, 0) + 1
        
        # Validate node existence
        from_node_exists = from_node in valid_organization_ids
        to_node_exists = to_node in valid_address_ids
        
        if from_node_exists and to_node_exists:
            validation_results['valid_edges'] += 1
            validation_results['node_type_stats']['organization']['valid'] += 1
            validation_results['node_type_stats']['address']['valid'] += 1
            validation_results['edges_per_organization'][from_node] += 1
            validation_results['addresses_per_organization'][from_node].add(to_node)
            validation_results['organizations_per_address'][to_node].add(from_node)
        else:
            validation_results['invalid_edges'] += 1
            if not from_node_exists:
                validation_results['missing_from_nodes'].add(from_node)
            if not to_node_exists:
                validation_results['missing_to_nodes'].add(to_node)
    
    return validation_results

def process_organization_batch(batch_data):
    """Process a batch of organizations to generate address edges"""
    organization_ids, address_ids, address_details_map, batch_start_idx = batch_data
    batch_edges = []
    used_pairs = set()
    
    # Configuration parameters for random assignment
    org_has_address_probability = 0.7  # 70% of organizations will have at least one address
    max_addresses_per_org = 5  # Maximum number of addresses per organization
    min_addresses_per_org = 1  # Minimum number of addresses if organization has addresses
    
    for i, organization_id in enumerate(organization_ids):
        # Determine if this organization will have address edges
        if random.random() < org_has_address_probability:
            # Get available addresses that haven't been used with this organization
            available_addresses = [addr_id for addr_id in address_ids 
                                 if (organization_id, addr_id) not in used_pairs]
            
            # If no available addresses, reuse some
            if len(available_addresses) == 0:
                available_addresses = address_ids.copy()
            
            # Random number of addresses (1 to max_addresses_per_org)
            num_address_edges = random.randint(min_addresses_per_org, min(max_addresses_per_org, len(available_addresses)))
            
            # Randomly select addresses without replacement
            selected_address_ids = random.sample(available_addresses, num_address_edges)
            
            for address_id in selected_address_ids:
                # Add to used pairs
                pair_key = (organization_id, address_id)
                used_pairs.add(pair_key)
                
                # Generate random VIBE address IDs for this organization
                num_vibe_ids = random.randint(1, 7)  # Random number of VIBE IDs (1-7)
                vibe_address_ids = [str(random.randint(100000000, 999999999)) for _ in range(num_vibe_ids)]
                
                # Get the address details from the address data
                address_details = address_details_map.get(address_id, {})
                
                # Construct the full address string
                street_line1 = address_details.get('STREET_ADDRESS_LINE1', '')
                street_line2 = address_details.get('STREET_ADDRESS_LINE2', '')
                city = address_details.get('CITY', '')
                state = address_details.get('STATE_PROVINCE', '')
                postal_code = address_details.get('POSTAL_CODE', '')
                
                # Build full address
                address_parts = [street_line1]
                if street_line2:
                    address_parts.append(street_line2)
                address_parts.extend([city, state, postal_code])
                full_address = " ".join(part for part in address_parts if part)
                
                batch_edges.append({
                    'edge_id': str(uuid.uuid4()),
                    'node_id_from': organization_id,
                    'node_id_to': address_id,
                    'edge_type': 'organization_address',
                    'edge_properties': {
                        'VIBE_ADDRESS_ID': vibe_address_ids,
                        'VIBE_RAW_ADDR_FULL': [full_address],
                        'SOURCE': 'VIBE'
                    }
                })
    
    return batch_edges

def generate_organization_address_edges():
    try:
        clear_terminal()
        start_time = time.time()
        
        # Configuration parameters for random assignment
        org_has_address_probability = 0.7  # 70% of organizations will have at least one address
        max_addresses_per_org = 5  # Maximum number of addresses per organization
        min_addresses_per_org = 1  # Minimum number of addresses if organization has addresses
        
        # Read organization and address data
        print("Reading organization and address data...")
        with open('src/data/output/gds/mock_organization_data.json', 'r') as f:
            organization_data = json.load(f)
        
        with open('src/data/output/gds/mock_address_data.json', 'r') as f:
            address_data = json.load(f)
        
        organization_df = pd.DataFrame(organization_data)
        address_df = pd.DataFrame(address_data)
        
        # Print data statistics
        print(f"\nData Statistics:")
        print(f"Total number of organizations: {len(organization_df)}")
        print(f"Total number of addresses: {len(address_df)}")
        
        # Convert to lists and create address details map for faster access
        organization_ids = organization_df['node_id'].tolist()
        address_ids = address_df['node_id'].tolist()
        
        # Create address details map for faster lookup
        address_details_map = {}
        for _, address in address_df.iterrows():
            address_details_map[address['node_id']] = address['node_properties']
        
        # Initialize edge data and counters
        edges = []
        edge_type_count = 0
        organizations_with_addresses = 0
        organizations_without_addresses = 0
        
        # Optimized batch processing with multiprocessing
        print("\nGenerating organization_address edges with optimized processing...")
        
        # Calculate optimal batch size based on data size
        total_organizations = len(organization_ids)
        num_cores = mp.cpu_count()
        batch_size = max(1, total_organizations // (num_cores * 2))  # Larger batches for better performance
        
        print(f"Using {num_cores} CPU cores with batch size of {batch_size}")
        
        # Create batches
        batches = []
        for i in range(0, total_organizations, batch_size):
            batch_end = min(i + batch_size, total_organizations)
            batch_organization_ids = organization_ids[i:batch_end]
            batches.append((batch_organization_ids, address_ids, address_details_map, i))
        
        # Process batches in parallel
        with ThreadPoolExecutor(max_workers=num_cores) as executor:
            # Submit all batches
            future_to_batch = {executor.submit(process_organization_batch, batch): batch for batch in batches}
            
            # Collect results with progress bar
            for future in tqdm(as_completed(future_to_batch), total=len(batches), desc="Processing batches"):
                batch_edges = future.result()
                edges.extend(batch_edges)
                edge_type_count += len(batch_edges)
        
        # Count organizations with and without addresses
        organizations_with_addresses = sum(1 for org_id in organization_ids 
                                         if any(edge['node_id_from'] == org_id for edge in edges))
        organizations_without_addresses = total_organizations - organizations_with_addresses
        
        # Save all edges as a single JSON array
        os.makedirs('src/data/output/gds', exist_ok=True)
        with open('src/data/output/gds/mock_organization-address_data.json', 'w') as f:
            json.dump(edges, f, indent=2)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Validate referential integrity
        validation_results = validate_referential_integrity(edges, organization_df, address_df)
        
        clear_terminal()
        # Print validation results
        print("\nReferential Integrity Validation Results:")
        print(f"Total edges generated: {validation_results['total_edges']}")
        print(f"Valid edges: {validation_results['valid_edges']}")
        print(f"Invalid edges: {validation_results['invalid_edges']}")
        
        # Calculate and display edges per organization distribution
        edges_per_org_dist = {}
        for org_id, count in validation_results['edges_per_organization'].items():
            edges_per_org_dist[count] = edges_per_org_dist.get(count, 0) + 1
        
        print("\nDistribution of Address Edges per Organization:")
        for count in sorted(edges_per_org_dist.keys()):
            print(f"Organizations with {count} address edges: {edges_per_org_dist[count]}")
        
        # Calculate and display addresses per organization distribution
        addresses_per_org_dist = {}
        for org_id, addresses in validation_results['addresses_per_organization'].items():
            num_addresses = len(addresses)
            addresses_per_org_dist[num_addresses] = addresses_per_org_dist.get(num_addresses, 0) + 1
        
        print("\nDistribution of Unique Addresses per Organization:")
        for count in sorted(addresses_per_org_dist.keys()):
            print(f"Organizations with {count} unique addresses: {addresses_per_org_dist[count]}")
        
        # Calculate and display organizations per address distribution
        orgs_per_addr_dist = {}
        for addr_id, organizations in validation_results['organizations_per_address'].items():
            num_orgs = len(organizations)
            orgs_per_addr_dist[num_orgs] = orgs_per_addr_dist.get(num_orgs, 0) + 1
        
        print("\nDistribution of Organizations per Address:")
        for count in sorted(orgs_per_addr_dist.keys()):
            print(f"Addresses with {count} organizations: {orgs_per_addr_dist[count]}")
        
        # Print processing statistics
        print(f"\nProcessing Statistics:")
        print(f"Total processing time: {processing_time:.2f} seconds")
        print(f"Edges generated per second: {edge_type_count / processing_time:.2f}")
        print(f"Average edges per organization: {edge_type_count / len(organization_ids):.2f}")
        print(f"Organizations with addresses: {organizations_with_addresses}")
        print(f"Organizations without addresses: {organizations_without_addresses}")
        
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
        print(f"Error generating organization-address edges: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    generate_organization_address_edges()
