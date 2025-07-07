import pandas as pd
import uuid
import random
from tqdm import tqdm
import time
import os

def validate_node_existence(node_df, node_id):
    """Validate that a node exists in the node_data.csv"""
    return node_id in node_df['node_id'].values

def generate_person_edges():
    try:
        start_time = time.time()
        
        # Read node_data.csv, excluding node_name column
        print("Reading node data...")
        node_df = pd.read_csv('src/data/input/node_data.csv', usecols=['node_id', 'node_type'])
        
        # Print node type statistics
        print("\nNode Type Statistics:")
        print(f"Total number of nodes: {len(node_df)}")
        node_counts = node_df['node_type'].value_counts()
        for node_type, count in node_counts.items():
            print(f"{node_type}: {count} nodes")
        
        # Get person nodes
        person_nodes = node_df[node_df['node_type'] == 'person']
        if person_nodes.empty:
            print("Warning: No person nodes found in node_data.csv")
            return None
        
        # Get other node types
        name_nodes = node_df[node_df['node_type'] == 'name']
        address_nodes = node_df[node_df['node_type'] == 'address']
        form_nodes = node_df[node_df['node_type'] == 'form']
        phone_nodes = node_df[node_df['node_type'] == 'phone']
        email_nodes = node_df[node_df['node_type'] == 'email']
        anumber_nodes = node_df[node_df['node_type'] == 'anumber']
        
        # Initialize edge data and counters
        edges = []
        missing_nodes = set()
        edge_type_counts = {
            'person_name': 0,
            'person_address': 0,
            'person_form': 0,
            'person_phone': 0,
            'person_email': 0,
            'person_anumber': 0
        }
        
        # Generate edges for each person with progress bar
        print("\nGenerating edges...")
        for _, person in tqdm(person_nodes.iterrows(), total=len(person_nodes), desc="Processing person nodes"):
            person_id = person['node_id']
            
            # Person to Name edges
            if not name_nodes.empty:
                num_name_edges = random.randint(1, min(3, len(name_nodes)))
                selected_names = name_nodes.sample(n=num_name_edges)
                for _, name in selected_names.iterrows():
                    name_id = name['node_id']
                    if validate_node_existence(node_df, name_id):
                        edges.append({
                            'edge_id': str(uuid.uuid4()),
                            'node_id_from': person_id,
                            'node_id_to': name_id,
                            'edge_type': 'person_name'
                        })
                        edge_type_counts['person_name'] += 1
                    else:
                        missing_nodes.add(name_id)
            
            # Person to Address edges
            if not address_nodes.empty:
                num_address_edges = random.randint(1, min(2, len(address_nodes)))
                selected_addresses = address_nodes.sample(n=num_address_edges)
                for _, address in selected_addresses.iterrows():
                    address_id = address['node_id']
                    if validate_node_existence(node_df, address_id):
                        edges.append({
                            'edge_id': str(uuid.uuid4()),
                            'node_id_from': person_id,
                            'node_id_to': address_id,
                            'edge_type': 'person_address'
                        })
                        edge_type_counts['person_address'] += 1
                    else:
                        missing_nodes.add(address_id)
            
            # Person to Form edges
            if not form_nodes.empty:
                num_form_edges = random.randint(1, min(3, len(form_nodes)))
                selected_forms = form_nodes.sample(n=num_form_edges)
                for _, form in selected_forms.iterrows():
                    form_id = form['node_id']
                    if validate_node_existence(node_df, form_id):
                        edges.append({
                            'edge_id': str(uuid.uuid4()),
                            'node_id_from': person_id,
                            'node_id_to': form_id,
                            'edge_type': 'person_form'
                        })
                        edge_type_counts['person_form'] += 1
                    else:
                        missing_nodes.add(form_id)
            
            # Person to Phone edges
            if not phone_nodes.empty:
                num_phone_edges = random.randint(1, min(2, len(phone_nodes)))
                selected_phones = phone_nodes.sample(n=num_phone_edges)
                for _, phone in selected_phones.iterrows():
                    phone_id = phone['node_id']
                    if validate_node_existence(node_df, phone_id):
                        edges.append({
                            'edge_id': str(uuid.uuid4()),
                            'node_id_from': person_id,
                            'node_id_to': phone_id,
                            'edge_type': 'person_phone'
                        })
                        edge_type_counts['person_phone'] += 1
                    else:
                        missing_nodes.add(phone_id)
            
            # Person to Email edges
            if not email_nodes.empty:
                num_email_edges = random.randint(1, min(2, len(email_nodes)))
                selected_emails = email_nodes.sample(n=num_email_edges)
                for _, email in selected_emails.iterrows():
                    email_id = email['node_id']
                    if validate_node_existence(node_df, email_id):
                        edges.append({
                            'edge_id': str(uuid.uuid4()),
                            'node_id_from': person_id,
                            'node_id_to': email_id,
                            'edge_type': 'person_email'
                        })
                        edge_type_counts['person_email'] += 1
                    else:
                        missing_nodes.add(email_id)
            
            # Person to Anumber edges
            if not anumber_nodes.empty:
                num_anumber_edges = random.randint(1, min(2, len(anumber_nodes)))
                selected_anumbers = anumber_nodes.sample(n=num_anumber_edges)
                for _, anumber in selected_anumbers.iterrows():
                    anumber_id = anumber['node_id']
                    if validate_node_existence(node_df, anumber_id):
                        edges.append({
                            'edge_id': str(uuid.uuid4()),
                            'node_id_from': person_id,
                            'node_id_to': anumber_id,
                            'edge_type': 'person_anumber'
                        })
                        edge_type_counts['person_anumber'] += 1
                    else:
                        missing_nodes.add(anumber_id)
            
            # Save progress periodically
            if len(edges) >= 10000:
                edge_df = pd.DataFrame(edges)
                edge_df.to_csv('person_edges.csv', mode='a', header=not os.path.exists('person_edges.csv'), index=False)
                edges = []  # Clear the list after saving
        
        # Save any remaining edges
        if edges:
            edge_df = pd.DataFrame(edges)
            edge_df.to_csv('person_edges.csv', mode='a', header=not os.path.exists('person_edges.csv'), index=False)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Print warning if any missing nodes were found
        if missing_nodes:
            print(f"\nWarning: Found {len(missing_nodes)} nodes referenced in edges that don't exist in node_data.csv")
            print("These edges were not created to maintain referential integrity.")
        
        # Print detailed edge statistics
        print("\nEdge Generation Statistics:")
        print(f"Total number of edges generated: {sum(edge_type_counts.values())}")
        print(f"Processing time: {processing_time:.2f} seconds")
        print(f"Edges per second: {sum(edge_type_counts.values()) / processing_time:.2f}")
        print("\nEdge Types Distribution:")
        for edge_type, count in edge_type_counts.items():
            print(f"{edge_type}: {count} edges")
        
        # Read the final edge file to get the complete DataFrame
        final_edge_df = pd.read_csv('person_edges.csv')
        return final_edge_df
        
    except Exception as e:
        print(f"Error generating edges: {str(e)}")
        return None

if __name__ == "__main__":
    edge_df = generate_person_edges()
    if edge_df is not None:
        print("\nSample of Generated Edges:")
        print(edge_df.head()) 