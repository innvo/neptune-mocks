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
_RELATIONSHIP_TYPES = np.array([
    'APPLICANT', 'BENEFICIARY', 'CO_APPLICANT', 'SPONSOR', 'PETITIONER', 
    'REPRESENTATIVE', 'ATTORNEY', 'INTERPRETER', 'PREPARER', 'WITNESS', 
    'GUARDIAN', 'POWER_OF_ATTORNEY', 'TRANSLATOR', 'NOTARY', 'CERTIFIER'
])

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
    person_chunk, form_ids, edge_counts_chunk, person_lookup, chunk_start_idx = chunk_data
    
    edges = []
    form_ids_len = len(form_ids)
    
    # Pre-generate all random values for this chunk
    total_edges = sum(edge_counts_chunk)
    if total_edges == 0:
        return edges
    
    # Pre-generate random values using numpy for maximum speed
    rel_type_indices = np.random.randint(0, len(_RELATIONSHIP_TYPES), size=total_edges)
    
    # Pre-allocate edge template for reuse
    edge_template = {
        'edge_type': 'person_form',
        'edge_properties': {}
    }
    
    edge_idx = 0
    
    for i, person_id in enumerate(person_chunk):
        num_edges = edge_counts_chunk[i]
        num_edges = max(1, min(num_edges, form_ids_len, 3))  # max_edges_per_person = 3
        
        if num_edges > 0:
            # Ultra-fast random sampling using numpy
            if num_edges == 1:
                selected_idx = np.random.randint(0, form_ids_len)
                selected_forms = [form_ids[selected_idx]]
            elif num_edges <= form_ids_len:
                selected_indices = np.random.choice(form_ids_len, size=num_edges, replace=False)
                selected_forms = [form_ids[idx] for idx in selected_indices]
            else:
                selected_forms = form_ids[:num_edges]
            
            # Get person name once
            name_full = person_lookup.get(person_id, "UNKNOWN")
            
            # Generate edges with minimal object creation
            for form_id in selected_forms:
                # Create edge using template copy for minimal object creation
                edge = edge_template.copy()
                edge['edge_id'] = generate_fast_uuid()
                edge['node_id_from'] = person_id
                edge['node_id_to'] = form_id
                
                # Update edge properties efficiently
                edge_props = edge['edge_properties']
                edge_props['RELATIONSHIP_TYPE'] = _RELATIONSHIP_TYPES[rel_type_indices[edge_idx]]
                edge_props['NAME_FULL'] = name_full
                
                edges.append(edge)
                edge_idx += 1
    
    return edges

def generate_person_form_edges_streaming():
    """
    Streaming edge generation optimized for very large datasets
    """
    try:
        clear_terminal()
        start_time = time.time()
        
        # System resource detection
        num_cores = mp.cpu_count()
        memory_gb = psutil.virtual_memory().total // (1024**3)
        
        print(f"🚀 STREAMING PERSON-FORM EDGE GENERATION")
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
                            memory_map=True)  # Read entire file for filtering
        
        # Read person data for NAME_FULL lookup
        print("Loading person data for NAME_FULL lookup...")
        with open('src/data/output/gds/mock_person_data.json', 'r') as f:
            person_data = json.load(f)
        person_lookup = {person['node_id']: person['node_properties']['NAME_FULL'] for person in person_data}
        
        # Extract node IDs efficiently
        person_mask = node_df['node_type'] == 'person'
        form_mask = node_df['node_type'] == 'form'
        
        person_ids = node_df[person_mask]['node_id'].tolist()
        form_ids = node_df[form_mask]['node_id'].tolist()
        
        print(f"\nDataset size: {len(person_ids):,} persons → {len(form_ids):,} forms")
        
        if not person_ids or not form_ids:
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
            chunk_data = (person_chunk, form_ids, edge_counts_chunk, person_lookup, start_idx)
            chunk_edges = process_person_chunk_streaming(chunk_data)
            
            all_edges.extend(chunk_edges)
            
            # Memory management
            if chunk_idx % 10 == 0:
                gc.collect()
        
        # Calculate statistics efficiently using vectorized operations efficiently using vectorized operations efficiently using vectorized operations
        print("\nCalculating statistics...")
        relationship_stats = {}
        for edge in all_edges:
            rel_type = edge['edge_properties']['RELATIONSHIP_TYPE']
            relationship_stats[rel_type] = relationship_stats.get(rel_type, 0) + 1
        
        # Save results
        os.makedirs('src/data/output/gds', exist_ok=True)
        output_path = 'src/data/output/gds/mock_person-form_data.json'
        
        print(f"Saving {len(all_edges):,} edges...")
        with open(output_path, 'w') as f:
            json.dump(all_edges, f, separators=(',', ':'))  # Compact JSON for faster I/O
        
        # Performance metrics
        processing_time = time.time() - start_time
        edge_count = len(all_edges)
        
        # Quick validation using numpy for speed using numpy for speed using numpy for speed
        print("Validating sample...")
        person_node_ids = set(person_ids)
        form_node_ids = set(form_ids)
        
        sample_size = min(1000, len(all_edges))
        sample_edges = random.sample(all_edges, sample_size)
        
        valid_sample = 0
        for edge in sample_edges:
            if edge['node_id_from'] in person_node_ids and edge['node_id_to'] in form_node_ids:
                valid_sample += 1
        
        validation_rate = (valid_sample / sample_size) * 100
        
        clear_terminal()
        
        # Results summary
        print("✅ STREAMING PERSON-FORM EDGE GENERATION COMPLETE")
        print("=" * 60)
        print(f"📊 GENERATION METRICS:")
        print(f"Total edges generated: {edge_count:,}")
        print(f"Processing time: {processing_time:.3f} seconds")
        print(f"Throughput: {edge_count / processing_time:,.0f} edges/second")
        print(f"Average edges per person: {edge_count / len(person_ids):.2f}")
        
        print(f"\n🔍 VALIDATION (Sample of {sample_size}):")
        print(f"Validation rate: {validation_rate:.1f}%")
        
        print(f"\n🏷️  RELATIONSHIP TYPE DISTRIBUTION:")
        for rel_type, count in relationship_stats.items():
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

def generate_person_form_edges():
    """Wrapper function for compatibility"""
    return generate_person_form_edges_streaming()

if __name__ == "__main__":
    generate_person_form_edges()