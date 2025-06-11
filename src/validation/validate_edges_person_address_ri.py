import pandas as pd
import json

def validate_edges():
    try:
        # Read the person node data
        print("Reading mock_person_data.json...")
        with open('src/data/output/gds/mock_person_data.json', 'r') as f:
            person_data = json.load(f)
        person_ids = set(person['node_id'] for person in person_data)
        print(f"Found {len(person_ids)} unique person nodes")
        
        # Read the address node data
        print("\nReading mock_address_data.json...")
        with open('src/data/output/gds/mock_address_data.json', 'r') as f:
            address_data = json.load(f)
        address_ids = set(address['node_id'] for address in address_data)
        print(f"Found {len(address_ids)} unique address nodes")
        
        # Read the edge data
        print("\nReading mock_person-address_data.json...")
        with open('src/data/output/gds/mock_person-address_data.json', 'r') as f:
            edge_data = json.load(f)
        edge_df = pd.DataFrame(edge_data)
        print(f"Found {len(edge_df)} edges to validate")
        
        # Check for missing source nodes (person nodes)
        missing_from = set(edge_df['node_id_from']) - person_ids
        if missing_from:
            print(f"\nERROR: Found {len(missing_from)} edges with missing person nodes:")
            for node_id in missing_from:
                print(f"  - Edge source node {node_id} not found in mock_person_data.json")
        
        # Check for missing target nodes (address nodes)
        missing_to = set(edge_df['node_id_to']) - address_ids
        if missing_to:
            print(f"\nERROR: Found {len(missing_to)} edges with missing address nodes:")
            for node_id in missing_to:
                print(f"  - Edge target node {node_id} not found in mock_address_data.json")
        
        # Print summary
        total_errors = len(missing_from) + len(missing_to)
        if total_errors == 0:
            print("\nSUCCESS: All edges have valid person and address nodes!")
        else:
            print(f"\nFAILURE: Found {total_errors} referential integrity errors")
            print(f"  - {len(missing_from)} missing person nodes")
            print(f"  - {len(missing_to)} missing address nodes")
        
        return total_errors == 0
        
    except FileNotFoundError as e:
        print(f"Error: Required file not found - {str(e)}")
        return False
    except Exception as e:
        print(f"Error during validation: {str(e)}")
        return False

if __name__ == "__main__":
    validate_edges() 