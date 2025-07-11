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
    person_chunk, form_ids, edge_counts_chunk, person_lookup, chunk_start_idx = chunk_data
    
    edges = []
    relationship_type_choices = ['APPLICANT', 'BENEFICIARY', 'CO_APPLICANT', 'SPONSOR', 'PETITIONER', 'REPRESENTATIVE', 'ATTORNEY', 'INTERPRETER', 'PREPARER', 'WITNESS', 'GUARDIAN', 'POWER_OF_ATTORNEY', 'TRANSLATOR', 'NOTARY', 'CERTIFIER']
    form_ids_len = len(form_ids)
    
    # Pre-allocate numpy array for random indices
    max_edges_per_person = 3
    
    for i, person_id in enumerate(person_chunk):
        num_edges = edge_counts_chunk[i]
        num_edges = max(1, min(num_edges, form_ids_len, max_edges_per_person))
        
        # Ultra-fast random sampling using numpy
        if num_edges == 1:
            selected_idx = np.random.randint(0, form_ids_len)
            selected_forms = [form_ids[selected_idx]]
        elif num_edges <= form_ids_len:
            selected_indices = np.random.choice(form_ids_len, size=num_edges, replace=False)
            selected_forms = [form_ids[idx] for idx in selected_indices]
        else:
            selected_forms = form_ids[:num_edges]
        
        # Generate edges with minimal object creation
        for j, form_id in enumerate(selected_forms):
            relationship_type = random.choice(relationship_type_choices)
            name_full = person_lookup.get(person_id, "UNKNOWN")
            
            edges.append({
                'edge_id': generate_fast_uuid(),
                'node_id_from': person_id,
                'node_id_to': form_id,
                'edge_type': 'person_form',
                'edge_properties': {
                    'RELATIONSHIP_TYPE': relationship_type,
                    'NAME_FULL': name_full
                }
            })
    
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
                            engine='c')
        
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
            chunk_data = (person_chunk, form_ids, edge_counts_chunk, person_lookup, start_idx)
            chunk_edges = process_person_chunk_streaming(chunk_data)
            
            all_edges.extend(chunk_edges)
            
            # Memory management
            if chunk_idx % 10 == 0:
                gc.collect()
        
        # Calculate statistics
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
            json.dump(all_edges, f, indent=2)
        
        # Performance metrics
        processing_time = time.time() - start_time
        edge_count = len(all_edges)
        
        # Quick validation
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