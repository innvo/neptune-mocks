import pandas as pd
import json
import os
from tqdm import tqdm
from datetime import datetime, timedelta
import random

# TODO: Not relevant for GDS 
def generate_variant_dates(base_date, count=6):
    """Generate slightly different dates based on the base date"""
    base = datetime.strptime(base_date, '%Y-%m-%d')
    dates = []
    for i in range(count):
        # Add random variation of -5 to +5 days
        variation = random.randint(-5, 5)
        variant_date = base + timedelta(days=variation)
        dates.append(variant_date.strftime('%Y-%m-%d'))
    return dates
    
# TODO: Replace with GDS data
def convert_to_gremlin():
    try:
        # Ensure output directory exists
        os.makedirs('src/data/output/neptune', exist_ok=True)
        
        # Read the mock person data
        print("Reading mock person data...")
        df = pd.read_csv('src/data/output/gds/mock_person_data.csv')
        # TODO: Replace with GDS data
        
        # Initialize list to store converted nodes
        nodes = []
        
        print("\nConverting data to Gremlin format...")
        for _, row in tqdm(df.iterrows(), total=len(df), desc="Processing nodes"):
            # Parse the node properties JSON
            properties = json.loads(row['node_properties'])
            
            # Create the node with required fields
            node = {
                'id': row['node_id']
            }
            
            # Add all properties from the JSON
            for key, value in properties.items():
                if isinstance(value, list):
                    # Convert list to string representation with semicolons for each element
                    if key.lower() == 'name_list':
                        # Convert all names to uppercase and remove commas
                        value = [v.upper().replace(',', '') for v in value]
                        # Format name list with semicolons
                        node['name_full_list:String[]'] = ';'.join(str(v) for v in value)
                        continue
                    elif key.lower() == 'birth_date_list':
                        # Generate variant dates based on the birth date
                        base_date = properties.get('birth_date', value[0])
                        variant_dates = generate_variant_dates(base_date)
                        node['date_of_birth_list:Date[]'] = ';'.join(variant_dates)
                        continue
                    value = ';'.join(str(v) for v in value)
                
                # Convert property name to lowercase for String suffix
                if key.lower() == 'name_full':
                    node['name_full:String'] = str(value).upper()
                elif key.lower() == 'birth_date':
                    node['date_of_birth:Date'] = str(value)
                else:
                    node[f'{key.lower()}:String'] = str(value)
            
            # Add person label
            node['~label'] = 'person'
            
            nodes.append(node)
        
        # Convert to DataFrame
        nodes_df = pd.DataFrame(nodes)
        
        # Reorder columns to ensure ~label is last
        cols = nodes_df.columns.tolist()
        cols.remove('~label')
        cols.append('~label')
        nodes_df = nodes_df[cols]
        
        # Save to CSV with proper quoting
        output_path = 'src/data/output/neptune/neptune_person_nodes_gremlin.csv'
        nodes_df.to_csv(output_path, index=False, quoting=1)
        
        # Print sample record
        print("\nSample Record:")
        sample = nodes[0]
        print(json.dumps(sample, indent=2))
        
        print(f"\nGenerated {len(nodes)} Gremlin-compatible nodes")
        print(f"Saved to {output_path}")
        return True
        
    except Exception as e:
        print(f"Error converting data: {str(e)}")
        return False

if __name__ == "__main__":
    convert_to_gremlin()