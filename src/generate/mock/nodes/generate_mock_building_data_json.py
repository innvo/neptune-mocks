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

def filter_building_addresses(address_data):
    """Filter out addresses that contain units, suites, floors, etc. and remove STREET_ADDRESS_LINE2"""
    # Regex patterns to match addresses with units, suites, floors, etc.
    unit_patterns = [
        r'\bSUITE\b',
        r'\bAPT\.?\b',
        r'\bUNIT\b',
        r'\bFLOOR\b',
        r'\bROOM\b',
        r'\bBUILDING\b'
    ]
    
    # Combine patterns with OR operator
    combined_pattern = '|'.join(unit_patterns)
    
    filtered_addresses = []
    
    for address_entry in address_data:
        address_props = address_entry['node_properties']
        
        # Check if any address field contains unit patterns
        address_full = address_props.get('ADDRESS_FULL', '')
        street_line1 = address_props.get('STREET_ADDRESS_LINE1', '')
        street_line2 = address_props.get('STREET_ADDRESS_LINE2', '')
        
        # Check if any field contains unit patterns
        if re.search(combined_pattern, address_full, re.IGNORECASE):
            continue
        
        # Create a copy of the address properties without STREET_ADDRESS_LINE2
        filtered_props = {k: v for k, v in address_props.items() if k != 'STREET_ADDRESS_LINE2'}
        
        # Create filtered address entry
        filtered_entry = {
            'node_id': address_entry['node_id'],
            'node_name': address_entry['node_name'],
            'node_properties': filtered_props
        }
        
        filtered_addresses.append(filtered_entry)
    
    return filtered_addresses

def generate_unique_building_id(existing_node_ids, fake):
    """Generate a unique building node_id that doesn't conflict with existing address node_ids"""
    max_attempts = 1000
    for _ in range(max_attempts):
        building_id = fake.uuid4()
        if building_id not in existing_node_ids:
            return building_id
    
    # If we can't generate a unique UUID after many attempts, use a different approach
    import time
    timestamp = int(time.time() * 1000000)  # Microsecond timestamp
    random_suffix = fake.random_int(min=1000, max=9999)
    return f"building-{timestamp}-{random_suffix}"

def validate_referential_integrity(building_data, address_data):
    """Validate referential integrity of building data against address data"""
    validation_results = {
        'total_buildings': len(building_data),
        'valid_buildings': 0,
        'invalid_buildings': 0,
        'missing_addresses': set(),
        'address_hash_mismatches': 0,
        'address_stats': {
            'total': len(address_data),
            'used_in_buildings': 0,
            'unused': 0
        }
    }
    
    # Get sets of valid address IDs for quick lookup
    valid_address_ids = {addr['node_id'] for addr in address_data}
    used_address_ids = set()
    
    # Validate each building against the original address data
    for building_entry in building_data:
        building_address_full = building_entry['node_properties'].get('ADDRESS_FULL', '')
        building_address_hash = building_entry['node_properties'].get('ADDRESS_HASH', '')
        
        # Find matching address in original data
        matching_address = None
        for addr in address_data:
            if addr['node_properties'].get('ADDRESS_FULL', '') == building_address_full:
                matching_address = addr
                break
        
        if matching_address:
            validation_results['valid_buildings'] += 1
            
            # Check if ADDRESS_HASH matches
            original_address_hash = matching_address['node_properties'].get('ADDRESS_HASH', '')
            if building_address_hash == original_address_hash:
                validation_results['address_stats']['used_in_buildings'] += 1
            else:
                validation_results['address_hash_mismatches'] += 1
                print(f"WARNING: ADDRESS_HASH mismatch for building {building_entry['node_id']}")
                print(f"  Building ADDRESS_HASH: {building_address_hash}")
                print(f"  Original ADDRESS_HASH: {original_address_hash}")
        else:
            validation_results['invalid_buildings'] += 1
    
    # Update address statistics
    validation_results['address_stats']['unused'] = len(valid_address_ids) - validation_results['address_stats']['used_in_buildings']
    
    return validation_results

def generate_mock_building_data():
    try:
        # Clear terminal at start
        clear_terminal()
        
        start_time = time.time()
        
        # Initialize Faker
        fake = Faker()
        
        # Read existing address data
        print("Reading existing address data...")
        address_data_path = os.path.join('src', 'data', 'output', 'gds', 'mock_address_data.json')
        
        if not os.path.exists(address_data_path):
            print(f"Error: Address data file not found at {address_data_path}")
            print("Please run the address data generator first.")
            return None
        
        with open(address_data_path, 'r') as f:
            address_data = json.load(f)
        
        print(f"Found {len(address_data)} addresses in the data file.")
        
        # Filter out addresses with units, suites, floors, etc. and remove STREET_ADDRESS_LINE2
        print("Filtering addresses to exclude units, suites, floors, etc...")
        filtered_address_data = filter_building_addresses(address_data)
        
        print(f"After filtering: {len(filtered_address_data)} addresses available for buildings")
        print(f"Filtered out {len(address_data) - len(filtered_address_data)} addresses with units/suites/floors")
        
        if len(filtered_address_data) == 0:
            print("Error: No addresses available after filtering. Cannot create building nodes.")
            return None
        
        # Get all existing node_ids to ensure uniqueness
        existing_node_ids = {addr['node_id'] for addr in address_data}
        print(f"Found {len(existing_node_ids)} existing node_ids to avoid conflicts")
        
        # Determine how many buildings to create (random number between 10% and 50% of filtered addresses)
        min_buildings = max(1, int(len(filtered_address_data) * 0.1))  # At least 10% of addresses
        max_buildings = int(len(filtered_address_data) * 0.5)  # Up to 50% of addresses
        num_buildings = random.randint(min_buildings, max_buildings)
        
        print(f"\nGenerating {num_buildings} building nodes (randomly selected from {len(filtered_address_data)} filtered addresses)")
        
        # Randomly select addresses to create buildings for
        selected_addresses = random.sample(filtered_address_data, num_buildings)
        
        # Initialize building data list
        building_data = []
        
        # Generate mock building data for selected addresses
        print("\nGenerating mock building data...")
        for address_entry in tqdm(selected_addresses, desc="Processing building nodes"):
            address_id = address_entry['node_id']
            address_props = address_entry['node_properties']
            
            # Generate unique building ID that doesn't conflict with existing address node_ids
            building_id = generate_unique_building_id(existing_node_ids, fake)
            
            # Use the street address line 1 as the building name
            building_full_name = address_props.get('STREET_ADDRESS_LINE1', 'UNKNOWN ADDRESS')
            
            # Create node properties JSON - copy address properties including ADDRESS_HASH
            node_properties = address_props.copy()
            
            # Ensure ADDRESS_HASH is preserved from the original address
            if 'ADDRESS_HASH' in address_props:
                node_properties['ADDRESS_HASH'] = address_props['ADDRESS_HASH']
            
            # Add to building data list
            building_data.append({
                'node_id': building_id,
                'node_name': building_full_name,
                'node_properties': node_properties
            })
        
        # Save to JSON
        output_path = os.path.join('src', 'data', 'output', 'gds', 'mock_building_data.json')
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(building_data, f, indent=2)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Validate referential integrity
        validation_results = validate_referential_integrity(building_data, filtered_address_data)
        
        # Print validation results
        print("\nReferential Integrity Validation Results:")
        print(f"Total buildings generated: {validation_results['total_buildings']}")
        print(f"Valid buildings: {validation_results['valid_buildings']}")
        print(f"Invalid buildings: {validation_results['invalid_buildings']}")
        print(f"ADDRESS_HASH mismatches: {validation_results['address_hash_mismatches']}")
        
        if validation_results['missing_addresses']:
            print(f"\nMissing or invalid addresses: {len(validation_results['missing_addresses'])}")
            print("Sample of missing addresses:", list(validation_results['missing_addresses'])[:5])
        
        print("\nAddress Usage Statistics:")
        print(f"Total addresses available: {validation_results['address_stats']['total']}")
        print(f"Addresses used in buildings: {validation_results['address_stats']['used_in_buildings']}")
        print(f"Unused addresses: {validation_results['address_stats']['unused']}")
        print(f"Usage percentage: {(validation_results['address_stats']['used_in_buildings'] / validation_results['address_stats']['total'] * 100):.1f}%")
        
        print("\nBuilding Data Generation Statistics:")
        print(f"Total number of building nodes processed: {len(building_data)}")
        print(f"Processing time: {processing_time:.2f} seconds")
        print(f"Buildings per second: {len(building_data) / processing_time:.2f}")
        print(f"Data saved to: {output_path}")
        
        return building_data
        
    except Exception as e:
        print(f"Error generating mock building data: {str(e)}")
        return None

if __name__ == "__main__":
    building_data = generate_mock_building_data()
    if building_data is not None:
        print("\nSample of Generated Building Data:")
        print(json.dumps(building_data[:3], indent=2))
