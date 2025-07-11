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
import gc

def clear_terminal():
    """Clear the terminal screen based on the operating system"""
    if platform.system() == 'Windows':
        os.system('cls')
    else:
        os.system('clear')



def process_building_batch_streaming(batch_data):
    """Process a batch of buildings to generate address edges with streaming output"""
    building_ids, building_hashes, address_hash_to_ids, batch_start_idx, output_file, is_first_batch = batch_data
    batch_edges = []
    missing_address_hashes = set()
    
    for i, building_id in enumerate(building_ids):
        building_address_hash = building_hashes[i]
        
        # Find matching addresses by ADDRESS_HASH
        matching_address_ids = address_hash_to_ids.get(building_address_hash, [])
        
        if matching_address_ids:
            # Each building can have multiple addresses (e.g., unit numbers, suites)
            for address_id in matching_address_ids:
                batch_edges.append({
                    'edge_id': str(uuid.uuid4()),
                    'node_id_from': building_id,
                    'node_id_to': address_id,
                    'edge_type': 'building_address',
                    'edge_properties': {}
                })
        else:
            missing_address_hashes.add(building_address_hash)
    
    # Write batch to file
    with open(output_file, 'a') as f:
        if is_first_batch:
            f.write('[\n')
        else:
            f.write(',\n')
        
        for i, edge in enumerate(batch_edges):
            if i > 0:
                f.write(',\n')
            f.write(json.dumps(edge, indent=2))
    
    return len(batch_edges), missing_address_hashes

def generate_building_address_edges_streaming():
    try:
        clear_terminal()
        start_time = time.time()
        
        # Read building and address data
        print("Reading building and address data...")
        with open('src/data/output/gds/mock_building_data.json', 'r') as f:
            building_data = json.load(f)
        
        with open('src/data/output/gds/mock_address_data.json', 'r') as f:
            address_data = json.load(f)
        
        building_df = pd.DataFrame(building_data)
        address_df = pd.DataFrame(address_data)
        
        # Print data statistics
        print(f"\nData Statistics:")
        print(f"Total number of buildings: {len(building_df)}")
        print(f"Total number of addresses: {len(address_df)}")
        
        # Create address hash mapping for quick lookup
        print("\nCreating address hash mapping...")
        address_hash_to_ids = {}
        for _, address in address_df.iterrows():
            address_hash = address['node_properties']['ADDRESS_HASH']
            if address_hash not in address_hash_to_ids:
                address_hash_to_ids[address_hash] = []
            address_hash_to_ids[address_hash].append(address['node_id'])
        
        print(f"Unique address hashes: {len(address_hash_to_ids)}")
        
        # Convert to lists for faster access
        building_ids = building_df['node_id'].tolist()
        building_hashes = [building['node_properties']['ADDRESS_HASH'] for building in building_data]
        
        # Initialize counters
        missing_address_hashes = set()
        edge_type_count = 0
        
        # Create output directory
        os.makedirs('src/data/output/gds', exist_ok=True)
        output_file = 'src/data/output/gds/mock_building-address_data_streaming.json'
        
        # Clear output file
        with open(output_file, 'w') as f:
            pass
        
        # Optimized batch processing with multiprocessing and streaming
        print("\nGenerating building_address edges with streaming processing...")
        
        # Calculate optimal batch size based on data size
        total_buildings = len(building_ids)
        num_cores = mp.cpu_count()
        batch_size = max(1, total_buildings // (num_cores * 4))  # Smaller batches for streaming
        
        print(f"Using {num_cores} CPU cores with batch size of {batch_size}")
        
        # Create batches
        batches = []
        for i in range(0, total_buildings, batch_size):
            batch_end = min(i + batch_size, total_buildings)
            batch_building_ids = building_ids[i:batch_end]
            batch_building_hashes = building_hashes[i:batch_end]
            is_first_batch = (i == 0)
            batches.append((batch_building_ids, batch_building_hashes, address_hash_to_ids, i, output_file, is_first_batch))
        
        # Process batches in parallel with streaming output
        with ThreadPoolExecutor(max_workers=num_cores) as executor:
            # Submit all batches
            future_to_batch = {executor.submit(process_building_batch_streaming, batch): batch for batch in batches}
            
            # Collect results with progress bar
            for future in tqdm(as_completed(future_to_batch), total=len(batches), desc="Processing batches"):
                batch_edge_count, batch_missing_hashes = future.result()
                edge_type_count += batch_edge_count
                missing_address_hashes.update(batch_missing_hashes)
                
                # Force garbage collection periodically
                if edge_type_count % (batch_size * num_cores) == 0:
                    gc.collect()
        
        # Close the JSON array
        with open(output_file, 'a') as f:
            f.write('\n]')
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        clear_terminal()
        # Print processing statistics
        print(f"\nProcessing Statistics:")
        print(f"Total processing time: {processing_time:.2f} seconds")
        print(f"Edges generated per second: {edge_type_count / processing_time:.2f}")
        print(f"Average edges per building: {edge_type_count / len(building_ids):.2f}")
        print(f"Output file: {output_file}")
        
        if missing_address_hashes:
            print(f"\nBuildings with missing address hash matches: {len(missing_address_hashes)}")
            print("Sample of missing address hashes:", list(missing_address_hashes)[:5])
        
        # Clean up memory
        del building_data, address_data, building_df, address_df, address_hash_to_ids
        gc.collect()
        
        return output_file
        
    except Exception as e:
        print(f"Error generating building-address edges: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    generate_building_address_edges_streaming() 