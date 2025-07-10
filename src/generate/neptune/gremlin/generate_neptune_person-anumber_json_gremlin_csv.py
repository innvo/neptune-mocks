import pandas as pd
import json
import os
from tqdm import tqdm
from pathlib import Path

def convert_person_anumber_edges():
    """Convert person-anumber edge data to Neptune Gremlin CSV format."""
    try:
        # Ensure output directory exists
        output_dir = Path("src/data/output/neptune")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Read the mock person-anumber data from JSON
        print("Reading mock person-anumber data...")
        input_file = Path("src/data/output/gds/mock_person-anumber_data.json")
        
        if not input_file.exists():
            print(f"Input file {input_file} not found!")
            return False
            
        with open(input_file, 'r') as f:
            edge_data = json.load(f)
        
        # Initialize list to store converted edges
        edges = []
        
        print("\nConverting person-anumber edges to Gremlin format...")
        for edge in tqdm(edge_data, desc="Processing edges"):
            # Create the edge with required fields
            edge_record = {
                '~id': edge['edge_id'],
                '~from': edge['node_id_from'],
                '~to': edge['node_id_to'],
                '~label': 'person_anumber;secondary'
            }
            
            # Add all properties from the JSON
            for key, value in edge['edge_properties'].items():
                if isinstance(value, list):
                    # Convert list to string representation with semicolons
                    value = ';'.join(str(v) for v in value)
                
                # Convert property name to lowercase and add type suffix
                if key.lower() == 'relationship_type':
                    edge_record['relationship_type:String'] = str(value)
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
        output_path = output_dir / "neptune_person_anumber_edges_gremlin.csv"
        edges_df.to_csv(output_path, index=False, quoting=1, quotechar='"', escapechar='\\')
        
        # Print sample record
        print("\nSample Edge Record:")
        sample = edges[0]
        print(json.dumps(sample, indent=2))
        
        print(f"\nGenerated {len(edges)} person-anumber edges")
        print(f"Saved to {output_path}")
        return True
        
    except Exception as e:
        print(f"Error converting person-anumber edges: {str(e)}")
        return False

def convert_to_gremlin():
    """Convert person-anumber edge data to Neptune Gremlin CSV format."""
    # Convert person-anumber edges only (anumber nodes are handled by generate_neptune_anumber_json_gremlin_csv.py)
    edges_success = convert_person_anumber_edges()
    
    if edges_success:
        print("\n✅ Successfully converted person-anumber data to Gremlin format")
    else:
        print("\n❌ Failed to convert person-anumber data to Gremlin format")
    
    return edges_success

if __name__ == "__main__":
    convert_to_gremlin()
