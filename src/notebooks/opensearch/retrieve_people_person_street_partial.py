## Retrieve people by partial street name

import subprocess
import json

# Partial street name to search for (you can change this to any partial street name you want to find)
partial_street = "93391 Phillip Ridges" 

# First, let's check if the index exists and what's in it
print("Checking if the 'people' index exists...")
index_check = subprocess.run([
    'curl', '-X', 'GET', 
    'http://localhost:9200/_cat/indices?v'
], capture_output=True, text=True)

print("Available indices:")
print(index_check.stdout)
print("="*50)

# Get total count of documents in people index
print("Getting total document count...")
count_result = subprocess.run([
    'curl', '-X', 'GET', 
    'http://localhost:9200/people/_count'
], capture_output=True, text=True)

try:
    count_response = json.loads(count_result.stdout)
    print(f"Total documents in 'people' index: {count_response.get('count', 0)}")
except:
    print("Could not get document count")

print("="*50)

# First, let's get a sample document to see the structure
print("Getting a sample document to check structure...")
sample_query = {
    "query": {
        "match_all": {}
    },
    "_source": True,
    "size": 1
}

sample_result = subprocess.run([
    'curl', '-X', 'POST', 
    'http://localhost:9200/people/_search',
    '-H', 'Content-Type: application/json',
    '-d', json.dumps(sample_query)
], capture_output=True, text=True)

try:
    sample_response = json.loads(sample_result.stdout)
    if 'hits' in sample_response and 'hits' in sample_response['hits'] and sample_response['hits']['hits']:
        print("Sample document structure:")
        print(json.dumps(sample_response['hits']['hits'][0]['_source'], indent=2))
        print("\n" + "="*50 + "\n")
    else:
        print("No documents found in the index")
        print("Sample response:", json.dumps(sample_response, indent=2))
except:
    print("Could not get sample document")
    print("Raw response:", sample_result.stdout)

# Query to get people by partial street name match
query = {
    "query": {
        "bool": {
            "should": [
                {
                    "nested": {
                        "path": "addresses",
                        "query": {
                            "match_phrase": {
                                "addresses.street": partial_street
                            }
                        }
                    }
                },
                {
                    "match_phrase": {
                        "addresses.street": partial_street
                    }
                }
            ]
        }
    },
    "_source": True,
    "size": 10
}

print(f"Executing query for partial street name: '{partial_street}'")
print("Query being sent:")
print(json.dumps(query, indent=2))
print("="*50)

result = subprocess.run([
    'curl', '-X', 'POST', 
    'http://localhost:9200/people/_search',
    '-H', 'Content-Type: application/json',
    '-d', json.dumps(query)
], capture_output=True, text=True)

# Parse and display the response
try:
    response_json = json.loads(result.stdout)
    
    if 'hits' in response_json and 'hits' in response_json['hits']:
        hits = response_json['hits']['hits']
        if hits:
            print(f"Found {len(hits)} record(s) for partial street name '{partial_street}':")
            print("=" * 50)
            
            for i, hit in enumerate(hits, 1):
                print(f"\nRecord {i}:")
                print(json.dumps(hit['_source'], indent=2))
                print("-" * 30)
        else:
            print(f"No records found for partial street name '{partial_street}'")
            print("Response:", json.dumps(response_json, indent=2))
    else:
        print("Unexpected response format:")
        print(json.dumps(response_json, indent=2))
    
    # Add summary section
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    if 'hits' in response_json and 'hits' in response_json['hits']:
        total_hits = response_json['hits']['total']['value'] if 'total' in response_json['hits'] else len(response_json['hits']['hits'])
        print(f"Search Term: '{partial_street}'")
        print(f"Total Results: {total_hits}")
        print(f"Results Shown: {len(response_json['hits']['hits'])}")
        
        if response_json['hits']['hits']:
            print("\nMatching Addresses Found:")
            for i, hit in enumerate(response_json['hits']['hits'], 1):
                person_id = hit['_source'].get('id', 'Unknown')
                names = hit['_source'].get('names', [])
                primary_name = names[0] if names else 'Unknown'
                
                # Find matching addresses
                addresses = hit['_source'].get('addresses', [])
                matching_addresses = []
                for addr in addresses:
                    if partial_street.lower() in addr.get('street', '').lower():
                        matching_addresses.append(addr['street'])
                
                print(f"  {i}. Person: {primary_name} (ID: {person_id})")
                for addr in matching_addresses:
                    print(f"     - {addr}")
        else:
            print("No matching addresses found.")
    else:
        print("Unable to generate summary due to unexpected response format.")
        
except json.JSONDecodeError:
    print("Raw response:")
    print(result.stdout)
    if result.stderr:
        print("Error:")
        print(result.stderr) 