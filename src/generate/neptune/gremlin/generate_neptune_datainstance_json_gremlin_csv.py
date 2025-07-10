import pandas as pd
import json
import os
from tqdm import tqdm

def convert_to_gremlin():
    """
    Convert mock datainstance data from JSON to Neptune Gremlin CSV format.
    
    Reads from: src/data/output/gds/mock_datainstance_data.json
    Outputs to: src/data/output/neptune/neptune_datainstance_nodes_gremlin.csv
    """
    try:
        # Ensure output directory exists
        os.makedirs('src/data/output/neptune', exist_ok=True)
        
        # Read the mock datainstance data from JSON
        print("Reading mock datainstance data...")
        with open('src/data/output/gds/mock_datainstance_data.json', 'r') as f:
            datainstance_data = json.load(f)
        
        # Initialize list to store converted nodes
        nodes = []
        
        print("\nConverting datainstance data to Gremlin format...")
        for datainstance in tqdm(datainstance_data, desc="Processing datainstance nodes"):
            # Get the node properties
            properties = datainstance['node_properties']
            
            # Create the node with required fields
            node = {
                '~id': datainstance['node_id']
            }
            
            # Add all properties from the JSON
            for key, value in properties.items():
                if isinstance(value, list):
                    # Convert list to string representation with semicolons for each element
                    value = ';'.join(str(v) for v in value)
                
                # Convert property name to lowercase and add appropriate type suffix
                if key.lower() == 'data_source':
                    node['data_source:String'] = str(value).upper()
                elif key.lower() == 'record_id':
                    node['record_id:String'] = str(value).upper()
                elif key.lower() == 'record_type':
                    node['record_type:String'] = str(value).upper()
                else:
                    # Default to String type for any other properties
                    node[f'{key.lower()}:String'] = str(value)
            
            # Add datainstance label
            node['~label'] = 'datainstance;secondary'
            
            nodes.append(node)
        
        # Convert to DataFrame
        nodes_df = pd.DataFrame(nodes)
        
        # Reorder columns to ensure ~label is last
        cols = nodes_df.columns.tolist()
        cols.remove('~label')
        cols.append('~label')
        nodes_df = nodes_df[cols]
        
        # Save to CSV with proper quoting
        output_path = 'src/data/output/neptune/neptune_datainstance_nodes_gremlin.csv'
        nodes_df.to_csv(output_path, index=False, quoting=1, quotechar='"', escapechar='\\')
        
        # Print sample record
        print("\nSample Record:")
        sample = nodes[0]
        print(json.dumps(sample, indent=2))
        
        # Print statistics
        print(f"\nGenerated {len(nodes)} Gremlin-compatible datainstance nodes")
        print(f"Saved to {output_path}")
        
        # Print data source and record type statistics
        data_sources = {}
        record_types = {}
        for datainstance in datainstance_data:
            props = datainstance['node_properties']
            data_source = props.get('DATA_SOURCE', 'UNKNOWN')
            record_type = props.get('RECORD_TYPE', 'UNKNOWN')
            
            data_sources[data_source] = data_sources.get(data_source, 0) + 1
            record_types[record_type] = record_types.get(record_type, 0) + 1
        
        print("\nData Source Distribution:")
        for source, count in sorted(data_sources.items()):
            print(f"  {source}: {count} records")
        
        print("\nRecord Type Distribution:")
        for record_type, count in sorted(record_types.items()):
            print(f"  {record_type}: {count} records")
        
        return True
        
    except Exception as e:
        print(f"Error converting datainstance data: {str(e)}")
        return False

if __name__ == "__main__":
    convert_to_gremlin()
