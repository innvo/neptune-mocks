import pandas as pd

def validate_edges():
    try:
        # Read the node data
        print("Reading node_data.csv...")
        node_df = pd.read_csv('node_data.csv', usecols=['node_id'])
        node_ids = set(node_df['node_id'].values)
        print(f"Found {len(node_ids)} unique nodes in node_data.csv")
        
        # Read the edge data
        print("\nReading person_edges.csv...")
        edge_df = pd.read_csv('person_edges.csv')
        print(f"Found {len(edge_df)} edges to validate")
        
        # Check for missing source nodes
        missing_from = set(edge_df['node_id_from']) - node_ids
        if missing_from:
            print(f"\nERROR: Found {len(missing_from)} edges with missing source nodes:")
            for node_id in missing_from:
                print(f"  - Edge source node {node_id} not found in node_data.csv")
        
        # Check for missing target nodes
        missing_to = set(edge_df['node_id_to']) - node_ids
        if missing_to:
            print(f"\nERROR: Found {len(missing_to)} edges with missing target nodes:")
            for node_id in missing_to:
                print(f"  - Edge target node {node_id} not found in node_data.csv")
        
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