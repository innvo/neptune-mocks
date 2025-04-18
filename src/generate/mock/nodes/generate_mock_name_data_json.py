import pandas as pd
from faker import Faker
import json
from tqdm import tqdm
import os
import time
import platform

def clear_terminal():
    """Clear the terminal screen"""
    if platform.system() == 'Windows':
        os.system('cls')
    else:
        os.system('clear')

def validate_referential_integrity(name_data, node_df):
    """Validate referential integrity of name data against node data"""
    validation_results = {
        'total_names': len(name_data),
        'valid_names': 0,
        'invalid_names': 0,
        'missing_nodes': set(),
        'node_type_stats': {
            'name': {'total': 0, 'valid': 0}
        }
    }
    
    # Get sets of valid node IDs for quick lookup
    valid_node_ids = set(node_df['node_id'].values)
    name_node_ids = set(node_df[node_df['node_type'] == 'name']['node_id'].values)
    
    for name_entry in name_data:
        node_id = name_entry['node_id']
        
        # Validate node existence and type
        node_exists = node_id in valid_node_ids
        is_name_node = node_id in name_node_ids
        
        if node_exists and is_name_node:
            validation_results['valid_names'] += 1
            validation_results['node_type_stats']['name']['valid'] += 1
        else:
            validation_results['invalid_names'] += 1
            if not node_exists or not is_name_node:
                validation_results['missing_nodes'].add(node_id)
    
    # Update total counts
    validation_results['node_type_stats']['name']['total'] = len(name_node_ids)
    
    return validation_results

def generate_mock_name_data():
    try:
        # Clear terminal at start
        clear_terminal()
        
        start_time = time.time()
        
        # Initialize Faker
        fake = Faker()
        
        # Read node_data.csv to get name nodes
        print("Reading node data...")
        node_df = pd.read_csv(os.path.join('src', 'data', 'input', 'node_data.csv'), usecols=['node_id', 'node_type'])
        
        # Print node type statistics
        print("\nNode Type Statistics:")
        print(f"Total number of nodes: {len(node_df)}")
        node_counts = node_df['node_type'].value_counts()
        for node_type, count in node_counts.items():
            print(f"{node_type}: {count} nodes")
        
        # Filter for name nodes
        name_nodes = node_df[node_df['node_type'] == 'name']
        if name_nodes.empty:
            print("Warning: No name nodes found in node_data.csv")
            return None
        
        # Initialize data list
        name_data = []
        
        # Generate mock data for each name node
        print("\nGenerating mock name data...")
        for _, node in tqdm(name_nodes.iterrows(), total=len(name_nodes), desc="Processing name nodes"):
            node_id = node['node_id']
            
            # Generate a fake name
            full_name = fake.name().upper()  # Convert to uppercase as per requirements
            
            # Create node properties JSON
            node_properties = {
                "NAME_FULL": full_name
            }
            
            # Add to data list
            name_data.append({
                'node_id': node_id,
                'node_name': full_name,
                'node_type': 'name',
                'node_properties': node_properties
            })
        
        # Save to JSON
        output_path = os.path.join('src', 'data', 'output', 'gds', 'mock_name_data.json')
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(name_data, f, indent=2)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Validate referential integrity
        validation_results = validate_referential_integrity(name_data, node_df)
        
        # Print validation results
        print("\nReferential Integrity Validation Results:")
        print(f"Total names generated: {validation_results['total_names']}")
        print(f"Valid names: {validation_results['valid_names']}")
        print(f"Invalid names: {validation_results['invalid_names']}")
        
        if validation_results['missing_nodes']:
            print(f"\nMissing or invalid name nodes: {len(validation_results['missing_nodes'])}")
            print("Sample of missing name nodes:", list(validation_results['missing_nodes'])[:5])
        
        print("\nNode Type Statistics:")
        for node_type, stats in validation_results['node_type_stats'].items():
            print(f"\n{node_type.capitalize()} Nodes:")
            print(f"  Total: {stats['total']}")
            print(f"  Used in valid names: {stats['valid']}")
        
        print("\nName Data Generation Statistics:")
        print(f"Total number of name nodes processed: {len(name_data)}")
        print(f"Processing time: {processing_time:.2f} seconds")
        print(f"Names per second: {len(name_data) / processing_time:.2f}")
        print(f"Data saved to: {output_path}")
        
        return name_data
        
    except Exception as e:
        print(f"Error generating mock name data: {str(e)}")
        return None

if __name__ == "__main__":
    name_data = generate_mock_name_data()
    if name_data is not None:
        print("\nSample of Generated Name Data:")
        print(json.dumps(name_data[:5], indent=2)) 