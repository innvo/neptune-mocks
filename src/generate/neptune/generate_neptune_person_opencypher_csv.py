import pandas as pd
import json
import os
from tqdm import tqdm

def convert_to_opencypher():
    try:
        # Ensure output directory exists
        os.makedirs('src/data/output', exist_ok=True)
        
        # Read the mock person data
        print("Reading mock person data...")
        df = pd.read_csv('src/data/output/mock_person_data.csv')
        
        # Initialize list to store converted nodes
        nodes = []
        
        print("\nConverting data to OpenCypher format...")
        for _, row in tqdm(df.iterrows(), total=len(df), desc="Processing nodes"):
            # Parse the node properties JSON
            properties = json.loads(row['node_properties'])
            
            # Create the node with required fields
            node = {
                ':ID': row['node_id']
            }
            
            # Add all properties from the JSON
            for key, value in properties.items():
                if isinstance(value, list):
                    # Convert list to string representation with single quotes for each element
                    if key.lower() == 'name_list':
                        # Convert all names to uppercase
                        value = [v.upper() for v in value]
                        # Format name list with single quotes for each element and double quotes for the array
                        node['name_full_list:String[]'] = '[' + ','.join(f"'{str(v)}'" for v in value) + ']'
                        continue
                    elif key.lower() == 'birth_date_list':
                        node[f'{key.lower()}:Date[]'] = '"[' + ','.join(f"'{str(v)}'" if isinstance(v, str) else str(v) for v in value) + ']"'
                        continue
                    value = '[' + ','.join(f"'{str(v)}'" if isinstance(v, str) else str(v) for v in value) + ']'
                # Convert property name to lowercase for String suffix
                if key.lower() == 'name_full':
                    node[f'{key.lower()}:String'] = f'"{str(value)}"'
                elif key.lower() == 'birth_date':
                    node[f'{key.lower()}:Date'] = f"'{str(value)}'"
                else:
                    node[f'{key.lower()}:String'] = f"'{str(value)}'"
            
            # Add person label
            node[':LABEL'] = 'person'
            
            nodes.append(node)
        
        # Convert to DataFrame
        nodes_df = pd.DataFrame(nodes)
        
        # Reorder columns to ensure :LABEL is last
        cols = nodes_df.columns.tolist()
        cols.remove(':LABEL')
        cols.append(':LABEL')
        nodes_df = nodes_df[cols]
        
        # Save to CSV
        output_path = 'src/data/output/neptune_person_nodes_opencypher.csv'
        nodes_df.to_csv(output_path, index=False)
        
        # Print sample record
        print("\nSample Record:")
        sample = nodes[0]
        print(json.dumps(sample, indent=2))
        
        print(f"\nGenerated {len(nodes)} OpenCypher-compatible nodes")
        print(f"Saved to {output_path}")
        return True
        
    except Exception as e:
        print(f"Error converting data: {str(e)}")
        return False

if __name__ == "__main__":
    convert_to_opencypher()