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
    base = datetime.strptime(base_date, '%Y-%m-%d')
    dates = []
    for i in range(count):
        variation = random.randint(-5, 5)
        variant_date = base + timedelta(days=variation)
        dates.append(variant_date.strftime('%Y-%m-%d'))
    return dates

def generate_name_variants(full_name):
    if not full_name:
        return []
    parts = full_name.split()
    if len(parts) < 2:
        return [full_name]
    first_name = parts[0]
    last_name = parts[-1]
    variants = [
        full_name,
        f"{last_name}, {first_name}",
        f"{first_name[0]}. {last_name}",
        f"{last_name}, {first_name[0]}.",
        f"{first_name} {last_name[0]}.",
        f"{last_name[0]}. {first_name}"
    ]
    return variants

def generate_mock_person_batch(batch_size):
    nodes = []
    for _ in range(batch_size):
        first_name = fake.first_name()
        last_name = fake.last_name()
        full_name = f"{first_name} {last_name}".upper()
        birth_date = fake.date_of_birth(minimum_age=18, maximum_age=80)
        birth_date_str = birth_date.strftime('%Y-%m-%d')
        name_variants = generate_name_variants(full_name)
        date_variants = generate_variant_dates(birth_date_str)
        anumber_primary = ""
        anumber_list = ""
        if random.random() > 0.3:
            anumber_primary = f"A{random.randint(10000000, 99999999)}"
            additional_anumbers = []
            for _ in range(random.randint(0, 3)):
                additional_anumbers.append(f"A{random.randint(10000000, 99999999)}")
            if additional_anumbers:
                anumber_list = f"{anumber_primary};{';'.join(additional_anumbers)}"
            else:
                anumber_list = anumber_primary
        node_id = str(uuid.uuid4())
        node = {
            '~id': node_id,
            'node_id': node_id,
            'name_full:String': full_name,
            'node_name': full_name,
            'name_full_list:String': ';'.join(name_variants),
            'date_of_birth:Date': birth_date_str,
            'date_of_birth_list:Date[]': ';'.join(date_variants),
            'anumber_primary:String': anumber_primary,
            'anumber_list:String[]': anumber_list,
            '~label': 'person;primary'
        }
        nodes.append(node)
    return nodes

def save_to_csv(nodes, output_path):
    df = pd.DataFrame(nodes)
    column_order = ['~id', 'node_id', 'node_name', 'name_full:String', 'name_full_list:String', 
                   'date_of_birth:Date', 'date_of_birth_list:Date[]', 'anumber_primary:String', 
                   'anumber_list:String[]', '~label']
    df = df[column_order]
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False, quoting=1, quotechar='"')
    print(f"Saved {len(nodes)} records to {output_path}")
    print("\nSample record:")
    sample = nodes[0]
    for key, value in sample.items():
        print(f"{key}: {value}")

def process_batch(batch_info):
    """Process a single batch and return the batch info with nodes"""
    batch_num, current_batch_size, output_path = batch_info
    print(f"Processing batch {batch_num + 1} with {current_batch_size} records...")
    nodes = generate_mock_person_batch(current_batch_size)
    save_to_csv(nodes, output_path)
    return batch_num + 1, len(nodes)

def main():
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

if __name__ == "__main__":
    main()