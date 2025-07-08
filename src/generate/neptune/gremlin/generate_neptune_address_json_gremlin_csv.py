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
        
        # Define all possible address columns with their types
        all_columns = {
            '~id': 'String',
            'node_id:String': 'String',
            'node_name:String': 'String',
            'address_full:String': 'String',
            'address_hash:String': 'String',
            'street_address_line1:String': 'String',
            'street_address_line2:String': 'String',
            'city:String': 'String',
            'state_province:String': 'String',
            'country:String': 'String',
            'postal_code:String': 'String',
            'zip_code5:String': 'String',
            'zip_code_plus4:String': 'String',
            'latitude:Double': 'Double',
            'longitude:Double': 'Double',
            'mailability_score:Int': 'Int',
            '~label': 'String'
        }
        
        # Initialize list to store converted nodes
        nodes = []
        
        print("\nConverting data to Gremlin format...")
        for address in tqdm(address_data, desc="Processing nodes"):
            # Get the node properties
            properties = address['node_properties']
            
            # Create the node with required fields
            node = {
                '~id': address['node_id'],
                'node_id:String': address['node_id'],  # Set node_id to the same value as ~id
                'node_name:String': properties.get('STREET_ADDRESS_LINE1', '')  # Set node_name to street_address_line1
            }
            
            # Add all properties from the JSON with appropriate type suffixes
            for key, value in properties.items():
                # Determine the appropriate type suffix based on the value type
                if isinstance(value, (int, float)):
                    # Handle numeric values
                    if key in ['LATITUDE', 'LONGITUDE']:
                        node[f'{key.lower()}:Double'] = float(value)
                    elif key == 'MAILABILITY_SCORE':
                        node[f'{key.lower()}:Int'] = int(value)
                    else:
                        # Default to String for other numeric fields
                        node[f'{key.lower()}:String'] = str(value)
                else:
                    # Handle string values
                    node[f'{key.lower()}:String'] = str(value)
            
            # Add address label
            node['~label'] = 'address'
            
            nodes.append(node)
        
        # Convert to DataFrame
        nodes_df = pd.DataFrame(nodes)
        
        # Ensure all columns exist in the DataFrame, filling missing ones with empty values
        for col_name in all_columns.keys():
            if col_name not in nodes_df.columns:
                # Fill with appropriate empty values based on type
                if all_columns[col_name] == 'Double':
                    nodes_df[col_name] = None
                elif all_columns[col_name] == 'Int':
                    nodes_df[col_name] = None
                else:
                    nodes_df[col_name] = ''
        
        # Reorder columns to match the defined order
        ordered_cols = list(all_columns.keys())
        # Ensure ~label is last
        ordered_cols.remove('~label')
        ordered_cols.append('~label')
        
        # Reorder the DataFrame columns
        nodes_df = nodes_df[ordered_cols]
        
        # Save to CSV with proper quoting
        output_path = 'src/data/output/neptune/neptune_address_nodes_gremlin.csv'
        nodes_df.to_csv(output_path, index=False, quoting=1, quotechar='"', escapechar='\\')
        
        # Print sample record
        print("\nSample Record:")
        sample = nodes[0]
        print(json.dumps(sample, indent=2))
        
        print(f"\nGenerated {len(nodes)} Gremlin-compatible nodes")
        print(f"CSV contains {len(ordered_cols)} columns: {', '.join(ordered_cols)}")
        print(f"Saved to {output_path}")
        return True
        
    except Exception as e:
        print(f"Error converting data: {str(e)}")
        return False

if __name__ == "__main__":
    convert_to_gremlin() 