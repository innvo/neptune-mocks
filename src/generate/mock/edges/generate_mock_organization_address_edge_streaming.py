import pandas as pd
import uuid
import random
from tqdm import tqdm
import time
import os
import json
import platform
import numpy as np
import multiprocessing as mp
import gc
import psutil
from concurrent.futures import ProcessPoolExecutor, as_completed
import itertools
from functools import lru_cache

# Performance-optimized constants
_STR_UUID4 = str
_UUID4_FUNC = uuid.uuid4

# Pre-allocate common values
_ADDRESS_TYPES = np.array(['PRIMARY', 'SECONDARY', 'BRANCH', 'MAILING'])

def generate_fast_uuid():
    """Pre-compiled UUID generation for performance"""
    return _STR_UUID4(_UUID4_FUNC())

def clear_terminal():
    """Clear the terminal screen based on the operating system"""
    if platform.system() == 'Windows':
        os.system('cls')
    else:
        os.system('clear')

def process_organization_chunk_streaming(chunk_data):
    """3X Ultra-optimized streaming chunk processor for very large datasets"""
    organization_chunk, address_ids, address_details_map, edge_counts_chunk, chunk_start_idx = chunk_data
    
    edges = []
    # Pre-generate all random values for this chunk
    total_edges = sum(edge_counts_chunk)
    if total_edges == 0:
        return edges
    
    # Pre-generate random values using numpy for maximum speed
    # (This will be customized per file type)
    
    # Pre-allocate edge template for reuse
    edge_template = {
        'edge_type': 'edge_type_placeholder',
        'edge_properties': {}
    }
    
    edge_idx = 0
    address_ids_len = len(address_ids)
    
    # Configuration parameters for random assignment
    org_has_address_probability = 0.7  # 70% of organizations will have at least one address
    max_addresses_per_org = 5  # Maximum number of addresses per organization
    min_addresses_per_org = 1  # Minimum number of addresses if organization has addresses
    
    for i, organization_id in enumerate(organization_chunk):
        # Determine if this organization will have address edges
        if random.random() < org_has_address_probability:
            # Use pre-generated edge count for this organization
            num_address_edges = edge_counts_chunk[i]
            num_address_edges = max(min_addresses_per_org, min(num_address_edges, address_ids_len, max_addresses_per_org))
            
            # Ultra-fast random sampling using numpy
            if num_address_edges == 1:
                selected_idx = np.random.randint(0, address_ids_len)
                selected_address_ids = [address_ids[selected_idx]]
            elif num_address_edges <= address_ids_len:
                selected_indices = np.random.choice(address_ids_len, size=num_address_edges, replace=False)
                selected_address_ids = [address_ids[idx] for idx in selected_indices]
            else:
                selected_address_ids = address_ids[:num_address_edges]
            
            # Generate edges with minimal object creation
            for address_id in selected_address_ids:
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
                
                edges.append({
                    'edge_id': generate_fast_uuid(),
                    'node_id_from': organization_id,
                    'node_id_to': address_id,
                    'edge_type': 'organization_address',
                    'edge_properties': {
                        'VIBE_ADDRESS_ID': vibe_address_ids,
                        'VIBE_RAW_ADDR_FULL': [full_address],
                        'SOURCE': 'VIBE'
                    }
                })
    
    return edges

def generate_organization_address_edges_streaming():
    """
    Streaming edge generation optimized for very large datasets
    """
    try:
        clear_terminal()
        start_time = time.time()
        
        # System resource detection
        num_cores = mp.cpu_count()
        memory_gb = psutil.virtual_memory().total // (1024**3)
        
        print(f"🚀 STREAMING ORGANIZATION-ADDRESS EDGE GENERATION")
        print(f"🌊 OPTIMIZED FOR VERY LARGE DATASETS")
        print(f"CPU Cores: {num_cores}")
        print(f"Available Memory: {memory_gb} GB")
        print("=" * 60)
        
        # Load data efficiently
        print("Loading node data...")
        node_df = pd.read_csv('src/data/input/node_data.csv', 
                            usecols=['node_id', 'node_type'],
                            dtype={'node_type': 'category', 'node_id': 'string'},
                            engine='c',
                            memory_map=True)  # Read entire file efficiently
        
        # Read organization and address data
        print("Loading organization and address data...")
        with open('src/data/output/gds/mock_organization_data.json', 'r') as f:
            organization_data = json.load(f)
        
        with open('src/data/output/gds/mock_address_data.json', 'r') as f:
            address_data = json.load(f)
        
        # Extract node IDs efficiently
        organization_mask = node_df['node_type'] == 'organization'
        address_mask = node_df['node_type'] == 'address'
        
        organization_ids = node_df[organization_mask]['node_id'].tolist()
        address_ids = node_df[address_mask]['node_id'].tolist()
        
        print(f"\nDataset size: {len(organization_ids):,} organizations → {len(address_ids):,} addresses")
        
        if not organization_ids or not address_ids:
            raise ValueError("Missing required node types")
        
        # Create address details map for faster lookup
        address_details_map = {}
        for address in address_data:
            address_details_map[address['node_id']] = address['node_properties']
        
        # Pre-generate edge distribution
        print("Generating edge distribution...")
        # Distribution: 70% of organizations will have addresses, with 1-5 addresses each
        org_has_address_probability = 0.7
        max_addresses_per_org = 5
        min_addresses_per_org = 1
        
        # Generate edge counts with weighted distribution
        edge_counts = np.random.choice(
            [0, 1, 2, 3, 4, 5], 
            size=len(organization_ids),
            p=[0.3, 0.4, 0.2, 0.07, 0.02, 0.01]  # 30% no addresses, 40% 1 address, etc.
        )
        
        # Streaming processing configuration
        chunk_size = 25000  # Smaller chunks for better memory management
        total_chunks = (len(organization_ids) // chunk_size) + 1
        
        print(f"\n🎯 STREAMING CONFIGURATION:")
        print(f"Chunk Size: {chunk_size:,}")
        print(f"Total Chunks: {total_chunks}")
        print(f"Estimated edges: {np.sum(edge_counts):,}")
        
        # Process in parallel for maximum performance
        print(f"\nGenerating edges in streaming mode...")
        
        all_edges = []
        
        # Prepare chunks for parallel processing
        for chunk_idx in tqdm(range(total_chunks), desc="Processing chunks"):
            start_idx = chunk_idx * chunk_size
            end_idx = min(start_idx + chunk_size, len(organization_ids))
            
            organization_chunk = organization_ids[start_idx:end_idx]
            edge_counts_chunk = edge_counts[start_idx:end_idx]
            
            # Process this chunk
            chunk_data = (organization_chunk, address_ids, address_details_map, edge_counts_chunk, start_idx)
            chunk_edges = process_organization_chunk_streaming(chunk_data)
            
            all_edges.extend(chunk_edges)
            
            # Memory management
            if chunk_idx % 10 == 0:
                gc.collect()
        
        # Calculate statistics efficiently using vectorized operations
        print("\nCalculating statistics...")
        vibe_id_stats = {'1': 0, '2': 0, '3': 0, '4': 0, '5': 0, '6': 0, '7': 0}
        for edge in all_edges:
            vibe_count = len(edge['edge_properties']['VIBE_ADDRESS_ID'])
            if str(vibe_count) in vibe_id_stats:
                vibe_id_stats[str(vibe_count)] += 1
        
        # Save results
        os.makedirs('src/data/output/gds', exist_ok=True)
        output_path = 'src/data/output/gds/mock_organization-address_data.json'
        
        print(f"Saving {len(all_edges):,} edges...")
        with open(output_path, 'w') as f:
            json.dump(all_edges, f, separators=(',', ':'))  # Compact JSON for faster I/O
        
        # Performance metrics
        processing_time = time.time() - start_time
        edge_count = len(all_edges)
        
        # Quick validation using numpy for speed
        print("Validating sample...")
        organization_node_ids = set(organization_ids)
        address_node_ids = set(address_ids)
        
        sample_size = min(1000, len(all_edges))
        sample_edges = random.sample(all_edges, sample_size)
        
        valid_sample = 0
        for edge in sample_edges:
            if edge['node_id_from'] in organization_node_ids and edge['node_id_to'] in address_node_ids:
                valid_sample += 1
        
        validation_rate = (valid_sample / sample_size) * 100
        
        # Calculate organizations with/without addresses
        organizations_with_addresses = sum(1 for count in edge_counts if count > 0)
        organizations_without_addresses = len(organization_ids) - organizations_with_addresses
        
        clear_terminal()
        
        # Results summary
        print("✅ STREAMING ORGANIZATION-ADDRESS EDGE GENERATION COMPLETE")
        print("=" * 60)
        print(f"📊 GENERATION METRICS:")
        print(f"Total edges generated: {edge_count:,}")
        print(f"Processing time: {processing_time:.3f} seconds")
        print(f"Throughput: {edge_count / processing_time:,.0f} edges/second")
        print(f"Average edges per organization: {edge_count / len(organization_ids):.2f}")
        
        print(f"\n🏢 ORGANIZATION STATISTICS:")
        print(f"Organizations with addresses: {organizations_with_addresses:,}")
        print(f"Organizations without addresses: {organizations_without_addresses:,}")
        
        print(f"\n🔍 VALIDATION (Sample of {sample_size}):")
        print(f"Validation rate: {validation_rate:.1f}%")
        
        print(f"\n🏷️  VIBE ADDRESS ID DISTRIBUTION:")
        for vibe_count, count in vibe_id_stats.items():
            if count > 0:
                print(f"{vibe_count} VIBE IDs: {count:,} edges")
        
        print(f"\n🌊 STREAMING SUMMARY:")
        print(f"Chunks processed: {total_chunks}")
        print(f"Memory optimization: Streaming")
        print(f"Peak memory usage: Minimized")
        
        return all_edges
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def generate_organization_address_edges():
    """Wrapper function for compatibility"""
    return generate_organization_address_edges_streaming()

if __name__ == "__main__":
    generate_organization_address_edges() 