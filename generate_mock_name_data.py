import pandas as pd
from faker import Faker
import json
from tqdm import tqdm

def generate_mock_name_data():
    try:
        # Initialize Faker
        fake = Faker()
        
        # Read node_data.csv to get name nodes
        print("Reading node data...")
        node_df = pd.read_csv('node_data.csv', usecols=['node_id', 'node_type'])
        
        # Filter for name nodes
        name_nodes = node_df[node_df['node_type'] == 'name']
        if name_nodes.empty:
            print("Warning: No name nodes found in node_data.csv")
            return None
        
        # Initialize data list
        name_data = []
        
        # Generate mock data for each name node
        print("\nGenerating mock name data...")
        for _, node in tqdm(name_nodes.iterrows(), total=len(name_nodes), desc="Processing name nodes"):
            node_id = node['node_id']
            
            # Generate a fake name
            full_name = fake.name().upper()  # Convert to uppercase as per requirements
            
            # Create node properties JSON
            node_properties = {
                "NAME_FULL": full_name
            }
            
            # Add to data list
            name_data.append({
                'node_id': node_id,
                'node_type': 'name',
                'node_name': full_name,
                'node_properties': json.dumps(node_properties)
            })
        
        # Create DataFrame
        name_df = pd.DataFrame(name_data)
        
        # Save to CSV
        name_df.to_csv('mock_name_data.csv', index=False)
        
        # Print statistics
        print("\nName Data Generation Statistics:")
        print(f"Total number of name nodes processed: {len(name_data)}")
        print("\nSample of Generated Name Data:")
        print(name_df.head())
        
        return name_df
        
    except Exception as e:
        print(f"Error generating mock name data: {str(e)}")
        return None

if __name__ == "__main__":
    name_df = generate_mock_name_data() 