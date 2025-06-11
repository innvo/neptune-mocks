import pandas as pd

def validate_edges():
    try:
        # Read the node data
        print("Reading person nodes...")
        person_nodes_df = pd.read_csv('src/data/output/neptune/neptune_person_nodes_gremlin.csv')
        person_ids = set(person_nodes_df['~id'])
        print(f"Found {len(person_ids)} unique person nodes")
        
        print("\nReading address nodes...")
        address_nodes_df = pd.read_csv('src/data/output/neptune/neptune_address_nodes_gremlin.csv')
        address_ids = set(address_nodes_df['~id'])
        print(f"Found {len(address_ids)} unique address nodes")
        
        # Read the edge data
        print("\nReading person-address edges...")
        edges_df = pd.read_csv('src/data/output/neptune/neptune_person_address_edges_gremlin.csv')
        print(f"Found {len(edges_df)} edges to validate")
        
        # Check for missing source nodes (person IDs)
        missing_from = set(edges_df['~from']) - person_ids
        if missing_from:
            print(f"\nERROR: Found {len(missing_from)} edges with missing source nodes:")
            for node_id in missing_from:
                print(f"  - Edge source node {node_id} not found in person nodes file")
        
        # Check for missing target nodes (address IDs)
        missing_to = set(edges_df['~to']) - address_ids
        if missing_to:
            print(f"\nERROR: Found {len(missing_to)} edges with missing target nodes:")
            for node_id in missing_to:
                print(f"  - Edge target node {node_id} not found in address nodes file")
        
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