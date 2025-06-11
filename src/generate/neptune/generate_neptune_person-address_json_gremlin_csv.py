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

def generate_person_address_edge_gremlin_csv():
    """Generate Neptune Gremlin CSV data for person-address edges."""
    # Input and output paths
    input_dir = Path("src/data/output/gds")
    output_dir = Path("src/data/output/neptune")
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all person-address edge JSON files
    edge_files = list(input_dir.glob("*person-address*.json"))
    
    if not edge_files:
        print("No person-address edge JSON files found!")
        return False
    
    # Prepare CSV data
    csv_data = []
    # Add header row for edges
    csv_data.append(["~id", "~from", "~to", "~label", "~properties"])
    
    for file_path in edge_files:
        try:
            # Read JSON data
            edge_data = read_json_file(file_path)
            
            # Process each edge
            for edge in edge_data:
                # Create edge ID
                edge_id = f"lives_at_{edge.get('id', '')}"
                
                # Create source and target vertex IDs
                from_id = f"person_{edge.get('from', '')}"
                to_id = f"address_{edge.get('to', '')}"
                
                # Create properties string
                properties = {
                    "type": edge.get("type", "lives_at"),
                    "since": edge.get("since", ""),
                    "is_current": edge.get("is_current", True)
                }
                
                # Convert properties to JSON string
                properties_str = json.dumps(properties)
                
                # Add row to CSV data
                csv_data.append([edge_id, from_id, to_id, "LIVES_AT", properties_str])
            
            print(f"Processed {file_path}")
            
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")
            return False
    
    # Write CSV file
    output_file = output_dir / "person_address_edges.csv"
    try:
        write_csv_file(csv_data, output_file)
        print(f"Successfully created {output_file}")
        return True
    except Exception as e:
        print(f"Error writing CSV file: {str(e)}")
        return False

if __name__ == "__main__":
    success = generate_person_address_edge_gremlin_csv()
    if not success:
        print("Failed to generate person-address edge Gremlin CSV data")
        exit(1) 