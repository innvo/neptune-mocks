import pandas as pd
import uuid
import random
from datetime import datetime, timedelta
import json
from faker import Faker
from tqdm import tqdm

# Initialize Faker
fake = Faker()

# Read node_data.csv and count person records
try:
    node_df = pd.read_csv('node_data.csv')
    NUM_RECORDS = len(node_df[node_df['node_type'] == 'person'])
    print(f"\nFound {NUM_RECORDS} person records in node_data.csv")
except Exception as e:
    print(f"Error reading node_data.csv: {str(e)}")
    NUM_RECORDS = 0  # Default to 0 if file not found or error

if NUM_RECORDS == 0:
    print("No person records found or error reading file. Exiting.")
    exit()

NODE_TYPES = ['person']

def generate_name_list(primary_first, primary_last):
    # Start with the primary name
    name_list = [{
        'NAME_FIRST': primary_first.upper(),
        'NAME_LAST': primary_last.upper(),
        'NAME_TYPE': 'PRIMARY'
    }]
    
    # Generate 1 to 5 additional names
    num_primary_other = random.randint(1, 5)
    for _ in range(num_primary_other):
        name_list.append({
            'NAME_FIRST': fake.first_name().upper(),
            'NAME_LAST': fake.last_name().upper(),
            'NAME_TYPE': 'PRIMARY'
        })
    
    return name_list

def generate_birth_date_list(primary_birth_date):
    # Start with the primary birth date
    birth_date_list = [{
        'BIRTH_DATE': primary_birth_date
    }]
    
    # Generate 1 to 5 additional birth dates
    num_primary_other = random.randint(0, 3)
    for _ in range(num_primary_other):
        # Generate a date within 5 years of the primary birth date
        days_offset = random.randint(-5*365, 5*365)
        additional_date = (datetime.strptime(primary_birth_date, '%Y-%m-%d') + timedelta(days=days_offset)).strftime('%Y-%m-%d')
        birth_date_list.append({
            'BIRTH_DATE': additional_date
        })
    
    return birth_date_list

def create_node_properties():
    # Generate primary name components
    primary_first = fake.first_name()
    primary_last = fake.last_name()
    
    # Generate primary birth date
    primary_birth_date = (datetime.now() - timedelta(days=random.randint(20*365, 60*365))).strftime('%Y-%m-%d')
    
    # Create name list and birth date list
    name_list = generate_name_list(primary_first, primary_last)
    birth_date_list = generate_birth_date_list(primary_birth_date)
    
    # Create the properties dictionary with NAME_FULL first
    return {
        'NAME_FULL': f"{primary_first.upper()} {primary_last.upper()}",
        'NAME_LIST': name_list,
        'BIRTH_DATE': primary_birth_date,
        'BIRTH_DATE_LIST': birth_date_list
    }

def pretty_print_random_record(df):
    """Pretty print a random record from the DataFrame"""
    if len(df) == 0:
        print("No records to display")
        return
    
    # Select a random record
    random_record = df.sample(1).iloc[0]
    
    print("\nRandom Record Sample:")
    print("=" * 80)
    print(f"Node ID: {random_record['node_id']}")
    print(f"Node Name: {random_record['node_name']}")
    print("\nNode Properties:")
    print("-" * 40)
    # Parse and pretty print the JSON
    try:
        props = json.loads(random_record['node_properties'])
        print(json.dumps(props, indent=2))
    except json.JSONDecodeError:
        print("Invalid JSON format")
    print("=" * 80)

def generate_mock_person_data():
    try:
        # Initialize Faker
        fake = Faker()
        
        # Read node_data.csv to get person nodes
        print("Reading node data...")
        node_df = pd.read_csv('node_data.csv', usecols=['node_id', 'node_type'])
        
        # Filter for person nodes
        person_nodes = node_df[node_df['node_type'] == 'person']
        if person_nodes.empty:
            print("Warning: No person nodes found in node_data.csv")
            return None
        
        # Initialize data list
        person_data = []
        
        # Generate mock data for each person node
        print("\nGenerating mock person data...")
        for _, node in tqdm(person_nodes.iterrows(), total=len(person_nodes), desc="Processing person nodes"):
            node_id = node['node_id']
            
            # Generate fake data
            full_name = fake.name().upper()  # Convert to uppercase as per requirements
            birth_date = fake.date_of_birth(minimum_age=18, maximum_age=90).strftime('%Y-%m-%d')
            # ssn = fake.ssn()
            # phone = fake.phone_number()
            # email = fake.email()
            
            # Split full name into first and last
            first_name, last_name = full_name.split(' ', 1)
            
            # Create node properties JSON with double quotes
            node_properties = {
                "NAME_FULL": full_name,
                "NAME_LIST": generate_name_list(first_name, last_name),
                "BIRTH_DATE": birth_date,
                "BIRTH_DATE_LIST": generate_birth_date_list(birth_date)
            }
            
            # Convert to JSON string with double quotes
            node_properties_json = json.dumps(node_properties)
            
            # Add to data list
            person_data.append({
                'node_id': node_id,
                'node_name': full_name,
                'node_properties': node_properties_json
            })
        
        # Create DataFrame
        person_df = pd.DataFrame(person_data)
        
        # Save to CSV
        person_df.to_csv('mock_person_data.csv', index=False)
        
        # Print statistics
        print("\nPerson Data Generation Statistics:")
        print(f"Total number of person nodes processed: {len(person_data)}")
        print("\nSample of Generated Person Data:")
        print(person_df.head())
        
        # Pretty print a random record
        pretty_print_random_record(person_df)
        
        return person_df
        
    except Exception as e:
        print(f"Error generating mock person data: {str(e)}")
        return None

if __name__ == "__main__":
    person_df = generate_mock_person_data()

def generate_node_data():
    # Generate node data
    node_data = {
        'node_id': [str(uuid.uuid4()) for _ in range(NUM_RECORDS)],
        'node_type': [random.choice(NODE_TYPES) for _ in range(NUM_RECORDS)]
    }
    
    # Create DataFrame
    node_df = pd.DataFrame(node_data)
    
    # Save to CSV
    node_df.to_csv('node_data.csv', index=False)
    print("\nNode data saved to 'mock_person_data.csv'")
    
    return node_df

# Generate node data
node_df = generate_node_data()

# Display the node DataFrame
print("\nGenerated Node Data:")
print(node_df) 