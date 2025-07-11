import pandas as pd
import json
import os
from tqdm import tqdm
from pathlib import Path

def convert_person_datainstance_edges():
    """Convert person-datainstance edge data to Neptune Gremlin CSV format."""
    try:
        # Ensure output directory exists
        output_dir = Path("src/data/output/neptune")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Read the mock person-datainstance data from JSON
        print("Reading mock person-datainstance data...")
        input_file = Path("src/data/output/gds/mock_person-datainstance_data.json")
        
        if not input_file.exists():
            print(f"Input file {input_file} not found!")
            return False
            
        with open(input_file, 'r') as f:
            edge_data = json.load(f)
        
        # Initialize list to store converted edges
        edges = []
        
        print("\nConverting person-datainstance edges to Gremlin format...")
        for edge in tqdm(edge_data, desc="Processing edges"):
            # Create the edge with required fields
            edge_record = {
                '~id': edge['edge_id'],
                '~from': edge['node_id_from'],
                '~to': edge['node_id_to'],
                '~label': 'person_datainstance;secondary'
            }
            
            # Add all properties from the JSON
            for key, value in edge['edge_properties'].items():
                if isinstance(value, list):
                    # Convert list to string representation with semicolons
                    value = ';'.join(str(v) for v in value)
                
                # Convert property name to lowercase and add type suffix
                if key.lower() == 'confidence_score':
                    edge_record['confidence_score:Float'] = float(value)
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
        output_path = output_dir / "neptune_person_datainstance_edges_gremlin.csv"
        edges_df.to_csv(output_path, index=False, quoting=1, quotechar='"', escapechar='\\')
        
        # Print sample record
        print("\nSample Edge Record:")
        sample = edges[0]
        print(json.dumps(sample, indent=2))
        
        print(f"\nGenerated {len(edges)} person-datainstance edges")
        print(f"Saved to {output_path}")
        return True
        
    except Exception as e:
        print(f"Error converting person-datainstance edges: {str(e)}")
        return False

def convert_to_gremlin():
    """Convert person-datainstance edge data to Neptune Gremlin CSV format."""
    # Convert person-datainstance edges only (datainstance nodes are handled by generate_neptune_datainstance_json_gremlin_csv.py)
    edges_success = convert_person_datainstance_edges()
    
    if edges_success:
        print("\n✅ Successfully converted person-datainstance data to Gremlin format")
    else:
        print("\n❌ Failed to convert person-datainstance data to Gremlin format")
    
    return edges_success

if __name__ == "__main__":
    convert_to_gremlin()
