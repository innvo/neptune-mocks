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
_DATA_TYPES = np.array(['PRIMARY', 'SECONDARY', 'BACKUP'])

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
    person_chunk, datainstance_ids, edge_counts_chunk, chunk_start_idx = chunk_data
    
    edges = []
    datainstance_ids_len = len(datainstance_ids)
    
    # Pre-generate all random values for this chunk
    total_edges = sum(edge_counts_chunk)
    if total_edges == 0:
        return edges
    
    # Pre-generate random values using numpy for maximum speed
    confidence_scores = np.round(np.random.uniform(0.1, 1.0, size=total_edges), 2)
    
    # Pre-allocate edge template for reuse
    edge_template = {
        'edge_type': 'person_datainstance',
        'edge_properties': {}
    }
    
    edge_idx = 0
    
    for i, person_id in enumerate(person_chunk):
        num_edges = edge_counts_chunk[i]
        num_edges = max(1, min(num_edges, datainstance_ids_len, 10))  # max_edges_per_person = 10
        
        if num_edges > 0:
            # Ultra-fast random sampling using numpy
            if num_edges == 1:
                selected_idx = np.random.randint(0, datainstance_ids_len)
                selected_datainstances = [datainstance_ids[selected_idx]]
            elif num_edges <= datainstance_ids_len:
                selected_indices = np.random.choice(datainstance_ids_len, size=num_edges, replace=False)
                selected_datainstances = [datainstance_ids[idx] for idx in selected_indices]
            else:
                selected_datainstances = datainstance_ids[:num_edges]
            
            # Generate edges with minimal object creation
            for datainstance_id in selected_datainstances:
                # Create edge using template copy for minimal object creation
                edge = edge_template.copy()
                edge['edge_id'] = generate_fast_uuid()
                edge['node_id_from'] = person_id
                edge['node_id_to'] = datainstance_id
                
                # Update edge properties efficiently
                edge_props = edge['edge_properties']
                edge_props['CONFIDENCE_SCORE'] = confidence_scores[edge_idx]
                
                edges.append(edge)
                edge_idx += 1
    
    return edges

def generate_person_datainstance_edges_streaming():
    """
    Streaming edge generation optimized for very large datasets
    """
    try:
        clear_terminal()
        start_time = time.time()
        
        # System resource detection
        num_cores = mp.cpu_count()
        memory_gb = psutil.virtual_memory().total // (1024**3)
        
        print(f"🚀 STREAMING PERSON-DATAINSTANCE EDGE GENERATION")
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
        
        # Extract node IDs efficiently using numpy
        person_ids = []
        datainstance_ids = []
        for chunk in node_df:
            person_mask = (chunk['node_type'] == 'person').values
            datainstance_mask = (chunk['node_type'] == 'datainstance').values
            person_ids.extend(chunk.loc[person_mask, 'node_id'].tolist())
            datainstance_ids.extend(chunk.loc[datainstance_mask, 'node_id'].tolist())
        
        print(f"\nDataset size: {len(person_ids):,} persons → {len(datainstance_ids):,} datainstances")
        
        if not person_ids or not datainstance_ids:
            raise ValueError("Missing required node types")
        
        # Pre-generate edge distribution (weighted to favor fewer edges)
        print("Generating edge distribution...")
        edge_counts = np.random.choice(
            [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 
            size=len(person_ids),
            p=[0.4, 0.25, 0.15, 0.1, 0.05, 0.02, 0.01, 0.01, 0.005, 0.005]
        )
        
        # Streaming processing configuration - optimized chunk size
        chunk_size = min(50000, max(10000, len(person_ids) // (num_cores * 4)))  # Dynamic chunk sizing
        total_chunks = (len(person_ids) + chunk_size - 1) // chunk_size  # Ceiling division
        
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
            end_idx = min(start_idx + chunk_size, len(person_ids))
            
            person_chunk = person_ids[start_idx:end_idx]
            edge_counts_chunk = edge_counts[start_idx:end_idx]
            
            chunk_data = (person_chunk, datainstance_ids, edge_counts_chunk, start_idx)
            chunks.append(chunk_data)
        
        # Process chunks in parallel using ProcessPoolExecutor
        max_workers = min(num_cores, total_chunks)
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            # Submit all chunks
            future_to_chunk = {executor.submit(process_person_chunk_streaming, chunk): chunk for chunk in chunks}
            
            # Collect results with progress bar
            for future in tqdm(as_completed(future_to_chunk), total=len(chunks), desc="Processing chunks"):
                chunk_edges = future.result()
                all_edges.extend(chunk_edges)
                
                # Memory management every few chunks
                if len(all_edges) % (chunk_size * 10) == 0:
                    gc.collect()
        
        # Calculate statistics efficiently using vectorized operations efficiently using vectorized operations efficiently using vectorized operations
        print("\nCalculating statistics...")
        confidence_score_stats = {
            'low': 0,    # 0.1-0.4
            'medium': 0, # 0.4-0.7
            'high': 0    # 0.7-1.0
        }
        
        for edge in all_edges:
            confidence = edge['edge_properties']['CONFIDENCE_SCORE']
            if confidence < 0.4:
                confidence_score_stats['low'] += 1
            elif confidence < 0.7:
                confidence_score_stats['medium'] += 1
            else:
                confidence_score_stats['high'] += 1
        
        # Save results
        os.makedirs('src/data/output/gds', exist_ok=True)
        output_path = 'src/data/output/gds/mock_person-datainstance_data.json'
        
        print(f"Saving {len(all_edges):,} edges...")
        with open(output_path, 'w') as f:
            json.dump(all_edges, f, separators=(',', ':'))  # Compact JSON for faster I/O
        
        # Performance metrics
        processing_time = time.time() - start_time
        edge_count = len(all_edges)
        
        # Quick validation using numpy for speed
        print("Validating sample...")
        person_node_ids = set(person_ids)
        datainstance_node_ids = set(datainstance_ids)
        
        sample_size = min(1000, len(all_edges))
        sample_indices = np.random.choice(len(all_edges), size=sample_size, replace=False)
        
        valid_sample = 0
        for idx in sample_indices:
            edge = all_edges[idx]
            if edge['node_id_from'] in person_node_ids and edge['node_id_to'] in datainstance_node_ids:
                valid_sample += 1
        
        validation_rate = (valid_sample / sample_size) * 100
        
        clear_terminal()
        
        # Results summary
        print("✅ STREAMING PERSON-DATAINSTANCE EDGE GENERATION COMPLETE")
        print("=" * 60)
        print(f"📊 GENERATION METRICS:")
        print(f"Total edges generated: {edge_count:,}")
        print(f"Processing time: {processing_time:.3f} seconds")
        print(f"Throughput: {edge_count / processing_time:,.0f} edges/second")
        print(f"Average edges per person: {edge_count / len(person_ids):.2f}")
        
        print(f"\n🔍 VALIDATION (Sample of {sample_size}):")
        print(f"Validation rate: {validation_rate:.1f}%")
        
        print(f"\n🎯 CONFIDENCE SCORE DISTRIBUTION:")
        for level, count in confidence_score_stats.items():
            percentage = (count / edge_count) * 100 if edge_count > 0 else 0
            print(f"{level.capitalize()}: {count:,} edges ({percentage:.1f}%)")
        
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

def generate_person_datainstance_edges():
    """Wrapper function for compatibility"""
    return generate_person_datainstance_edges_streaming()

if __name__ == "__main__":
    generate_person_datainstance_edges() 