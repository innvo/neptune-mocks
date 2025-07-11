import pandas as pd
import json
import os
from tqdm import tqdm

def convert_to_gremlin():
    """
    Convert mock phone data from JSON to Neptune Gremlin CSV format.
    
    Reads from: src/data/output/gds/mock_phone_data.json
    Outputs to: src/data/output/neptune/neptune_phone_nodes_gremlin.csv
    """
    try:
        # Ensure output directory exists
        os.makedirs('src/data/output/neptune', exist_ok=True)
        
        # Read the mock phone data from JSON
        print("Reading mock phone data...")
        with open('src/data/output/gds/mock_phone_data.json', 'r') as f:
            phone_data = json.load(f)
        
        # Initialize list to store converted nodes
        nodes = []
        
        print("\nConverting phone data to Gremlin format...")
        for phone in tqdm(phone_data, desc="Processing phone nodes"):
            # Get the node properties
            properties = phone['node_properties']
            
            # Create the node with required fields
            node = {
                '~id': phone['node_id']
            }
            
            # Add all properties from the JSON
            for key, value in properties.items():
                if isinstance(value, list):
                    # Convert list to string representation with semicolons for each element
                    value = ';'.join(str(v) for v in value)
                
                # Convert property name to lowercase and add appropriate type suffix
                if key.lower() == 'phone_number':
                    node['phone_number:String'] = str(value)
                else:
                    # Default to String type for any other properties
                    node[f'{key.lower()}:String'] = str(value)
            
            # Add phone label
            node['~label'] = 'phone;secondary'
            
            nodes.append(node)
        
        # Convert to DataFrame
        nodes_df = pd.DataFrame(nodes)
        
        # Reorder columns to ensure ~label is last
        cols = nodes_df.columns.tolist()
        cols.remove('~label')
        cols.append('~label')
        nodes_df = nodes_df[cols]
        
        # Save to CSV with proper quoting
        output_path = 'src/data/output/neptune/neptune_phone_nodes_gremlin.csv'
        nodes_df.to_csv(output_path, index=False, quoting=1, quotechar='"', escapechar='\\')
        
        # Print sample record
        print("\nSample Record:")
        sample = nodes[0]
        print(json.dumps(sample, indent=2))
        
        # Print statistics
        print(f"\nGenerated {len(nodes)} Gremlin-compatible phone nodes")
        print(f"Saved to {output_path}")
        
        # Print phone format statistics
        phone_formats = {}
        for phone in phone_data:
            props = phone['node_properties']
            phone_number = props.get('PHONE_NUMBER', '')
            
            # Categorize phone number formats
            if '(' in phone_number and ')' in phone_number:
                phone_formats['(XXX) XXX-XXXX'] = phone_formats.get('(XXX) XXX-XXXX', 0) + 1
            elif '-' in phone_number:
                phone_formats['XXX-XXX-XXXX'] = phone_formats.get('XXX-XXX-XXXX', 0) + 1
            elif '.' in phone_number:
                phone_formats['XXX.XXX.XXXX'] = phone_formats.get('XXX.XXX.XXXX', 0) + 1
            elif '+' in phone_number:
                phone_formats['+1-XXX-XXX-XXXX'] = phone_formats.get('+1-XXX-XXX-XXXX', 0) + 1
            else:
                phone_formats['XXXXXXXXXX'] = phone_formats.get('XXXXXXXXXX', 0) + 1
        
        print("\nPhone Number Format Distribution:")
        for format_type, count in sorted(phone_formats.items(), key=lambda x: x[1], reverse=True):
            print(f"  {format_type}: {count} records")
        
        return True
        
    except Exception as e:
        print(f"Error converting phone data: {str(e)}")
        return False

if __name__ == "__main__":
    convert_to_gremlin() 