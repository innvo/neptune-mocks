import pandas as pd
from tqdm import tqdm

def validate_name_data():
    try:
        print("Reading data files...")
        
        # Read both CSV files
        mock_name_df = pd.read_csv('mock_name_data.csv')
        node_df = pd.read_csv('node_data.csv', usecols=['node_id', 'node_type'])
        
        # Get all name nodes from node_data.csv
        name_nodes = set(node_df[node_df['node_type'] == 'name']['node_id'])
        
        # Initialize counters and lists for errors
        total_mock_records = len(mock_name_df)
        missing_nodes = []
        wrong_type_nodes = []
        
        print("\nValidating name data...")
        # Check each record in mock_name_data.csv
        for _, row in tqdm(mock_name_df.iterrows(), total=total_mock_records, desc="Validating records"):
            node_id = row['node_id']
            
            # Check if node exists in node_data.csv
            if node_id not in node_df['node_id'].values:
                missing_nodes.append(node_id)
            # Check if node is of type 'name'
            elif node_id not in name_nodes:
                wrong_type_nodes.append(node_id)
        
        # Print validation results
        print("\nValidation Results:")
        print(f"Total records in mock_name_data.csv: {total_mock_records}")
        print(f"Total name nodes in node_data.csv: {len(name_nodes)}")
        
        if missing_nodes:
            print(f"\nError: Found {len(missing_nodes)} nodes in mock_name_data.csv that don't exist in node_data.csv")
            print("First 5 missing nodes:", missing_nodes[:5])
        
        if wrong_type_nodes:
            print(f"\nError: Found {len(wrong_type_nodes)} nodes that are not of type 'name' in node_data.csv")
            print("First 5 wrong type nodes:", wrong_type_nodes[:5])
        
        if not missing_nodes and not wrong_type_nodes:
            print("\nValidation successful! All records in mock_name_data.csv are valid name nodes from node_data.csv")
            return True
        else:
            return False
            
    except Exception as e:
        print(f"Error during validation: {str(e)}")
        return False

if __name__ == "__main__":
    validation_result = validate_name_data() 