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

def validate_referential_integrity(phone_data, node_df):
    """Validate referential integrity of phone data against node data"""
    validation_results = {
        'total_phones': len(phone_data),
        'valid_phones': 0,
        'invalid_phones': 0,
        'missing_nodes': set(),
        'node_type_stats': {
            'phone': {'total': 0, 'valid': 0}
        }
    }
    
    # Get sets of valid node IDs for quick lookup
    valid_node_ids = set(node_df['node_id'].values)
    phone_node_ids = set(node_df[node_df['node_type'] == 'phone']['node_id'].values)
    
    for phone_entry in phone_data:
        node_id = phone_entry['node_id']
        
        # Validate node existence and type
        node_exists = node_id in valid_node_ids
        is_phone_node = node_id in phone_node_ids
        
        if node_exists and is_phone_node:
            validation_results['valid_phones'] += 1
            validation_results['node_type_stats']['phone']['valid'] += 1
        else:
            validation_results['invalid_phones'] += 1
            if not node_exists or not is_phone_node:
                validation_results['missing_nodes'].add(node_id)
    
    # Update total counts
    validation_results['node_type_stats']['phone']['total'] = len(phone_node_ids)
    
    return validation_results

def generate_phone_number():
    """Generate a realistic phone number"""
    # Phone number formats
    formats = [
        # US formats
        "({area}) {prefix}-{line}",
        "{area}-{prefix}-{line}",
        "{area}.{prefix}.{line}",
        "{area} {prefix} {line}",
        # International formats
        "+1-{area}-{prefix}-{line}",
        "1-{area}-{prefix}-{line}",
        # Simple formats
        "{area}{prefix}{line}",
        "{area}-{prefix}{line}"
    ]
    
    # Generate components
    area_code = str(random.randint(200, 999))  # Valid US area codes
    prefix = str(random.randint(200, 999))     # Valid prefix
    line_number = str(random.randint(1000, 9999))  # 4-digit line number
    
    # Choose a random format
    format_template = random.choice(formats)
    
    return format_template.format(
        area=area_code,
        prefix=prefix,
        line=line_number
    )

def generate_mock_phone_data():
    try:
        # Clear terminal at start
        clear_terminal()
        
        start_time = time.time()
        
        # Read node_data.csv to get phone nodes
        print("Reading node data...")
        node_df = pd.read_csv(os.path.join('src', 'data', 'input', 'node_data.csv'), usecols=['node_id', 'node_type'])
        
        # Print node type statistics
        print("\nNode Type Statistics:")
        print(f"Total number of nodes: {len(node_df)}")
        node_counts = node_df['node_type'].value_counts()
        for node_type, count in node_counts.items():
            print(f"{node_type}: {count} nodes")
        
        # Filter for phone nodes
        phone_nodes = node_df[node_df['node_type'] == 'phone']
        if phone_nodes.empty:
            print("Warning: No phone nodes found in node_data.csv")
            print("Note: You may need to add 'phone' to NODE_TYPES in generate_node_data.py")
            return None
        
        # Initialize data list
        phone_data = []
        
        # Generate mock data for each phone node
        print("\nGenerating mock phone data...")
        for _, node in tqdm(phone_nodes.iterrows(), total=len(phone_nodes), desc="Processing phone nodes"):
            node_id = node['node_id']
            
            # Generate a phone number
            phone_value = generate_phone_number()
            
            # Create node properties JSON
            node_properties = {
                "PHONE_NUMBER": phone_value
            }
            
            # Add to data list
            phone_data.append({
                'node_id': node_id,
                'node_name': phone_value,
                'node_type': 'phone',
                'node_properties': node_properties
            })
        
        # Save to JSON
        output_path = os.path.join('src', 'data', 'output', 'gds', 'mock_phone_data.json')
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(phone_data, f, indent=2)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Validate referential integrity
        validation_results = validate_referential_integrity(phone_data, node_df)
        
        # Print validation results
        print("\nReferential Integrity Validation Results:")
        print(f"Total phones generated: {validation_results['total_phones']}")
        print(f"Valid phones: {validation_results['valid_phones']}")
        print(f"Invalid phones: {validation_results['invalid_phones']}")
        
        if validation_results['missing_nodes']:
            print(f"\nMissing or invalid phone nodes: {len(validation_results['missing_nodes'])}")
            print("Sample of missing phone nodes:", list(validation_results['missing_nodes'])[:5])
        
        print("\nNode Type Statistics:")
        for node_type, stats in validation_results['node_type_stats'].items():
            print(f"\n{node_type.capitalize()} Nodes:")
            print(f"  Total: {stats['total']}")
            print(f"  Used in valid phones: {stats['valid']}")
        
        # Count phone numbers (basic statistics)
        print("\nPhone Data Summary:")
        print(f"Total unique phone numbers generated: {len(phone_data)}")
        
        print("\nPhone Data Generation Statistics:")
        print(f"Total number of phone nodes processed: {len(phone_data)}")
        print(f"Processing time: {processing_time:.2f} seconds")
        print(f"Phones per second: {len(phone_data) / processing_time:.2f}")
        print(f"Data saved to: {output_path}")
        
        return phone_data
        
    except Exception as e:
        print(f"Error generating mock phone data: {str(e)}")
        return None

if __name__ == "__main__":
    phone_data = generate_mock_phone_data()
    if phone_data is not None:
        print("\nSample of Generated Phone Data:")
        print(json.dumps(phone_data[:5], indent=2)) 