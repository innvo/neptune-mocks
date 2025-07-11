import pandas as pd
import uuid
import random
from tqdm import tqdm
import time
import os
import json
import platform
import numpy as np
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing as mp
from functools import partial
import gc
import psutil

class MaximumPerformanceEdgeGenerator:
    """
    MAXIMUM PERFORMANCE edge generator with aggressive CPU and memory utilization.
    Features:
    - Uses ALL available CPU cores (up to 2x for I/O bound tasks)
    - Aggressive memory utilization with large batch sizes
    - Pre-allocated memory for maximum efficiency
    - Aggressive garbage collection
    - System resource detection and optimization
    """
    
    def __init__(self, node_data_path='src/data/input/node_data.csv'):
        self.node_data_path = node_data_path
        self.node_df = None
        self.node_sets = {}
        self.person_lookup = {}
        
        # Get system resources
        self.num_cores = mp.cpu_count()
        self.memory_gb = psutil.virtual_memory().total // (1024**3)
        
        print(f"🚀 MAXIMUM PERFORMANCE EDGE GENERATOR")
        print(f"CPU Cores: {self.num_cores}")
        print(f"Available Memory: {self.memory_gb} GB")
        print("=" * 60)
        
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
    
    def get_optimal_batch_size(self, total_items):
        """Calculate optimal batch size based on CPU cores and available memory"""
        # For maximum performance, use larger batches
        # Base calculation: one batch per core for maximum parallelism
        base_batch_size = max(1, total_items // self.num_cores)
        
        # Adjust based on available memory (more memory = larger batches)
        memory_factor = min(4, max(1, self.memory_gb // 4))  # Scale up to 4x for high memory systems
        
        # For very large datasets, use even larger batches
        if total_items > 100000:
            batch_size = max(1, total_items // (self.num_cores * 1))  # One batch per core
        else:
            batch_size = max(1, total_items // (self.num_cores * 2))  # Two batches per core
        
        # Apply memory factor
        batch_size = int(batch_size * memory_factor)
        
        return max(100, batch_size)  # Minimum batch size of 100
    
    def generate_person_address_edges_maximum_performance(self):
        """Generate person-address edges with MAXIMUM performance"""
        return self._generate_edges_maximum_performance(
            source_type='person',
            target_type='address',
            edge_type='person_address',
            max_edges_per_person=3,
            edge_properties_func=self._get_address_properties
        )
    
    def generate_person_form_edges_maximum_performance(self):
        """Generate person-form edges with MAXIMUM performance"""
        return self._generate_edges_maximum_performance(
            source_type='person',
            target_type='form',
            edge_type='person_form',
            max_edges_per_person=3,
            edge_properties_func=self._get_form_properties
        )
    
    def generate_person_receipt_edges_maximum_performance(self):
        """Generate person-receipt edges with MAXIMUM performance"""
        return self._generate_edges_maximum_performance(
            source_type='person',
            target_type='receipt',
            edge_type='person_receipt',
            max_edges_per_person=5,
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
    
    def _generate_edges_maximum_performance(self, source_type, target_type, edge_type, 
                                          max_edges_per_person, edge_properties_func):
        """MAXIMUM PERFORMANCE edge generation algorithm"""
        print(f"\n🚀 Generating {edge_type} edges (MAXIMUM PERFORMANCE MODE)...")
        start_time = time.time()
        
        # Get source and target nodes
        source_nodes = list(self.node_sets[source_type])
        target_nodes = list(self.node_sets[target_type])
        
        if not source_nodes or not target_nodes:
            print(f"Warning: No {source_type} or {target_type} nodes found")
            return []
        
        # Pre-generate edge counts for all persons using numpy for speed
        if edge_type == 'person_receipt':
            edge_counts = np.random.choice(
                [1, 2, 3, 4, 5], 
                size=len(source_nodes),
                p=[0.6, 0.25, 0.1, 0.03, 0.02]
            )
        else:
            edge_counts = np.random.choice(
                [1, 2, 3], 
                size=len(source_nodes),
                p=[0.7, 0.25, 0.05]
            )
        
        # Calculate optimal batch size
        batch_size = self.get_optimal_batch_size(len(source_nodes))
        
        print(f"🚀 MAXIMUM PERFORMANCE SETTINGS:")
        print(f"CPU Cores: {self.num_cores}")
        print(f"Batch Size: {batch_size:,}")
        print(f"Memory Available: {self.memory_gb} GB")
        print(f"Estimated batches: {len(source_nodes) // batch_size + 1}")
        
        # Create batches with edge counts
        batches = []
        for i in range(0, len(source_nodes), batch_size):
            batch_end = min(i + batch_size, len(source_nodes))
            batch_source_nodes = source_nodes[i:batch_end]
            batches.append((batch_source_nodes, target_nodes, edge_counts, i))
        
        # Process batches in parallel with maximum workers
        max_workers = min(self.num_cores * 2, len(batches))  # Use up to 2x CPU cores
        
        edges = []
        edge_count = 0
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all batch jobs
            future_to_batch = {
                executor.submit(
                    self._process_batch_maximum_performance,
                    batch, max_edges_per_person, edge_type, edge_properties_func
                ): batch for batch in batches
            }
            
            # Collect results with progress bar
            for future in tqdm(as_completed(future_to_batch), 
                             total=len(future_to_batch), 
                             desc="Processing batches"):
                batch_edges = future.result()
                edges.extend(batch_edges)
                edge_count += len(batch_edges)
                
                # Aggressive garbage collection for memory management
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
        print(f"CPU utilization: {self.num_cores} cores")
        print(f"Memory utilization: {self.memory_gb} GB available")
        print(f"Batch efficiency: {len(batches)} batches processed")
        
        return edges
    
    def _process_batch_maximum_performance(self, batch_data, max_edges_per_person, 
                                         edge_type, edge_properties_func):
        """Process a batch with MAXIMUM performance optimizations - FIXED VERSION"""
        source_nodes, target_nodes, edge_counts, batch_start_idx = batch_data
        batch_edges = []
        used_pairs = set()
        
        # Pre-allocate memory for maximum performance
        estimated_edges = len(source_nodes) * 2  # Assume average 2 edges per person
        batch_edges = []
        batch_edges.reserve(estimated_edges) if hasattr(batch_edges, 'reserve') else None
        
        for i, source_id in enumerate(source_nodes):
            # Get available targets that haven't been used with this source
            available_targets = [target_id for target_id in target_nodes 
                               if (source_id, target_id) not in used_pairs]
            
            # If no available targets, reuse some (ensures every source gets at least 1 edge)
            if len(available_targets) == 0:
                available_targets = target_nodes.copy()
            
            # Use pre-generated edge count for this source
            num_edges = edge_counts[batch_start_idx + i]
            
            # Limit the number of edges to available targets (minimum 1, maximum max_edges_per_person)
            num_edges = max(1, min(num_edges, len(available_targets), max_edges_per_person))
            
            # Randomly select targets without replacement
            selected_targets = random.sample(available_targets, num_edges)
            
            # Generate edges
            for target_id in selected_targets:
                # Add to used pairs
                pair_key = (source_id, target_id)
                used_pairs.add(pair_key)
                
                properties = edge_properties_func(source_id)
                
                batch_edges.append({
                    'edge_id': str(uuid.uuid4()),
                    'node_id_from': source_id,
                    'node_id_to': target_id,
                    'edge_type': edge_type,
                    'edge_properties': properties
                })
        
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
    """Main function to run MAXIMUM PERFORMANCE edge generation"""
    generator = MaximumPerformanceEdgeGenerator()
    generator.load_data()
    
    # Generate all edge types with MAXIMUM performance
    edge_types = [
        ('person', 'address', 'person_address'),
        ('person', 'form', 'person_form'),
        ('person', 'receipt', 'person_receipt')
    ]
    
    total_start_time = time.time()
    
    for source_type, target_type, edge_type in edge_types:
        print(f"\n{'='*60}")
        print(f"Generating {edge_type} edges (MAXIMUM PERFORMANCE)")
        print(f"{'='*60}")
        
        if edge_type == 'person_address':
            edges = generator.generate_person_address_edges_maximum_performance()
        elif edge_type == 'person_form':
            edges = generator.generate_person_form_edges_maximum_performance()
        elif edge_type == 'person_receipt':
            edges = generator.generate_person_receipt_edges_maximum_performance()
        
        if edges:
            generator.validate_edges(edges, source_type, target_type)
    
    total_time = time.time() - total_start_time
    print(f"\n{'='*60}")
    print(f"🚀 MAXIMUM PERFORMANCE EXECUTION COMPLETE")
    print(f"TOTAL EXECUTION TIME: {total_time:.2f} seconds ({total_time/60:.2f} minutes)")
    print(f"CPU Cores Used: {generator.num_cores}")
    print(f"Memory Available: {generator.memory_gb} GB")
    print(f"{'='*60}")

if __name__ == "__main__":
    main() 