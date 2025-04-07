import pandas as pd
import uuid
import random
from datetime import datetime, timedelta
import json
from faker import Faker

# Initialize Faker
fake = Faker()

# Configuration
NUM_RECORDS = 2  # Number of records to generate

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
        'BIRTH_DATE': primary_birth_date,
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

# Generate mock data
data = {
    'node_id': [str(uuid.uuid4()) for _ in range(NUM_RECORDS)],
    'node_type': ['PERSON'] * NUM_RECORDS,
    'node_name': [f'PERSON_{i+1}' for i in range(NUM_RECORDS)],
    'node_properties': [create_node_properties() for _ in range(NUM_RECORDS)]
}

# Create DataFrame
df = pd.DataFrame(data)

# Display the DataFrame
print("\nGenerated Mock Data:")
print(df)

# Pretty print node_properties
print("\nNode Properties (JSON):")
for i, props in enumerate(df['node_properties']):
    print(f"\nPerson {i+1}:")
    print(json.dumps(props, indent=2))

# Save to CSV
df.to_csv('mock_person_data.csv', index=False)
print("\nData saved to 'mock_person_data.csv'")

def generate_node_data():
    # Generate node data
    node_data = {
        'node_id': [str(uuid.uuid4()) for _ in range(NUM_NODE_RECORDS)],
        'node_type': [random.choice(NODE_TYPES) for _ in range(NUM_NODE_RECORDS)]
    }
    
    # Create DataFrame
    node_df = pd.DataFrame(node_data)
    
    # Save to CSV
    node_df.to_csv('node_data.csv', index=False)
    print("\nNode data saved to 'node_data.csv'")
    
    return node_df

# Generate node data
node_df = generate_node_data()

# Display the node DataFrame
print("\nGenerated Node Data:")
print(node_df) 