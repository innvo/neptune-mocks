import pandas as pd

def validate_edges():
    try:
        # Read the person data
        print("Reading mock_person_data.csv...")
        person_df = pd.read_csv('mock_person_data.csv')
        person_ids = set(person_df['node_id'].values)
        print(f"Found {len(person_ids)} person nodes")
        
        # Read the node data for name nodes
        print("\nReading node_data.csv...")
        node_df = pd.read_csv('node_data.csv', usecols=['node_id', 'node_type'])
        name_nodes = node_df[node_df['node_type'] == 'name']
        name_ids = set(name_nodes['node_id'].values)
        print(f"Found {len(name_ids)} name nodes")
        
        # Read the edge data
        print("\nReading mock_person_name_data.csv...")
        edge_df = pd.read_csv('mock_person_name_data.csv')
        print(f"Found {len(edge_df)} edges to validate")
        
        # Initialize counters
        valid_edges = []
        invalid_edges = []
        
        # Validate each edge
        print("\nValidating edges...")
        for _, edge in edge_df.iterrows():
            edge_id = edge['edge_id']
            node_id_from = edge['node_id_from']
            node_id_to = edge['node_id_to']
            
            # Check if source node is a valid person
            is_valid_person = node_id_from in person_ids
            # Check if target node is a valid name
            is_valid_name = node_id_to in name_ids
            
            if is_valid_person and is_valid_name:
                valid_edges.append({
                    'edge_id': edge_id,
                    'node_id_from': node_id_from,
                    'node_id_to': node_id_to,
                    'status': 'VALID'
                })
            else:
                invalid_edges.append({
                    'edge_id': edge_id,
                    'node_id_from': node_id_from,
                    'node_id_to': node_id_to,
                    'status': 'INVALID',
                    'reason': 'Invalid person node' if not is_valid_person else 'Invalid name node'
                })
        
        # Print validation results
        print("\nValidation Results:")
        print(f"Total edges processed: {len(edge_df)}")
        print(f"Valid edges: {len(valid_edges)}")
        print(f"Invalid edges: {len(invalid_edges)}")
        
        if valid_edges:
            print("\nSample of Valid Edges:")
            valid_df = pd.DataFrame(valid_edges[:5])
            print(valid_df)
        
        if invalid_edges:
            print("\nSample of Invalid Edges:")
            invalid_df = pd.DataFrame(invalid_edges[:5])
            print(invalid_df)
            
            # Print detailed error counts
            invalid_person_count = sum(1 for edge in invalid_edges if edge['reason'] == 'Invalid person node')
            invalid_name_count = sum(1 for edge in invalid_edges if edge['reason'] == 'Invalid name node')
            print(f"\nInvalid Edge Details:")
            print(f"Edges with invalid person nodes: {invalid_person_count}")
            print(f"Edges with invalid name nodes: {invalid_name_count}")
        
        # Save validation results to CSV
        if valid_edges:
            valid_df = pd.DataFrame(valid_edges)
            valid_df.to_csv('valid_edges.csv', index=False)
            print("\nSaved valid edges to valid_edges.csv")
        
        if invalid_edges:
            invalid_df = pd.DataFrame(invalid_edges)
            invalid_df.to_csv('invalid_edges.csv', index=False)
            print("Saved invalid edges to invalid_edges.csv")
        
        return len(invalid_edges) == 0
        
    except FileNotFoundError as e:
        print(f"Error: Required file not found - {str(e)}")
        return False
    except Exception as e:
        print(f"Error during validation: {str(e)}")
        return False

if __name__ == "__main__":
    validate_edges() 