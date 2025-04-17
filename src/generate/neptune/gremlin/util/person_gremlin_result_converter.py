"""
Neptune Gremlin to OpenCypher Person Converter Module

This module provides functionality to convert Neptune Gremlin JSON responses
containing person data into OpenCypher-compatible format. It handles the conversion
of date formats and property structures.

Functions:
    convert_epoch_to_iso(value): Convert epoch milliseconds to ISO format
    clean_properties(properties): Clean and format vertex properties
    transform_gremlin_response(response): Transform Gremlin response to OpenCypher format
    convert_gremlin_to_opencypher(input_file): Convert a Gremlin JSON file to OpenCypher format
"""

import json
import os
from datetime import datetime

def convert_epoch_to_iso(value):
    """
    Convert epoch milliseconds to ISO format YYYY-MM-DDTHH:MM:SSZ.
    
    Args:
        value: An epoch timestamp in milliseconds or any other value
        
    Returns:
        str: ISO formatted date string if input is a timestamp,
             original value otherwise
    """
    if isinstance(value, int) or isinstance(value, float):
        dt = datetime.utcfromtimestamp(value / 1000)
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    return value

def clean_properties(properties):
    """
    Clean and format vertex properties, handling date conversions.
    
    Args:
        properties (dict): Dictionary of vertex properties
        
    Returns:
        dict: Cleaned properties with converted dates and flattened single-item lists
    """
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
    """
    Transform raw Neptune Gremlin response to OpenCypher-style JSON.
    
    Args:
        response (dict): Raw Gremlin response containing person vertices
        
    Returns:
        dict: Transformed data in OpenCypher format
    """
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

def convert_gremlin_to_opencypher(input_file):
    """
    Convert a Gremlin JSON file to OpenCypher format and save to a new file.
    
    Args:
        input_file (str): Path to the input Gremlin JSON file
        
    Returns:
        bool: True if conversion was successful, False otherwise
        
    Raises:
        FileNotFoundError: If input file doesn't exist
        json.JSONDecodeError: If input file is not valid JSON
    """
    try:
        # Read the input file
        with open(input_file, 'r') as f:
            gremlin_data = json.load(f)

        # Transform the data
        opencypher_data = transform_gremlin_response(gremlin_data)

        # Create output filename
        output_file = os.path.splitext(input_file)[0] + '_converted.json'

        # Write the transformed data
        with open(output_file, 'w') as f:
            json.dump(opencypher_data, f, indent=2)

        print(f"Successfully converted {input_file} to {output_file}")
        return True

    except Exception as e:
        print(f"Error converting file: {str(e)}")
        return False

# Example usage when run as a script
if __name__ == "__main__":
    import sys
    
    # Use command line argument if provided, otherwise use default
    input_file = sys.argv[1] if len(sys.argv) > 1 else "src/generate/neptune/gremlin/json/person_gremlin_10.json"
    
    # Convert the file
    convert_gremlin_to_opencypher(input_file) 