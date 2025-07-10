import pandas as pd
import json
import os
from tqdm import tqdm
from datetime import datetime, timedelta
import random

def convert_to_gremlin():
    try:
        # Ensure output directory exists
        os.makedirs('src/data/output/neptune', exist_ok=True)
        
        # Read the mock organization data from JSON
        print("Reading mock organization data...")
        with open('src/data/output/gds/mock_organization_data.json', 'r') as f:
            organization_data = json.load(f)
        
        # Initialize list to store converted nodes
        nodes = []
        
        print("\nConverting data to Gremlin format...")
        for organization in tqdm(organization_data, desc="Processing nodes"):
            # Get the node properties
            properties = organization['node_properties']
            
            # Create the node with required fields
            node = {
                '~id': organization['node_id']
            }
            
            # Add node_id and node_name as explicit properties
            node['node_id:String'] = organization['node_id']
            node['node_name:String'] = organization['node_name']
            
            # Add all properties from the JSON
            for key, value in properties.items():
                if isinstance(value, list):
                    if key.lower() == 'duns_number_list':
                        # Format DUNS number list with semicolons
                        node['duns_number_list:String[]'] = ';'.join(str(v) for v in value)
                        continue
                    elif key.lower() == 'organization_detail_list':
                        # Handle organization detail list - convert to JSON string
                        node['organization_detail_list:String[]'] = json.dumps(value)
                        continue
                    else:
                        # Convert other lists to string representation with semicolons
                        value = ';'.join(str(v) for v in value)
                
                # Convert property name to lowercase for String suffix
                if key.lower() == 'organization_name':
                    node['organization_name:String'] = str(value).upper()
                else:
                    node[f'{key.lower()}:String'] = str(value)
            
            # Add organization and primary labels
            node['~label'] = 'organization;primary'
            
            nodes.append(node)
        
        # Convert to DataFrame
        nodes_df = pd.DataFrame(nodes)
        
        # Reorder columns to ensure ~label is last
        cols = nodes_df.columns.tolist()
        cols.remove('~label')
        cols.append('~label')
        nodes_df = nodes_df[cols]
        
        # Save to CSV with proper quoting
        output_path = 'src/data/output/neptune/nepture_organization_nodes_gremlin.csv'
        nodes_df.to_csv(output_path, index=False, quoting=1, quotechar='"', escapechar='\\')
        
        # Print sample record
        print("\nSample Record:")
        sample = nodes[0]
        print(json.dumps(sample, indent=2))
        
        print(f"\nGenerated {len(nodes)} Gremlin-compatible organization nodes")
        print(f"Saved to {output_path}")
        return True
        
    except Exception as e:
        print(f"Error converting data: {str(e)}")
        return False

if __name__ == "__main__":
    convert_to_gremlin()
