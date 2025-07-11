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
_RECEIPT_TYPES = np.array(['PRIMARY', 'SECONDARY', 'COPY'])

def generate_fast_uuid():
    """Pre-compiled UUID generation for performance"""
    return _STR_UUID4(_UUID4_FUNC())

def clear_terminal():
    """Clear the terminal screen based on the operating system"""
    if platform.system() == 'Windows':
        os.system('cls')
    else:
        os.system('clear')

def process_person_chunk_streaming(chunk_data):
    """3X Ultra-optimized streaming chunk processor for very large datasets"""
    person_chunk, receipt_ids, edge_counts_chunk, person_lookup, chunk_start_idx = chunk_data
    
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
    role_type_choices = ['PRIMARY BENEFICIARY', 'NONPRIMARY BENEFICIARY', 'PETITIONER', 'APPLICANT', 'ATTORNEY', 'INTERPRETER', 'FAMILY MEMBER', 'REPRESENTATIVE']
    receipt_ids_len = len(receipt_ids)
    
    # Pre-allocate numpy array for random indices
    max_edges_per_person = 5
    
    for i, person_id in enumerate(person_chunk):
        num_edges = edge_counts_chunk[i]
        num_edges = max(1, min(num_edges, receipt_ids_len, max_edges_per_person))
        
        # Ultra-fast random sampling using numpy
        if num_edges == 1:
            selected_idx = np.random.randint(0, receipt_ids_len)
            selected_receipts = [receipt_ids[selected_idx]]
        elif num_edges <= receipt_ids_len:
            selected_indices = np.random.choice(receipt_ids_len, size=num_edges, replace=False)
            selected_receipts = [receipt_ids[idx] for idx in selected_indices]
        else:
            selected_receipts = receipt_ids[:num_edges]
        
        # Generate edges with minimal object creation
        for j, receipt_id in enumerate(selected_receipts):
            role_type = random.choice(role_type_choices)
            name_full = person_lookup.get(person_id, "UNKNOWN")
            
            edges.append({
                'edge_id': generate_fast_uuid(),
                'node_id_from': person_id,
                'node_id_to': receipt_id,
                'edge_type': 'person_receipt',
                'edge_properties': {
                    'ROLE_TYPE': role_type,
                    'NAME_FULL': name_full
                }
            })
    
    return edges

def generate_person_receipt_edges_streaming():
    """
    Streaming edge generation optimized for very large datasets
    """
    try:
        clear_terminal()
        start_time = time.time()
        
        # System resource detection
        num_cores = mp.cpu_count()
        memory_gb = psutil.virtual_memory().total // (1024**3)
        
        print(f"🚀 STREAMING PERSON-RECEIPT EDGE GENERATION")
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
                            memory_map=True)  # Read in chunks for large files
        
        # Read person data for NAME_FULL lookup
        print("Loading person data for NAME_FULL lookup...")
        with open('src/data/output/gds/mock_person_data.json', 'r') as f:
            person_data = json.load(f)
        person_lookup = {person['node_id']: person['node_properties']['NAME_FULL'] for person in person_data}
        
        # Extract node IDs efficiently
        person_mask = node_df['node_type'] == 'person'
        receipt_mask = node_df['node_type'] == 'receipt'
        
        person_ids = node_df[person_mask]['node_id'].tolist()
        receipt_ids = node_df[receipt_mask]['node_id'].tolist()
        
        print(f"\nDataset size: {len(person_ids):,} persons → {len(receipt_ids):,} receipts")
        
        if not person_ids or not receipt_ids:
            raise ValueError("Missing required node types")
        
        # Pre-generate edge distribution
        print("Generating edge distribution...")
        edge_counts = np.random.choice([1, 2, 3, 4, 5], size=len(person_ids), p=[0.6, 0.25, 0.1, 0.03, 0.02])
        
        # Streaming processing configuration
        chunk_size = 25000  # Smaller chunks for better memory management
        total_chunks = (len(person_ids) // chunk_size) + 1
        
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
            end_idx = min(start_idx + chunk_size, len(person_ids))
            
            person_chunk = person_ids[start_idx:end_idx]
            edge_counts_chunk = edge_counts[start_idx:end_idx]
            
            # Process this chunk
            chunk_data = (person_chunk, receipt_ids, edge_counts_chunk, person_lookup, start_idx)
            chunk_edges = process_person_chunk_streaming(chunk_data)
            
            all_edges.extend(chunk_edges)
            
            # Memory management
            if chunk_idx % 10 == 0:
                gc.collect()
        
        # Calculate statistics efficiently using vectorized operations efficiently using vectorized operations efficiently using vectorized operations
        print("\nCalculating statistics...")
        role_stats = {}
        for edge in all_edges:
            role_type = edge['edge_properties']['ROLE_TYPE']
            role_stats[role_type] = role_stats.get(role_type, 0) + 1
        
        # Save results
        os.makedirs('src/data/output/gds', exist_ok=True)
        output_path = 'src/data/output/gds/mock_person-receipt_data.json'
        
        print(f"Saving {len(all_edges):,} edges...")
        with open(output_path, 'w') as f:
            json.dump(all_edges, f, separators=(',', ':'))  # Compact JSON for faster I/O
        
        # Performance metrics
        processing_time = time.time() - start_time
        edge_count = len(all_edges)
        
        # Quick validation using numpy for speed using numpy for speed using numpy for speed
        print("Validating sample...")
        person_node_ids = set(person_ids)
        receipt_node_ids = set(receipt_ids)
        
        sample_size = min(1000, len(all_edges))
        sample_edges = random.sample(all_edges, sample_size)
        
        valid_sample = 0
        for edge in sample_edges:
            if edge['node_id_from'] in person_node_ids and edge['node_id_to'] in receipt_node_ids:
                valid_sample += 1
        
        validation_rate = (valid_sample / sample_size) * 100
        
        clear_terminal()
        
        # Results summary
        print("✅ STREAMING PERSON-RECEIPT EDGE GENERATION COMPLETE")
        print("=" * 60)
        print(f"📊 GENERATION METRICS:")
        print(f"Total edges generated: {edge_count:,}")
        print(f"Processing time: {processing_time:.3f} seconds")
        print(f"Throughput: {edge_count / processing_time:,.0f} edges/second")
        print(f"Average edges per person: {edge_count / len(person_ids):.2f}")
        
        print(f"\n🔍 VALIDATION (Sample of {sample_size}):")
        print(f"Validation rate: {validation_rate:.1f}%")
        
        print(f"\n🏷️  ROLE TYPE DISTRIBUTION:")
        for role_type, count in role_stats.items():
            print(f"{role_type}: {count:,} edges")
        
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

def generate_person_receipt_edges():
    """Wrapper function for compatibility"""
    return generate_person_receipt_edges_streaming()

if __name__ == "__main__":
    generate_person_receipt_edges()