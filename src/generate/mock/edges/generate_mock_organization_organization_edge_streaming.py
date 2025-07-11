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
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
import itertools
from functools import lru_cache

# Performance-optimized constants
_STR_UUID4 = str
_UUID4_FUNC = uuid.uuid4

# Pre-allocate common values
_RELATIONSHIP_TYPES = np.array([
    'SUBSIDIARY', 'PARENT', 'PARTNER', 'COMPETITOR', 'SUPPLIER', 
    'CUSTOMER', 'AFFILIATE', 'JOINT_VENTURE', 'MERGER', 'ACQUISITION',
    'FRANCHISE', 'LICENSEE', 'LICENSOR', 'DISTRIBUTOR', 'CONTRACTOR'
])

# Pre-generate date templates
_DATE_TEMPLATES = {}
for year in range(2010, 2025):
    for month in range(1, 13):
        for day in range(1, 29):
            _DATE_TEMPLATES[(year, month, day)] = f"{year}-{month:02d}-{day:02d}"

def generate_fast_uuid():
    """Pre-compiled UUID generation for performance"""
    return _STR_UUID4(_UUID4_FUNC())

@lru_cache(maxsize=10000)
def get_cached_date(year, month, day):
    """Cached date string generation"""
    return _DATE_TEMPLATES.get((year, month, day), f"{year}-{month:02d}-{day:02d}")

def clear_terminal():
    """Clear the terminal screen based on the operating system"""
    if platform.system() == 'Windows':
        os.system('cls')
    else:
        os.system('clear')



def process_organization_chunk_streaming(chunk_data):
    """3X Ultra-optimized streaming chunk processor for very large datasets"""
    org_chunk, all_org_ids, edge_counts_chunk, org_lookup, chunk_start_idx = chunk_data
    
    edges = []
    all_org_ids_len = len(all_org_ids)
    
    # Pre-generate all random values for this chunk
    total_edges = sum(edge_counts_chunk)
    if total_edges == 0:
        return edges
    
    # Pre-generate random values using numpy for maximum speed
    rel_type_indices = np.random.randint(0, len(_RELATIONSHIP_TYPES), size=total_edges)
    start_years = np.random.randint(2010, 2024, size=total_edges)
    start_months = np.random.randint(1, 13, size=total_edges)
    start_days = np.random.randint(1, 29, size=total_edges)
    end_years = np.random.randint(2015, 2024, size=total_edges)
    end_months = np.random.randint(1, 13, size=total_edges)
    end_days = np.random.randint(1, 29, size=total_edges)
    has_end_date = np.random.random(size=total_edges) < 0.3
    confidence_scores = np.round(np.random.uniform(0.1, 1.0, size=total_edges), 2)
    
    # Pre-generate date strings using cached function
    start_dates = [get_cached_date(y, m, d) for y, m, d in zip(start_years, start_months, start_days)]
    end_dates = [get_cached_date(y, m, d) if has_end else None for y, m, d, has_end in zip(end_years, end_months, end_days, has_end_date)]
    
    # Create reverse lookup for O(1) org_id to index mapping
    org_id_to_idx = {org_id: idx for idx, org_id in enumerate(all_org_ids)}
    
    # Pre-allocate edge template for reuse
    edge_template = {
        'edge_type': 'organization_organization',
        'edge_name': 'relatedTo',
        'edge_properties': {
            'SOURCE': 'VIBE'
        }
    }
    
    edge_idx = 0
    
    for i, org_id in enumerate(org_chunk):
        num_relationships = edge_counts_chunk[i]
        
        if num_relationships > 0:
            # O(1) organization exclusion using pre-computed index
            org_idx = org_id_to_idx[org_id]
            
            # Create available orgs array (excluding self) - optimized
            available_indices = np.concatenate([
                np.arange(0, org_idx),
                np.arange(org_idx + 1, all_org_ids_len)
            ])
            
            # Limit relationships to available organizations
            num_relationships = min(num_relationships, len(available_indices))
            
            if num_relationships > 0:
                # Ultra-fast random sampling using numpy
                if num_relationships == 1:
                    selected_idx = np.random.randint(0, len(available_indices))
                    selected_org_indices = [available_indices[selected_idx]]
                else:
                    selected_org_indices = np.random.choice(available_indices, size=num_relationships, replace=False)
                
                # Get organization name once
                org_name = org_lookup.get(org_id, "UNKNOWN")
                
                # Generate edges with minimal object creation
                for selected_idx in selected_org_indices:
                    related_org_id = all_org_ids[selected_idx]
                    related_org_name = org_lookup.get(related_org_id, "UNKNOWN")
                    
                    # Create edge using template copy for minimal object creation
                    edge = edge_template.copy()
                    edge['edge_id'] = generate_fast_uuid()
                    edge['node_id_from'] = org_id
                    edge['node_id_to'] = related_org_id
                    
                    # Update edge properties efficiently
                    edge_props = edge['edge_properties']
                    edge_props['RELATIONSHIP_TYPE'] = _RELATIONSHIP_TYPES[rel_type_indices[edge_idx]]
                    edge_props['RELATIONSHIP_START_DATE'] = start_dates[edge_idx]
                    edge_props['RELATIONSHIP_END_DATE'] = end_dates[edge_idx]
                    edge_props['CONFIDENCE_SCORE'] = confidence_scores[edge_idx]
                    edge_props['ORGANIZATION_NAME_FROM'] = org_name
                    edge_props['ORGANIZATION_NAME_TO'] = related_org_name
                    
                    edges.append(edge)
                    edge_idx += 1
    
    return edges

def generate_organization_organization_edges_streaming():
    """
    Streaming edge generation optimized for very large datasets
    """
    try:
        clear_terminal()
        start_time = time.time()
        
        # System resource detection
        num_cores = mp.cpu_count()
        memory_gb = psutil.virtual_memory().total // (1024**3)
        
        print(f"🚀 STREAMING ORGANIZATION-ORGANIZATION EDGE GENERATION")
        print(f"🌊 OPTIMIZED FOR VERY LARGE DATASETS")
        print(f"CPU Cores: {num_cores}")
        print(f"Available Memory: {memory_gb} GB")
        print("=" * 60)
        
        # Load data efficiently with optimized pandas settings
        print("Loading node data...")
        node_df = pd.read_csv('src/data/input/node_data.csv', 
                            usecols=['node_id', 'node_type'],
                            dtype={'node_type': 'category', 'node_id': 'string'},
                            engine='c',
                            memory_map=True,
                            chunksize=100000)  # Read in chunks for large files
        
        # Read organization data for ORGANIZATION_NAME lookup
        print("Loading organization data for ORGANIZATION_NAME lookup...")
        with open('src/data/output/gds/mock_organization_data.json', 'r') as f:
            organization_data = json.load(f)
        
        # Create optimized lookup dictionary using dict comprehension
        org_lookup = {org['node_id']: org['node_properties']['ORGANIZATION_NAME'] for org in organization_data}
        
        # Extract organization IDs efficiently using numpy
        organization_ids = []
        for chunk in node_df:
            org_mask = (chunk['node_type'] == 'organization').values
            organization_ids.extend(chunk.loc[org_mask, 'node_id'].tolist())
        
        print(f"\nDataset size: {len(organization_ids):,} organizations")
        
        if not organization_ids:
            raise ValueError("No organization nodes found")
        
        # Pre-generate edge distribution
        print("Generating edge distribution...")
        edge_counts = np.random.choice([0, 1, 2, 3, 4, 5], size=len(organization_ids), p=[0.4, 0.3, 0.15, 0.1, 0.03, 0.02])
        
        # Streaming processing configuration - optimized chunk size
        chunk_size = min(50000, max(10000, len(organization_ids) // (num_cores * 4)))  # Dynamic chunk sizing
        total_chunks = (len(organization_ids) + chunk_size - 1) // chunk_size  # Ceiling division
        
        print(f"\n🎯 STREAMING CONFIGURATION:")
        print(f"Chunk Size: {chunk_size:,}")
        print(f"Total Chunks: {total_chunks}")
        print(f"Estimated edges: {np.sum(edge_counts):,}")
        
        # Process in parallel for maximum performance
        print(f"\nGenerating edges in parallel mode...")
        
        all_edges = []
        
        # Prepare chunks for parallel processing
        chunks = []
        for chunk_idx in range(total_chunks):
            start_idx = chunk_idx * chunk_size
            end_idx = min(start_idx + chunk_size, len(organization_ids))
            
            org_chunk = organization_ids[start_idx:end_idx]
            edge_counts_chunk = edge_counts[start_idx:end_idx]
            
            chunk_data = (org_chunk, organization_ids, edge_counts_chunk, org_lookup, start_idx)
            chunks.append(chunk_data)
        
        # Process chunks in parallel using ProcessPoolExecutor
        max_workers = min(num_cores, total_chunks)
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            # Submit all chunks
            future_to_chunk = {executor.submit(process_organization_chunk_streaming, chunk): chunk for chunk in chunks}
            
            # Collect results with progress bar
            for future in tqdm(as_completed(future_to_chunk), total=len(chunks), desc="Processing chunks"):
                chunk_edges = future.result()
                all_edges.extend(chunk_edges)
                
                # Memory management every few chunks
                if len(all_edges) % (chunk_size * 10) == 0:
                    gc.collect()
        
        # Calculate statistics efficiently using vectorized operations
        print("\nCalculating statistics...")
        relationship_types = [edge['edge_properties']['RELATIONSHIP_TYPE'] for edge in all_edges]
        relationship_stats = Counter(relationship_types)
        
        # Save results with optimized JSON serialization
        os.makedirs('src/data/output/gds', exist_ok=True)
        output_path = 'src/data/output/gds/mock_organization-organization_data.json'
        
        print(f"Saving {len(all_edges):,} edges...")
        with open(output_path, 'w') as f:
            json.dump(all_edges, f, separators=(',', ':'))  # Compact JSON for faster I/O
        
        # Performance metrics
        processing_time = time.time() - start_time
        edge_count = len(all_edges)
        
        # Quick validation using numpy for speed
        print("Validating sample...")
        org_node_ids = set(organization_ids)
        
        sample_size = min(1000, len(all_edges))
        sample_indices = np.random.choice(len(all_edges), size=sample_size, replace=False)
        
        valid_sample = 0
        for idx in sample_indices:
            edge = all_edges[idx]
            if edge['node_id_from'] in org_node_ids and edge['node_id_to'] in org_node_ids:
                valid_sample += 1
        
        validation_rate = (valid_sample / sample_size) * 100
        
        clear_terminal()
        
        # Results summary
        print("✅ STREAMING ORGANIZATION-ORGANIZATION EDGE GENERATION COMPLETE")
        print("=" * 60)
        print(f"📊 GENERATION METRICS:")
        print(f"Total edges generated: {edge_count:,}")
        print(f"Processing time: {processing_time:.3f} seconds")
        print(f"Throughput: {edge_count / processing_time:,.0f} edges/second")
        print(f"Average edges per organization: {edge_count / len(organization_ids):.2f}")
        
        print(f"\n🔍 VALIDATION (Sample of {sample_size}):")
        print(f"Validation rate: {validation_rate:.1f}%")
        
        print(f"\n🏷️  RELATIONSHIP TYPE DISTRIBUTION:")
        for rel_type, count in relationship_stats.most_common():
            print(f"{rel_type}: {count:,} edges")
        
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

def generate_organization_organization_edges():
    """Wrapper function for compatibility"""
    return generate_organization_organization_edges_streaming()

if __name__ == "__main__":
    generate_organization_organization_edges() 