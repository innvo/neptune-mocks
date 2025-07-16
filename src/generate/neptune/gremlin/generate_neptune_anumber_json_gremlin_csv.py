import pandas as pd
import json
import os
from tqdm import tqdm

def convert_to_gremlin():
    try:
        # Ensure output directory exists
        os.makedirs('src/data/output/neptune', exist_ok=True)
        
        # Read the mock anumber data from JSON
        print("Reading mock anumber data...")
        with open('src/data/output/gds/mock_anumber_data.json', 'r') as f:
            anumber_data = json.load(f)
        
        # Define all possible anumber columns with their types
        all_columns = {
            '~id': 'String',
            'node_id:String': 'String',  # Add type suffix for node_id
            'node_name:String': 'String',  # Add type suffix for node_name
            'anumber:String': 'String',
            'anumber_type:String': 'String',
            'issue_date:String': 'String',
            'status:String': 'String',
            '~label': 'String'
        }
        
        # Initialize list to store converted nodes
        nodes = []
        
        print("\nConverting data to Gremlin format...")
        for anumber in tqdm(anumber_data, desc="Processing nodes"):
            # Get the node properties
            properties = anumber['node_properties']
            
            # Create the node with required fields
            node = {
                '~id': anumber['node_id'],
                'node_id:String': anumber['node_id'],  # Set node_id to the same value as ~id
                'node_name:String': anumber['node_name']  # Use the node_name from the JSON
            }
            
            # Add all properties from the JSON with appropriate type suffixes
            for key, value in properties.items():
                # Handle string values
                node[f'{key.lower()}:String'] = str(value) if value is not None else ''
            
            # Add anumber and primary labels
            node['~label'] = 'anumber;secondary'
            
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
        
        # Ensure node_id and node_name come right after ~id
        ordered_cols.remove('~id')
        ordered_cols.remove('node_id:String')
        ordered_cols.remove('node_name:String')
        ordered_cols = ['~id', 'node_id:String', 'node_name:String'] + [col for col in ordered_cols if col not in ['~id', 'node_id:String', 'node_name:String', '~label']] + ['~label']
        
        # Reorder the DataFrame columns
        nodes_df = nodes_df[ordered_cols]
        
        # Save to CSV with proper quoting
        output_path = 'src/data/output/neptune/neptune_anumber_nodes_gremlin.csv'
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
