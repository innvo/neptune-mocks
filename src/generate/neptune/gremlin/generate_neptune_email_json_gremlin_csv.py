import pandas as pd
import json
import os
from tqdm import tqdm

def convert_to_gremlin():
    """
    Convert mock email data from JSON to Neptune Gremlin CSV format.
    
    Reads from: src/data/output/gds/mock_email_data.json
    Outputs to: src/data/output/neptune/neptune_email_nodes_gremlin.csv
    """
    try:
        # Ensure output directory exists
        os.makedirs('src/data/output/neptune', exist_ok=True)
        
        # Read the mock email data from JSON
        print("Reading mock email data...")
        with open('src/data/output/gds/mock_email_data.json', 'r') as f:
            email_data = json.load(f)
        
        # Initialize list to store converted nodes
        nodes = []
        
        print("\nConverting email data to Gremlin format...")
        for email in tqdm(email_data, desc="Processing email nodes"):
            # Get the node properties
            properties = email['node_properties']
            
            # Create the node with required fields
            node = {
                '~id': email['node_id']
            }
            
            # Add all properties from the JSON
            for key, value in properties.items():
                if isinstance(value, list):
                    # Convert list to string representation with semicolons for each element
                    value = ';'.join(str(v) for v in value)
                
                # Convert property name to lowercase and add appropriate type suffix
                if key.lower() == 'email_address':
                    node['email_address:String'] = str(value).lower()
                else:
                    # Default to String type for any other properties
                    node[f'{key.lower()}:String'] = str(value)
            
            # Add email label
            node['~label'] = 'email;secondary'
            
            nodes.append(node)
        
        # Convert to DataFrame
        nodes_df = pd.DataFrame(nodes)
        
        # Reorder columns to ensure ~label is last
        cols = nodes_df.columns.tolist()
        cols.remove('~label')
        cols.append('~label')
        nodes_df = nodes_df[cols]
        
        # Save to CSV with proper quoting
        output_path = 'src/data/output/neptune/neptune_email_nodes_gremlin.csv'
        nodes_df.to_csv(output_path, index=False, quoting=1, quotechar='"', escapechar='\\')
        
        # Print sample record
        print("\nSample Record:")
        sample = nodes[0]
        print(json.dumps(sample, indent=2))
        
        # Print statistics
        print(f"\nGenerated {len(nodes)} Gremlin-compatible email nodes")
        print(f"Saved to {output_path}")
        
        # Print email domain statistics
        email_domains = {}
        for email in email_data:
            props = email['node_properties']
            email_address = props.get('EMAIL_ADDRESS', '')
            if '@' in email_address:
                domain = email_address.split('@')[1].lower()
                email_domains[domain] = email_domains.get(domain, 0) + 1
        
        print("\nEmail Domain Distribution:")
        for domain, count in sorted(email_domains.items(), key=lambda x: x[1], reverse=True):
            print(f"  {domain}: {count} records")
        
        return True
        
    except Exception as e:
        print(f"Error converting email data: {str(e)}")
        return False

if __name__ == "__main__":
    convert_to_gremlin()
