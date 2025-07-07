import requests
import json

def get_person_count():
    url = "https://localhost:8182/gremlin"
    headers = {"Content-Type": "application/json"}
    data = {"gremlin": "g.V().hasLabel(\"person\").count()"}
    
    response = requests.post(url, headers=headers, json=data, verify=False)
    count = response.json()["result"]["data"]["@value"][0]
    
    # Convert to OpenCypher format
    opencypher_result = {
        "results": [{
            "count": count
        }]
    }
    
    return opencypher_result

if __name__ == "__main__":
    result = get_person_count()
    print(json.dumps(result, indent=2)) 