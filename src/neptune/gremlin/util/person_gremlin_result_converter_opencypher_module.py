import json
import os
from datetime import datetime

def convert_epoch_to_iso(value):
    """Convert epoch millis to ISO format YYYY-MM-DDTHH:MM:SSZ."""
    if isinstance(value, int) or isinstance(value, float):
        dt = datetime.utcfromtimestamp(value / 1000)
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    return value

def clean_properties(properties):
    """Flatten lists with single values and convert dates."""
    cleaned = {}
    for key, val in properties.items():
        if isinstance(val, list):
            if len(val) == 1:
                # Handle single value
                if key in ['date_of_birth', 'date_of_birth_list']:
                    cleaned[key] = convert_epoch_to_iso(val[0])
                else:
                    cleaned[key] = val[0]
            else:
                # Handle list of values
                if key in ['date_of_birth', 'date_of_birth_list']:
                    cleaned[key] = [convert_epoch_to_iso(v) for v in val]
                else:
                    cleaned[key] = val
        else:
            if key in ['date_of_birth', 'date_of_birth_list']:
                cleaned[key] = convert_epoch_to_iso(val)
            else:
                cleaned[key] = val
    return cleaned

def transform_gremlin_response(response):
    """Transform raw Neptune response to OpenCypher-style JSON."""
    raw_results = response.get('result', {}).get('data', {}).get('@value', [])
    transformed_results = []

    for vertex in raw_results:
        if not isinstance(vertex, dict) or '@type' not in vertex or vertex['@type'] != 'g:Vertex':
            continue

        vertex_data = vertex.get('@value', {})
        if not vertex_data:
            continue

        # Extract properties
        properties = {}
        for prop_key, prop_values in vertex_data.get('properties', {}).items():
            values = []
            for prop_value in prop_values:
                if isinstance(prop_value, dict) and '@type' in prop_value and prop_value['@type'] == 'g:VertexProperty':
                    value_data = prop_value.get('@value', {})
                    if 'value' in value_data:
                        value = value_data['value']
                        if isinstance(value, dict) and '@type' in value and value['@type'] == 'g:Date':
                            values.append(value.get('@value'))
                        else:
                            values.append(value)
            properties[prop_key] = values

        transformed = {
            "n": {
                "~id": vertex_data.get('id'),
                "~entityType": "node",
                "~labels": [vertex_data.get('label')],
                "~properties": clean_properties(properties)
            }
        }

        transformed_results.append(transformed)

    return {"results": transformed_results}

def convert_gremlin_to_opencypher(input_file, output_dir=None):
    """Convert Gremlin JSON to OpenCypher format and save to new file."""
    try:
        # Read the input file
        with open(input_file, 'r') as f:
            gremlin_data = json.load(f)

        # Transform the data
        opencypher_data = transform_gremlin_response(gremlin_data)

        # Create output filename
        input_filename = os.path.basename(input_file)
        output_filename = os.path.splitext(input_filename)[0] + '_converted.json'
        
        if output_dir:
            output_file = os.path.join(output_dir, output_filename)
        else:
            output_file = os.path.splitext(input_file)[0] + '_converted.json'

        # Write the transformed data
        with open(output_file, 'w') as f:
            json.dump(opencypher_data, f, indent=2)

        print(f"Successfully converted {input_file} to {output_file}")
        return True

    except Exception as e:
        print(f"Error converting file: {str(e)}")
        return False

if __name__ == "__main__":
    # Example usage
    input_file = "src/neptune/gremlin/data/input/person_gremlin_10.json"
    output_dir = "src/neptune/gremlin/data/output"
    convert_gremlin_to_opencypher(input_file, output_dir)
