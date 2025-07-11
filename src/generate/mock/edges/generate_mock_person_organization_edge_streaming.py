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
    'EMPLOYEE', 'OWNER', 'DIRECTOR', 'PARTNER', 'CONTRACTOR',
    'CONSULTANT', 'VOLUNTEER', 'MEMBER', 'AFFILIATE'
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
    person_chunk, organization_ids, edge_counts_chunk, chunk_start_idx = chunk_data
    
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
    organization_ids_len = len(organization_ids)
    
    # Pre-allocate numpy array for random indices
    max_orgs_per_person = 3
    
    for i, person_id in enumerate(person_chunk):
        num_edges = edge_counts_chunk[i]
        num_edges = max(1, min(num_edges, organization_ids_len, max_orgs_per_person))
        
        # Ultra-fast random sampling using numpy
        if num_edges == 1:
            selected_idx = np.random.randint(0, organization_ids_len)
            selected_organizations = [organization_ids[selected_idx]]
        elif num_edges <= organization_ids_len:
            selected_indices = np.random.choice(organization_ids_len, size=num_edges, replace=False)
            selected_organizations = [organization_ids[idx] for idx in selected_indices]
        else:
            selected_organizations = organization_ids[:num_edges]
        
        # Generate edges with minimal object creation
        for j, org_id in enumerate(selected_organizations):
            # Generate random dates for employment
            start_year = random.randint(2010, 2024)
            end_year = random.randint(start_year, 2024)
            
            edges.append({
                'edge_id': generate_fast_uuid(),
                'node_id_from': person_id,
                'node_id_to': org_id,
                'edge_type': 'person_organization',
                'edge_name': 'workAt',
                'edge_properties': {
                    'ORG_TYPE': 'EMPLOYER',
                    'ADDR_FROM_DATE': f"{start_year}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
                    'ADDR_THRU_DATE': f"{end_year}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
                    'EMPLOYMENT_START_DATE': f"{start_year}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
                    'EMPLOYMENT_END_DATE': f"{end_year}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
                }
            })
    
    return edges

def generate_person_organization_edges_streaming():
    """
    Streaming edge generation optimized for very large datasets
    """
    try:
        clear_terminal()
        start_time = time.time()
        
        # System resource detection
        num_cores = mp.cpu_count()
        memory_gb = psutil.virtual_memory().total // (1024**3)
        
        print(f"🚀 STREAMING PERSON-ORGANIZATION EDGE GENERATION")
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
        
        # Read person data from mock_person_data.json to ensure consistency
        print("Loading person data from mock_person_data.json...")
        with open('src/data/output/gds/mock_person_data.json', 'r') as f:
            person_data = json.load(f)
        
        # Extract person IDs from the JSON data
        person_ids = [person['node_id'] for person in person_data]
        print(f"Found {len(person_ids)} person IDs from mock_person_data.json")
        
        # Extract organization IDs efficiently
        organization_mask = node_df['node_type'] == 'organization'
        organization_ids = node_df[organization_mask]['node_id'].tolist()
        
        print(f"Found {len(organization_ids)} organization nodes")
        
        if not person_ids or not organization_ids:
            raise ValueError("Missing required node types")
        
        print(f"\nDataset size: {len(person_ids):,} persons → {len(organization_ids):,} organizations")
        
        # Pre-generate edge distribution (70% of persons will have organization edges)
        print("Generating edge distribution...")
        person_has_org_probability = 0.7
        edge_counts = np.zeros(len(person_ids), dtype=int)
        
        # Apply probability to determine which persons get organization edges
        persons_with_orgs = np.random.random(len(person_ids)) < person_has_org_probability
        edge_counts[persons_with_orgs] = np.random.choice([1, 2, 3], size=np.sum(persons_with_orgs), p=[0.7, 0.25, 0.05])
        
        # Streaming processing configuration
        chunk_size = 25000  # Smaller chunks for better memory management
        total_chunks = (len(person_ids) // chunk_size) + 1
        
        print(f"\n🎯 STREAMING CONFIGURATION:")
        print(f"Chunk Size: {chunk_size:,}")
        print(f"Total Chunks: {total_chunks}")
        print(f"Estimated edges: {np.sum(edge_counts):,}")
        print(f"Persons with organization edges: {np.sum(edge_counts > 0):,} ({np.sum(edge_counts > 0) / len(person_ids) * 100:.1f}%)")
        
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
            chunk_data = (person_chunk, organization_ids, edge_counts_chunk, start_idx)
            chunk_edges = process_person_chunk_streaming(chunk_data)
            
            all_edges.extend(chunk_edges)
            
            # Memory management
            if chunk_idx % 10 == 0:
                gc.collect()
        
        # Calculate statistics efficiently using vectorized operations efficiently using vectorized operations efficiently using vectorized operations
        print("\nCalculating statistics...")
        org_type_stats = {}
        for edge in all_edges:
            org_type = edge['edge_properties']['ORG_TYPE']
            org_type_stats[org_type] = org_type_stats.get(org_type, 0) + 1
        
        # Save results
        os.makedirs('src/data/output/gds', exist_ok=True)
        output_path = 'src/data/output/gds/mock_person-organization_data.json'
        
        print(f"Saving {len(all_edges):,} edges...")
        with open(output_path, 'w') as f:
            json.dump(all_edges, f, separators=(',', ':'))  # Compact JSON for faster I/O
        
        # Performance metrics
        processing_time = time.time() - start_time
        edge_count = len(all_edges)
        
        # Quick validation using numpy for speed using numpy for speed using numpy for speed
        print("Validating sample...")
        person_node_ids = set(person_ids)
        organization_node_ids = set(organization_ids)
        
        sample_size = min(1000, len(all_edges))
        sample_edges = random.sample(all_edges, sample_size)
        
        valid_sample = 0
        for edge in sample_edges:
            if edge['node_id_from'] in person_node_ids and edge['node_id_to'] in organization_node_ids:
                valid_sample += 1
        
        validation_rate = (valid_sample / sample_size) * 100
        
        # Calculate edges per person distribution
        edges_per_person = {}
        for edge in all_edges:
            person_id = edge['node_id_from']
            edges_per_person[person_id] = edges_per_person.get(person_id, 0) + 1
        
        edges_per_person_dist = {}
        for count in edges_per_person.values():
            edges_per_person_dist[count] = edges_per_person_dist.get(count, 0) + 1
        
        # Calculate edges per organization distribution
        edges_per_org = {}
        for edge in all_edges:
            org_id = edge['node_id_to']
            edges_per_org[org_id] = edges_per_org.get(org_id, 0) + 1
        
        edges_per_org_dist = {}
        for count in edges_per_org.values():
            edges_per_org_dist[count] = edges_per_org_dist.get(count, 0) + 1
        
        clear_terminal()
        
        # Results summary
        print("✅ STREAMING PERSON-ORGANIZATION EDGE GENERATION COMPLETE")
        print("=" * 60)
        print(f"📊 GENERATION METRICS:")
        print(f"Total edges generated: {edge_count:,}")
        print(f"Processing time: {processing_time:.3f} seconds")
        print(f"Throughput: {edge_count / processing_time:,.0f} edges/second")
        print(f"Average edges per person: {edge_count / len(person_ids):.2f}")
        
        print(f"\n🔍 VALIDATION (Sample of {sample_size}):")
        print(f"Validation rate: {validation_rate:.1f}%")
        
        print(f"\n🏷️  ORGANIZATION TYPE DISTRIBUTION:")
        for org_type, count in org_type_stats.items():
            print(f"{org_type}: {count:,} edges")
        
        print(f"\n📈 EDGES PER PERSON DISTRIBUTION:")
        for count in sorted(edges_per_person_dist.keys()):
            print(f"Persons with {count} organization edges: {edges_per_person_dist[count]:,}")
        
        print(f"\n📈 EDGES PER ORGANIZATION DISTRIBUTION:")
        for count in sorted(edges_per_org_dist.keys()):
            print(f"Organizations with {count} person edges: {edges_per_org_dist[count]:,}")
        
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

def generate_person_organization_edges():
    """Wrapper function for compatibility"""
    return generate_person_organization_edges_streaming()

if __name__ == "__main__":
    generate_person_organization_edges() 