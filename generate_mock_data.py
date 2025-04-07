import pandas as pd
import uuid
import random
from datetime import datetime, timedelta
import json
from faker import Faker

# Initialize Faker
fake = Faker()

# Configuration
NUM_RECORDS = 1 # Number of records to generate

# Generate mock data
data = {
    'node_id': [str(uuid.uuid4()) for _ in range(NUM_RECORDS)],
    'node_type': ['person'] * NUM_RECORDS,
    'node_name': [f'Person_{i+1}' for i in range(NUM_RECORDS)],
    'node_properties': [
        {
            'NAME_FULL': fake.name(),
            'age': random.randint(20, 60),
            'occupation': random.choice(['Engineer', 'Doctor', 'Teacher', 'Artist', 'Writer']),
            'location': random.choice(['New York', 'London', 'Tokyo', 'Paris', 'Sydney']),
            'birth_date': (datetime.now() - timedelta(days=random.randint(20*365, 60*365))).strftime('%Y-%m-%d')
        } for _ in range(NUM_RECORDS)
    ]
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