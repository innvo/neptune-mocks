import pandas as pd
import uuid
import random
from datetime import datetime, timedelta
import json
from faker import Faker
from tqdm import tqdm
import os
import time
import platform

# Initialize Faker
fake = Faker()

# Ensure the data/output directory exists
os.makedirs('data/output', exist_ok=True)

# Read node_data.csv and count person records
try:
    node_df = pd.read_csv('src/data/input/node_data.csv')
    NUM_RECORDS = len(node_df[node_df['node_type'] == 'person'])
    print(f"\nFound {NUM_RECORDS} person records in src/data/input/node_data.csv")
except Exception as e:
    print(f"Error reading data/input/node_data.csv: {str(e)}")
    NUM_RECORDS = 0  # Default to 0 if file not found or error

if NUM_RECORDS == 0:
    print("No person records found or error reading file. Exiting.")
    exit()

NODE_TYPES = ['person']

def clear_terminal():
    """Clear the terminal screen"""
    if platform.system() == 'Windows':
        os.system('cls')
    else:
        os.system('clear')

def validate_referential_integrity(person_data, node_df):
    """Validate referential integrity of person data against node data"""
    validation_results = {
        'total_persons': len(person_data),
        'valid_persons': 0,
        'invalid_persons': 0,
        'missing_nodes': set(),
        'node_type_stats': {
            'person': {'total': 0, 'valid': 0}
        }
    }
    
    # Get sets of valid node IDs for quick lookup
    valid_node_ids = set(node_df['node_id'].values)
    person_node_ids = set(node_df[node_df['node_type'] == 'person']['node_id'].values)
    
    for person_entry in person_data:
        node_id = person_entry['node_id']
        
        # Validate node existence and type
        node_exists = node_id in valid_node_ids
        is_person_node = node_id in person_node_ids
        
        if node_exists and is_person_node:
            validation_results['valid_persons'] += 1
            validation_results['node_type_stats']['person']['valid'] += 1
        else:
            validation_results['invalid_persons'] += 1
            if not node_exists or not is_person_node:
                validation_results['missing_nodes'].add(node_id)
    
    # Update total counts
    validation_results['node_type_stats']['person']['total'] = len(person_node_ids)
    
    return validation_results

def generate_name_list(first_name, last_name):
    """Generate variations of a person's name"""
    name_variations = [
        f"{first_name} {last_name}",
        f"{last_name}, {first_name}",
        f"{first_name[0]}. {last_name}",
        f"{last_name}, {first_name[0]}.",
        f"{first_name} {last_name[0]}.",
        f"{last_name[0]}. {first_name}"
    ]
    # Join all variations with semicolons
    return ';'.join(name.upper() for name in name_variations)

def generate_birth_date_list(birth_date):
    """Generate variations of a birth date, with slight variations"""
    date_obj = datetime.strptime(birth_date, '%Y-%m-%d')
    # Create variations by adding/subtracting a few days
    variations = [
        date_obj,  # Original date
        date_obj + timedelta(days=1),  # +1 day
        date_obj - timedelta(days=1),  # -1 day
        date_obj + timedelta(days=2),  # +2 days
        date_obj - timedelta(days=2),  # -2 days
        date_obj + timedelta(days=3)   # +3 days
    ]
    return [date.strftime('%Y-%m-%d').upper() for date in variations]

def generate_anumber_list():
    """Generate a list of anumbers (0-3 anumbers per person)"""
    # Randomly decide how many anumbers this person has (0-3)
    num_anumbers = random.randint(0, 3)
    if num_anumbers == 0:
        return []
    
    # Generate the specified number of unique anumbers
    anumbers = set()
    while len(anumbers) < num_anumbers:
        # Generate a 10-digit number as a string
        anumber = ''.join([str(random.randint(0, 9)) for _ in range(10)])
        anumbers.add(anumber)
    
    return list(anumbers)

def select_primary_anumber(anumber_list):
    """Select a primary anumber from the anumber list"""
    if not anumber_list:
        return None
    return random.choice(anumber_list)

def create_node_properties():
    # Generate primary name components
    primary_first = fake.first_name()
    primary_last = fake.last_name()
    
    # Generate primary birth date
    primary_birth_date = (datetime.now() - timedelta(days=random.randint(20*365, 60*365))).strftime('%Y-%m-%d')
    
    # Create name list and birth date list
    name_full_list = generate_name_list(primary_first, primary_last)
    birth_date_list = generate_birth_date_list(primary_birth_date)
    
    # Generate anumber list and select primary anumber
    anumber_list = generate_anumber_list()
    primary_anumber = select_primary_anumber(anumber_list)
    
    # Create the properties dictionary
    return {
        'NAME_FULL': f"{primary_first.upper()} {primary_last.upper()}",
        'NAME_FULL_LIST': name_full_list,
        'BIRTH_DATE': primary_birth_date,
        'BIRTH_DATE_LIST': birth_date_list,
        'ANUMBER_PRIMARY': primary_anumber,
        'ANUMBER_LIST': anumber_list
   
    }

def generate_mock_person_data():
    """Generate mock person data with realistic properties"""
    try:
        # Clear terminal at start
        clear_terminal()
        
        start_time = time.time()
        
        # Initialize Faker
        fake = Faker()
        
        # Read node_data.csv
        print("Reading node data...")
        node_df = pd.read_csv('src/data/input/node_data.csv')
        
        # Print node type statistics
        print("\nNode Type Statistics:")
        print(f"Total number of nodes: {len(node_df)}")
        node_counts = node_df['node_type'].value_counts()
        for node_type, count in node_counts.items():
            print(f"{node_type}: {count} nodes")
        
        # Filter for person nodes
        person_nodes = node_df[node_df['node_type'] == 'person']
        print(f"Found {len(person_nodes)} person nodes")
        
        if person_nodes.empty:
            print("Warning: No person nodes found in node_data.csv")
            return None
        
        # Initialize data list
        data = []
        
        # Generate mock data for each person node
        print("\nGenerating mock person data...")
        for _, row in tqdm(person_nodes.iterrows(), total=len(person_nodes), desc="Processing person nodes"):
            # Generate realistic person data
            first_name = fake.first_name().upper()
            last_name = fake.last_name().upper()
            full_name = f"{first_name} {last_name}"
            
            # Generate birth date (between 18 and 80 years ago)
            birth_date = fake.date_of_birth(minimum_age=18, maximum_age=80).strftime('%Y-%m-%d').upper()
            
            # Generate name and birth date lists
            name_full_list = generate_name_list(first_name, last_name)
            birth_date_list = generate_birth_date_list(birth_date)
            
            # Generate anumber list and select primary anumber
            anumber_list = generate_anumber_list()
            anumber_primary = select_primary_anumber(anumber_list)
            
            # Create node properties as a dictionary
            node_properties = {
                "NAME_FULL": full_name,
                "NAME_FULL_LIST": name_full_list,
                "BIRTH_DATE": birth_date,
                "BIRTH_DATE_LIST": birth_date_list,
                "ANUMBER_PRIMARY": anumber_primary,
                "ANUMBER_LIST": anumber_list,
            }
            
            # Add to data list
            data.append({
                'node_id': row['node_id'],
                'node_name': full_name,
                'node_properties': node_properties
            })
        
        # Save to JSON file
        output_path = 'src/data/output/gds/mock_person_data.json'
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Validate referential integrity
        validation_results = validate_referential_integrity(data, node_df)
        
        # Print validation results
        print("\nReferential Integrity Validation Results:")
        print(f"Total persons generated: {validation_results['total_persons']}")
        print(f"Valid persons: {validation_results['valid_persons']}")
        print(f"Invalid persons: {validation_results['invalid_persons']}")
        
        if validation_results['missing_nodes']:
            print(f"\nMissing or invalid person nodes: {len(validation_results['missing_nodes'])}")
            print("Sample of missing person nodes:", list(validation_results['missing_nodes'])[:5])
        
        print("\nNode Type Statistics:")
        for node_type, stats in validation_results['node_type_stats'].items():
            print(f"\n{node_type.capitalize()} Nodes:")
            print(f"  Total: {stats['total']}")
            print(f"  Used in valid persons: {stats['valid']}")
        
        print("\nPerson Data Generation Statistics:")
        print(f"Total number of person nodes processed: {len(data)}")
        print(f"Processing time: {processing_time:.2f} seconds")
        print(f"Persons per second: {len(data) / processing_time:.2f}")
        print(f"Data saved to: {output_path}")
        
        return data
        
    except Exception as e:
        print(f"Error generating mock person data: {str(e)}")
        return None

if __name__ == "__main__":
    # Clear terminal before starting
    clear_terminal()
    person_data = generate_mock_person_data()
    if person_data is not None:
        print("\nSample of Generated Person Data:")
        print(json.dumps(person_data[:5], indent=2))

def generate_node_data():
    # Initialize Faker
    fake = Faker()
    
    # Generate node data
    node_data = {
        'node_id': [str(uuid.uuid4()) for _ in range(NUM_RECORDS)],
        'node_type': [random.choice(NODE_TYPES) for _ in range(NUM_RECORDS)],
        'node_name': [],
        'node_properties': []
    }
    
    # Generate properties for each node
    for _ in range(NUM_RECORDS):
        # Generate primary name components
        primary_first = fake.first_name()
        primary_last = fake.last_name()
        full_name = f"{primary_first.upper()} {primary_last.upper()}"
        
        # Generate primary birth date
        primary_birth_date = (datetime.now() - timedelta(days=random.randint(20*365, 60*365))).strftime('%Y-%m-%d')
        
        # Create name list and birth date list
        name_full_list = generate_name_list(primary_first, primary_last)
        birth_date_list = generate_birth_date_list(primary_birth_date)
        
        # Create the properties dictionary
        properties = {
            'NAME_FULL': full_name,
            'NAME_FULL_LIST': name_full_list,
            'BIRTH_DATE': primary_birth_date,
            'BIRTH_DATE_LIST': birth_date_list
        }
        
        # Add to node data
        node_data['node_name'].append(full_name)
        node_data['node_properties'].append(properties)  # Store as dictionary instead of JSON string
    
    # Create DataFrame
    node_df = pd.DataFrame(node_data)
    
    return node_df

# Generate node data
node_df = generate_node_data()

# Display the node DataFrame
print("\nGenerated Node Data:")
print(node_df) 