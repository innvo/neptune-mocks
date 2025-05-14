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

def validate_referential_integrity(address_data, node_df):
    """Validate referential integrity of address data against node data"""
    validation_results = {
        'total_addresses': len(address_data),
        'valid_addresses': 0,
        'invalid_addresses': 0,
        'missing_nodes': set(),
        'node_type_stats': {
            'address': {'total': 0, 'valid': 0}
        }
    }
    
    # Get sets of valid node IDs for quick lookup
    valid_node_ids = set(node_df['node_id'].values)
    address_node_ids = set(node_df[node_df['node_type'] == 'address']['node_id'].values)
    
    for address_entry in address_data:
        node_id = address_entry['node_id']
        
        # Validate node existence and type
        node_exists = node_id in valid_node_ids
        is_address_node = node_id in address_node_ids
        
        if node_exists and is_address_node:
            validation_results['valid_addresses'] += 1
            validation_results['node_type_stats']['address']['valid'] += 1
        else:
            validation_results['invalid_addresses'] += 1
            if not node_exists or not is_address_node:
                validation_results['missing_nodes'].add(node_id)
    
    # Update total counts
    validation_results['node_type_stats']['address']['total'] = len(address_node_ids)
    
    return validation_results

def generate_mock_address_data():
    try:
        # Clear terminal at start
        clear_terminal()
        
        start_time = time.time()
        
        # Initialize Faker
        fake = Faker()
        
        # Read node_data.csv to get address nodes
        print("Reading node data...")
        node_df = pd.read_csv(os.path.join('src', 'data', 'input', 'node_data.csv'), usecols=['node_id', 'node_type'])
        
        # Print node type statistics
        print("\nNode Type Statistics:")
        print(f"Total number of nodes: {len(node_df)}")
        node_counts = node_df['node_type'].value_counts()
        for node_type, count in node_counts.items():
            print(f"{node_type}: {count} nodes")
        
        # Filter for address nodes
        address_nodes = node_df[node_df['node_type'] == 'address']
        if address_nodes.empty:
            print("Warning: No address nodes found in node_data.csv")
            return None
        
        # Initialize data list
        address_data = []
        
        # Generate mock data for each address node
        print("\nGenerating mock address data...")
        for _, node in tqdm(address_nodes.iterrows(), total=len(address_nodes), desc="Processing address nodes"):
            node_id = node['node_id']
            
            # Generate a fake address
            full_address = fake.address().upper()  # Convert to uppercase as per requirements
            full_address = full_address.replace('\n', ' ').strip()  # Remove carriage returns and extra spaces
            
            # Create node properties JSON
            node_properties = {
                "ADDRESS_FULL": full_address
            }
            
            # Add to data list
            address_data.append({
                'node_id': node_id,
                'node_name': full_address,
                'node_properties': node_properties
            })
        
        # Save to JSON
        output_path = os.path.join('src', 'data', 'output', 'gds', 'mock_address_data.json')
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(address_data, f, indent=2)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Validate referential integrity
        validation_results = validate_referential_integrity(address_data, node_df)
        
        # Print validation results
        print("\nReferential Integrity Validation Results:")
        print(f"Total addresses generated: {validation_results['total_addresses']}")
        print(f"Valid addresses: {validation_results['valid_addresses']}")
        print(f"Invalid addresses: {validation_results['invalid_addresses']}")
        
        if validation_results['missing_nodes']:
            print(f"\nMissing or invalid address nodes: {len(validation_results['missing_nodes'])}")
            print("Sample of missing address nodes:", list(validation_results['missing_nodes'])[:5])
        
        print("\nNode Type Statistics:")
        for node_type, stats in validation_results['node_type_stats'].items():
            print(f"\n{node_type.capitalize()} Nodes:")
            print(f"  Total: {stats['total']}")
            print(f"  Used in valid addresses: {stats['valid']}")
        
        print("\nAddress Data Generation Statistics:")
        print(f"Total number of address nodes processed: {len(address_data)}")
        print(f"Processing time: {processing_time:.2f} seconds")
        print(f"Addresses per second: {len(address_data) / processing_time:.2f}")
        print(f"Data saved to: {output_path}")
        
        return address_data
        
    except Exception as e:
        print(f"Error generating mock address data: {str(e)}")
        return None

if __name__ == "__main__":
    address_data = generate_mock_address_data()
    if address_data is not None:
        print("\nSample of Generated Address Data:")
        print(json.dumps(address_data[:5], indent=2))
