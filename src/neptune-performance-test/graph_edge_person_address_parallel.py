#!/usr/bin/env python3
"""
High-Performance Person-Address Edge Generator
Creates edges between person and address nodes with optimized parallel processing.
Each person can have 0-10 addresses with PRIMARY/SECONDARY types.
"""

import csv
import os
import uuid
import random
import time
import gc
import pickle
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import cpu_count
from typing import List, Dict

class NodeIndexer:
    def __init__(self, csv_output_dir="src/neptune-performance-test/csv_output"):
        """Simple node indexer for loading person and address IDs"""
        self.csv_output_dir = csv_output_dir
        self.indexes = {}
    
    def create_memory_indexes(self):
        """Create in-memory indexes for person and address nodes"""
        print("🔍 Creating in-memory node indexes...")
        start_time = time.time()
        
        node_types = ['person', 'address']
        
        for node_type in node_types:
            print(f"  Indexing {node_type} nodes...")
            self.indexes[node_type] = []
            
            # Find all CSV files for this node type
            csv_files = []
            
            if not os.path.exists(self.csv_output_dir):
                print(f"    Warning: Directory {self.csv_output_dir} not found")
                continue
                
            for file in os.listdir(self.csv_output_dir):
                if file.startswith(f"{node_type}-") and file.endswith(".csv"):
                    csv_files.append(os.path.join(self.csv_output_dir, file))
            
            # Read IDs from each file
            for csv_file in sorted(csv_files):
                try:
                    with open(csv_file, 'r') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            self.indexes[node_type].append(row['~id'])
                except Exception as e:
                    print(f"    Warning: Could not read {csv_file}: {e}")
            
            print(f"    Indexed {len(self.indexes[node_type]):,} {node_type} IDs")
        
        elapsed = time.time() - start_time
        total_ids = sum(len(ids) for ids in self.indexes.values())
        print(f"  ✓ Indexed {total_ids:,} total IDs in {elapsed:.2f}s")
        
        return self.indexes
    
    def save_indexes_to_pickle(self, output_file="node_indexes.pkl"):
        """Save indexes to pickle file"""
        output_path = os.path.join(self.csv_output_dir, output_file)
        print(f"💾 Saving indexes to {output_file}...")
        
        try:
            with open(output_path, 'wb') as f:
                pickle.dump(self.indexes, f)
            
            file_size = os.path.getsize(output_path) / (1024 * 1024)
            print(f"  ✓ Saved to {output_file} ({file_size:.1f}MB)")
            return True
        except Exception as e:
            print(f"  ❌ Failed to save: {e}")
            return False
    
    def load_indexes_from_pickle(self, input_file="node_indexes.pkl"):
        """Load indexes from pickle file"""
        input_path = os.path.join(self.csv_output_dir, input_file)
        
        if not os.path.exists(input_path):
            print(f"  Index file {input_file} not found")
            return False
        
        print(f"📖 Loading indexes from {input_file}...")
        
        try:
            with open(input_path, 'rb') as f:
                self.indexes = pickle.load(f)
            
            total_ids = sum(len(ids) for ids in self.indexes.values())
            print(f"  ✓ Loaded {total_ids:,} total IDs")
            return True
        except Exception as e:
            print(f"  ❌ Failed to load: {e}")
            return False

class PersonAddressEdgeGenerator:
    def __init__(self, 
                 csv_output_dir="src/neptune-performance-test/csv_output",
                 file_size_limit=1000000,
                 max_workers=14,
                 max_memory_gb=48):
        """
        Initialize the Person-Address Edge Generator
        
        Args:
            csv_output_dir (str): Directory containing CSV files
            file_size_limit (int): Records per edge file
            max_workers (int): Maximum worker processes
            max_memory_gb (int): Maximum memory usage in GB
        """
        self.csv_output_dir = csv_output_dir
        self.file_size_limit = file_size_limit
        self.max_workers = min(max_workers, cpu_count())
        self.max_memory_gb = max_memory_gb
        
        # Edge generation counters
        self.edge_count = 0
        self.file_count = 0
        self.current_file_count = 0
        
        # Performance tracking
        self.start_time = None
        self.total_edges_generated = 0
        
        # Address types with weights (PRIMARY more common)
        self.address_types = [
            ("PRIMARY", 0.7),      # 70% primary addresses
            ("SECONDARY", 0.3)     # 30% secondary addresses
        ]
        
        print(f"PersonAddressEdgeGenerator initialized:")
        print(f"  Output directory: {csv_output_dir}")
        print(f"  File size limit: {file_size_limit:,} records per file")
        print(f"  Max workers: {self.max_workers}")
        print(f"  Max memory: {max_memory_gb}GB")
    
    def _get_weighted_address_type(self) -> str:
        """Get random address type based on weights"""
        rand = random.random()
        cumulative = 0
        for addr_type, weight in self.address_types:
            cumulative += weight
            if rand <= cumulative:
                return addr_type
        return "PRIMARY"  # Fallback
    
    def _generate_edge_id(self) -> str:
        """Generate unique edge ID"""
        return str(uuid.uuid4())
    
    def _process_person_batch(self, person_batch: List[str], address_ids: List[str], 
                             batch_id: int) -> List[Dict]:
        """
        Process a batch of person IDs to create edges
        
        Args:
            person_batch: List of person IDs
            address_ids: Available address IDs
            batch_id: Batch identifier for tracking
            
        Returns:
            List of edge dictionaries
        """
        edges = []
        
        for person_id in person_batch:
            # Each person gets 0-10 addresses (weighted towards fewer)
            num_addresses = random.choices(
                range(11),  # 0-10 addresses
                weights=[5, 25, 30, 20, 10, 5, 3, 1, 1, 0, 0],  # Weighted distribution
                k=1
            )[0]
            
            if num_addresses == 0:
                continue  # This person has no addresses
            
            # Select random addresses (ensure no duplicates for same person)
            if num_addresses >= len(address_ids):
                selected_addresses = address_ids[:]
            else:
                selected_addresses = random.sample(address_ids, num_addresses)
            
            # Create edges for this person
            person_edges = []
            has_primary = False
            
            for i, address_id in enumerate(selected_addresses):
                # First address is usually PRIMARY, others can be SECONDARY
                if i == 0 and not has_primary:
                    address_type = "PRIMARY"
                    has_primary = True
                else:
                    address_type = self._get_weighted_address_type()
                    if address_type == "PRIMARY" and has_primary:
                        address_type = "SECONDARY"  # Only one PRIMARY per person
                    elif address_type == "PRIMARY":
                        has_primary = True
                
                edge = {
                    '~id': self._generate_edge_id(),
                    '~from': person_id,
                    '~to': address_id,
                    'address_type:String': address_type,
                    '~label': 'person_address;primary'
                }
                
                person_edges.append(edge)
            
            edges.extend(person_edges)
        
        return edges
    
    def _write_edges_to_csv(self, edges: List[Dict], output_file: str):
        """
        Write edges to CSV file with proper headers
        
        Args:
            edges: List of edge dictionaries
            output_file: Output file path
        """
        fieldnames = ['~id', '~from', '~to', 'address_type:String', '~label']
        
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for edge in edges:
                writer.writerow(edge)
    
    def _get_output_filename(self) -> str:
        """Generate output filename with incrementing counter"""
        self.file_count += 1
        return os.path.join(self.csv_output_dir, f"person_address_edge-{self.file_count}.csv")
    
    def generate_person_address_edges(self, batch_size: int = 50000):
        """
        Generate person-address edges using parallel processing
        
        Args:
            batch_size: Number of person records to process per batch
        """
        print(f"\n= GENERATING PERSON-ADDRESS EDGES")
        print("=" * 50)
        
        # Initialize node indexer
        print("📋 Loading node indexes...")
        indexer = NodeIndexer(self.csv_output_dir)
        
        # Try to load existing indexes first
        if not indexer.load_indexes_from_pickle():
            print("Creating new indexes...")
            indexer.create_memory_indexes()
            indexer.save_indexes_to_pickle()
        
        # Get available node IDs
        person_ids = indexer.indexes.get('person', [])
        address_ids = indexer.indexes.get('address', [])
        
        if not person_ids:
            print("L No person IDs found! Generate person data first.")
            return
        
        if not address_ids:
            print("L No address IDs found! Generate address data first.")
            return
        
        print(f"=� Found {len(person_ids):,} person IDs")
        print(f"=� Found {len(address_ids):,} address IDs")
        
        # Create output directory
        os.makedirs(self.csv_output_dir, exist_ok=True)
        
        # Start timing
        self.start_time = time.time()
        
        # Split person IDs into batches for parallel processing
        person_batches = []
        for i in range(0, len(person_ids), batch_size):
            batch = person_ids[i:i + batch_size]
            person_batches.append(batch)
        
        print(f"= Processing {len(person_batches)} batches with {self.max_workers} workers...")
        
        # Process batches in parallel
        all_edges = []
        
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all batches
            future_to_batch = {}
            for batch_id, person_batch in enumerate(person_batches):
                future = executor.submit(
                    self._process_person_batch,
                    person_batch,
                    address_ids,
                    batch_id
                )
                future_to_batch[future] = batch_id
            
            # Collect results as they complete
            completed_batches = 0
            for future in as_completed(future_to_batch):
                batch_id = future_to_batch[future]
                
                try:
                    batch_edges = future.result()
                    all_edges.extend(batch_edges)
                    completed_batches += 1
                    
                    print(f"   Batch {batch_id + 1}/{len(person_batches)} complete "
                          f"({len(batch_edges):,} edges)")
                    
                    # Write to file when we reach the limit
                    if len(all_edges) >= self.file_size_limit:
                        self._write_edges_batch(all_edges)
                        all_edges = []  # Clear for next batch
                        gc.collect()  # Force garbage collection
                        
                except Exception as e:
                    print(f"L Batch {batch_id} failed: {str(e)}")
        
        # Write remaining edges
        if all_edges:
            self._write_edges_batch(all_edges)
        
        # Calculate final statistics
        elapsed_time = time.time() - self.start_time
        edge_rate = self.total_edges_generated / elapsed_time if elapsed_time > 0 else 0
        
        print(f"\n EDGE GENERATION COMPLETED")
        print("=" * 50)
        print(f"Total edges generated: {self.total_edges_generated:,}")
        print(f"Files created: {self.file_count}")
        print(f"Generation time: {elapsed_time:.2f}s ({elapsed_time/60:.1f}m)")
        print(f"Edge generation rate: {edge_rate:,.0f} edges/second")
        print(f"Average edges per file: {self.total_edges_generated//max(1,self.file_count):,}")
    
    def _write_edges_batch(self, edges: List[Dict]):
        """Write a batch of edges to CSV file"""
        if not edges:
            return
        
        output_file = self._get_output_filename()
        self._write_edges_to_csv(edges, output_file)
        
        self.total_edges_generated += len(edges)
        print(f"  =� Wrote {len(edges):,} edges to {os.path.basename(output_file)}")

def main():
    """
    Main execution function for testing
    """
    print("= PERSON-ADDRESS EDGE GENERATOR")
    print("=" * 50)
    
    # Configuration
    CSV_OUTPUT_DIR = "src/neptune-performance-test/csv_output"
    FILE_SIZE_LIMIT = 1000000  # 1M edges per file
    MAX_WORKERS = 14
    MAX_MEMORY_GB = 48
    BATCH_SIZE = 25000  # Person records per batch
    
    # Initialize generator
    generator = PersonAddressEdgeGenerator(
        csv_output_dir=CSV_OUTPUT_DIR,
        file_size_limit=FILE_SIZE_LIMIT,
        max_workers=MAX_WORKERS,
        max_memory_gb=MAX_MEMORY_GB
    )
    
    # Generate person-address edges
    generator.generate_person_address_edges(batch_size=BATCH_SIZE)
    
    print("\n<� Person-address edge generation completed!")

if __name__ == "__main__":
    main()