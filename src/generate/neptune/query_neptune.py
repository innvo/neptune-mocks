import json
import subprocess
from datetime import datetime

def convert_epoch_to_iso(value):
    """Convert epoch millis to ISO format."""
    if isinstance(value, int) or isinstance(value, float):
        return datetime.utcfromtimestamp(value / 1000).isoformat() + 'Z'
    return value

def clean_properties(properties):
    """Flatten lists with single values and convert dates."""
    cleaned = {}
    for key, val in properties.items():
        # Neptune gives all values as lists
        if isinstance(val, list):
            if len(val) == 1:
                # Try converting to ISO if it's a number
                single = convert_epoch_to_iso(val[0])
                cleaned[key] = single
            else:
                # Convert each list item if it looks like epoch millis
                cleaned[key] = [convert_epoch_to_iso(v) for v in val]
        else:
            cleaned[key] = val
    return cleaned

def transform_gremlin_response(response):
    """Transform raw Neptune response to OpenCypher-style JSON."""
    raw_results = response.get('result', {}).get('data', {}).get('@value', [])
    transformed_results = []

    for result in raw_results:
        if not result.get('@value'):
            continue

        # The response structure is different - we need to parse the @value array
        value_array = result.get('@value', [])
        if len(value_array) < 2:
            continue

        # The second element contains the node data
        node_data = value_array[1].get('@value', [])
        if not node_data:
            continue

        # Convert the flat array into a dictionary
        node_dict = {}
        for i in range(0, len(node_data), 2):
            if i + 1 < len(node_data):
                key = node_data[i]
                value = node_data[i + 1]
                
                # Handle special cases for values that are wrapped in @value
                if isinstance(value, dict) and '@value' in value:
                    value = value['@value']
                
                node_dict[key] = value

        # Extract properties from the node dictionary
        properties = {}
        if '~properties' in node_dict:
            prop_array = node_dict['~properties']
            if isinstance(prop_array, dict) and '@value' in prop_array:
                prop_array = prop_array['@value']
            
            for i in range(0, len(prop_array), 2):
                if i + 1 < len(prop_array):
                    key = prop_array[i].get('@value') if isinstance(prop_array[i], dict) else prop_array[i]
                    value = prop_array[i + 1]
                    
                    # Handle list values
                    if isinstance(value, dict) and value.get('@type') == 'g:List':
                        value = value.get('@value', [])
                        # Handle date values in lists
                        value = [v.get('@value') if isinstance(v, dict) and v.get('@type') == 'g:Date' else v for v in value]
                    properties[key] = value

        transformed = {
            "n": {
                "~id": node_dict.get('~id'),
                "~entityType": node_dict.get('~entityType'),
                "~labels": node_dict.get('~labels', []),
                "~properties": clean_properties(properties)
            }
        }

        transformed_results.append(transformed)

    return {"results": transformed_results}

def query_neptune(vertex_id):
    """Query Neptune for a vertex and return transformed results."""
    # Construct the Gremlin query
    gremlin_query = {
        "gremlin": f'g.V("{vertex_id}").project("n").by(project("~id", "~entityType", "~labels", "~properties").by(id()).by(constant("node")).by(label().fold()).by(valueMap(true)))'
    }

    # Execute the curl command
    cmd = [
        'curl', '-k', '-X', 'POST',
        'https://localhost:8182/gremlin',
        '-H', 'Content-Type: application/json',
        '-d', json.dumps(gremlin_query)
    ]
    
    try:
        # Run the curl command and capture output
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Curl command failed: {result.stderr}")
        
        # Parse the JSON response
        response = json.loads(result.stdout)
        
        # Transform the response
        transformed = transform_gremlin_response(response)
        
        return transformed
        
    except Exception as e:
        print(f"Error querying Neptune: {str(e)}")
        return None

if __name__ == "__main__":
    # Example vertex ID
    vertex_id = "d9a07d51-34ca-47e1-8365-1678a5540e53"
    
    # Query Neptune and get transformed results
    results = query_neptune(vertex_id)
    
    if results:
        # Print the results
        print(json.dumps(results, indent=2))
    else:
        print("Failed to get results from Neptune") 