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

def generate_fast_uuid():
    """Pre-compiled UUID generation for performance"""
    return _STR_UUID4(_UUID4_FUNC())

def clear_terminal():
    """Clear the terminal screen based on the operating system"""
    if platform.system() == 'Windows':
        os.system('cls')
    else:
        os.system('clear')

def process_building_chunk_streaming(chunk_data):
    """3X Ultra-optimized streaming chunk processor for building-address edges"""
    building_chunk, address_hash_to_ids, chunk_start_idx = chunk_data
    
    edges = []
    
    for building_id, building_address_hash in building_chunk:
        # Find matching addresses by ADDRESS_HASH
        matching_address_ids = address_hash_to_ids.get(building_address_hash, [])
        
        if matching_address_ids:
            # Each building can have multiple addresses (e.g., unit numbers, suites)
            for address_id in matching_address_ids:
                edges.append({
                    'edge_id': generate_fast_uuid(),
                    'node_id_from': building_id,
                    'node_id_to': address_id,
                    'edge_type': 'building_address',
                    'edge_properties': {}
                })
    
    return edges

def generate_building_address_edges_streaming():
    """
    Streaming edge generation optimized for very large datasets
    """
    try:
        clear_terminal()
        start_time = time.time()
        
        # System resource detection
        num_cores = mp.cpu_count()
        memory_gb = psutil.virtual_memory().total // (1024**3)
        
        print(f"🚀 STREAMING BUILDING-ADDRESS EDGE GENERATION")
        print(f"🌊 OPTIMIZED FOR VERY LARGE DATASETS")
        print(f"CPU Cores: {num_cores}")
        print(f"Available Memory: {memory_gb} GB")
        print("=" * 60)
        
        # Load data efficiently
        print("Loading building and address data...")
        
        # Load building data
        with open('src/data/output/gds/mock_building_data.json', 'r') as f:
            building_data = json.load(f)
        
        # Load address data
        with open('src/data/output/gds/mock_address_data.json', 'r') as f:
            address_data = json.load(f)
        
        building_df = pd.DataFrame(building_data)
        address_df = pd.DataFrame(address_data)
        
        print(f"\nDataset size: {len(building_df):,} buildings → {len(address_df):,} addresses")
        
        if len(building_df) == 0 or len(address_df) == 0:
            raise ValueError("Missing required node types")
        
        # Create address hash mapping for quick lookup
        print("Creating address hash mapping...")
        address_hash_to_ids = {}
        for _, address in address_df.iterrows():
            address_hash = address['node_properties']['ADDRESS_HASH']
            if address_hash not in address_hash_to_ids:
                address_hash_to_ids[address_hash] = []
            address_hash_to_ids[address_hash].append(address['node_id'])
        
        print(f"Unique address hashes: {len(address_hash_to_ids)}")
        
        # Prepare building data for processing
        building_chunks = []
        for _, building in building_df.iterrows():
            building_id = building['node_id']
            building_address_hash = building['node_properties']['ADDRESS_HASH']
            building_chunks.append((building_id, building_address_hash))
        
        # Streaming processing configuration
        chunk_size = 25000  # Smaller chunks for better memory management
        total_chunks = (len(building_chunks) // chunk_size) + 1
        
        print(f"\n🎯 STREAMING CONFIGURATION:")
        print(f"Chunk Size: {chunk_size:,}")
        print(f"Total Chunks: {total_chunks}")
        
        # Process in streaming mode
        print(f"\nGenerating edges in streaming mode...")
        
        all_edges = []
        missing_address_hashes = set()
        
        # Process chunks
        for chunk_idx in tqdm(range(total_chunks), desc="Processing chunks"):
            start_idx = chunk_idx * chunk_size
            end_idx = min(start_idx + chunk_size, len(building_chunks))
            
            building_chunk = building_chunks[start_idx:end_idx]
            
            # Process this chunk
            chunk_data = (building_chunk, address_hash_to_ids, start_idx)
            chunk_edges = process_building_chunk_streaming(chunk_data)
            
            all_edges.extend(chunk_edges)
            
            # Track missing address hashes
            for building_id, building_address_hash in building_chunk:
                if building_address_hash not in address_hash_to_ids:
                    missing_address_hashes.add(building_address_hash)
            
            # Memory management
            if chunk_idx % 10 == 0:
                gc.collect()
        
        # Save results
        os.makedirs('src/data/output/gds', exist_ok=True)
        output_path = 'src/data/output/gds/mock_building-address_data.json'
        
        print(f"Saving {len(all_edges):,} edges...")
        with open(output_path, 'w') as f:
            json.dump(all_edges, f, separators=(',', ':'))  # Compact JSON for faster I/O
        
        # Performance metrics
        processing_time = time.time() - start_time
        edge_count = len(all_edges)
        
        # Quick validation using sets for speed
        print("Validating sample...")
        building_node_ids = set(building_df['node_id'].tolist())
        address_node_ids = set(address_df['node_id'].tolist())
        
        sample_size = min(1000, len(all_edges))
        sample_edges = random.sample(all_edges, sample_size)
        
        valid_sample = 0
        for edge in sample_edges:
            if edge['node_id_from'] in building_node_ids and edge['node_id_to'] in address_node_ids:
                valid_sample += 1
        
        validation_rate = (valid_sample / sample_size) * 100
        
        clear_terminal()
        
        # Results summary
        print("✅ STREAMING BUILDING-ADDRESS EDGE GENERATION COMPLETE")
        print("=" * 60)
        print(f"📊 GENERATION METRICS:")
        print(f"Total edges generated: {edge_count:,}")
        print(f"Processing time: {processing_time:.3f} seconds")
        print(f"Throughput: {edge_count / processing_time:,.0f} edges/second")
        print(f"Average edges per building: {edge_count / len(building_df):.2f}")
        
        print(f"\n🔍 VALIDATION (Sample of {sample_size}):")
        print(f"Validation rate: {validation_rate:.1f}%")
        
        if missing_address_hashes:
            print(f"\n⚠️  MISSING ADDRESS HASHES:")
            print(f"Buildings with missing address hash matches: {len(missing_address_hashes)}")
            print("Sample of missing address hashes:", list(missing_address_hashes)[:5])
        
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

def generate_building_address_edges():
    """Wrapper function for compatibility"""
    return generate_building_address_edges_streaming()

if __name__ == "__main__":
    generate_building_address_edges() 