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

def process_person_chunk_streaming(chunk_data):
    """Streaming chunk processor optimized for very large datasets"""
    person_chunk, name_ids, edge_counts_chunk, chunk_start_idx = chunk_data
    
    edges = []
    name_ids_len = len(name_ids)
    
    # Pre-allocate numpy array for random indices
    max_edges_per_person = 3
    
    for i, person_id in enumerate(person_chunk):
        num_edges = edge_counts_chunk[i]
        num_edges = max(1, min(num_edges, name_ids_len, max_edges_per_person))
        
        # Ultra-fast random sampling using numpy
        if num_edges == 1:
            selected_idx = np.random.randint(0, name_ids_len)
            selected_names = [name_ids[selected_idx]]
        elif num_edges <= name_ids_len:
            selected_indices = np.random.choice(name_ids_len, size=num_edges, replace=False)
            selected_names = [name_ids[idx] for idx in selected_indices]
        else:
            selected_names = name_ids[:num_edges]
        
        # Generate edges with minimal object creation
        for j, name_id in enumerate(selected_names):
            # First name is always PRIMARY
            if j == 0:
                name_type = 'PRIMARY'
            else:
                name_type = random.choice(['OTHER', 'ALIAS'])
            
            edges.append({
                'edge_id': generate_fast_uuid(),
                'node_id_from': person_id,
                'node_id_to': name_id,
                'edge_type': 'person_name',
                'edge_properties': {
                    'NAME_TYPE': name_type
                }
            })
    
    return edges

def generate_person_name_edges():
    """
    Streaming edge generation optimized for very large datasets
    """
    try:
        clear_terminal()
        start_time = time.time()
        
        # System resource detection
        num_cores = mp.cpu_count()
        memory_gb = psutil.virtual_memory().total // (1024**3)
        
        print(f"🚀 STREAMING PERSON-NAME EDGE GENERATION")
        print(f"🌊 OPTIMIZED FOR VERY LARGE DATASETS")
        print(f"CPU Cores: {num_cores}")
        print(f"Available Memory: {memory_gb} GB")
        print("=" * 60)
        
        # Load data efficiently
        print("Loading node data...")
        node_df = pd.read_csv('src/data/input/node_data.csv', 
                            usecols=['node_id', 'node_type'],
                            dtype={'node_type': 'category', 'node_id': 'string'},
                            engine='c')
        
        # Extract node IDs efficiently
        person_mask = node_df['node_type'] == 'person'
        name_mask = node_df['node_type'] == 'name'
        
        person_ids = node_df[person_mask]['node_id'].tolist()
        name_ids = node_df[name_mask]['node_id'].tolist()
        
        print(f"\nDataset size: {len(person_ids):,} persons → {len(name_ids):,} names")
        
        if not person_ids or not name_ids:
            raise ValueError("Missing required node types")
        
        # Pre-generate edge distribution
        print("Generating edge distribution...")
        edge_counts = np.random.choice([1, 2, 3], size=len(person_ids), p=[0.7, 0.25, 0.05])
        
        # Streaming processing configuration
        chunk_size = 25000  # Smaller chunks for better memory management
        total_chunks = (len(person_ids) // chunk_size) + 1
        
        print(f"\n🎯 STREAMING CONFIGURATION:")
        print(f"Chunk Size: {chunk_size:,}")
        print(f"Total Chunks: {total_chunks}")
        print(f"Estimated edges: {np.sum(edge_counts):,}")
        
        # Process in streaming fashion
        print(f"\nGenerating edges in streaming mode...")
        
        all_edges = []
        
        # Process chunks sequentially to minimize memory usage
        for chunk_idx in tqdm(range(total_chunks), desc="Processing chunks"):
            start_idx = chunk_idx * chunk_size
            end_idx = min(start_idx + chunk_size, len(person_ids))
            
            person_chunk = person_ids[start_idx:end_idx]
            edge_counts_chunk = edge_counts[start_idx:end_idx]
            
            # Process this chunk
            chunk_data = (person_chunk, name_ids, edge_counts_chunk, start_idx)
            chunk_edges = process_person_chunk_streaming(chunk_data)
            
            all_edges.extend(chunk_edges)
            
            # Memory management
            if chunk_idx % 10 == 0:
                gc.collect()
        
        # Calculate statistics
        print("\nCalculating statistics...")
        name_type_stats = {'PRIMARY': 0, 'OTHER': 0, 'ALIAS': 0}
        for edge in all_edges:
            name_type = edge['edge_properties']['NAME_TYPE']
            name_type_stats[name_type] += 1
        
        # Save results
        os.makedirs('src/data/output/gds', exist_ok=True)
        output_path = 'src/data/output/gds/mock_person-name_data.json'
        
        print(f"Saving {len(all_edges):,} edges...")
        with open(output_path, 'w') as f:
            json.dump(all_edges, f, indent=2)
        
        # Performance metrics
        processing_time = time.time() - start_time
        edge_count = len(all_edges)
        
        # Quick validation
        print("Validating sample...")
        person_node_ids = set(person_ids)
        name_node_ids = set(name_ids)
        
        sample_size = min(1000, len(all_edges))
        sample_edges = random.sample(all_edges, sample_size)
        
        valid_sample = 0
        for edge in sample_edges:
            if edge['node_id_from'] in person_node_ids and edge['node_id_to'] in name_node_ids:
                valid_sample += 1
        
        validation_rate = (valid_sample / sample_size) * 100
        
        clear_terminal()
        
        # Results summary
        print("✅ STREAMING PERSON-NAME EDGE GENERATION COMPLETE")
        print("=" * 60)
        print(f"📊 GENERATION METRICS:")
        print(f"Total edges generated: {edge_count:,}")
        print(f"Processing time: {processing_time:.3f} seconds")
        print(f"Throughput: {edge_count / processing_time:,.0f} edges/second")
        print(f"Average edges per person: {edge_count / len(person_ids):.2f}")
        
        print(f"\n🔍 VALIDATION (Sample of {sample_size}):")
        print(f"Validation rate: {validation_rate:.1f}%")
        
        print(f"\n🏷️  NAME TYPE DISTRIBUTION:")
        for name_type, count in name_type_stats.items():
            print(f"{name_type}: {count:,} edges")
        
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

if __name__ == "__main__":
    generate_person_name_edges() 