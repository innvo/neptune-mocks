import pandas as pd
import json
import os
from tqdm import tqdm

def convert_receipt_nodes():
    try:
        # Ensure output directory exists
        os.makedirs('src/data/output/neptune', exist_ok=True)
        
        # Read the mock receipt data from JSON
        print("Reading mock receipt data...")
        with open('src/data/output/gds/mock_receipt_data.json', 'r') as f:
            receipt_data = json.load(f)
        
        # Initialize list to store converted nodes
        nodes = []
        
        print("\nConverting receipt nodes to Gremlin format...")
        for receipt in tqdm(receipt_data, desc="Processing receipt nodes"):
            # Get the node properties
            properties = receipt['node_properties']
            
            # Create the node with required fields
            node = {
                '~id': receipt['node_id']
            }
            
            # Add all properties from the JSON
            for key, value in properties.items():
                # Convert property name to lowercase for String suffix
                if key.lower() == 'amount':
                    node[f'{key.lower()}:Double'] = float(value)
                else:
                    node[f'{key.lower()}:String'] = str(value)
            
            # Add receipt label
            node['~label'] = 'receipt'
            
            nodes.append(node)
        
        # Convert to DataFrame
        nodes_df = pd.DataFrame(nodes)
        
        # Reorder columns to ensure ~label is last
        cols = nodes_df.columns.tolist()
        cols.remove('~label')
        cols.append('~label')
        nodes_df = nodes_df[cols]
        
        # Save to CSV with proper quoting
        output_path = 'src/data/output/neptune/neptune_receipt_nodes_gremlin.csv'
        nodes_df.to_csv(output_path, index=False, quoting=1, quotechar='"', escapechar='\\')
        
        print(f"\nGenerated {len(nodes)} receipt nodes")
        print(f"Saved to {output_path}")
        return True
        
    except Exception as e:
        print(f"Error converting receipt nodes: {str(e)}")
        return False

def convert_person_receipt_edges():
    try:
        # Read the mock person-receipt data from JSON
        print("\nReading mock person-receipt data...")
        with open('src/data/output/gds/mock_person-receipt_data.json', 'r') as f:
            edge_data = json.load(f)
        
        # Initialize list to store converted edges
        edges = []
        
        print("\nConverting person-receipt edges to Gremlin format...")
        for edge in tqdm(edge_data, desc="Processing edges"):
            # Create the edge with required fields
            edge_record = {
                '~id': edge['edge_id'],
                '~from': edge['node_id_from'],
                '~to': edge['node_id_to'],
                '~label': edge['edge_type']
            }
            
            # Add all properties from the JSON
            for key, value in edge['edge_properties'].items():
                if key.lower() == 'amount':
                    edge_record[f'{key.lower()}:Double'] = float(value)
                else:
                    edge_record[f'{key.lower()}:String'] = str(value)
            
            edges.append(edge_record)
        
        # Convert to DataFrame
        edges_df = pd.DataFrame(edges)
        
        # Reorder columns to ensure ~label is last
        cols = edges_df.columns.tolist()
        cols.remove('~label')
        cols.append('~label')
        edges_df = edges_df[cols]
        
        # Save to CSV with proper quoting
        output_path = 'src/data/output/neptune/neptune_person_receipt_edges_gremlin.csv'
        edges_df.to_csv(output_path, index=False, quoting=1, quotechar='"', escapechar='\\')
        
        print(f"\nGenerated {len(edges)} person-receipt edges")
        print(f"Saved to {output_path}")
        return True
        
    except Exception as e:
        print(f"Error converting person-receipt edges: {str(e)}")
        return False

def convert_to_gremlin():
    # Convert receipt nodes
    nodes_success = convert_receipt_nodes()
    
    # Convert person-receipt edges
    edges_success = convert_person_receipt_edges()
    
    return nodes_success and edges_success

if __name__ == "__main__":
    convert_to_gremlin() 