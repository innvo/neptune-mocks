import pandas as pd
import json
import os
from tqdm import tqdm

def convert_building_address_edges():
    try:
        # Ensure output directory exists
        os.makedirs('src/data/output/neptune', exist_ok=True)
        
        # Read the mock building-address data from JSON
        print("Reading mock building-address data...")
        with open('src/data/output/gds/mock_building-address_data.json', 'r') as f:
            edge_data = json.load(f)
        
        # Initialize list to store converted edges
        edges = []
        
        print("\nConverting building-address edges to Gremlin format...")
        for edge in tqdm(edge_data, desc="Processing edges"):
            # Create the edge with required fields
            edge_record = {
                '~id': edge['edge_id'],
                '~from': edge['node_id_from'],
                '~to': edge['node_id_to'],
                '~label': f"{edge['edge_type']};primary"
            }
            
            # Add all properties from the JSON
            for key, value in edge['edge_properties'].items():
                # Convert property name to lowercase for String suffix
                if isinstance(value, (int, float)):
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
        output_path = 'src/data/output/neptune/neptune_building-address_edges_gremlin.csv'
        edges_df.to_csv(output_path, index=False, quoting=1, quotechar='"', escapechar='\\')
        
        print(f"\nGenerated {len(edges)} building-address edges")
        print(f"Saved to {output_path}")
        return True
        
    except Exception as e:
        print(f"Error converting building-address edges: {str(e)}")
        return False

def convert_to_gremlin():
    # Convert building-address edges
    edges_success = convert_building_address_edges()
    
    return edges_success

if __name__ == "__main__":
    convert_to_gremlin()
