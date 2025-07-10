import pandas as pd
import random
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

def validate_referential_integrity(anumber_data, node_df):
    """Validate referential integrity of anumber data against node data"""
    validation_results = {
        'total_anumbers': len(anumber_data),
        'valid_anumbers': 0,
        'invalid_anumbers': 0,
        'missing_nodes': set(),
        'node_type_stats': {
            'anumber': {'total': 0, 'valid': 0}
        }
    }
    
    # Get sets of valid node IDs for quick lookup
    valid_node_ids = set(node_df['node_id'].values)
    anumber_node_ids = set(node_df[node_df['node_type'] == 'anumber']['node_id'].values)
    
    for anumber_entry in anumber_data:
        node_id = anumber_entry['node_id']
        
        # Validate node existence and type
        node_exists = node_id in valid_node_ids
        is_anumber_node = node_id in anumber_node_ids
        
        if node_exists and is_anumber_node:
            validation_results['valid_anumbers'] += 1
            validation_results['node_type_stats']['anumber']['valid'] += 1
        else:
            validation_results['invalid_anumbers'] += 1
            if not node_exists or not is_anumber_node:
                validation_results['missing_nodes'].add(node_id)
    
    # Update total counts
    validation_results['node_type_stats']['anumber']['total'] = len(anumber_node_ids)
    
    return validation_results

def generate_anumber():
    """Generate a realistic A-Number (10-digit number)"""
    # A-Numbers are 10-digit numbers
    digits = ''.join([str(random.randint(0, 9)) for _ in range(10)])
    return digits

def generate_mock_anumber_data():
    try:
        # Clear terminal at start
        clear_terminal()
        
        start_time = time.time()
        
        # Read node_data.csv to get anumber nodes
        print("Reading node data...")
        node_df = pd.read_csv(os.path.join('src', 'data', 'input', 'node_data.csv'), usecols=['node_id', 'node_type'])
        
        # Print node type statistics
        print("\nNode Type Statistics:")
        print(f"Total number of nodes: {len(node_df)}")
        node_counts = node_df['node_type'].value_counts()
        for node_type, count in node_counts.items():
            print(f"{node_type}: {count} nodes")
        
        # Filter for anumber nodes
        anumber_nodes = node_df[node_df['node_type'] == 'anumber']
        if anumber_nodes.empty:
            print("Warning: No anumber nodes found in node_data.csv")
            return None
        
        # Initialize data list
        anumber_data = []
        
        # Generate mock data for each anumber node
        print("\nGenerating mock anumber data...")
        for _, node in tqdm(anumber_nodes.iterrows(), total=len(anumber_nodes), desc="Processing anumber nodes"):
            node_id = node['node_id']
            
            # Generate an A-Number (10-digit number)
            anumber_value = generate_anumber()
            
            # Create node properties JSON
            node_properties = {
                "ANUMBER": anumber_value,
                "ANUMBER_TYPE": "PRIMARY",
                "ISSUE_DATE": None,  # Could be populated with realistic dates if needed
                "STATUS": random.choice(["ACTIVE", "INACTIVE", "PENDING"])
            }
            
            # Add to data list
            anumber_data.append({
                'node_id': node_id,
                'node_name': anumber_value,
                'node_type': 'anumber',
                'node_properties': node_properties
            })
        
        # Save to JSON
        output_path = os.path.join('src', 'data', 'output', 'gds', 'mock_anumber_data.json')
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(anumber_data, f, indent=2)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Validate referential integrity
        validation_results = validate_referential_integrity(anumber_data, node_df)
        
        # Print validation results
        print("\nReferential Integrity Validation Results:")
        print(f"Total anumbers generated: {validation_results['total_anumbers']}")
        print(f"Valid anumbers: {validation_results['valid_anumbers']}")
        print(f"Invalid anumbers: {validation_results['invalid_anumbers']}")
        
        if validation_results['missing_nodes']:
            print(f"\nMissing or invalid anumber nodes: {len(validation_results['missing_nodes'])}")
            print("Sample of missing anumber nodes:", list(validation_results['missing_nodes'])[:5])
        
        print("\nNode Type Statistics:")
        for node_type, stats in validation_results['node_type_stats'].items():
            print(f"\n{node_type.capitalize()} Nodes:")
            print(f"  Total: {stats['total']}")
            print(f"  Used in valid anumbers: {stats['valid']}")
        
        # Count anumber types
        anumber_types = {}
        status_counts = {}
        for entry in anumber_data:
            anumber_type = entry['node_properties']['ANUMBER_TYPE']
            status = entry['node_properties']['STATUS']
            anumber_types[anumber_type] = anumber_types.get(anumber_type, 0) + 1
            status_counts[status] = status_counts.get(status, 0) + 1
        
        print("\nA-Number Type Statistics:")
        for anumber_type, count in anumber_types.items():
            print(f"{anumber_type}: {count} anumbers")
        
        print("\nStatus Statistics:")
        for status, count in status_counts.items():
            print(f"{status}: {count} anumbers")
        
        print("\nA-Number Data Generation Statistics:")
        print(f"Total number of anumber nodes processed: {len(anumber_data)}")
        print(f"Processing time: {processing_time:.2f} seconds")
        print(f"A-Numbers per second: {len(anumber_data) / processing_time:.2f}")
        print(f"Data saved to: {output_path}")
        
        return anumber_data
        
    except Exception as e:
        print(f"Error generating mock anumber data: {str(e)}")
        return None

if __name__ == "__main__":
    anumber_data = generate_mock_anumber_data()
    if anumber_data is not None:
        print("\nSample of Generated A-Number Data:")
        print(json.dumps(anumber_data[:5], indent=2))
