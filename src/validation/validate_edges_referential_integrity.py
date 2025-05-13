import pandas as pd
import json

def validate_edges():
    try:
        # Read the node data
        print("Reading mock_person_data.json...")
        with open('src/data/output/gds/mock_person_data.json', 'r') as f:
            person_data = json.load(f)
        node_ids = set(person['node_id'] for person in person_data)
        print(f"Found {len(node_ids)} unique nodes in mock_person_data.json")
        
        # Read the edge data
        print("\nReading mock_person-name_data.json...")
        with open('src/data/output/gds/mock_person-name_data.json', 'r') as f:
            edge_data = [json.loads(line) for line in f]
        edge_df = pd.DataFrame(edge_data)
        print(f"Found {len(edge_df)} edges to validate")
        
        # Check for missing source nodes
        missing_from = set(edge_df['node_id_from']) - node_ids
        if missing_from:
            print(f"\nERROR: Found {len(missing_from)} edges with missing source nodes:")
            for node_id in missing_from:
                print(f"  - Edge source node {node_id} not found in mock_person_data.json")
        
        # Check for missing target nodes
        missing_to = set(edge_df['node_id_to']) - node_ids
        if missing_to:
            print(f"\nERROR: Found {len(missing_to)} edges with missing target nodes:")
            for node_id in missing_to:
                print(f"  - Edge target node {node_id} not found in mock_person_data.json")
        
        # Print summary
        total_errors = len(missing_from) + len(missing_to)
        if total_errors == 0:
            print("\nSUCCESS: All edges have valid source and target nodes!")
        else:
            print(f"\nFAILURE: Found {total_errors} referential integrity errors")
            print(f"  - {len(missing_from)} missing source nodes")
            print(f"  - {len(missing_to)} missing target nodes")
        
        return total_errors == 0
        
    except FileNotFoundError as e:
        print(f"Error: Required file not found - {str(e)}")
        return False
    except Exception as e:
        print(f"Error during validation: {str(e)}")
        return False

if __name__ == "__main__":
    validate_edges() 