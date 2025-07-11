import pandas as pd
import json
import os
from tqdm import tqdm

def convert_person_organization_edges():
    try:
        # Read the mock person-organization data from JSON
        print("\nReading mock person-organization data...")
        with open('src/data/output/gds/mock_person-organization_data.json', 'r') as f:
            edge_data = json.load(f)
        
        # Initialize list to store converted edges
        edges = []
        
        print("\nConverting person-organization edges to Gremlin format...")
        for edge in tqdm(edge_data, desc="Processing edges"):
            # Create the edge with required fields
            edge_record = {
                '~id': edge['edge_id'],
                '~from': edge['node_id_from'],
                '~to': edge['node_id_to'],
                '~label': 'person_organization;primary'
            }
            
            # Add all properties from the JSON
            for key, value in edge['edge_properties'].items():
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
        output_path = 'src/data/output/neptune/neptune_person_organization_edges_gremlin.csv'
        edges_df.to_csv(output_path, index=False, quoting=1, quotechar='"', escapechar='\\')
        
        print(f"\nGenerated {len(edges)} person-organization edges")
        print(f"Saved to {output_path}")
        return True
        
    except Exception as e:
        print(f"Error converting person-organization edges: {str(e)}")
        return False

def convert_to_gremlin():
    # Only convert person-organization edges
    return convert_person_organization_edges()

if __name__ == "__main__":
    convert_to_gremlin()
