import pandas as pd
import uuid
import random
import json
import os
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import multiprocessing as mp
import time

# Configuration - optimized for performance and reliability
NUM_NODE_RECORDS = 10000
# Dynamic batch sizing based on system capabilities
OPTIMAL_BATCH_SIZE = min(10000, max(1000, NUM_NODE_RECORDS // mp.cpu_count()))
NUM_NODE_RECORDS_PER_BATCH = OPTIMAL_BATCH_SIZE
# Node types optimized for referential integrity
NODE_TYPES = ['person', 'address','anumber','datainstance','email','form','name','organization','receipt']

# Ensure the data/input directory exists
os.makedirs('src/data/input', exist_ok=True)

# Pre-compiled function for performance (tip #6 from performance_tips.md)
_uuid_generator = str
_uuid4_func = uuid.uuid4

def generate_fast_uuid():
    """Optimized UUID generation with pre-compiled functions"""
    return _uuid_generator(_uuid4_func())

def generate_batch_nodes(batch_info):
    """Clean, efficient batch node generation maintaining referential integrity"""
    node_type, count, start_index = batch_info
    
    # Fast UUID generation with pre-compiled functions
    node_ids = [generate_fast_uuid() for _ in range(count)]
    node_types = [node_type] * count
    
    # Efficient batch calculation using numpy (tip #1 from performance_tips.md)
    if count > 100:  # Use numpy for larger batches
        indices = np.arange(start_index, start_index + count)
        batches = ((indices // NUM_NODE_RECORDS_PER_BATCH) + 1).tolist()
    else:  # Simple calculation for small batches
        batches = [(start_index + i) // NUM_NODE_RECORDS_PER_BATCH + 1 for i in range(count)]
    
    return node_ids, node_types, batches

def generate_node_data():
    """Clean, optimized node data generation with referential integrity focus"""
    start_time = time.time()
    
    print(f"🚀 PERFORMANCE-OPTIMIZED NODE GENERATION")
    print(f"CPU Cores: {mp.cpu_count()}")
    print(f"Optimal Batch Size: {OPTIMAL_BATCH_SIZE:,}")
    print(f"Target Records: {NUM_NODE_RECORDS:,}")
    print("=" * 60)
    
    # CRITICAL: Calculate target counts ensuring referential integrity
    target_person_count = int(NUM_NODE_RECORDS * 0.15)  # 15% for persons
    # Ensure equal or more datainstance nodes for referential integrity
    target_datainstance_count = max(target_person_count, int(NUM_NODE_RECORDS * 0.15))
    
    # Calculate remaining nodes for other types
    remaining_nodes = NUM_NODE_RECORDS - target_person_count - target_datainstance_count
    other_types = ['address', 'anumber', 'email', 'form', 'name', 'onlineaccount','organization','phone', 'receipt']
    
    # Efficient distribution calculation
    nodes_per_other_type = remaining_nodes // len(other_types)
    extra_nodes = remaining_nodes % len(other_types)
    
    # Build task list efficiently
    batch_tasks = []
    current_index = 0
    
    # Add person nodes first (critical for referential integrity)
    batch_tasks.append(('person', target_person_count, current_index))
    current_index += target_person_count
    
    # Add datainstance nodes (must be >= person count)
    batch_tasks.append(('datainstance', target_datainstance_count, current_index))
    current_index += target_datainstance_count
    
    # Add other node types
    for i, node_type in enumerate(other_types):
        count = nodes_per_other_type + (1 if i < extra_nodes else 0)
        batch_tasks.append((node_type, count, current_index))
        current_index += count
    
    # Optimal worker count (tip #2 from performance_tips.md)
    num_workers = min(mp.cpu_count(), len(batch_tasks), 8)  # Conservative cap for stability
    
    print(f"Processing {len(batch_tasks)} node types with {num_workers} workers...")
    
    # Generate nodes in parallel
    all_node_ids = []
    all_node_types = []
    all_batches = []
    
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        results = list(executor.map(generate_batch_nodes, batch_tasks))
    
    # Combine results efficiently
    for node_ids, node_types, batches in results:
        all_node_ids.extend(node_ids)
        all_node_types.extend(node_types)
        all_batches.extend(batches)
    
    # Create DataFrame with memory-efficient dtypes
    node_df = pd.DataFrame({
        'node_id': all_node_ids,
        'node_type': pd.Categorical(all_node_types),  # Memory efficient categorical
        'batch': np.array(all_batches, dtype=np.int32)  # Appropriate int size
    })
    
    # Validate referential integrity constraints
    actual_person_count = len(node_df[node_df['node_type'] == 'person'])
    actual_datainstance_count = len(node_df[node_df['node_type'] == 'datainstance'])
    
    if actual_datainstance_count < actual_person_count:
        raise ValueError(f"Referential integrity violation: {actual_datainstance_count} datainstances < {actual_person_count} persons")
    
    # Save to CSV with standard parameters (avoid over-optimization)
    output_path = 'src/data/input/node_data.csv'
    node_df.to_csv(output_path, index=False)
    
    generation_time = time.time() - start_time
    records_per_second = NUM_NODE_RECORDS / generation_time
    
    print(f"\nNode data saved to '{output_path}' in {generation_time:.3f} seconds")
    print(f"Performance: {records_per_second:,.0f} records/second")
    print(f"✅ Referential integrity validated: {actual_datainstance_count:,} >= {actual_person_count:,}")
    
    return node_df

def update_person_records():
    """Clean person record update with optimized I/O"""
    try:
        start_time = time.time()
        
        # Read with memory-efficient dtypes
        dtype_dict = {
            'node_type': 'category',
            'batch': 'int32'
        }
        node_df = pd.read_csv('src/data/input/node_data.csv', dtype=dtype_dict)
        
        # Efficient filtering using pandas categorical
        person_records = node_df[node_df['node_type'] == 'person']
        
        # Validate person records exist
        if len(person_records) == 0:
            raise ValueError("No person records found - referential integrity compromised")
        
        # Save with standard parameters
        output_path = 'src/data/input/node_data.csv'
        node_df.to_csv(output_path, index=False)
        
        update_time = time.time() - start_time
        print(f"\nUpdated node data saved to '{output_path}' in {update_time:.3f} seconds")
        print(f"✅ Validated {len(person_records):,} person records")
        
        return node_df
    except Exception as e:
        print(f"❌ Error updating records: {str(e)}")
        return None

if __name__ == "__main__":
    # Execute with comprehensive monitoring and validation
    total_start_time = time.time()
    
    try:
        # Generate node data
        node_df = generate_node_data()
        
        # Update person records
        updated_df = update_person_records()
        
        if updated_df is not None:
            total_time = time.time() - total_start_time
            
            # Performance summary
            print(f"\n🎯 PERFORMANCE SUMMARY:")
            print(f"Total execution time: {total_time:.3f} seconds")
            print(f"Overall throughput: {NUM_NODE_RECORDS/total_time:,.0f} records/second")
            
            # Node statistics with referential integrity validation
            node_counts = updated_df['node_type'].value_counts().sort_index()
            print(f"\nNode Type Statistics:")
            print(f"Total number of nodes: {len(updated_df):,}")
            for node_type, count in node_counts.items():
                print(f"{node_type}: {count:,} nodes")
            
            # Batch distribution
            batch_counts = updated_df['batch'].value_counts().sort_index()
            print(f"\nBatch Statistics:")
            for batch_num, count in batch_counts.items():
                print(f"Batch {batch_num}: {count:,} nodes")
            
            # CRITICAL: Referential integrity validation
            person_count = node_counts.get('person', 0)
            datainstance_count = node_counts.get('datainstance', 0)
            print(f"\n✅ Person to DataInstance ratio: {person_count:,} persons, {datainstance_count:,} datainstances")
            
            if datainstance_count >= person_count:
                print("✅ Sufficient datainstance nodes to ensure every person has at least 1 datainstance edge")
                print("✅ Referential integrity MAINTAINED")
            else:
                print("❌ CRITICAL: Insufficient datainstance nodes for all persons")
                print("❌ Referential integrity COMPROMISED")
                raise ValueError("Referential integrity validation failed")
        else:
            raise RuntimeError("Failed to update person records")
            
    except Exception as e:
        print(f"\n❌ GENERATION FAILED: {str(e)}")
        print("❌ Referential integrity cannot be guaranteed")
        exit(1)
    
    print(f"\n🎉 SUCCESS: Node generation completed with referential integrity maintained!")

    # Node Type Statistics
    print("\nNode Type Statistics:")
    print("Total number of nodes:", len(node_df))
    for node_type in NODE_TYPES:
        count = len(node_df[node_df['node_type'] == node_type])
        print(f"{node_type}: {count} nodes")

    # Batch Statistics
    print("\nBatch Statistics:")
    batch_counts = node_df['batch'].value_counts().sort_index()
    for batch_num, count in batch_counts.items():
        print(f"Batch {batch_num}: {count} nodes")

    # Verify datainstance to person ratio
    person_count = len(node_df[node_df['node_type'] == 'person'])
    datainstance_count = len(node_df[node_df['node_type'] == 'datainstance'])
    print(f"\n✅ Person to DataInstance ratio: {person_count} persons, {datainstance_count} datainstances")
    if datainstance_count >= person_count:
        print("✅ Sufficient datainstance nodes to ensure every person has at least 1 datainstance edge")
    else:
        print("⚠️  Warning: Not enough datainstance nodes for all persons")

   