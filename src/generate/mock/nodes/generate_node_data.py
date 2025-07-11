import pandas as pd
import uuid
import random
import json
import os

# Configuration
NUM_NODE_RECORDS = 10000 # Number of node records to generate
NUM_NODE_RECORDS_PER_BATCH = 1000
#NODE_TYPES = ['person', 'name', 'address', 'anumber', 'receipt', 'form', 'email', 'phone']

NODE_TYPES = ['person', 'address','anumber','datainstance','email','form','organization','receipt']

# Ensure the data/input directory exists
os.makedirs('src/data/input', exist_ok=True)

def generate_node_data():
    # Calculate target counts for each node type to ensure proper distribution
    # We want to ensure there are enough datainstance nodes for all persons
    target_person_count = int(NUM_NODE_RECORDS * 0.15)  # 15% for persons
    target_datainstance_count = max(target_person_count, int(NUM_NODE_RECORDS * 0.12))  # At least as many as persons, or 12%
    
    # Calculate remaining nodes for other types
    remaining_nodes = NUM_NODE_RECORDS - target_person_count - target_datainstance_count
    other_types = ['address', 'anumber', 'email', 'form', 'organization', 'receipt']
    
    # Distribute remaining nodes among other types
    nodes_per_other_type = remaining_nodes // len(other_types)
    extra_nodes = remaining_nodes % len(other_types)
    
    # Generate node data with controlled distribution
    node_data = {
        'node_id': [],
        'node_type': [],
        'batch': []
    }
    
    # Add person nodes
    for i in range(target_person_count):
        node_data['node_id'].append(str(uuid.uuid4()))
        node_data['node_type'].append('person')
        node_data['batch'].append(i // NUM_NODE_RECORDS_PER_BATCH + 1)
    
    # Add datainstance nodes
    for i in range(target_datainstance_count):
        node_data['node_id'].append(str(uuid.uuid4()))
        node_data['node_type'].append('datainstance')
        node_data['batch'].append((target_person_count + i) // NUM_NODE_RECORDS_PER_BATCH + 1)
    
    # Add other type nodes
    current_index = target_person_count + target_datainstance_count
    for i, node_type in enumerate(other_types):
        count = nodes_per_other_type + (1 if i < extra_nodes else 0)
        for j in range(count):
            node_data['node_id'].append(str(uuid.uuid4()))
            node_data['node_type'].append(node_type)
            node_data['batch'].append((current_index + j) // NUM_NODE_RECORDS_PER_BATCH + 1)
        current_index += count
    
    # Create DataFrame
    node_df = pd.DataFrame(node_data)
    
    # Save to CSV in data/input directory
    output_path = 'src/data/input/node_data.csv'
    node_df.to_csv(output_path, index=False)
    print(f"\nNode data saved to '{output_path}'")
    
    return node_df

def update_person_records():
    try:
        # Read node_data.csv from data/input directory
        node_df = pd.read_csv('src/data/input/node_data.csv')
        
        # Filter for person records
        person_records = node_df[node_df['node_type'] == 'person']
        
        # Save updated DataFrame to data/input directory
        output_path = 'src/data/input/node_data.csv'
        node_df.to_csv(output_path, index=False)
        print(f"\nUpdated node data saved to '{output_path}'")
        
        return node_df
    except Exception as e:
        print(f"Error updating records: {str(e)}")
        return None

if __name__ == "__main__":
    # Generate node data
    node_df = generate_node_data()
    
    # Update person records
    updated_df = update_person_records()
    
    if updated_df is not None:
        # Display the updated DataFrame
        print("\nUpdated Node Data:")
        print(updated_df[updated_df['node_type'] == 'person'])

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

   