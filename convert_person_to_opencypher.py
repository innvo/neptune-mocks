import pandas as pd
import json
import uuid
from datetime import datetime

def convert_to_opencypher():
    try:
        print("Reading mock_person_data.csv...")
        person_df = pd.read_csv('mock_person_data.csv')
        
        # Initialize list for nodes
        nodes = []
        
        print("\nConverting data to OpenCypher format...")
        for _, row in person_df.iterrows():
            # Create base node entry
            node_id = row['node_id']
            node = {
                '~id': node_id,
                '~label': 'person',
                'name:String': row['node_name']
            }
            
            # Parse and add properties
            try:
                props = json.loads(row['node_properties'])
                for key, value in props.items():
                    if key == 'BIRTH_DATE':
                        # Convert BIRTH_DATE to DateTime format
                        try:
                            # Parse the date string to ensure it's valid
                            dt = datetime.strptime(value, '%Y-%m-%d')
                            # Format for Neptune DateTime in yyyy-MM-dd format
                            node['BIRTH_DATE:DateTime'] = dt.strftime('%Y-%m-%d')
                        except ValueError as e:
                            print(f"Warning: Invalid date format for BIRTH_DATE in node {node_id}: {value}")
                            continue
                    elif isinstance(value, list):
                        # Convert lists to string representation
                        value = '[' + ','.join(f'"{v}"' if isinstance(v, str) else str(v) for v in value) + ']'
                        node[f'{key}:String'] = value
                    else:
                        # All other properties as String
                        node[f'{key}:String'] = str(value)
            except json.JSONDecodeError as e:
                print(f"Warning: Invalid JSON in properties for node {node_id}: {str(e)}")
                continue
            
            nodes.append(node)
        
        # Create DataFrame
        nodes_df = pd.DataFrame(nodes)
        
        # Save to CSV file
        print("\nSaving OpenCypher CSV file...")
        nodes_df.to_csv('neptune_person_nodes.csv', index=False)
        print("Saved nodes to neptune_person_nodes.csv")
        
        # Print sample data
        print("\nSample Node Data:")
        print(nodes_df.head())
        
        # Print statistics
        print("\nConversion Statistics:")
        print(f"Total nodes converted: {len(nodes)}")
        print("\nColumns in output file:")
        for col in nodes_df.columns:
            print(f"- {col}")
        
        return True
        
    except Exception as e:
        print(f"Error converting data: {str(e)}")
        return False

if __name__ == "__main__":
    convert_to_opencypher() 