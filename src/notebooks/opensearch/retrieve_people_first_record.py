## Retrieve the first record

import subprocess
import json

# Query to get the first record
query = {
    "query": {
        "match_all": {}
    },
    "_source": True,
    "size": 1
}

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
            print(f"Found {len(hits)} record(s):")
            print("=" * 50)
            
            for i, hit in enumerate(hits, 1):
                print(f"\nRecord {i}:")
                print(json.dumps(hit['_source'], indent=2))
                print("-" * 30)
        else:
            print("No records found")
            print("Response:", json.dumps(response_json, indent=2))
    else:
        print("Unexpected response format:")
        print(json.dumps(response_json, indent=2))
        
except json.JSONDecodeError:
    print("Raw response:")
    print(result.stdout)
    if result.stderr:
        print("Error:")
        print(result.stderr) 