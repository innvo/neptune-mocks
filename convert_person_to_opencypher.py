import pandas as pd
import json
import uuid
from datetime import datetime
import re

def parse_birth_date(value, node_id):
    """Parse and format BIRTH_DATE as DateTime"""
    try:
        dt = datetime.strptime(value, '%Y-%m-%d')
        return dt.strftime('%m-%d-%Y')
    except ValueError as e:
        print(f"Warning: Invalid date format for BIRTH_DATE in node {node_id}: {value}")
        return None

def parse_name_full(value):
    """Parse and format NAME_FULL"""
    return str(value)

def parse_list_value(value):
    """Parse and format list values (NAME_LIST, BIRTH_DATE_LIST)"""
    if isinstance(value, list):
        # Format each string value with single double quote
        formatted_values = []
        for v in value:
            if isinstance(v, str):
                formatted_values.append('"' + v + '"')
            else:
                formatted_values.append(str(v))
        return '[' + ','.join(formatted_values) + ']'
    return str(value)

def parse_string_value(value):
    """Parse and format other string values"""
    return f"'{str(value)}'"

def post_process_csv(input_file, output_file):
    """Clean up double quotes in the CSV file"""
    print("\nPost-processing CSV file...")
    with open(input_file, 'r') as f:
        content = f.read()
    
    # Replace double double quotes with single double quotes
    content = content.replace('""', '"')
    
    with open(output_file, 'w') as f:
        f.write(content)
    
    print(f"Post-processed file saved to {output_file}")

def convert_to_opencypher():
    try:
        print("Reading mock_person_data.csv...")
        person_df = pd.read_csv('mock_person_data.csv')
        
        # Initialize list for nodes
        nodes = []
        
        print("\nConverting data to OpenCypher format...")
        for _, row in person_df.iterrows():
            # Create base node entry
            node_id = row['node_id']
            node = {
                '~id': node_id,
                '~label': 'person',
                'name:String': row['node_name']
            }
            
            # Parse and add properties
            try:
                props = json.loads(row['node_properties'])
                for key, value in props.items():
                    if key == 'BIRTH_DATE':
                        formatted_date = parse_birth_date(value, node_id)
                        if formatted_date:
                            node['BIRTH_DATE:DateTime'] = formatted_date
                    elif key == 'NAME_FULL':
                        node[f'{key}:String'] = parse_name_full(value)
                    elif key in ['NAME_LIST', 'BIRTH_DATE_LIST']:
                        node[f'{key}:String'] = parse_list_value(value)
                    else:
                        node[f'{key}:String'] = parse_string_value(value)
            except json.JSONDecodeError as e:
                print(f"Warning: Invalid JSON in properties for node {node_id}: {str(e)}")
                continue
            
            nodes.append(node)
        
        # Create DataFrame
        nodes_df = pd.DataFrame(nodes)
        
        # Save to CSV file
        print("\nSaving OpenCypher CSV file...")
        temp_file = 'neptune_person_nodes_temp.csv'
        final_file = 'neptune_person_nodes.csv'
        nodes_df.to_csv(temp_file, index=False, quoting=1)  # Use single quotes
        
        # Post-process the CSV file
        post_process_csv(temp_file, final_file)
        
        # Remove temporary file
        import os
        os.remove(temp_file)
        
        print("Saved nodes to neptune_person_nodes.csv")
        
        # Print sample data
        print("\nSample Node Data:")
        print(nodes_df.head())
        
        # Print statistics
        print("\nConversion Statistics:")
        print(f"Total nodes converted: {len(nodes)}")
        print("\nColumns in output file:")
        for col in nodes_df.columns:
            print(f"- {col}")
        
        return True
        
    except Exception as e:
        print(f"Error converting data: {str(e)}")
        return False

if __name__ == "__main__":
    convert_to_opencypher() 