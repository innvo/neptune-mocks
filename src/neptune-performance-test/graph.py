#!/usr/bin/env python3
"""
CSV Mock Data Generator for Gremlin Data Load Format
Generates CSV files with mock data for nodes: person, address, building, form, name, email, phone
"""

import csv
import os
import random
import uuid
import gc
import psutil
import time
import queue
import threading
from datetime import datetime, timedelta
from faker import Faker
from multiprocessing import Pool, Manager, cpu_count
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed

class GremlinCSVGenerator:
    def __init__(self, file_size_limit=1000000, output_dir="output"):
        """
        Initialize the CSV generator
        
        Args:
            file_size_limit (int): Maximum number of records per file before splitting
            output_dir (str): Directory to save CSV files
        """
        self.file_size_limit = file_size_limit
        self.output_dir = output_dir
        self.fake = Faker()
        
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
    
    def _write_header(self, writer, node_type):
        """Write CSV header based on node type"""
        headers = {
            'person': ["~id", "name_full:String", "name_full_list:String", "date_of_birth:Date", "date_of_birth_list:Date[]", "anumber_primary:String", "anumber_list:String[]", "~label"],
            'address': ["~id", "~from", "~to", "address_type:String", "~label", "street:String", "city:String", "state:String", "zip_code:String"],
            'building': ["~id", "~from", "~to", "address_type:String", "~label", "building_name:String", "building_type:String"],
            'form': ["~id", "~from", "~to", "address_type:String", "~label", "form_number:String", "form_type:String", "filed_date:Date"],
            'name': ["~id", "~from", "~to", "address_type:String", "~label", "first_name:String", "last_name:String", "middle_name:String"],
            'email': ["~id", "~from", "~to", "address_type:String", "~label", "email_address:String", "email_type:String"],
            'phone': ["~id", "~from", "~to", "address_type:String", "~label", "phone_number:String", "phone_type:String"]
        }
        writer.writeheader()
    
    def _generate_person_data(self):
        """Generate mock person data"""
        # Generate base data
        first_name = self.fake.first_name().upper()
        last_name = self.fake.last_name().upper()
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
        base_birth_date = self.fake.date_of_birth(minimum_age=18, maximum_age=80)
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
    
    def _generate_address_data(self):
        """Generate mock address data"""
        return {
            "~id": f"address_{uuid.uuid4()}",
            "~from": "",
            "~to": "",
            "address_type:String": random.choice(["primary", "secondary", "mailing"]),
            "~label": "address",
            "street:String": self.fake.street_address(),
            "city:String": self.fake.city(),
            "state:String": self.fake.state_abbr(),
            "zip_code:String": self.fake.zipcode()
        }
    
    def _generate_building_data(self):
        """Generate mock building data"""
        building_types = ["office", "residential", "commercial", "industrial"]
        return {
            "~id": f"building_{uuid.uuid4()}",
            "~from": "",
            "~to": "",
            "address_type:String": "primary",
            "~label": "building", 
            "building_name:String": self.fake.company(),
            "building_type:String": random.choice(building_types)
        }
    
    def _generate_form_data(self):
        """Generate mock form data"""
        form_types = ["I-130", "I-485", "N-400", "I-765", "I-94"]
        return {
            "~id": f"form_{uuid.uuid4()}",
            "~from": "",
            "~to": "",
            "address_type:String": "primary",
            "~label": "form",
            "form_number:String": random.choice(form_types) + f"-{random.randint(100000, 999999)}",
            "form_type:String": random.choice(form_types),
            "filed_date:Date": self.fake.date_between(start_date='-5y', end_date='today').strftime('%Y-%m-%d')
        }
    
    def _generate_name_data(self):
        """Generate mock name data"""
        return {
            "~id": f"name_{uuid.uuid4()}",
            "~from": "",
            "~to": "",
            "address_type:String": "primary",
            "~label": "name",
            "first_name:String": self.fake.first_name(),
            "last_name:String": self.fake.last_name(),
            "middle_name:String": self.fake.first_name() if random.choice([True, False]) else ""
        }
    
    def _generate_email_data(self):
        """Generate mock email data"""
        email_types = ["personal", "work", "business", "other"]
        return {
            "~id": f"email_{uuid.uuid4()}",
            "~from": "",
            "~to": "",
            "address_type:String": "primary",
            "~label": "email",
            "email_address:String": self.fake.email(),
            "email_type:String": random.choice(email_types)
        }
    
    def _generate_phone_data(self):
        """Generate mock phone data"""
        phone_types = ["mobile", "home", "work", "fax"]
        return {
            "~id": f"phone_{uuid.uuid4()}",
            "~from": "",
            "~to": "",
            "address_type:String": "primary",
            "~label": "phone",
            "phone_number:String": self.fake.phone_number(),
            "phone_type:String": random.choice(phone_types)
        }
    
    def generate_node_data(self, node_type, count):
        """
        Generate CSV data for a specific node type
        
        Args:
            node_type (str): Type of node to generate (person, address, building, form, name, email, phone)
            count (int): Number of records to generate
        """
        if node_type not in self.node_counts:
            raise ValueError(f"Invalid node type: {node_type}")
        
        # Data generation methods
        generators = {
            'person': self._generate_person_data,
            'address': self._generate_address_data,
            'building': self._generate_building_data,
            'form': self._generate_form_data,
            'name': self._generate_name_data,
            'email': self._generate_email_data,
            'phone': self._generate_phone_data
        }
        
        current_file = None
        current_writer = None
        
        for _ in range(count):
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
                self._write_header(current_writer, node_type)
                
                print(f"Created new file: {filepath}")
            
            # Generate and write data
            data = generators[node_type]()
            current_writer.writerow(data)
            self.node_counts[node_type] += 1
        
        # Close the last file
        if current_file:
            current_file.close()
    
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
    
    def print_summary(self):
        """Print generation summary"""
        print("\n" + "="*50)
        print("GENERATION SUMMARY")
        print("="*50)
        for node_type, count in self.node_counts.items():
            files_created = self.file_counters[node_type] if count > 0 else 0
            print(f"{node_type.capitalize()}: {count:,} records across {files_created} file(s)")
        print("="*50)

def main():
    """Main execution function"""
    # Configuration variables
    FILE_SIZE_LIMIT = 1000000  # Records per file
    OUTPUT_DIR = "src/neptune-performance-test/csv_output"
    
    # Node generation counts
    GENERATION_COUNTS = {
        'person': 5000000,
        'address': 2500000,
        'building': 1500,
        'form': 2000,
        'name': 4000,
        'email': 3500,
        'phone': 4500
    }
    
    print("Starting Gremlin CSV Mock Data Generation")
    print(f"File size limit: {FILE_SIZE_LIMIT:,} records per file")
    print(f"Output directory: {OUTPUT_DIR}")
    
    # Initialize generator
    generator = GremlinCSVGenerator(
        file_size_limit=FILE_SIZE_LIMIT,
        output_dir=OUTPUT_DIR
    )
    
    # Generate data for each node type
    for node_type, count in GENERATION_COUNTS.items():
        print(f"\nGenerating {count:,} {node_type} records...")
        generator.generate_node_data(node_type, count)
    
    # Print summary
    generator.print_summary()
    print("\n<� Generation completed successfully!")

if __name__ == "__main__":
    main()