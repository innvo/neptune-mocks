import json
import random
from faker import Faker

# Configuration
RECORD_COUNT = 1000

fake = Faker()
Faker.seed(42)

def generate_person(person_id):
    return {
        "id": f"person-{person_id}",
        "type": "person",
        "names": [fake.name() for _ in range(10)],
        "aliases": [fake.user_name() for _ in range(10)],
        "emails": [fake.email() for _ in range(10)],
        "phones": [fake.phone_number() for _ in range(10)],
        "addresses": [
            {
                "id": f"addr-{person_id}-{i}",
                "street": fake.street_address(),
                "city": fake.city(),
                "state": fake.state(),
                "zip": fake.zipcode()
            }
            for i in range(10)
        ]
    }

def generate_bulk_person_data(count=1000, output_file="src/data/output/opensearch/person-bulk.json"):
    with open(output_file, "w") as f:
        for i in range(count):
            person = generate_person(i)
            action = {"index": {"_index": "people", "_id": person["id"]}}
            f.write(json.dumps(action) + "\n")
            f.write(json.dumps(person) + "\n")

    print(f"{count} records written to {output_file}")

if __name__ == "__main__":
    generate_bulk_person_data(count=RECORD_COUNT)
