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
    input_dir = Path("src/data/output/gds")
    output_dir = Path("src/data/output/neptune")
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all address JSON files
    address_files = list(input_dir.glob("*address*.json"))
    
    if not address_files:
        print("No address JSON files found!")
        return False
    
    # Prepare CSV data
    csv_data = []
    # Add header row
    csv_data.append(["~id", "~label", "~properties"])
    
    for file_path in address_files:
        try:
            # Read JSON data
            address_data = read_json_file(file_path)
            
            # Process each address
            for address in address_data:
                # Create vertex ID
                vertex_id = f"address_{address.get('id', '')}"
                
                # Create properties string
                properties = {
                    "street": address.get("street", ""),
                    "city": address.get("city", ""),
                    "state": address.get("state", ""),
                    "zip": address.get("zip", ""),
                    "country": address.get("country", "")
                }
                
                # Convert properties to JSON string
                properties_str = json.dumps(properties)
                
                # Add row to CSV data
                csv_data.append([vertex_id, "Address", properties_str])
            
            print(f"Processed {file_path}")
            
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")
            return False
    
    # Write CSV file
    output_file = output_dir / "address_vertices.csv"
    try:
        write_csv_file(csv_data, output_file)
        print(f"Successfully created {output_file}")
        return True
    except Exception as e:
        print(f"Error writing CSV file: {str(e)}")
        return False

if __name__ == "__main__":
    success = generate_address_gremlin_csv()
    if not success:
        print("Failed to generate address Gremlin CSV data")
        exit(1) 