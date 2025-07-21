import uuid
import random
import os
import csv
import glob
import time
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List, Tuple

# Constants
NODES_DIR = 'src/data/output/neptune/nodes'
EDGE_OUTPUT_BASE = 'src/data/output/neptune/edges/neptune_person_address_edges_gremlin'
MAX_FILE_SIZE_BYTES = 2.5 * 1024 * 1024 * 1024  # 2.5GB
SAFETY_MARGIN = 0.9
BATCH_SIZE = 10000
NUM_WORKERS = mp.cpu_count()
WRITER_BUFFER_SIZE = 64 * 1024
ADDRESS_TYPES = ['PRIMARY', 'SECONDARY', 'TERTIARY']


def find_csv_files(pattern: str) -> List[str]:
    files = glob.glob(os.path.join(NODES_DIR, pattern))
    files.sort()
    return files

def load_address_ids(address_file: str) -> List[str]:
    ids = []
    with open(address_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            ids.append(row['~id'])
    return ids

def load_all_address_ids() -> List[str]:
    address_files = find_csv_files('neptune_address_nodes_gremlin_*.csv')
    all_ids = []
    for f in address_files:
        all_ids.extend(load_address_ids(f))
    return all_ids

def person_id_generator(person_file: str):
    with open(person_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield row['~id']

def generate_edges_for_person(person_id: str, address_ids: List[str]) -> List[Tuple[str, str, str, str, str]]:
    num_addresses = random.randint(0, 3)
    if num_addresses == 0 or not address_ids:
        return []
    selected = random.sample(address_ids, min(num_addresses, len(address_ids)))
    edges = []
    for i, addr_id in enumerate(selected):
        edge_id = str(uuid.uuid4())
        address_type = ADDRESS_TYPES[i] if i < len(ADDRESS_TYPES) else 'PRIMARY'
        edges.append((edge_id, person_id, addr_id, address_type, '~person-add'))
    return edges

def process_person_file(person_file: str, address_ids: List[str]) -> List[Tuple[str, str, str, str, str]]:
    edges = []
    for person_id in person_id_generator(person_file):
        edges.extend(generate_edges_for_person(person_id, address_ids))
    return edges

def estimate_row_size(row: Tuple[str, str, str, str, str]) -> int:
    """Estimate the size of a CSV row in bytes"""
    # Rough estimation: each field + comma + newline
    return sum(len(str(field)) for field in row) + 5 # For commas and newline

def get_output_filename(file_index: int) -> str:
    """Get the output filename with index"""
    return f"{EDGE_OUTPUT_BASE}_{file_index:03d}.csv"

def main():
    start = time.time()
    person_files = find_csv_files('neptune_person_nodes_gremlin_*.csv')
    address_ids = load_all_address_ids()
    print(f"Found {len(person_files)} person files, {len(address_ids)} address IDs.")
    
    # Prepare output directory
    os.makedirs(os.path.dirname(EDGE_OUTPUT_BASE), exist_ok=True)
    
    # Initialize file management variables
    current_file_index = 0
    current_file_size = 0
    current_writer = None
    current_file = None
    total_edges = 0
    files_created = 0
    
    def create_new_file():
        nonlocal current_file, current_writer, current_file_index, current_file_size, files_created
        if current_file:
            current_file.close()
        
        current_file_index += 1
        filename = get_output_filename(current_file_index)
        current_file = open(filename, 'w', newline='', encoding='utf-8', buffering=WRITER_BUFFER_SIZE)
        current_writer = csv.writer(current_file, quoting=csv.QUOTE_MINIMAL)
        current_writer.writerow(['~id', '~from', '~to', 'address_type:String', '~label'])
        current_file_size = 0
        files_created += 1
        print(f"Created new file: {filename}")
    
    # Create first file
    create_new_file()
    
    try:
        with ProcessPoolExecutor(max_workers=NUM_WORKERS) as executor:
            futures = [executor.submit(process_person_file, pf, address_ids) for pf in person_files]
            
            for i, future in enumerate(as_completed(futures), 1):
                batch_edges = future.result()
                
                for edge in batch_edges:
                    # Check if we need to create a new file
                    estimated_size = estimate_row_size(edge)
                    if current_file_size + estimated_size > MAX_FILE_SIZE_BYTES * SAFETY_MARGIN:
                        create_new_file()
                    
                    # Write the edge
                    current_writer.writerow(edge)
                    current_file_size += estimated_size
                    total_edges += 1
                
                print(f"Processed {i}/{len(person_files)} person files, total edges: {total_edges}, current file size: {current_file_size / (1024*1024*1024):.2f}GB")
    
    finally:
        if current_file:
            current_file.close()
    
    elapsed = time.time() - start
    print(f"Done. Total edges: {total_edges}. Files created: {files_created}. Time: {elapsed:.1f}s")

if __name__ == '__main__':
    main() 