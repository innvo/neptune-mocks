import pandas as pd
import uuid
import random
from tqdm import tqdm
import time
import os
import json
import platform
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing
from collections import defaultdict
import gc

class HighPerformanceEdgeGenerator:
    """
    High-performance edge generator with maximum optimizations for large datasets.
    Features:
    - Very large batch sizes to minimize parallelization overhead
    - Memory-efficient processing
    - Optimized data structures
    - Reduced function call overhead
    """
    
    def __init__(self, node_data_path='src/data/input/node_data.csv'):
        self.node_data_path = node_data_path
        self.node_df = None
        self.node_sets = {}
        self.person_lookup = {}
        
    def load_data(self):
        """Load and preprocess data efficiently"""
        print("Loading node data...")
        start_time = time.time()
        
        # Read only necessary columns
        self.node_df = pd.read_csv(self.node_data_path, usecols=['node_id', 'node_type'])
        
        # Create efficient lookup structures
        self.node_sets = {
            node_type: set(self.node_df[self.node_df['node_type'] == node_type]['node_id'].values)
            for node_type in self.node_df['node_type'].unique()
        }
        
        # Create person lookup dictionary
        try:
            with open('src/data/output/gds/mock_person_data.json', 'r') as f:
                person_data = json.load(f)
            self.person_lookup = {
                person['node_id']: person['node_properties']['NAME_FULL'] 
                for person in person_data
            }
        except FileNotFoundError:
            print("Warning: Person data not found, using default names")
            self.person_lookup = {}
        
        load_time = time.time() - start_time
        print(f"Data loaded in {load_time:.2f} seconds")
        
        # Print statistics
        print(f"Total nodes: {len(self.node_df)}")
        for node_type, node_set in self.node_sets.items():
            print(f"{node_type}: {len(node_set)} nodes")
    
    def generate_person_address_edges_high_performance(self):
        """Generate person-address edges with maximum performance"""
        return self._generate_edges_high_performance(
            source_type='person',
            target_type='address',
            edge_type='person_address',
            max_edges_per_person=3,
            max_people_per_target=3,
            edge_properties_func=self._get_address_properties
        )
    
    def generate_person_form_edges_high_performance(self):
        """Generate person-form edges with maximum performance"""
        return self._generate_edges_high_performance(
            source_type='person',
            target_type='form',
            edge_type='person_form',
            max_edges_per_person=3,
            max_people_per_target=10,
            edge_properties_func=self._get_form_properties
        )
    
    def generate_person_receipt_edges_high_performance(self):
        """Generate person-receipt edges with maximum performance"""
        return self._generate_edges_high_performance(
            source_type='person',
            target_type='receipt',
            edge_type='person_receipt',
            max_edges_per_person=5,
            max_people_per_target=4,
            edge_properties_func=self._get_receipt_properties
        )
    
    def _get_address_properties(self, person_id):
        """Get address edge properties"""
        address_types = ['PRIMARY', 'SECONDARY', 'TERTIARY']
        return {'ADDRESS_TYPE': random.choice(address_types)}
    
    def _get_form_properties(self, person_id):
        """Get form edge properties"""
        relationship_types = [
            'APPLICANT', 'BENEFICIARY', 'CO_APPLICANT', 'SPONSOR', 'PETITIONER',
            'REPRESENTATIVE', 'ATTORNEY', 'INTERPRETER', 'PREPARER', 'WITNESS',
            'GUARDIAN', 'POWER_OF_ATTORNEY', 'TRANSLATOR', 'NOTARY', 'CERTIFIER'
        ]
        name_full = self.person_lookup.get(person_id, "UNKNOWN")
        return {
            'RELATIONSHIP_TYPE': random.choice(relationship_types),
            'NAME_FULL': name_full
        }
    
    def _get_receipt_properties(self, person_id):
        """Get receipt edge properties"""
        role_types = [
            'PRIMARY BENEFICIARY', 'NONPRIMARY BENEFICIARY', 'APPLICANT', 'PETITIONER',
            'ATTORNEY', 'INTERPRETER', 'PREPARER', 'REPRESENTATIVE', 'SPOUSE',
            'PARENT', 'CHILD', 'SIBLING', 'GUARDIAN'
        ]
        name_full = self.person_lookup.get(person_id, "UNKNOWN")
        role_type = random.choice(role_types)
        return {
            'ROLE_TYPE': role_type,
            'ROLE_TYPE_STD': role_type,
            'NAME_FULL': name_full
        }
    
    def _generate_edges_high_performance(self, source_type, target_type, edge_type, 
                                       max_edges_per_person, max_people_per_target, 
                                       edge_properties_func):
        """High-performance edge generation algorithm with maximum optimizations"""
        print(f"\nGenerating {edge_type} edges (HIGH PERFORMANCE MODE)...")
        start_time = time.time()
        
        # Get source and target nodes
        source_nodes = list(self.node_sets[source_type])
        target_nodes = list(self.node_sets[target_type])
        
        if not source_nodes or not target_nodes:
            print(f"Warning: No {source_type} or {target_type} nodes found")
            return []
        
        # Initialize tracking structures
        target_usage = defaultdict(int)
        edges = []
        
        # HIGH PERFORMANCE: Use very large batches to minimize overhead
        num_cores = multiprocessing.cpu_count()
        
        # For very large datasets, use even larger batches
        if len(source_nodes) > 100000:
            batch_size = max(1, len(source_nodes) // (num_cores * 1))  # One batch per core
        else:
            batch_size = max(1, len(source_nodes) // (num_cores * 2))  # Two batches per core
        
        print(f"Using {num_cores} CPU cores with batch size {batch_size:,}")
        
        # Split source nodes into batches
        source_batches = [
            source_nodes[i:i + batch_size] 
            for i in range(0, len(source_nodes), batch_size)
        ]
        
        print(f"Processing {len(source_batches)} batches...")
        
        # Process batches in parallel with optimized worker count
        max_workers = min(num_cores, len(source_batches))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all batch jobs
            future_to_batch = {
                executor.submit(
                    self._process_batch_high_performance,
                    batch, target_nodes, target_usage, max_edges_per_person,
                    max_people_per_target, edge_type, edge_properties_func
                ): batch for batch in source_batches
            }
            
            # Collect results with progress bar
            for future in tqdm(as_completed(future_to_batch), 
                             total=len(future_to_batch), 
                             desc="Processing batches"):
                batch_edges = future.result()
                edges.extend(batch_edges)
                
                # Force garbage collection periodically to free memory
                if len(edges) % 10000 == 0:
                    gc.collect()
        
        # Save edges
        output_path = f'src/data/output/gds/mock_{edge_type}_data.json'
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(edges, f, indent=2)
        
        processing_time = time.time() - start_time
        print(f"Generated {len(edges):,} edges in {processing_time:.2f} seconds")
        print(f"Edges per second: {len(edges) / processing_time:,.2f}")
        
        return edges
    
    def _process_batch_high_performance(self, source_batch, target_nodes, target_usage,
                                      max_edges_per_person, max_people_per_target,
                                      edge_type, edge_properties_func):
        """Process a batch of source nodes with maximum performance optimizations"""
        batch_edges = []
        
        # Pre-compute available targets for this batch to avoid repeated filtering
        available_targets = [target_id for target_id in target_nodes if target_usage[target_id] < max_people_per_target]
        
        for source_id in source_batch:
            # Use pre-computed available targets
            if len(available_targets) == 0:
                break
            
            # Determine number of edges for this source
            num_edges = random.randint(1, min(max_edges_per_person, len(available_targets)))
            selected_targets = random.sample(available_targets, num_edges)
            
            # Generate edges
            for target_id in selected_targets:
                properties = edge_properties_func(source_id)
                
                batch_edges.append({
                    'edge_id': str(uuid.uuid4()),
                    'node_id_from': source_id,
                    'node_id_to': target_id,
                    'edge_type': edge_type,
                    'edge_properties': properties
                })
                
                target_usage[target_id] += 1
                
                # Remove target from available list if it reaches max usage
                if target_usage[target_id] >= max_people_per_target:
                    available_targets.remove(target_id)
        
        return batch_edges
    
    def validate_edges(self, edges, source_type, target_type):
        """Validate generated edges efficiently"""
        print(f"\nValidating {len(edges)} edges...")
        
        source_nodes = self.node_sets[source_type]
        target_nodes = self.node_sets[target_type]
        
        valid_edges = 0
        invalid_edges = 0
        
        for edge in edges:
            if (edge['node_id_from'] in source_nodes and 
                edge['node_id_to'] in target_nodes):
                valid_edges += 1
            else:
                invalid_edges += 1
        
        print(f"Valid edges: {valid_edges:,}")
        print(f"Invalid edges: {invalid_edges:,}")
        print(f"Validation accuracy: {valid_edges / len(edges) * 100:.2f}%")
        
        return valid_edges, invalid_edges

def main():
    """Main function to run high-performance edge generation"""
    generator = HighPerformanceEdgeGenerator()
    generator.load_data()
    
    # Generate all edge types with maximum performance
    edge_types = [
        ('person', 'address', 'person_address'),
        ('person', 'form', 'person_form'),
        ('person', 'receipt', 'person_receipt')
    ]
    
    total_start_time = time.time()
    
    for source_type, target_type, edge_type in edge_types:
        print(f"\n{'='*60}")
        print(f"Generating {edge_type} edges (HIGH PERFORMANCE)")
        print(f"{'='*60}")
        
        if edge_type == 'person_address':
            edges = generator.generate_person_address_edges_high_performance()
        elif edge_type == 'person_form':
            edges = generator.generate_person_form_edges_high_performance()
        elif edge_type == 'person_receipt':
            edges = generator.generate_person_receipt_edges_high_performance()
        
        if edges:
            generator.validate_edges(edges, source_type, target_type)
    
    total_time = time.time() - total_start_time
    print(f"\n{'='*60}")
    print(f"TOTAL EXECUTION TIME: {total_time:.2f} seconds ({total_time/60:.2f} minutes)")
    print(f"{'='*60}")

if __name__ == "__main__":
    main() 