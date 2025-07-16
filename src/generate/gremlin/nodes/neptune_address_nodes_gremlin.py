import pandas as pd
import uuid
import random
import json
import os
from datetime import datetime, timedelta
from faker import Faker
import numpy as np
from dotenv import load_dotenv
import multiprocessing as mp
from functools import partial

fake = Faker()

def find_dotenv(start_dir):
    """Find .env file by searching up the directory tree"""
    current_dir = start_dir
    while True:
        env_path = os.path.join(current_dir, '.env')
        if os.path.isfile(env_path):
            return env_path
        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:
            break
        current_dir = parent_dir
    return None

def generate_variant_dates(base_date, count=6):
    """Generate slightly different dates based on the base date"""
    base = datetime.strptime(base_date, '%Y-%m-%d')
    dates = []
    for i in range(count):
        variation = random.randint(-5, 5)
        variant_date = base + timedelta(days=variation)
        dates.append(variant_date.strftime('%Y-%m-%d'))
    return dates



def generate_mock_address_batch(batch_size):
    """Generate a batch of mock person data in Neptune Gremlin format"""
    
    nodes = []
    
    for _ in range(batch_size):
        # Generate basic addressdata
       
        
        # Create the node
        node_id = str(uuid.uuid4())
        
        
        
        node = {
            '~id': node_id,
            '~label': 'address'
        }
        
        nodes.append(node)
    
    return nodes

def generate_mock_address_data(num_records=1000):
    """Generate mock person data in Neptune Gremlin format (legacy function)"""
    
    print(f"Generating {num_records:,} mock person records...")
    
    nodes = []
    
    for i in range(num_records):
        if i % 100000 == 0:
            print(f"Progress: {i:,}/{num_records:,} records generated")
        # Generate basic person data
        first_name = fake.first_name()
        last_name = fake.last_name()
        full_name = f"{first_name} {last_name}".upper()
        
        # Generate birth date
        birth_date = fake.date_of_birth(minimum_age=18, maximum_age=80)
        birth_date_str = birth_date.strftime('%Y-%m-%d')
        
        # Generate name variants
        name_variants = generate_name_variants(full_name)
        
        # Generate date variants
        date_variants = generate_variant_dates(birth_date_str)
        
        # Generate anumber data (some records may not have anumbers)
        anumber_primary = ""
        anumber_list = ""
        
        if random.random() > 0.3:  # 70% chance of having anumber
            anumber_primary = f"A{random.randint(10000000, 99999999)}"
            # Generate additional anumbers for some records
            additional_anumbers = []
            for _ in range(random.randint(0, 3)):
                additional_anumbers.append(f"A{random.randint(10000000, 99999999)}")
        
            if additional_anumbers:
                anumber_list = f"{anumber_primary};{';'.join(additional_anumbers)}"
            else:
                anumber_list = anumber_primary
        
        # Create the node
        node_id = str(uuid.uuid4())
        
        # Format arrays properly for Neptune using semicolon delimiters (legacy function)
        name_full_list_formatted = f'{";".join(name_variants)}'
        date_of_birth_list_formatted = f'{";".join(date_variants)}'
        
        # Handle anumber list formatting
        if anumber_list:
            anumber_array = anumber_list.split(';')
            anumber_list_formatted = f'{";".join(anumber_array)}'
        else:
            anumber_list_formatted = ''
        
        node = {
            '~id': node_id,
            '~label': 'person'
        }
        
        nodes.append(node)
    
    return nodes

def save_to_csv(nodes, output_path):
    """Save nodes to CSV file with proper Neptune formatting"""
    import csv
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Define column order
    column_order = ['~id',
                     '~label']
    
    # Write CSV with proper formatting
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=column_order, quoting=csv.QUOTE_MINIMAL)
        
        # Write header
        writer.writeheader()
        
        # Write data rows
        for node in nodes:
            # Ensure all columns are present and in correct order
            ordered_node = {}
            for col in column_order:
                ordered_node[col] = node.get(col, '')
            writer.writerow(ordered_node)
    
    print(f"Saved {len(nodes)} records to {output_path}")
    
    # Display sample record from CSV
    print("\nSample record from CSV:")
    try:
        import csv
        with open(output_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            sample = next(reader)
            for key, value in sample.items():
                print(f"{key}: {value}")
    except Exception as e:
        print(f"Error reading sample from CSV: {e}")

def process_batch(batch_info):
    """Process a single batch and return the batch info with nodes"""
    batch_num, current_batch_size, output_path = batch_info
    print(f"Processing batch {batch_num + 1} with {current_batch_size} records...")
    nodes = generate_mock_person_batch(current_batch_size)
    save_to_csv(nodes, output_path)
    return batch_num + 1, len(nodes)

def main():
    """Main function to generate mock person data"""
    
    # Find .env file by searching up the directory tree
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = find_dotenv(script_dir)
    if not env_path:
        raise FileNotFoundError(f"❌ ERROR: .env file not found in any parent directory of {script_dir}. Please create a .env file in the project root with PERSON_RECORDS=<number>, BATCH_SIZE=<number>, and NUMBER_WORKERS=<number>")
    print(f"Using .env file at: {env_path}")
    load_dotenv(env_path)
    
    # Read and validate environment variables
    person_records_env = os.getenv('PERSON_RECORDS')
    batch_size_env = os.getenv('BATCH_SIZE')
    number_workers_env = os.getenv('NUMBER_WORKERS')
    
    if person_records_env is None:
        raise ValueError("❌ ERROR: PERSON_RECORDS environment variable not found in .env file. Please add PERSON_RECORDS=<number> to your .env file.")
    if batch_size_env is None:
        raise ValueError("❌ ERROR: BATCH_SIZE environment variable not found in .env file. Please add BATCH_SIZE=<number> to your .env file.")
    if number_workers_env is None:
        raise ValueError("❌ ERROR: NUMBER_WORKERS environment variable not found in .env file. Please add NUMBER_WORKERS=<number> to your .env file.")
    
    try:
        num_records = int(person_records_env)
    except ValueError:
        raise ValueError(f"❌ ERROR: PERSON_RECORDS must be a valid integer. Current value: '{person_records_env}'")
    try:
        batch_size = int(batch_size_env)
    except ValueError:
        raise ValueError(f"❌ ERROR: BATCH_SIZE must be a valid integer. Current value: '{batch_size_env}'")
    try:
        number_workers = int(number_workers_env)
    except ValueError:
        raise ValueError(f"❌ ERROR: NUMBER_WORKERS must be a valid integer. Current value: '{number_workers_env}'")
    
    if batch_size <= 0:
        raise ValueError("❌ ERROR: BATCH_SIZE must be greater than 0.")
    if number_workers <= 0:
        raise ValueError("❌ ERROR: NUMBER_WORKERS must be greater than 0.")
    
    # Limit number of workers to available CPU cores
    max_workers = mp.cpu_count()
    if number_workers > max_workers:
        print(f"⚠️  WARNING: NUMBER_WORKERS ({number_workers}) exceeds available CPU cores ({max_workers}). Using {max_workers} workers.")
        number_workers = max_workers
    
    print(f"Environment variable PERSON_RECORDS: {person_records_env}")
    print(f"Environment variable BATCH_SIZE: {batch_size_env}")
    print(f"Environment variable NUMBER_WORKERS: {number_workers_env}")
    print(f"Number of records to generate: {num_records:,}")
    print(f"Batch size: {batch_size:,}")
    print(f"Number of workers: {number_workers}")
    
    # Prepare batch information
    num_batches = (num_records + batch_size - 1) // batch_size
    batch_info_list = []
    
    for batch_num in range(num_batches):
        current_batch_size = min(batch_size, num_records - batch_num * batch_size)
        output_path = f'src/data/output/neptune/nodes/neptune_person_nodes_gremlin_{batch_num + 1:05d}.csv'
        batch_info_list.append((batch_num, current_batch_size, output_path))
    
    # Process batches in parallel
    print(f"\n🚀 Starting parallel processing with {number_workers} workers...")
    with mp.Pool(processes=number_workers) as pool:
        results = pool.map(process_batch, batch_info_list)
    
    # Summary
    total_generated = sum(records for _, records in results)
    print(f"\n✅ Successfully generated {total_generated:,} person nodes in {num_batches} batches using {number_workers} workers.")
    
    return True

if __name__ == "__main__":
    main()