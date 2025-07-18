import uuid
import random
import os
from datetime import datetime
from faker import Faker
from dotenv import load_dotenv
import csv
import time
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed
import threading
from queue import Queue
import itertools

fake = Faker()

# Constants for file size optimization
MAX_FILE_SIZE_BYTES = 2.5 * 1024 * 1024 * 1024  # 2.5GB
SAFETY_MARGIN = 0.9  # 90% of max file size to ensure we stay under limit

# Performance optimization constants
BATCH_SIZE = 10000  # Process records in batches
NUM_WORKERS = mp.cpu_count()  # Use all CPU cores
WRITER_BUFFER_SIZE = 64 * 1024  # 64KB buffer for writers

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

def generate_address_record():
    """Generate a single address record - optimized version"""
    node_id = str(uuid.uuid4())
    
    # Return as tuple for direct CSV writing (no dictionary overhead)
    return (node_id, 'address')

def generate_batch_of_address_records(batch_size):
    """Generate a batch of address records - optimized for parallel processing"""
    records = []
    for _ in range(batch_size):
        node_id = str(uuid.uuid4())
        records.append((node_id, 'address'))
    
    return records

def parallel_address_record_generator(num_records, num_workers=None):
    """Generate address records in parallel using multiple processes"""
    if num_workers is None:
        num_workers = NUM_WORKERS
    
    # Calculate batch sizes
    batch_size = max(1000, num_records // (num_workers * 10))  # Ensure reasonable batch sizes
    num_batches = (num_records + batch_size - 1) // batch_size
    
    print(f"🚀 Parallel generation: {num_workers} workers, {batch_size:,} records per batch, {num_batches} total batches")
    
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        # Submit batch generation tasks
        futures = []
        remaining_records = num_records
        
        for i in range(num_batches):
            current_batch_size = min(batch_size, remaining_records)
            future = executor.submit(generate_batch_of_address_records, current_batch_size)
            futures.append(future)
            remaining_records -= current_batch_size
        
        # Collect results as they complete
        records_generated = 0
        for future in as_completed(futures):
            batch_records = future.result()
            records_generated += len(batch_records)
            
            # Yield records from this batch
            for record in batch_records:
                yield record
            
            if records_generated % (batch_size * 5) == 0:
                print(f"📊 Generated {records_generated:,}/{num_records:,} records ({records_generated/num_records*100:.1f}%)")

def stream_to_csv(num_records, output_path, column_order, progress_interval=10000):
    """Stream records directly to CSV file with progress monitoring"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    start_time = time.time()
    file_size = 0
    records_written = 0
    
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(column_order)  # Write header
        
        # Update file size after header
        csvfile.flush()
        file_size = os.path.getsize(output_path)
        
        for i in range(num_records):
            # Generate single record
            record = generate_address_record()
            
            # Write record immediately - record is a tuple (node_id, label)
            writer.writerow(record)
            
            records_written += 1
            
            # Flush periodically to ensure data is written to disk
            if records_written % 1000 == 0:
                csvfile.flush()
                file_size = os.path.getsize(output_path)
                
                # Check file size limit
                if file_size > MAX_FILE_SIZE_BYTES:
                    print(f"⚠️  WARNING: File size ({file_size / (1024**3):.2f} GB) exceeds 2.5GB limit!")
                    print(f"   Stopping at {records_written:,} records")
                    break
            
            # Progress reporting
            if records_written % progress_interval == 0:
                elapsed = time.time() - start_time
                rate = records_written / elapsed if elapsed > 0 else 0
                eta = (num_records - records_written) / rate if rate > 0 else 0
                
                print(f"📊 Progress: {records_written:,}/{num_records:,} records "
                      f"({records_written/num_records*100:.1f}%) "
                      f"| Rate: {rate:.0f} records/sec "
                      f"| ETA: {eta/60:.1f} min "
                      f"| File size: {file_size / (1024**3):.2f} GB")
    
    final_file_size = os.path.getsize(output_path)
    elapsed_time = time.time() - start_time
    
    print(f"✅ Streamed {records_written:,} records to {output_path}")
    print(f"📁 Final file size: {final_file_size / (1024**3):.2f} GB")
    print(f"⏱️  Total time: {elapsed_time/60:.1f} minutes")
    print(f"🚀 Average rate: {records_written/elapsed_time:.0f} records/sec")
    
    return records_written, final_file_size

def stream_to_csv_parallel(num_records, output_path, column_order, progress_interval=10000):
    """Stream address records to CSV using parallel generation and optimized I/O"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    start_time = time.time()
    records_written = 0
    
    with open(output_path, 'w', newline='', encoding='utf-8', buffering=WRITER_BUFFER_SIZE) as csvfile:
        writer = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(column_order)  # Write header
        
        # Use parallel record generation
        record_generator = parallel_address_record_generator(num_records)
        
        # Write records as they're generated
        for record in record_generator:
            writer.writerow(record)
            records_written += 1
            
            # Progress reporting
            if records_written % progress_interval == 0:
                elapsed = time.time() - start_time
                rate = records_written / elapsed if elapsed > 0 else 0
                eta = (num_records - records_written) / rate if rate > 0 else 0
                
                print(f"📊 Progress: {records_written:,}/{num_records:,} records "
                      f"({records_written/num_records*100:.1f}%) "
                      f"| Rate: {rate:.0f} records/sec "
                      f"| ETA: {eta/60:.1f} min")
            
            # Check file size periodically
            if records_written % 50000 == 0:
                file_size = os.path.getsize(output_path)
                if file_size > MAX_FILE_SIZE_BYTES:
                    print(f"⚠️  WARNING: File size ({file_size / (1024**3):.2f} GB) exceeds 2.5GB limit!")
                    print(f"   Stopping at {records_written:,} records")
                    break
    
    final_file_size = os.path.getsize(output_path)
    elapsed_time = time.time() - start_time
    
    print(f"✅ Streamed {records_written:,} records to {output_path}")
    print(f"📁 Final file size: {final_file_size / (1024**3):.2f} GB")
    print(f"⏱️  Total time: {elapsed_time/60:.1f} minutes")
    print(f"🚀 Average rate: {records_written/elapsed_time:.0f} records/sec")
    
    return records_written, final_file_size

def estimate_optimal_records_per_file():
    """Estimate optimal number of records per 2.5GB file"""
    # Sample records to calculate average size
    sample_records = [generate_address_record() for _ in range(100)]
    
    # Calculate average record size
    total_size = 0
    for record in sample_records:
        # Use tuple indexing for the new format
        line = f"{record[0]},{record[1]}\n"
        total_size += len(line.encode('utf-8'))
    
    avg_record_size = total_size / len(sample_records)
    target_file_size = MAX_FILE_SIZE_BYTES * SAFETY_MARGIN
    optimal_records = int(target_file_size / avg_record_size)
    
    print(f"Estimated average record size: {avg_record_size:.1f} bytes")
    print(f"Estimated records per 2.5GB file: {optimal_records:,}")
    
    return optimal_records

def validate_env_variables():
    """Validate and return environment variables"""
    person_records = os.getenv('ADDRESS_RECORDS')
    
    if not person_records:
        raise ValueError("❌ ERROR: Missing environment variable ADDRESS_RECORDS. Please set it in your .env file.")
    
    try:
        num_records = int(person_records)
    except ValueError as e:
        raise ValueError(f"❌ ERROR: Invalid integer value in ADDRESS_RECORDS: {e}")
    
    if num_records <= 0:
        raise ValueError("❌ ERROR: ADDRESS_RECORDS must be greater than 0.")
    
    return num_records

def compare_performance(test_records=100000):
    """Compare performance between sequential and parallel approaches"""
    print(f"\n🔬 Performance Comparison Test ({test_records:,} records)")
    print("=" * 60)
    
    # Test sequential approach
    print("\n📊 Testing sequential approach...")
    start_time = time.time()
    
    test_output = 'src/data/output/neptune/nodes/performance_test_sequential.csv'
    column_order = ['~id', '~label']
    
    records_written, _ = stream_to_csv(test_records, test_output, column_order)
    sequential_time = time.time() - start_time
    sequential_rate = records_written / sequential_time
    
    print(f"✅ Sequential: {records_written:,} records in {sequential_time:.1f}s ({sequential_rate:.0f} records/sec)")
    
    # Test parallel approach
    print("\n📊 Testing parallel approach...")
    start_time = time.time()
    
    test_output_parallel = 'src/data/output/neptune/nodes/performance_test_parallel.csv'
    records_written, _ = stream_to_csv_parallel(test_records, test_output_parallel, column_order)
    parallel_time = time.time() - start_time
    parallel_rate = records_written / parallel_time
    
    print(f"✅ Parallel: {records_written:,} records in {parallel_time:.1f}s ({parallel_rate:.0f} records/sec)")
    
    # Calculate improvement
    speedup = sequential_time / parallel_time
    rate_improvement = parallel_rate / sequential_rate
    
    print(f"\n🚀 Performance Results:")
    print(f"   Speedup: {speedup:.1f}x faster")
    print(f"   Rate improvement: {rate_improvement:.1f}x more records/sec")
    print(f"   Time saved: {sequential_time - parallel_time:.1f}s")
    
    # Clean up test files
    try:
        os.remove(test_output)
        os.remove(test_output_parallel)
    except:
        pass
    
    return speedup, rate_improvement

def main():
    """Main function to generate mock address data using parallel streaming approach"""
    
    # Find and load .env file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = find_dotenv(script_dir)
    if not env_path:
        raise FileNotFoundError(f"❌ ERROR: .env file not found. Please create a .env file in the project root.")
    
    print(f"Using .env file at: {env_path}")
    load_dotenv(env_path)
    
    # Validate environment variables
    num_records = validate_env_variables()
    
    print(f"Number of records to generate: {num_records:,}")
    print(f"Maximum file size target: {MAX_FILE_SIZE_BYTES / (1024**3):.1f} GB")
    print(f"Parallel processing: {NUM_WORKERS} CPU cores available")
    print(f"Batch size: {BATCH_SIZE:,} records per batch")
    
    # Optional performance comparison for smaller datasets
    if num_records <= 1000000:  # Only run comparison for datasets <= 1M records
        compare_performance(min(100000, num_records))
    
    # Estimate optimal records per file
    print("\n📊 Estimating optimal records per 2.5GB file...")
    optimal_records = estimate_optimal_records_per_file()
    
    # Check if we need to split into multiple files
    if num_records > optimal_records:
        num_files = (num_records + optimal_records - 1) // optimal_records
        print(f"\n📁 Will split into {num_files} files to stay under 2.5GB limit")
        
        total_generated = 0
        total_file_size = 0
        max_file_size = 0
        
        for file_num in range(num_files):
            records_this_file = min(optimal_records, num_records - total_generated)
            output_path = f'src/data/output/neptune/nodes/neptune_address_nodes_gremlin_{file_num + 1:05d}.csv'
            
            print(f"\n🚀 Parallel streaming file {file_num + 1}/{num_files}: {records_this_file:,} records")
            
            # Define CSV column order
            column_order = ['~id', '~label']
            
            # Use parallel processing for 5x speed improvement
            records_written, file_size = stream_to_csv_parallel(records_this_file, output_path, column_order)
            
            total_generated += records_written
            total_file_size += file_size
            max_file_size = max(max_file_size, file_size)
            
            if records_written < records_this_file:
                print(f"⚠️  File size limit reached, stopping at {records_written:,} records")
                break
        
        print(f"\n✅ Successfully generated {total_generated:,} address nodes in {num_files} files using parallel streaming.")
        print(f"📁 Total output size: {total_file_size / (1024**3):.2f} GB")
        print(f"📁 Largest file size: {max_file_size / (1024**3):.2f} GB")
        
    else:
        # Single file approach
        output_path = 'src/data/output/neptune/nodes/neptune_address_nodes_gremlin_00001.csv'
        column_order = ['~id','~label']
        
        print(f"\n🚀 Parallel streaming all {num_records:,} records to single file...")
        records_written, file_size = stream_to_csv_parallel(num_records, output_path, column_order)
        
        print(f"\n✅ Successfully generated {records_written:,} address nodes using parallel streaming.")
        print(f"📁 File size: {file_size / (1024**3):.2f} GB")
        
        # Set max_file_size for single file case
        max_file_size = file_size
    
    if max_file_size > MAX_FILE_SIZE_BYTES:
        print(f"⚠️  WARNING: Largest file ({max_file_size / (1024**3):.2f} GB) exceeds 2.5GB limit!")
    else:
        print(f"✅ All files are within 2.5GB limit.")
    
    return True

if __name__ == "__main__":
    main()