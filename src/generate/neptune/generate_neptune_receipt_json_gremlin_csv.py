import json
import csv
import os
from pathlib import Path

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

def generate_receipt_gremlin_csv():
    """Generate Neptune Gremlin CSV data from receipt JSON files."""
    # Input and output paths
    input_file = Path("src/data/output/gds/mock_receipt_data.json")
    output_dir = Path("src/data/output/neptune")
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not input_file.exists():
        print(f"Input file {input_file} not found!")
        return False
    
    try:
        # Read JSON data
        receipt_data = read_json_file(input_file)
        
        # Prepare CSV data
        csv_data = []
        # Add header row
        csv_data.append(["~id", "~label", "~properties"])
        
        # Process each receipt
        for receipt in receipt_data:
            # Create vertex ID
            vertex_id = f"receipt_{receipt.get('node_id', '')}"
            
            # Get properties from node_properties
            node_properties = receipt.get('node_properties', {})
            
            # Create properties dictionary
            properties = {
                "receipt_number": node_properties.get('RECEIPT_NUMBER', ''),
                "form_number": node_properties.get('FORM_NUMBER', ''),
                "receipt_date": node_properties.get('RECEIPT_DATE_ESTIMATED', ''),
                "status": node_properties.get('STATUS', ''),
                "status_std": node_properties.get('STATUS_STD', ''),
                "name": receipt.get('node_name', '')
            }
            
            # Convert properties to JSON string
            properties_str = json.dumps(properties)
            
            # Add row to CSV data
            csv_data.append([vertex_id, "Receipt", properties_str])
        
        # Write CSV file
        output_file = output_dir / "receipt_vertices.csv"
        write_csv_file(csv_data, output_file)
        print(f"Successfully created {output_file}")
        return True
        
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        return False

if __name__ == "__main__":
    address_success = generate_address_gremlin_csv()
    receipt_success = generate_receipt_gremlin_csv()
    
    if not address_success:
        print("Failed to generate address Gremlin CSV data")
    if not receipt_success:
        print("Failed to generate receipt Gremlin CSV data")
    
    if not (address_success and receipt_success):
        exit(1) 