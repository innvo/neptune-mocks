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
    """Generate random variations of a person's name with NAME_FIRST and NAME_LAST labels"""
    # Create unique variations
    variations = [
        {
            'NAME_FIRST': first_name,
            'NAME_LAST': last_name
        },
        {
            'NAME_FIRST': f"{first_name[0]}.",
            'NAME_LAST': last_name
        },
        {
            'NAME_FIRST': first_name,
            'NAME_LAST': f"{last_name[0]}."
        }
    ]
    
    # Always include the first variation (full name)
    name_list = [variations[0]]
    
    # Randomly select 0-2 additional variations
    num_additional = random.randint(0, 2)
    if num_additional > 0:
        additional_variations = random.sample(variations[1:], num_additional)
        name_list.extend(additional_variations)
    
    return name_list

def generate_birth_date_list(birth_date):
    """Generate 1-3 variations of a birth date in mm-dd-yyyy format, including the original date"""
    date_obj = datetime.strptime(birth_date, '%Y-%m-%d')
    original_date = date_obj.strftime('%m-%d-%Y')  # Convert original to mm-dd-yyyy
    
    # Generate two additional dates by adding/subtracting random days (within 5 days)
    potential_dates = [
        (date_obj + timedelta(days=random.randint(1, 5))).strftime('%m-%d-%Y'),
        (date_obj - timedelta(days=random.randint(1, 5))).strftime('%m-%d-%Y')
    ]
    
    # Always include the original date
    date_list = [original_date]
    
    # Randomly add 0-2 more dates
    num_additional = random.randint(0, 2)
    if num_additional > 0:
        date_list.extend(random.sample(potential_dates, num_additional))
    
    return date_list

def create_node_properties():
    """Create node properties with realistic data"""
    # Generate primary name components
    primary_first = fake.first_name().upper()
    primary_last = fake.last_name().upper()
    
    # Generate primary birth date (between 18 and 80 years ago)
    primary_birth_date = (datetime.now() - timedelta(days=random.randint(18*365, 80*365))).strftime('%Y-%m-%d')
    
    # Create name list and birth date list
    name_list = generate_name_list(primary_first, primary_last)
    birth_date_list = generate_birth_date_list(primary_birth_date)
    
    # Create the properties dictionary
    return {
        'NAME_FULL': f"{primary_first} {primary_last}",
        'NAME_LIST': name_list,
        'BIRTH_DATE': primary_birth_date,
        'BIRTH_DATE_LIST': birth_date_list
    }

def generate_mock_person_data():
    """Generate mock person data with realistic properties"""
    try:
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
            # Get node properties
            node_properties = create_node_properties()
            
            # Add to data list
            data.append({
                'node_id': row['node_id'],
                'node_name': node_properties['NAME_FULL'],
                'node_properties': json.dumps(node_properties).replace('"', "'")
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
        print(json.dumps(json.loads(sample['node_properties'].replace("'", '"')), indent=2))
        
        print(f"\nGenerated {len(data)} person records")
        return True
        
    except Exception as e:
        print(f"Error generating mock person data: {str(e)}")
        return False

if __name__ == "__main__":
    generate_mock_person_data()

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
        primary_first = fake.first_name().upper()
        primary_last = fake.last_name().upper()
        full_name = f"{primary_first} {primary_last}"
        
        # Generate primary birth date
        primary_birth_date = (datetime.now() - timedelta(days=random.randint(20*365, 60*365))).strftime('%Y-%m-%d')
        
        # Create name list and birth date list
        name_list = generate_name_list(primary_first, primary_last)
        birth_date_list = generate_birth_date_list(primary_birth_date)
        
        # Create the properties dictionary
        properties = {
            'NAME_FULL': full_name,
            'NAME_LIST': name_list,
            'BIRTH_DATE': primary_birth_date,
            'BIRTH_DATE_LIST': birth_date_list
        }
        
        # Add to node data
        node_data['node_name'].append(full_name)
        node_data['node_properties'].append(json.dumps(properties))
    
    # Create DataFrame
    node_df = pd.DataFrame(node_data)
    
    # Save to CSV
    node_df.to_csv('mock_person_data.csv', index=False)
    print("\nNode data saved to 'mock_person_data.csv'")
    
    return node_df

# Generate node data
node_df = generate_node_data()

# Display the node DataFrame
print("\nGenerated Node Data:")
print(node_df) 