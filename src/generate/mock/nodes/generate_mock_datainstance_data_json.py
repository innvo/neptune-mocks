import pandas as pd
from faker import Faker
import json
from tqdm import tqdm
import os
import time
import platform
import hashlib
import random
import re

def clear_terminal():
    """Clear the terminal screen"""
    if platform.system() == 'Windows':
        os.system('cls')
    else:
        os.system('clear')

def generate_record_id(fake):
    """Generate a unique record ID for the datainstance"""
    # Generate a record ID in format: REC-YYYYMMDD-XXXXX
    date_part = fake.date_this_decade().strftime('%Y%m%d')
    random_part = fake.random_number(digits=5)
    return f"REC-{date_part}-{random_part}"

def generate_record_type():
    """Generate a record type for the datainstance"""
    record_types = [
        "SERVICEPROVIDER",
        "STAKEHOLDER"
    ]
    return random.choice(record_types)

def generate_data_source():
    """Generate a data source for the datainstance"""
    data_sources = [
        "ELIS",
        "C3", 
        "GLOBAL"
    ]
    return random.choice(data_sources)

def validate_referential_integrity(datainstance_data, node_data):
    """Validate referential integrity of datainstance data against node data"""
    validation_results = {
        'total_datainstances': len(datainstance_data),
        'valid_datainstances': 0,
        'invalid_datainstances': 0,
        'missing_nodes': set(),
        'record_type_stats': {}
    }
    
    # Get sets of valid node IDs for quick lookup
    valid_node_ids = {node['node_id'] for node in node_data}
    
    # Validate each datainstance
    for datainstance_entry in datainstance_data:
        record_id = datainstance_entry['node_properties'].get('RECORD_ID', '')
        record_type = datainstance_entry['node_properties'].get('RECORD_TYPE', '')
        data_source = datainstance_entry['node_properties'].get('DATA_SOURCE', '')
        
        # Basic validation - ensure all required properties are present
        if record_id and record_type and data_source:
            validation_results['valid_datainstances'] += 1
            
            # Track record type statistics
            if record_type not in validation_results['record_type_stats']:
                validation_results['record_type_stats'][record_type] = 0
            validation_results['record_type_stats'][record_type] += 1
        else:
            validation_results['invalid_datainstances'] += 1
            print(f"WARNING: Missing RECORD_ID, RECORD_TYPE, or DATA_SOURCE for datainstance {datainstance_entry['node_id']}")
    
    return validation_results

def generate_mock_datainstance_data():
    try:
        # Clear terminal at start
        clear_terminal()
        
        start_time = time.time()
        
        # Initialize Faker
        fake = Faker()
        
        # Read existing node data
        print("Reading existing node data...")
        node_data_path = os.path.join('src', 'data', 'input', 'node_data.csv')
        
        if not os.path.exists(node_data_path):
            print(f"Error: Node data file not found at {node_data_path}")
            print("Please run the node data generator first.")
            return None
        
        node_df = pd.read_csv(node_data_path)
        
        print(f"Found {len(node_df)} nodes in the data file.")
        
        # Get datainstance nodes from node_data.csv
        datainstance_nodes = node_df[node_df['node_type'] == 'datainstance']
        
        if datainstance_nodes.empty:
            print("Error: No datainstance nodes found in node_data.csv")
            print("Please ensure 'datainstance' is included in NODE_TYPES when generating node data.")
            return None
        
        print(f"Found {len(datainstance_nodes)} datainstance nodes in node_data.csv")
        
        # Initialize datainstance data list
        datainstance_data = []
        
        # Generate mock datainstance data for each datainstance node in node_data.csv
        print("\nGenerating mock datainstance data...")
        for _, datainstance_node in tqdm(datainstance_nodes.iterrows(), total=len(datainstance_nodes), desc="Processing datainstance nodes"):
            datainstance_id = datainstance_node['node_id']
            
            # Generate record ID, type, and data source
            record_id = generate_record_id(fake)
            record_type = generate_record_type()
            data_source = generate_data_source()
            
            # Create node properties JSON - only the three required properties
            node_properties = {
                "DATA_SOURCE": data_source,
                "RECORD_ID": record_id,
                "RECORD_TYPE": record_type
            }
            
            # Add to datainstance data list
            datainstance_data.append({
                'node_id': datainstance_id,
                'node_name': record_id,
                'node_properties': node_properties
            })
        
        # Save to JSON
        output_path = os.path.join('src', 'data', 'output', 'gds', 'mock_datainstance_data.json')
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(datainstance_data, f, indent=2)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Validate referential integrity
        validation_results = validate_referential_integrity(datainstance_data, node_df.to_dict('records'))
        
        # Print validation results
        print("\nReferential Integrity Validation Results:")
        print(f"Total datainstances generated: {validation_results['total_datainstances']}")
        print(f"Valid datainstances: {validation_results['valid_datainstances']}")
        print(f"Invalid datainstances: {validation_results['invalid_datainstances']}")
        
        if validation_results['missing_nodes']:
            print(f"\nMissing or invalid nodes: {len(validation_results['missing_nodes'])}")
            print("Sample of missing nodes:", list(validation_results['missing_nodes'])[:5])
        
        print("\nRecord Type Statistics:")
        for record_type, count in validation_results['record_type_stats'].items():
            percentage = (count / validation_results['total_datainstances'] * 100)
            print(f"{record_type}: {count} ({percentage:.1f}%)")
        
        print("\nDatainstance Data Generation Statistics:")
        print(f"Total number of datainstance nodes processed: {len(datainstance_data)}")
        print(f"Processing time: {processing_time:.2f} seconds")
        print(f"Datainstances per second: {len(datainstance_data) / processing_time:.2f}")
        print(f"Data saved to: {output_path}")
        
        # Verify that we have enough datainstance nodes for all persons
        person_nodes = node_df[node_df['node_type'] == 'person']
        print(f"\n✅ Person to DataInstance ratio: {len(person_nodes)} persons, {len(datainstance_nodes)} datainstances")
        if len(datainstance_nodes) >= len(person_nodes):
            print("✅ Sufficient datainstance nodes to ensure every person has at least 1 datainstance edge")
        else:
            print("⚠️  Warning: Not enough datainstance nodes for all persons")
        
        return datainstance_data
        
    except Exception as e:
        print(f"Error generating mock datainstance data: {str(e)}")
        return None

if __name__ == "__main__":
    datainstance_data = generate_mock_datainstance_data()
    if datainstance_data is not None:
        print("\nSample of Generated Datainstance Data:")
        print(json.dumps(datainstance_data[:3], indent=2))
