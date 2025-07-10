import json
import csv
import os
from pathlib import Path
import pandas as pd
from tqdm import tqdm

def read_json_file(file_path):
    """Read and parse a JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)

def write_csv_file(data, output_path):
    """Write data to a CSV file."""
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(data)

def generate_address_gremlin_csv():
    """Generate Neptune Gremlin CSV data from address JSON files."""
    # Input and output paths
    input_file = Path("src/data/output/gds/mock_address_data.json")
    output_dir = Path("src/data/output/neptune")
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not input_file.exists():
        print(f"Input file {input_file} not found!")
        return False
    
    try:
        # Read JSON data
        address_data = read_json_file(input_file)
        
        # Prepare CSV data
        csv_data = []
        # Add header row
        csv_data.append(["~id", "~label", "~properties"])
        
        # Process each address
        for address in address_data:
            # Create vertex ID
            vertex_id = f"address_{address.get('node_id', '')}"
            
            # Get the full address from node_properties
            full_address = address.get('node_properties', {}).get('ADDRESS_FULL', '')
            
            # Create properties string
            properties = {
                "address_full": full_address,
                "name": address.get('node_name', '')
            }
            
            # Convert properties to JSON string
            properties_str = json.dumps(properties)
            
            # Add row to CSV data
            csv_data.append([vertex_id, "Address", properties_str])
        
        # Write CSV file
        output_file = output_dir / "address_vertices.csv"
        write_csv_file(csv_data, output_file)
        print(f"Successfully created {output_file}")
        return True
        
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        return False

def convert_to_gremlin():
    """Convert receipt data to Neptune Gremlin CSV format."""
    try:
        # Ensure output directory exists
        output_dir = Path("src/data/output/neptune")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Read the mock receipt data from JSON
        print("Reading mock receipt data...")
        input_file = Path("src/data/output/gds/mock_receipt_data.json")
        
        if not input_file.exists():
            print(f"Input file {input_file} not found!")
            return False
            
        with open(input_file, 'r') as f:
            receipt_data = json.load(f)
        
        # Initialize list to store converted nodes
        nodes = []
        
        print("\nConverting data to Gremlin format...")
        for receipt in tqdm(receipt_data, desc="Processing nodes"):
            # Get the node properties
            properties = receipt.get('node_properties', {})
            
            # Create the node with required fields
            node = {
                '~id': receipt.get('node_id', '')
            }
            
            # Add all properties from the JSON
            for key, value in properties.items():
                if isinstance(value, list):
                    # Convert list to string representation with semicolons
                    value = ';'.join(str(v) for v in value)
                
                # Convert property name to lowercase and add type suffix
                if key.lower() == 'receipt_date_estimated':
                    node['receipt_date:Date'] = str(value)
                elif key.lower() == 'receipt_number':
                    node['receipt_number:String'] = str(value)
                elif key.lower() == 'form_number':
                    node['form_number:String'] = str(value)
                elif key.lower() == 'status':
                    node['status:String'] = str(value)
                elif key.lower() == 'status_std':
                    node['status_std:String'] = str(value)
                else:
                    node[f'{key.lower()}:String'] = str(value)
            
            # Add receipt and primary labels
            node['~label'] = 'receipt;primary'
            
            nodes.append(node)
        
        # Convert to DataFrame
        nodes_df = pd.DataFrame(nodes)
        
        # Reorder columns to ensure ~label is last
        cols = nodes_df.columns.tolist()
        cols.remove('~label')
        cols.append('~label')
        nodes_df = nodes_df[cols]
        
        # Save to CSV with proper quoting
        output_path = output_dir / "neptune_receipt_nodes_gremlin.csv"
        nodes_df.to_csv(output_path, index=False, quoting=1, quotechar='"', escapechar='\\')
        
        # Print sample record
        print("\nSample Record:")
        sample = nodes[0]
        print(json.dumps(sample, indent=2))
        
        print(f"\nGenerated {len(nodes)} Gremlin-compatible nodes")
        print(f"Saved to {output_path}")
        return True
        
    except Exception as e:
        print(f"Error converting data: {str(e)}")
        return False

if __name__ == "__main__":
    address_success = generate_address_gremlin_csv()
    receipt_success = convert_to_gremlin()
    
    if not address_success:
        print("Failed to generate address Gremlin CSV data")
    if not receipt_success:
        print("Failed to generate receipt Gremlin CSV data")
    
    if not (address_success and receipt_success):
        exit(1) 