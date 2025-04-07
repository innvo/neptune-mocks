import pandas as pd
import uuid
import random

# Configuration
NUM_NODE_RECORDS = 100  # Number of node records to generate
NODE_TYPES = ['person', 'name', 'address', 'anumber', 'receipt', 'form', 'email']

def generate_node_data():
    # Generate node data
    node_data = {
        'node_id': [str(uuid.uuid4()) for _ in range(NUM_NODE_RECORDS)],
        'node_type': [random.choice(NODE_TYPES) for _ in range(NUM_NODE_RECORDS)]
    }
    
    # Create DataFrame
    node_df = pd.DataFrame(node_data)
    
    # Save to CSV
    node_df.to_csv('node_data.csv', index=False)
    print("\nNode data saved to 'node_data.csv'")
    
    return node_df

if __name__ == "__main__":
    # Generate node data
    node_df = generate_node_data()
    
    # Display the node DataFrame
    print("\nGenerated Node Data:")
    print(node_df) 