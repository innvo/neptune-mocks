import pandas as pd
import uuid
import random
import json
import os

# Configuration
NUM_NODE_RECORDS =20  # Number of node records to generate

#NODE_TYPES = ['person', 'name', 'address', 'anumber', 'receipt', 'form', 'email', 'phone']

NODE_TYPES = ['person', 'address']

# Ensure the data/input directory exists
os.makedirs('src/data/input', exist_ok=True)

def generate_node_data():
    # Generate node data
    node_data = {
        'node_id': [str(uuid.uuid4()) for _ in range(NUM_NODE_RECORDS)],
        'node_type': [random.choice(NODE_TYPES) for _ in range(NUM_NODE_RECORDS)]
    }
    
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
        
        # Read mock_person_data.csv from data/input directory
        person_df = pd.read_csv('src/data/input/mock_person_data.csv')
        
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

   