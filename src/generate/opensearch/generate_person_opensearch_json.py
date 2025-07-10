import json
import random
from faker import Faker
from tqdm import tqdm
import os
from typing import List, Dict, Any
import time

# Configuration
RECORD_COUNT = 10000000
BATCH_SIZE = 10000  # Process records in batches
BUFFER_SIZE = 2048 * 2048  # 1MB buffer for file writing

# Initialize Faker with seed for reproducibility
Faker.seed(42)
fake = Faker()

# Pre-generate common data to avoid repeated calls
print("Pre-generating common data...")
COMMON_NAMES = [fake.name() for _ in range(1000)]
COMMON_USERNAMES = [fake.user_name() for _ in range(1000)]
COMMON_EMAILS = [fake.email() for _ in range(1000)]
COMMON_PHONES = [fake.phone_number() for _ in range(1000)]
COMMON_CITIES = [fake.city() for _ in range(500)]
COMMON_STATES = [fake.state() for _ in range(100)]
COMMON_ZIPS = [fake.zipcode() for _ in range(1000)]
COMMON_STREETS = [fake.street_address() for _ in range(1000)]

def get_random_items(items: List[str], count: int) -> List[str]:
    """Get random items from a list, with replacement."""
    return [random.choice(items) for _ in range(count)]

def generate_person(person_id: int) -> Dict[str, Any]:
    """Generate a single person record efficiently."""
    return {
        "id": f"person-{person_id}",
        "type": "person",
        "names": get_random_items(COMMON_NAMES, 10),
        "aliases": get_random_items(COMMON_USERNAMES, 10),
        "emails": get_random_items(COMMON_EMAILS, 10),
        "phones": get_random_items(COMMON_PHONES, 10),
        "addresses": [
            {
                "id": f"addr-{person_id}-{j}",
                "street": random.choice(COMMON_STREETS),
                "city": random.choice(COMMON_CITIES),
                "state": random.choice(COMMON_STATES),
                "zip": random.choice(COMMON_ZIPS)
            }
            for j in range(10)
        ]
    }

def generate_bulk_person_data(count=None, output_file="src/data/output/opensearch/person-bulk.json"):
    """
    Generate bulk person data for OpenSearch with high performance optimizations.
    
    Optimizations:
    - Pre-generated common data
    - Batch processing to reduce overhead
    - Buffered file I/O
    - Memory-efficient data structures
    """
    if count is None:
        count = RECORD_COUNT
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    start_time = time.time()
    
    # Calculate number of batches
    num_batches = (count + BATCH_SIZE - 1) // BATCH_SIZE
    print(f"Processing {count} records in {num_batches} batches of {BATCH_SIZE}")
    
    # Write to file with large buffer
    with open(output_file, "w", buffering=BUFFER_SIZE) as f:
        records_written = 0
        
        # Process in batches with progress bar
        with tqdm(total=count, desc="Generating person data", unit="records") as pbar:
            for batch_start in range(0, count, BATCH_SIZE):
                batch_end = min(batch_start + BATCH_SIZE, count)
                batch_size = batch_end - batch_start
                
                # Generate batch of records
                for i in range(batch_size):
                    person_id = batch_start + i
                    person = generate_person(person_id)
                    
                    # Create action and data lines
                    action = {"index": {"_index": "people", "_id": person["id"]}}
                    f.write(json.dumps(action) + "\n")
                    f.write(json.dumps(person) + "\n")
                    
                    records_written += 1
                    pbar.update(1)
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    records_per_second = count / elapsed_time
    
    print(f"✅ {records_written} records written to {output_file}")
    print(f"⏱️  Total time: {elapsed_time:.2f} seconds")
    print(f"🚀 Performance: {records_per_second:.0f} records/second")
    print(f"📊 File size: {os.path.getsize(output_file) / (1024*1024):.1f} MB")

if __name__ == "__main__":
    generate_bulk_person_data(count=RECORD_COUNT)
