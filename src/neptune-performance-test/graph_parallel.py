#!/usr/bin/env python3
"""
High-Performance CSV Mock Data Generator for Gremlin Data Load Format
Generates CSV files with mock data using parallel processing and streaming
Optimized for up to 14 CPUs and 48GB RAM
"""

import csv
import os
import random
import uuid
import gc
import psutil
import time
import threading
from datetime import datetime, timedelta
from faker import Faker
from multiprocessing import cpu_count
from concurrent.futures import ProcessPoolExecutor, as_completed

# Worker function for parallel data generation
def generate_batch_data(args):
    """Generate a batch of data in parallel worker process"""
    node_type, start_idx, batch_size, seed = args
    
    # Create separate Faker instance with unique seed for each worker
    fake = Faker()
    Faker.seed(seed + start_idx)
    random.seed(seed + start_idx)
    
    batch_data = []
    
    for i in range(batch_size):
        if node_type == 'person':
            data = _generate_person_data_worker(fake)
        elif node_type == 'address':
            data = _generate_address_data_worker(fake)
        elif node_type == 'building':
            data = _generate_building_data_worker(fake)
        elif node_type == 'form':
            data = _generate_form_data_worker(fake)
        elif node_type == 'name':
            data = _generate_name_data_worker(fake)
        elif node_type == 'email':
            data = _generate_email_data_worker(fake)
        elif node_type == 'phone':
            data = _generate_phone_data_worker(fake)
        else:
            continue
            
        batch_data.append(data)
    
    return batch_data

def _generate_person_data_worker(fake):
    """Worker function for person data generation"""
    # Generate base data
    first_name = fake.first_name().upper()
    last_name = fake.last_name().upper()
    full_name = f"{first_name} {last_name}"
    
    # Generate name variations
    name_variations = [
        full_name,
        f"{last_name}, {first_name}",
        f"{first_name[0]}. {last_name}",
        f"{last_name}, {first_name[0]}.",
        f"{first_name} {last_name[0]}.",
        f"{last_name[0]}. {first_name}"
    ]
    
    # Generate base birth date
    base_birth_date = fake.date_of_birth(minimum_age=18, maximum_age=80)
    birth_date_str = base_birth_date.strftime('%Y-%m-%d')
    
    # Generate date variations (±1-5 days)
    date_variations = [birth_date_str]
    for i in range(1, 6):
        date_plus = (base_birth_date + timedelta(days=i)).strftime('%Y-%m-%d')
        date_minus = (base_birth_date - timedelta(days=i)).strftime('%Y-%m-%d')
        date_variations.extend([date_plus, date_minus])
    
    # Generate primary anumber
    primary_anumber = str(random.randint(1000000000, 9999999999))
    
    # Generate additional anumbers (1-3 total)
    anumber_count = random.randint(1, 3)
    anumber_list = [primary_anumber]
    for _ in range(anumber_count - 1):
        additional_anumber = str(random.randint(1000000000, 9999999999))
        anumber_list.append(additional_anumber)
    
    return {
        "~id": str(uuid.uuid4()),
        "name_full:String": full_name,
        "name_full_list:String": ";".join(name_variations),
        "date_of_birth:Date": birth_date_str,
        "date_of_birth_list:Date[]": ";".join(date_variations),
        "anumber_primary:String": primary_anumber,
        "anumber_list:String[]": ":".join(anumber_list),
        "~label": "person;primary"
    }

def _generate_address_data_worker(fake):
    """Worker function for address data generation"""
    return {
        "~id": f"address_{uuid.uuid4()}",
        "~from": "",
        "~to": "",
        "address_type:String": random.choice(["primary", "secondary", "mailing"]),
        "~label": "address",
        "street:String": fake.street_address(),
        "city:String": fake.city(),
        "state:String": fake.state_abbr(),
        "zip_code:String": fake.zipcode()
    }

def _generate_building_data_worker(fake):
    """Worker function for building data generation"""
    building_types = ["office", "residential", "commercial", "industrial"]
    return {
        "~id": f"building_{uuid.uuid4()}",
        "~from": "",
        "~to": "",
        "address_type:String": "primary",
        "~label": "building", 
        "building_name:String": fake.company(),
        "building_type:String": random.choice(building_types)
    }

def _generate_form_data_worker(fake):
    """Worker function for form data generation"""
    form_types = ["I-130", "I-485", "N-400", "I-765", "I-94"]
    return {
        "~id": f"form_{uuid.uuid4()}",
        "~from": "",
        "~to": "",
        "address_type:String": "primary",
        "~label": "form",
        "form_number:String": random.choice(form_types) + f"-{random.randint(100000, 999999)}",
        "form_type:String": random.choice(form_types),
        "filed_date:Date": fake.date_between(start_date='-5y', end_date='today').strftime('%Y-%m-%d')
    }

def _generate_name_data_worker(fake):
    """Worker function for name data generation"""
    return {
        "~id": f"name_{uuid.uuid4()}",
        "~from": "",
        "~to": "",
        "address_type:String": "primary",
        "~label": "name",
        "first_name:String": fake.first_name(),
        "last_name:String": fake.last_name(),
        "middle_name:String": fake.first_name() if random.choice([True, False]) else ""
    }

def _generate_email_data_worker(fake):
    """Worker function for email data generation"""
    email_types = ["personal", "work", "business", "other"]
    return {
        "~id": f"email_{uuid.uuid4()}",
        "~from": "",
        "~to": "",
        "address_type:String": "primary",
        "~label": "email",
        "email_address:String": fake.email(),
        "email_type:String": random.choice(email_types)
    }

def _generate_phone_data_worker(fake):
    """Worker function for phone data generation"""
    phone_types = ["mobile", "home", "work", "fax"]
    return {
        "~id": f"phone_{uuid.uuid4()}",
        "~from": "",
        "~to": "",
        "address_type:String": "primary",
        "~label": "phone",
        "phone_number:String": fake.phone_number(),
        "phone_type:String": random.choice(phone_types)
    }

class HighPerformanceGremlinCSVGenerator:
    def __init__(self, file_size_limit=1000000, output_dir="csv_output", max_workers=14, max_memory_gb=48):
        """
        Initialize the high-performance CSV generator
        
        Args:
            file_size_limit (int): Maximum number of records per file before splitting
            output_dir (str): Directory to save CSV files
            max_workers (int): Maximum number of worker processes
            max_memory_gb (int): Maximum memory usage in GB
        """
        self.file_size_limit = file_size_limit
        self.output_dir = output_dir
        self.max_workers = min(max_workers, cpu_count())
        self.max_memory_gb = max_memory_gb
        self.batch_size = 50000  # Records per batch for streaming
        
        # Dynamic batch sizing based on available memory
        available_memory = psutil.virtual_memory().available / (1024 ** 3)
        if available_memory < 16:
            self.batch_size = 25000
        elif available_memory < 8:
            self.batch_size = 10000
        
        # Node type counters
        self.node_counts = {
            'person': 0,
            'address': 0, 
            'building': 0,
            'form': 0,
            'name': 0,
            'email': 0,
            'phone': 0
        }
        
        # File counters for splitting
        self.file_counters = {
            'person': 1,
            'address': 1,
            'building': 1, 
            'form': 1,
            'name': 1,
            'email': 1,
            'phone': 1
        }
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        # System info
        total_memory = psutil.virtual_memory().total / (1024 ** 3)
        print(f"🚀 High-Performance Generator Initialized")
        print(f"   Workers: {self.max_workers}/{cpu_count()} CPUs")
        print(f"   Memory: {available_memory:.1f}GB available / {total_memory:.1f}GB total")
        print(f"   Batch size: {self.batch_size:,} records")
        print(f"   File limit: {self.file_size_limit:,} records per file")
    
    def _get_filename(self, node_type):
        """Generate filename with counter for file splitting"""
        counter = self.file_counters[node_type]
        return f"{node_type}-{counter}.csv"
    
    def _get_filepath(self, node_type):
        """Get full filepath for a node type"""
        filename = self._get_filename(node_type)
        return os.path.join(self.output_dir, filename)
    
    def _should_create_new_file(self, node_type):
        """Check if we should create a new file for this node type"""
        return self.node_counts[node_type] % self.file_size_limit == 0 and self.node_counts[node_type] > 0
    
    def _get_fieldnames(self, node_type):
        """Get fieldnames for CSV DictWriter"""
        headers = {
            'person': ["~id", "name_full:String", "name_full_list:String", "date_of_birth:Date", "date_of_birth_list:Date[]", "anumber_primary:String", "anumber_list:String[]", "~label"],
            'address': ["~id", "~from", "~to", "address_type:String", "~label", "street:String", "city:String", "state:String", "zip_code:String"],
            'building': ["~id", "~from", "~to", "address_type:String", "~label", "building_name:String", "building_type:String"],
            'form': ["~id", "~from", "~to", "address_type:String", "~label", "form_number:String", "form_type:String", "filed_date:Date"],
            'name': ["~id", "~from", "~to", "address_type:String", "~label", "first_name:String", "last_name:String", "middle_name:String"],
            'email': ["~id", "~from", "~to", "address_type:String", "~label", "email_address:String", "email_type:String"],
            'phone': ["~id", "~from", "~to", "address_type:String", "~label", "phone_number:String", "phone_type:String"]
        }
        return headers[node_type]
    
    def _get_memory_usage_gb(self):
        """Get current memory usage in GB"""
        process = psutil.Process()
        return process.memory_info().rss / (1024 ** 3)
    
    def _should_limit_batch_size(self):
        """Check if we should reduce batch size due to memory pressure"""
        current_memory = self._get_memory_usage_gb()
        if current_memory > self.max_memory_gb * 0.8:  # 80% threshold
            return True
        return False
    
    def generate_node_data_parallel(self, node_type, count):
        """
        Generate CSV data for a specific node type using parallel processing and streaming
        
        Args:
            node_type (str): Type of node to generate
            count (int): Number of records to generate
        """
        if node_type not in self.node_counts:
            raise ValueError(f"Invalid node type: {node_type}")
        
        print(f"\n📊 Generating {count:,} {node_type} records with {self.max_workers} workers...")
        start_time = time.time()
        
        # Calculate optimal batch size based on memory and worker count
        dynamic_batch_size = min(self.batch_size, max(count // (self.max_workers * 4), 1000))
        if self._should_limit_batch_size():
            dynamic_batch_size = dynamic_batch_size // 2
        
        # Create batches for parallel processing
        batches = []
        for i in range(0, count, dynamic_batch_size):
            batch_count = min(dynamic_batch_size, count - i)
            batches.append((node_type, i, batch_count, random.randint(1, 1000000)))
        
        print(f"   Processing {len(batches)} batches of ~{dynamic_batch_size:,} records each")
        
        # Process batches in parallel and stream to files
        current_file = None
        current_writer = None
        records_written = 0
        filepath = None
        
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all batches
            future_to_batch = {executor.submit(generate_batch_data, batch): batch for batch in batches}
            
            # Process completed batches and stream to files
            for future in as_completed(future_to_batch):
                try:
                    batch_data = future.result()
                    
                    # Stream batch data to CSV files
                    for data in batch_data:
                        # Check if we need a new file
                        if self._should_create_new_file(node_type) or current_file is None:
                            if current_file:
                                current_file.close()
                                print(f"   ✓ Completed: {os.path.basename(filepath)} ({records_written:,} records)")
                            
                            # Increment file counter if not the first file
                            if current_file is not None:
                                self.file_counters[node_type] += 1
                            
                            # Open new file
                            filepath = self._get_filepath(node_type)
                            current_file = open(filepath, 'w', newline='')
                            current_writer = csv.DictWriter(current_file, fieldnames=self._get_fieldnames(node_type))
                            current_writer.writeheader()
                            records_written = 0
                            print(f"   📁 Created: {os.path.basename(filepath)}")
                        
                        # Write data
                        current_writer.writerow(data)
                        self.node_counts[node_type] += 1
                        records_written += 1
                    
                    # Force garbage collection after each batch
                    del batch_data
                    gc.collect()
                    
                    # Check memory usage
                    current_mem = self._get_memory_usage_gb()
                    if current_mem > self.max_memory_gb * 0.9:
                        print(f"   ⚠️  Memory warning: {current_mem:.1f}GB used")
                        gc.collect()
                    
                except Exception as e:
                    print(f"   ❌ Error processing batch: {e}")
        
        # Close the last file
        if current_file:
            current_file.close()
            print(f"   ✓ Completed: {os.path.basename(filepath)} ({records_written:,} records)")
        
        elapsed_time = time.time() - start_time
        rate = count / elapsed_time if elapsed_time > 0 else 0
        print(f"   ⚡ Generated {count:,} {node_type} records in {elapsed_time:.2f}s ({rate:,.0f} records/sec)")
    
    def generate_node_data(self, node_type, count):
        """
        Main method to generate node data (automatically chooses parallel vs sequential)
        """
        if count >= 10000:  # Use parallel processing for larger datasets
            self.generate_node_data_parallel(node_type, count)
        else:
            self.generate_node_data_sequential(node_type, count)
    
    def generate_node_data_sequential(self, node_type, count):
        """
        Generate CSV data sequentially (for smaller datasets)
        """
        print(f"\n📊 Generating {count:,} {node_type} records sequentially...")
        
        if node_type not in self.node_counts:
            raise ValueError(f"Invalid node type: {node_type}")
        
        fake = Faker()
        current_file = None
        current_writer = None
        
        for i in range(count):
            # Check if we need to create a new file
            if self._should_create_new_file(node_type) or current_file is None:
                if current_file:
                    current_file.close()
                
                # Increment file counter if not the first file
                if current_file is not None:
                    self.file_counters[node_type] += 1
                
                # Open new file
                filepath = self._get_filepath(node_type)
                current_file = open(filepath, 'w', newline='')
                current_writer = csv.DictWriter(current_file, fieldnames=self._get_fieldnames(node_type))
                current_writer.writeheader()
                
                print(f"   📁 Created: {os.path.basename(filepath)}")
            
            # Generate data using worker functions for consistency
            if node_type == 'person':
                data = _generate_person_data_worker(fake)
            elif node_type == 'address':
                data = _generate_address_data_worker(fake)
            elif node_type == 'building':
                data = _generate_building_data_worker(fake)
            elif node_type == 'form':
                data = _generate_form_data_worker(fake)
            elif node_type == 'name':
                data = _generate_name_data_worker(fake)
            elif node_type == 'email':
                data = _generate_email_data_worker(fake)
            elif node_type == 'phone':
                data = _generate_phone_data_worker(fake)
            
            current_writer.writerow(data)
            self.node_counts[node_type] += 1
        
        # Close the last file
        if current_file:
            current_file.close()
    
    def print_summary(self):
        """Print generation summary"""
        print("\n" + "="*60)
        print("🎯 GENERATION SUMMARY")
        print("="*60)
        total_records = sum(self.node_counts.values())
        for node_type, count in self.node_counts.items():
            files_created = self.file_counters[node_type] if count > 0 else 0
            print(f"{node_type.capitalize():>12}: {count:>10,} records across {files_created:>2} file(s)")
        print("-" * 60)
        print(f"{'Total':>12}: {total_records:>10,} records")
        print("="*60)
        
        # Memory usage
        final_memory = self._get_memory_usage_gb()
        print(f"Final memory usage: {final_memory:.1f}GB")

def main():
    """Main execution function"""
    # Configuration variables for high-performance generation
    FILE_SIZE_LIMIT = 1000000  # 1M records per file
    OUTPUT_DIR = "src/neptune-performance-test/csv_output"
    MAX_WORKERS = 14  # Up to 14 CPUs
    MAX_MEMORY_GB = 48  # Up to 48GB RAM
    
    # High-volume node generation counts
    GENERATION_COUNTS = {
        'person': 10000000,   # 10M person records 
        'address': 3000000,   # 3M address records
        'building': 150000,  # 1.5M building records
        'form': 2000000,      # 2M form records
        'name': 4000000,      # 4M name records
        'email': 3500000,     # 3.5M email records
        'phone': 4500000      # 4.5M phone records
    }
    
    print("🚀 HIGH-PERFORMANCE GREMLIN CSV MOCK DATA GENERATION")
    print("=" * 70)
    print(f"Target: {sum(GENERATION_COUNTS.values()):,} total records")
    print(f"Resources: {MAX_WORKERS} CPUs, {MAX_MEMORY_GB}GB RAM")
    print(f"File size limit: {FILE_SIZE_LIMIT:,} records per file")
    print("=" * 70)
    
    # Initialize high-performance generator
    generator = HighPerformanceGremlinCSVGenerator(
        file_size_limit=FILE_SIZE_LIMIT,
        output_dir=OUTPUT_DIR,
        max_workers=MAX_WORKERS,
        max_memory_gb=MAX_MEMORY_GB
    )
    
    # Track total execution time
    total_start_time = time.time()
    
    # Generate data for each node type
    for node_type, count in GENERATION_COUNTS.items():
        generator.generate_node_data(node_type, count)
        
        # Force garbage collection between node types
        gc.collect()
    
    total_time = time.time() - total_start_time
    total_records = sum(GENERATION_COUNTS.values())
    overall_rate = total_records / total_time if total_time > 0 else 0
    
    # Print final summary
    generator.print_summary()
    print(f"\n⚡ PERFORMANCE SUMMARY")
    print(f"Total execution time: {total_time:.2f} seconds ({total_time/60:.1f} minutes)")
    print(f"Overall generation rate: {overall_rate:,.0f} records/second")
    print("\n🎉 High-performance generation completed successfully!")

if __name__ == "__main__":
    main()