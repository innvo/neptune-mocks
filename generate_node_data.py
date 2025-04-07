import pandas as pd
import uuid
import random
import json

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

def update_person_records():
    try:
        # Read node_data.csv
        node_df = pd.read_csv('node_data.csv')
        
        # Read mock_person_data.csv
        person_df = pd.read_csv('mock_person_data.csv')
        
        # Filter for person records
        person_records = node_df[node_df['node_type'] == 'person']
        
        # Update person records with NAME_FULL from JSON
        for index, row in person_records.iterrows():
            if index < len(person_df):
                # Get the node_properties JSON string
                node_properties = person_df.iloc[index]['node_properties']
                # Parse the JSON string
                props = json.loads(node_properties.replace("'", '"'))
                # Update node_name with NAME_FULL
                node_df.at[index, 'node_name'] = props['NAME_FULL']
        
        # Save updated DataFrame
        node_df.to_csv('node_data.csv', index=False)
        print("\nUpdated node data saved to 'node_data.csv'")
        
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