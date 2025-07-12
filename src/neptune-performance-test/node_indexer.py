#!/usr/bin/env python3
"""
Node ID Indexer for Fast Edge Creation
Creates indexes of node IDs for fast retrieval during edge generation
"""

import csv
import os
import json
import sqlite3
import random
import pickle
from collections import defaultdict
from typing import Dict, List, Set
import time

class NodeIndexer:
    def __init__(self, csv_output_dir="csv_output"):
        """
        Initialize the Node Indexer
        
        Args:
            csv_output_dir (str): Directory containing CSV files
        """
        self.csv_output_dir = csv_output_dir
        self.indexes = {}  # In-memory indexes
        self.db_path = os.path.join(csv_output_dir, "node_index.db")
        
    def create_memory_indexes(self):
        """
        Create in-memory indexes for all node types
        Fast but memory-intensive approach
        """
        print("🔍 Creating in-memory node indexes...")
        start_time = time.time()
        
        node_types = ['person', 'address', 'building', 'form', 'name', 'email', 'phone']
        
        for node_type in node_types:
            print(f"  Indexing {node_type} nodes...")
            self.indexes[node_type] = []
            
            # Find all CSV files for this node type
            pattern = f"{node_type}-*.csv"
            csv_files = []
            
            for file in os.listdir(self.csv_output_dir):
                if file.startswith(f"{node_type}-") and file.endswith(".csv"):
                    csv_files.append(os.path.join(self.csv_output_dir, file))
            
            # Read IDs from each file
            for csv_file in sorted(csv_files):
                with open(csv_file, 'r') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        self.indexes[node_type].append(row['~id'])
            
            print(f"    Indexed {len(self.indexes[node_type]):,} {node_type} IDs")
        
        elapsed = time.time() - start_time
        total_ids = sum(len(ids) for ids in self.indexes.values())
        print(f"  ✓ Indexed {total_ids:,} total IDs in {elapsed:.2f}s")
        
        return self.indexes
    
    def save_indexes_to_json(self, output_file="node_indexes.json"):
        """
        Save indexes to JSON file for persistence
        """
        output_path = os.path.join(self.csv_output_dir, output_file)
        print(f"💾 Saving indexes to {output_file}...")
        
        with open(output_path, 'w') as f:
            json.dump(self.indexes, f)
        
        file_size = os.path.getsize(output_path) / (1024 * 1024)
        print(f"  ✓ Saved to {output_file} ({file_size:.1f}MB)")
    
    def load_indexes_from_json(self, input_file="node_indexes.json"):
        """
        Load indexes from JSON file
        """
        input_path = os.path.join(self.csv_output_dir, input_file)
        
        if not os.path.exists(input_path):
            print(f"❌ Index file {input_file} not found")
            return False
        
        print(f"📖 Loading indexes from {input_file}...")
        
        with open(input_path, 'r') as f:
            self.indexes = json.load(f)
        
        total_ids = sum(len(ids) for ids in self.indexes.values())
        print(f"  ✓ Loaded {total_ids:,} total IDs")
        
        return True
    
    def save_indexes_to_pickle(self, output_file="node_indexes.pkl"):
        """
        Save indexes to pickle file (faster than JSON)
        """
        output_path = os.path.join(self.csv_output_dir, output_file)
        print(f"💾 Saving indexes to {output_file} (pickle)...")
        
        with open(output_path, 'wb') as f:
            pickle.dump(self.indexes, f)
        
        file_size = os.path.getsize(output_path) / (1024 * 1024)
        print(f"  ✓ Saved to {output_file} ({file_size:.1f}MB)")
    
    def load_indexes_from_pickle(self, input_file="node_indexes.pkl"):
        """
        Load indexes from pickle file (faster than JSON)
        """
        input_path = os.path.join(self.csv_output_dir, input_file)
        
        if not os.path.exists(input_path):
            print(f"❌ Index file {input_file} not found")
            return False
        
        print(f"📖 Loading indexes from {input_file} (pickle)...")
        start_time = time.time()
        
        with open(input_path, 'rb') as f:
            self.indexes = pickle.load(f)
        
        elapsed = time.time() - start_time
        total_ids = sum(len(ids) for ids in self.indexes.values())
        print(f"  ✓ Loaded {total_ids:,} total IDs in {elapsed:.3f}s")
        
        return True
    
    def create_sqlite_index(self):
        """
        Create SQLite database index for very large datasets
        Memory-efficient but slower than in-memory
        """
        print("🗄️  Creating SQLite node index...")
        start_time = time.time()
        
        # Remove existing database
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        
        # Create database and table
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE node_ids (
                node_type TEXT,
                node_id TEXT,
                row_index INTEGER,
                PRIMARY KEY (node_type, row_index)
            )
        ''')
        
        cursor.execute('CREATE INDEX idx_node_type ON node_ids(node_type)')
        cursor.execute('CREATE INDEX idx_node_id ON node_ids(node_id)')
        
        node_types = ['person', 'address', 'building', 'form', 'name', 'email', 'phone']
        total_inserted = 0
        
        for node_type in node_types:
            print(f"  Indexing {node_type} nodes...")
            
            # Find all CSV files for this node type
            csv_files = []
            for file in os.listdir(self.csv_output_dir):
                if file.startswith(f"{node_type}-") and file.endswith(".csv"):
                    csv_files.append(os.path.join(self.csv_output_dir, file))
            
            row_index = 0
            batch_data = []
            
            # Read IDs from each file
            for csv_file in sorted(csv_files):
                with open(csv_file, 'r') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        batch_data.append((node_type, row['~id'], row_index))
                        row_index += 1
                        
                        # Insert in batches for performance
                        if len(batch_data) >= 10000:
                            cursor.executemany(
                                'INSERT INTO node_ids (node_type, node_id, row_index) VALUES (?, ?, ?)',
                                batch_data
                            )
                            total_inserted += len(batch_data)
                            batch_data = []
            
            # Insert remaining data
            if batch_data:
                cursor.executemany(
                    'INSERT INTO node_ids (node_type, node_id, row_index) VALUES (?, ?, ?)',
                    batch_data
                )
                total_inserted += len(batch_data)
            
            print(f"    Indexed {row_index:,} {node_type} IDs")
        
        conn.commit()
        conn.close()
        
        elapsed = time.time() - start_time
        db_size = os.path.getsize(self.db_path) / (1024 * 1024)
        print(f"  ✓ Indexed {total_inserted:,} total IDs in {elapsed:.2f}s")
        print(f"  📁 Database size: {db_size:.1f}MB")
    
    def get_random_ids(self, node_type: str, count: int) -> List[str]:
        """
        Get random node IDs for edge creation (in-memory approach)
        
        Args:
            node_type (str): Type of node
            count (int): Number of random IDs to return
            
        Returns:
            List[str]: List of random node IDs
        """
        if node_type not in self.indexes:
            return []
        
        available_ids = self.indexes[node_type]
        if not available_ids:
            return []
        
        # Return random sample
        sample_size = min(count, len(available_ids))
        return random.sample(available_ids, sample_size)
    
    def get_random_ids_sqlite(self, node_type: str, count: int) -> List[str]:
        """
        Get random node IDs using SQLite (for large datasets)
        
        Args:
            node_type (str): Type of node
            count (int): Number of random IDs to return
            
        Returns:
            List[str]: List of random node IDs
        """
        if not os.path.exists(self.db_path):
            print("❌ SQLite index not found. Run create_sqlite_index() first.")
            return []
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get random IDs using SQL
        cursor.execute('''
            SELECT node_id FROM node_ids 
            WHERE node_type = ? 
            ORDER BY RANDOM() 
            LIMIT ?
        ''', (node_type, count))
        
        results = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return results
    
    def get_node_count(self, node_type: str) -> int:
        """
        Get total count of nodes for a type
        """
        if node_type in self.indexes:
            return len(self.indexes[node_type])
        
        # Fallback to SQLite if in-memory not available
        if os.path.exists(self.db_path):
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM node_ids WHERE node_type = ?', (node_type,))
            count = cursor.fetchone()[0]
            conn.close()
            return count
        
        return 0
    
    def benchmark_retrieval(self, test_count=10000):
        """
        Benchmark different retrieval methods
        """
        print(f"\n🔬 BENCHMARKING NODE ID RETRIEVAL ({test_count:,} random retrievals)")
        print("=" * 60)
        
        # Test in-memory retrieval
        if self.indexes:
            start_time = time.time()
            for _ in range(test_count):
                random_type = random.choice(list(self.indexes.keys()))
                self.get_random_ids(random_type, 1)
            elapsed = time.time() - start_time
            rate = test_count / elapsed
            print(f"In-Memory:     {elapsed:.3f}s ({rate:,.0f} ops/sec)")
        
        # Test SQLite retrieval
        if os.path.exists(self.db_path):
            start_time = time.time()
            for _ in range(test_count):
                random_type = random.choice(['person', 'address', 'building', 'form', 'name', 'email', 'phone'])
                self.get_random_ids_sqlite(random_type, 1)
            elapsed = time.time() - start_time
            rate = test_count / elapsed
            print(f"SQLite:        {elapsed:.3f}s ({rate:,.0f} ops/sec)")
        
        print("=" * 60)
    
    def print_summary(self):
        """
        Print index summary
        """
        print("\n📊 NODE INDEX SUMMARY")
        print("=" * 40)
        
        if self.indexes:
            for node_type, ids in self.indexes.items():
                print(f"{node_type.capitalize():>12}: {len(ids):>10,} IDs")
            
            total_ids = sum(len(ids) for ids in self.indexes.values())
            print("-" * 40)
            print(f"{'Total':>12}: {total_ids:>10,} IDs")
        
        if os.path.exists(self.db_path):
            db_size = os.path.getsize(self.db_path) / (1024 * 1024)
            print(f"SQLite DB size: {db_size:.1f}MB")
        
        print("=" * 40)

def main():
    """
    Example usage of the Node Indexer
    """
    print("🔍 NODE ID INDEXER FOR FAST EDGE CREATION")
    print("=" * 50)
    
    # Initialize indexer
    indexer = NodeIndexer()
    
    # Create indexes (choose your approach)
    print("\n1️⃣  Creating in-memory indexes...")
    indexer.create_memory_indexes()
    
    # Save for persistence
    print("\n2️⃣  Saving indexes...")
    indexer.save_indexes_to_pickle()  # Faster than JSON
    indexer.save_indexes_to_json()    # Human-readable
    
    # Create SQLite index for very large datasets
    print("\n3️⃣  Creating SQLite index...")
    indexer.create_sqlite_index()
    
    # Demonstrate usage
    print("\n4️⃣  Testing random ID retrieval...")
    
    # Get random person IDs for creating person-address edges
    person_ids = indexer.get_random_ids('person', 5)
    print(f"Random person IDs: {person_ids[:3]}...")
    
    # Get random address IDs
    address_ids = indexer.get_random_ids('address', 5)
    print(f"Random address IDs: {address_ids[:3]}...")
    
    # Performance benchmark
    indexer.benchmark_retrieval(1000)
    
    # Summary
    indexer.print_summary()
    
    print("\n✅ Index creation completed!")
    print("\nUsage for edge creation:")
    print("  - indexer.get_random_ids('person', 100)  # Fast in-memory")
    print("  - indexer.get_random_ids_sqlite('person', 100)  # Memory-efficient")

if __name__ == "__main__":
    main()