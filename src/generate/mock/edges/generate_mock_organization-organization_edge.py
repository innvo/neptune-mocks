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
            'organization': {'total': 0, 'valid': 0}
        },
        'edges_per_organization': {},  # Track edges per organization
        'organizations_per_organization': {}  # Track unique organizations per organization
    }
    
    # Get sets of valid node IDs for quick lookup
    valid_node_ids = set(node_df['node_id'].values)
    organization_node_ids = set(node_df[node_df['node_type'] == 'organization']['node_id'].values)
    
    # Initialize counters
    for org_id in organization_node_ids:
        validation_results['edges_per_organization'][org_id] = 0
        validation_results['organizations_per_organization'][org_id] = set()
    
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
        from_node_is_organization = from_node in organization_node_ids
        to_node_is_organization = to_node in organization_node_ids
        
        if from_node_exists and to_node_exists and from_node_is_organization and to_node_is_organization:
            validation_results['valid_edges'] += 1
            validation_results['node_type_stats']['organization']['valid'] += 1
            validation_results['edges_per_organization'][from_node] += 1
            validation_results['organizations_per_organization'][from_node].add(to_node)
        else:
            validation_results['invalid_edges'] += 1
            if not from_node_exists or not from_node_is_organization:
                validation_results['missing_from_nodes'].add(from_node)
            if not to_node_exists or not to_node_is_organization:
                validation_results['missing_to_nodes'].add(to_node)
    
    # Update total counts
    validation_results['node_type_stats']['organization']['total'] = len(organization_node_ids)
    
    return validation_results

def process_organization_batch(batch_data):
    """Process a batch of organizations to generate organization edges"""
    organization_ids, all_organization_ids, batch_start_idx = batch_data
    batch_edges = []
    used_pairs = set()
    
    # Configuration for edge generation
    org_has_relationship_probability = 0.6  # 60% of organizations will have relationships
    max_relationships_per_org = 5
    
    # Relationship types for organizations
    relationship_types = [
        'SUBSIDIARY', 'PARENT', 'PARTNER', 'COMPETITOR', 'SUPPLIER', 
        'CUSTOMER', 'AFFILIATE', 'JOINT_VENTURE', 'MERGER', 'ACQUISITION',
        'FRANCHISE', 'LICENSEE', 'LICENSOR', 'DISTRIBUTOR', 'CONTRACTOR'
    ]
    
    for i, org_id in enumerate(organization_ids):
        # Determine if this organization will have relationships with other organizations
        if random.random() < org_has_relationship_probability:
            # Get available organizations that haven't been used with this organization
            available_orgs = [oid for oid in all_organization_ids 
                            if oid != org_id and (org_id, oid) not in used_pairs]
            
            # If no available organizations, reuse some (excluding self)
            if len(available_orgs) == 0:
                available_orgs = [oid for oid in all_organization_ids if oid != org_id]
            
            # Random number of relationships (1 to max_relationships_per_org)
            num_relationships = random.randint(1, min(max_relationships_per_org, len(available_orgs)))
            
            # Randomly select organizations without replacement
            selected_orgs = random.sample(available_orgs, num_relationships)
            
            for related_org_id in selected_orgs:
                # Add to used pairs
                pair_key = (org_id, related_org_id)
                used_pairs.add(pair_key)
                
                # Generate random relationship type
                relationship_type = random.choice(relationship_types)
                
                # Generate random dates for the relationship
                start_date = f"{random.randint(2010, 2024)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
                end_date = None
                if random.random() < 0.3:  # 30% chance of having an end date
                    end_date = f"{random.randint(2015, 2024)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
                
                # Generate random confidence score
                confidence_score = round(random.uniform(0.1, 1.0), 2)
                
                batch_edges.append({
                    'edge_id': str(uuid.uuid4()),
                    'node_id_from': org_id,
                    'node_id_to': related_org_id,
                    'edge_type': 'organization_organization',
                    'edge_name': 'relatedTo',
                    'edge_properties': {
                        'RELATIONSHIP_TYPE': relationship_type,
                        'RELATIONSHIP_START_DATE': start_date,
                        'RELATIONSHIP_END_DATE': end_date,
                        'CONFIDENCE_SCORE': confidence_score,
                        'SOURCE': 'VIBE'
                    }
                })
    
    return batch_edges

def generate_organization_organization_edges():
    try:
        clear_terminal()
        start_time = time.time()
        
        # Read organization data from mock_organization_data.json to ensure consistency
        print("Reading organization data from mock_organization_data.json...")
        with open('src/data/output/gds/mock_organization_data.json', 'r') as f:
            organization_data = json.load(f)
        
        # Extract organization IDs from the JSON data
        organization_ids = [org['node_id'] for org in organization_data]
        print(f"Found {len(organization_ids)} organization IDs from mock_organization_data.json")
        
        # Read organization data from node_data.csv for validation
        print("Reading organization data from node_data.csv...")
        node_df = pd.read_csv('src/data/input/node_data.csv', usecols=['node_id', 'node_type'])
        
        # Get organization nodes
        organization_nodes = node_df[node_df['node_type'] == 'organization']
        if organization_nodes.empty:
            print("Warning: No organization nodes found in node_data.csv")
            return None
        
        print(f"Found {len(organization_nodes)} organization nodes")
        
        # Initialize edge data and counters
        edges = []
        edge_type_count = 0
        
        # Optimized batch processing with multiprocessing
        print("\nGenerating organization_organization edges with optimized processing...")
        
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
            batches.append((batch_organization_ids, organization_ids, i))
        
        # Process batches in parallel
        with ThreadPoolExecutor(max_workers=num_cores) as executor:
            # Submit all batches
            future_to_batch = {executor.submit(process_organization_batch, batch): batch for batch in batches}
            
            # Collect results with progress bar
            for future in tqdm(as_completed(future_to_batch), total=len(batches), desc="Processing batches"):
                batch_edges = future.result()
                edges.extend(batch_edges)
                edge_type_count += len(batch_edges)
        
        # Save all edges as a single JSON array
        os.makedirs('src/data/output/gds', exist_ok=True)
        with open('src/data/output/gds/mock_organization-organization_data.json', 'w') as f:
            json.dump(edges, f, indent=2)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Create a combined node dataframe for validation
        # Create organization nodes dataframe from mock_organization_data.json
        organization_nodes_data = []
        for org in organization_data:
            organization_nodes_data.append({
                'node_id': org['node_id'],
                'node_type': 'organization'
            })
        organization_nodes_df = pd.DataFrame(organization_nodes_data)
        
        # Validate referential integrity
        validation_results = validate_referential_integrity(edges, organization_nodes_df)
        
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
        
        print("\nDistribution of Organization Edges per Organization:")
        for count in sorted(edges_per_org_dist.keys()):
            print(f"Organizations with {count} organization edges: {edges_per_org_dist[count]}")
        
        # Calculate and display organizations per organization distribution
        orgs_per_org_dist = {}
        for org_id, orgs in validation_results['organizations_per_organization'].items():
            num_orgs = len(orgs)
            orgs_per_org_dist[num_orgs] = orgs_per_org_dist.get(num_orgs, 0) + 1
        
        print("\nDistribution of Unique Organizations per Organization:")
        for count in sorted(orgs_per_org_dist.keys()):
            print(f"Organizations with {count} unique organization relationships: {orgs_per_org_dist[count]}")
        
        # Print processing statistics
        print(f"\nProcessing Statistics:")
        print(f"Total processing time: {processing_time:.2f} seconds")
        print(f"Edges generated per second: {edge_type_count / processing_time:.2f}")
        print(f"Average edges per organization: {edge_type_count / len(organization_ids):.2f}")
        
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
        print(f"Error generating organization-organization edges: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    generate_organization_organization_edges()
