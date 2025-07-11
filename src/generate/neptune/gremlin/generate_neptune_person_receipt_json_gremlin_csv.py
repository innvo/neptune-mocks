import pandas as pd
import json
import os
from tqdm import tqdm
from pathlib import Path

def convert_person_receipt_edges():
    """Convert person-receipt edge data to Neptune Gremlin CSV format."""
    try:
        # Ensure output directory exists
        output_dir = Path("src/data/output/neptune")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Read the mock person-receipt data from JSON
        print("Reading mock person-receipt data...")
        input_file = Path("src/data/output/gds/mock_person-receipt_data.json")
        
        if not input_file.exists():
            print(f"Input file {input_file} not found!")
            return False
            
        with open(input_file, 'r') as f:
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
                '~label': 'person_receipt;primary'
            }
            
            # Add all properties from the JSON
            for key, value in edge['edge_properties'].items():
                if isinstance(value, list):
                    # Convert list to string representation with semicolons
                    value = ';'.join(str(v) for v in value)
                
                # Convert property name to lowercase and add type suffix
                if key.lower() == 'amount':
                    edge_record[f'{key.lower()}:Double'] = float(value)
                elif key.lower() == 'receipt_date_estimated':
                    edge_record['receipt_date:Date'] = str(value)
                elif key.lower() == 'receipt_number':
                    edge_record['receipt_number:String'] = str(value)
                elif key.lower() == 'form_number':
                    edge_record['form_number:String'] = str(value)
                elif key.lower() == 'status':
                    edge_record['status:String'] = str(value)
                elif key.lower() == 'status_std':
                    edge_record['status_std:String'] = str(value)
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
        output_path = output_dir / "neptune_person_receipt_edges_gremlin.csv"
        edges_df.to_csv(output_path, index=False, quoting=1, quotechar='"', escapechar='\\')
        
        # Print sample record
        print("\nSample Edge Record:")
        sample = edges[0]
        print(json.dumps(sample, indent=2))
        
        print(f"\nGenerated {len(edges)} person-receipt edges")
        print(f"Saved to {output_path}")
        return True
        
    except Exception as e:
        print(f"Error converting person-receipt edges: {str(e)}")
        return False

def convert_to_gremlin():
    """Convert person-receipt edge data to Neptune Gremlin CSV format."""
    # Convert person-receipt edges only (receipt nodes are handled by generate_neptune_receipt_json_gremlin_csv.py)
    edges_success = convert_person_receipt_edges()
    
    if edges_success:
        print("\n✅ Successfully converted person-receipt data to Gremlin format")
    else:
        print("\n❌ Failed to convert person-receipt data to Gremlin format")
    
    return edges_success

if __name__ == "__main__":
    convert_to_gremlin() 