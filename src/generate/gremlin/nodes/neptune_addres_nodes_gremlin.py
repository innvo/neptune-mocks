import uuid
import random
import os
from datetime import datetime
from faker import Faker
from dotenv import load_dotenv
import csv
import time

fake = Faker()

# Constants for file size optimization
MAX_FILE_SIZE_BYTES = 2.5 * 1024 * 1024 * 1024  # 2.5GB
SAFETY_MARGIN = 0.9  # 90% of max file size to ensure we stay under limit

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
    """Generate a single addressrecord"""
   
    node_id = str(uuid.uuid4())
    
    return {
        '~id': node_id,
        '~label': 'address'
    }

def stream_to_csv(num_records, output_path, column_order, progress_interval=10000):
    """Stream records directly to CSV file with progress monitoring"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    start_time = time.time()
    file_size = 0
    records_written = 0
    
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=column_order, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        
        # Update file size after header
        csvfile.flush()
        file_size = os.path.getsize(output_path)
        
        for i in range(num_records):
            # Generate single record
            record = generate_address_record()
            
            # Write record immediately
            ordered_record = {col: record.get(col, '') for col in column_order}
            writer.writerow(ordered_record)
            
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

def estimate_optimal_records_per_file():
    """Estimate optimal number of records per 2.5GB file"""
    # Sample records to calculate average size
    sample_records = [generate_address_record() for _ in range(100)]
    
    # Calculate average record size
    total_size = 0
    for record in sample_records:
        line = f"{record['~id']},{record['~label']}\n"
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

def main():
    """Main function to generate mock address data using streaming approach"""
    
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
    print(f"Streaming approach: Records will be generated and written incrementally")
    
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
            
            print(f"\n🚀 Streaming file {file_num + 1}/{num_files}: {records_this_file:,} records")
            
            # Define CSV column order
            column_order = ['~id', '~label']
            
            records_written, file_size = stream_to_csv(records_this_file, output_path, column_order)
            
            total_generated += records_written
            total_file_size += file_size
            max_file_size = max(max_file_size, file_size)
            
            if records_written < records_this_file:
                print(f"⚠️  File size limit reached, stopping at {records_written:,} records")
                break
        
        print(f"\n✅ Successfully generated {total_generated:,} address nodes in {num_files} files using streaming.")
        print(f"📁 Total output size: {total_file_size / (1024**3):.2f} GB")
        print(f"📁 Largest file size: {max_file_size / (1024**3):.2f} GB")
        
    else:
        # Single file approach
        output_path = 'src/data/output/neptune/nodes/neptune_address_nodes_gremlin_00001.csv'
        column_order = ['~id','~label']
        
        print(f"\n🚀 Streaming all {num_records:,} records to single file...")
        records_written, file_size = stream_to_csv(num_records, output_path, column_order)
        
        print(f"\n✅ Successfully generated {records_written:,} address nodes using streaming.")
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