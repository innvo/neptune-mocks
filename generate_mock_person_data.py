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

def generate_name_list(first_name, last_name):
    """Generate variations of a person's name"""
    name_list = [
        f"{first_name} {last_name}",
        f"{last_name}, {first_name}",
        f"{first_name[0]}. {last_name}",
        f"{last_name}, {first_name[0]}.",
        f"{first_name} {last_name[0]}.",
        f"{last_name[0]}. {first_name}"
    ]
    return name_list

def generate_birth_date_list(birth_date):
    """Generate variations of a birth date"""
    date_obj = datetime.strptime(birth_date, '%Y-%m-%d')
    date_list = [
        birth_date,  # YYYY-MM-DD
        date_obj.strftime('%m/%d/%Y'),  # MM/DD/YYYY
        date_obj.strftime('%d-%m-%Y'),  # DD-MM-YYYY
        date_obj.strftime('%Y%m%d'),  # YYYYMMDD
        date_obj.strftime('%m%d%Y'),  # MMDDYYYY
        date_obj.strftime('%d%m%Y')  # DDMMYYYY
    ]
    return date_list

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


def generate_mock_person_data():
    """Generate mock person data with realistic properties"""
    try:
        # Initialize Faker
        fake = Faker()
        
        # Read node_data.csv
        print("Reading node data...")
        node_df = pd.read_csv('node_data.csv')
        
        # Filter for person nodes
        person_nodes = node_df[node_df['node_type'] == 'person']
        print(f"Found {len(person_nodes)} person nodes")
        
        # Initialize data list
        data = []
        
        # Generate mock data for each person node
        print("\nGenerating mock person data...")
        for _, row in tqdm(person_nodes.iterrows(), total=len(person_nodes), desc="Processing person nodes"):
            # Generate realistic person data
            first_name = fake.first_name().upper
            last_name = fake.last_name().upper
            full_name = f"{first_name} {last_name}".upper()
            
            # Generate birth date (between 18 and 80 years ago)
            birth_date = fake.date_of_birth(minimum_age=18, maximum_age=80).strftime('%Y-%m-%d')
            
            # Generate SSN (format: XXX-XX-XXXX)
            ssn = f"{random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(1000, 9999)}"
            
            # Generate phone number
            phone = fake.phone_number()
            
            # Generate email
            email = fake.email()
            
            # Generate name and birth date lists
            name_list = generate_name_list(first_name, last_name)
            birth_date_list = generate_birth_date_list(birth_date)
            
            # Create node properties as a dictionary
            node_properties = {
                "NAME_FULL": full_name,
                "NAME_LIST": name_list,
                "BIRTH_DATE": birth_date,
                "BIRTH_DATE_LIST": birth_date_list,
                "SSN": ssn,
                "PHONE": phone,
                "EMAIL": email
            }
            
            # Convert to JSON string
            node_properties_json = json.dumps(node_properties)
            
            # Add to data list
            data.append({
                'node_id': row['node_id'],
                'node_name': full_name,
                'node_properties': node_properties_json
            })
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Save to CSV
        df.to_csv('mock_person_data.csv', index=False)
        
        # Print sample record
        print("\nSample Record:")
        sample = data[0]
        print(f"Node ID: {sample['node_id']}")
        print(f"Node Name: {sample['node_name']}")
        print("Node Properties:")
        print(json.dumps(json.loads(sample['node_properties']), indent=2))
        
        # Pretty print a random record
        pretty_print_random_record(df)
        
        print(f"\nGenerated {len(data)} person records")
        return True
        
    except Exception as e:
        print(f"Error generating mock person data: {str(e)}")
        return False

if __name__ == "__main__":
    generate_mock_person_data()

def generate_node_data():
    # Generate node data
    node_data = {
        'node_id': [str(uuid.uuid4()) for _ in range(NUM_RECORDS)],
        'node_type': [random.choice(NODE_TYPES) for _ in range(NUM_RECORDS)]
    }
    
    # Create DataFrame
    node_df = pd.DataFrame(node_data)
    
    # Save to CSV
    node_df.to_csv('xxx.csv', index=False)
    print("\nNode data saved to 'mock_person_data.csv'")
    
    return node_df

# Generate node data
node_df = generate_node_data()

# Display the node DataFrame
print("\nGenerated Node Data:")
print(node_df) 