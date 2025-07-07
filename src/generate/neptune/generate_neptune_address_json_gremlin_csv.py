import pandas as pd
import json
import os
from tqdm import tqdm

def convert_to_gremlin():
    try:
        # Ensure output directory exists
        os.makedirs('src/data/output/neptune', exist_ok=True)
        
        # Read the mock address data from JSON
        print("Reading mock address data...")
        with open('src/data/output/gds/mock_address_data.json', 'r') as f:
            address_data = json.load(f)
        
        # Initialize list to store converted nodes
        nodes = []
        
        print("\nConverting data to Gremlin format...")
        for address in tqdm(address_data, desc="Processing nodes"):
            # Get the node properties
            properties = address['node_properties']
            
            # Create the node with required fields
            node = {
                '~id': address['node_id']
            }
            
            # Add all properties from the JSON
            for key, value in properties.items():
                # Convert property name to lowercase for String suffix
                if key.lower() == 'address_full':
                    node['address_full:String'] = str(value)
                else:
                    node[f'{key.lower()}:String'] = str(value)
            
            # Add address label
            node['~label'] = 'address'
            
            nodes.append(node)
        
        # Convert to DataFrame
        nodes_df = pd.DataFrame(nodes)
        
        # Reorder columns to ensure ~label is last
        cols = nodes_df.columns.tolist()
        cols.remove('~label')
        cols.append('~label')
        nodes_df = nodes_df[cols]
        
        # Save to CSV with proper quoting
        output_path = 'src/data/output/neptune/neptune_address_nodes_gremlin.csv'
        nodes_df.to_csv(output_path, index=False, quoting=1, quotechar='"', escapechar='\\')
        
        # Print sample record
        print("\nSample Record:")
        sample = nodes[0]
        print(json.dumps(sample, indent=2))
        
        print(f"\nGenerated {len(nodes)} Gremlin-compatible nodes")
        print(f"Saved to {output_path}")
        return True
        
    except Exception as e:
        print(f"Error converting data: {str(e)}")
        return False

if __name__ == "__main__":
    convert_to_gremlin() 