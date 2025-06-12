import pandas as pd

def validate_person_address_edges():
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
            print("\nSUCCESS: All person-address edges have valid source and target nodes!")
        else:
            print(f"\nFAILURE: Found {total_errors} referential integrity errors in person-address edges")
            print(f"  - {len(missing_from)} missing source nodes")
            print(f"  - {len(missing_to)} missing target nodes")
        
        return total_errors == 0
        
    except FileNotFoundError as e:
        print(f"Error: Required file not found - {str(e)}")
        return False
    except Exception as e:
        print(f"Error during validation: {str(e)}")
        return False

def validate_person_receipt_edges():
    try:
        # Read the node data
        print("\nReading person nodes...")
        person_nodes_df = pd.read_csv('src/data/output/neptune/neptune_person_nodes_gremlin.csv')
        person_ids = set(person_nodes_df['~id'])
        print(f"Found {len(person_ids)} unique person nodes")
        
        print("\nReading receipt nodes...")
        receipt_nodes_df = pd.read_csv('src/data/output/neptune/neptune_receipt_nodes_gremlin.csv')
        receipt_ids = set(receipt_nodes_df['~id'])
        print(f"Found {len(receipt_ids)} unique receipt nodes")
        
        # Read the edge data
        print("\nReading person-receipt edges...")
        edges_df = pd.read_csv('src/data/output/neptune/neptune_person_receipt_edges_gremlin.csv')
        print(f"Found {len(edges_df)} edges to validate")
        
        # Check for missing source nodes (person IDs)
        missing_from = set(edges_df['~from']) - person_ids
        if missing_from:
            print(f"\nERROR: Found {len(missing_from)} edges with missing source nodes:")
            for node_id in missing_from:
                print(f"  - Edge source node {node_id} not found in person nodes file")
        
        # Check for missing target nodes (receipt IDs)
        missing_to = set(edges_df['~to']) - receipt_ids
        if missing_to:
            print(f"\nERROR: Found {len(missing_to)} edges with missing target nodes:")
            for node_id in missing_to:
                print(f"  - Edge target node {node_id} not found in receipt nodes file")
        
        # Print summary
        total_errors = len(missing_from) + len(missing_to)
        if total_errors == 0:
            print("\nSUCCESS: All person-receipt edges have valid source and target nodes!")
        else:
            print(f"\nFAILURE: Found {total_errors} referential integrity errors in person-receipt edges")
            print(f"  - {len(missing_from)} missing source nodes")
            print(f"  - {len(missing_to)} missing target nodes")
        
        return total_errors == 0
        
    except FileNotFoundError as e:
        print(f"Error: Required file not found - {str(e)}")
        return False
    except Exception as e:
        print(f"Error during validation: {str(e)}")
        return False

def validate_edges():
    print("\n=== Starting Gremlin CSV Validation ===")
    person_address_valid = validate_person_address_edges()
    person_receipt_valid = validate_person_receipt_edges()
    
    if not (person_address_valid and person_receipt_valid):
        print("\n❌ Gremlin validation failed")
        return False
    
    print("\n✅ Gremlin validation passed")
    return True

if __name__ == "__main__":
    validate_edges() 