import pandas as pd
import uuid
import random
from tqdm import tqdm
import time
import os
import json
import platform
import subprocess

# Define role type mappings
ROLE_TYPE_MAPPINGS = {
    'PRIMARY BENEFICIARY': 'PRIMARY BENEFICIARY',
    'INCIDENT OFFICIAL': 'INCIDENT OFFICIAL',
    'SPOUSE': 'NONPRIMARY BENEFICIARY',
    'SON': 'NONPRIMARY BENEFICIARY',
    'BENEFICIARY': 'PRIMARY BENEFICIARY',
    'DERIVATIVE APPLICANT': 'NONPRIMARY BENEFICIARY',
    'STEPFATHER': 'NONPRIMARY BENEFICIARY',
    'MOTHER': 'MOTHER',
    'MOTHER': 'NONPRIMARY BENEFICIARY',
    'STEPSON': 'NONPRIMARY BENEFICIARY',
    'SPOUSE': 'SPOUSE',
    'PARENT': 'NONPRIMARY BENEFICIARY',
    'WIFE': 'NONPRIMARY BENEFICIARY',
    'ADOPTED DAUGHTER': 'NONPRIMARY BENEFICIARY',
    'BENEFICIARY\'S SPOUSE': 'NONPRIMARY BENEFICIARY',
    'APPLICANT': 'APPLICANT',
    'ADOPTED SON': 'NONPRIMARY BENEFICIARY',
    'GRANDMOTHER': 'NONPRIMARY BENEFICIARY',
    'PARENT 1': 'PRIMARY BENEFICIARY',
    'HOUSEHOLD MEMBER': 'NONPRIMARY BENEFICIARY',
    'APPLICANT': 'PRIMARY BENEFICIARY',
    'STEPDAUGHTER': 'NONPRIMARY BENEFICIARY',
    'INTERPRETER': 'INTERPRETER',
    'FAMILY MEMBER': 'FAMILY MEMBER',
    'I130 OTHER BENEFICIARY': 'BENEFICIARY',
    'PARENT 2 NAME AT BIRTH': 'NONPRIMARY BENEFICIARY',
    'ADOPTIVE FATHER': 'NONPRIMARY BENEFICIARY',
    'BROTHER': 'NONPRIMARY BENEFICIARY',
    'PARENTS': 'NONPRIMARY BENEFICIARY',
    'PRINCIPAL ALIEN': 'PRIMARY BENEFICIARY',
    'ATTORNEY AT INTERVIEW': 'ATTORNEY',
    'SISTER': 'NONPRIMARY BENEFICIARY',
    'PARENT 2': 'PRIMARY BENEFICIARY',
    'GRANDFATHER': 'NONPRIMARY BENEFICIARY',
    'PETITIONER': 'PETITIONER',
    'ATTORNEY': 'ATTORNEY',
    'HUSBAND': 'NONPRIMARY BENEFICIARY',
    'PARENT 1 NAME AT BIRTH': 'NONPRIMARY BENEFICIARY',
    'FATHER': 'FATHER',
    'HOUSEHOLD RELATIVE': 'NONPRIMARY BENEFICIARY',
    'PRINCIPAL APPLICANT': 'PRIMARY BENEFICIARY',
    'INTENDING IMMIGRANT NO NEED FOR I864A': 'PRIMARY BENEFICIARY',
    'PRINCIPAL APPLICANT': 'PRIMARY BENEFICIARY',
    'I130 OTHER BENEFICIARY': 'NONPRIMARY BENEFICIARY',
    'PARENT 1': 'NONPRIMARY BENEFICIARY',
    'USCIS CIVIL SURGEON': 'CIVIL SURGEON',
    'IMPLICATED FAMILY MEMBER': 'FAMILY MEMBER',
    'FAMILY MEMBER': 'NONPRIMARY BENEFICIARY',
    'AUTHORIZED SIGNATORY': 'PETITIONER',
    'BENEFICIARY': 'BENEFICIARY',
    'PRINCIPAL APPLICANT': 'PRINCIPAL APPLICANT',
    'SPONSOR AFFIDAVIT OF SUPP': 'PETITIONER',
    'SPOUSE': 'PRIMARY BENEFICIARY',
    'INTERPRETER IN G1256': 'INTERPRETER',
    'SPONSOR': 'PETITIONER',
    'CHILD': 'NONPRIMARY BENEFICIARY',
    'INTERPRETER AT INTERVIEW': 'INTERPRETER',
    'PARENT 2': 'NONPRIMARY BENEFICIARY',
    'REPRESENTATIVE': 'REPRESENTATIVE',
    'ADOPTIVE MOTHER': 'NONPRIMARY BENEFICIARY',
    'DAUGHTER': 'NONPRIMARY BENEFICIARY',
    'BENEFICIARY, SEPARATE PETITION': 'PRIMARY BENEFICIARY',
    'FATHER': 'NONPRIMARY BENEFICIARY',
    'STUDENT': 'STUDENT',
    'PREPARER': 'PREPARER',
    'BENEFICIARY\'S FAMILY MEMBER': 'NONPRIMARY BENEFICIARY',
    'PARENT': 'CF-PARENT',
    'STEPMOTHER': 'NONPRIMARY BENEFICIARY',
    'USCIS OFFICER AS INTERPRETER': 'INTERPRETER',
    'GRANDSON': 'NONPRIMARY BENEFICIARY',
    'LANGUAGE SERVICE PROVIDER': 'INTERPRETER',
    'BENEFICIARY\'S LANGUAGE SERVICE PROVIDER': 'INTERPRETER',
    'BENEFICIARY\'S INTERPRETER IN G1256': 'INTERPRETER',
    'GRANDDAUGHTER': 'NONPRIMARY BENEFICIARY',
    'FIANCE': 'NONPRIMARY BENEFICIARY',
    'INTERPRETER VIA PHONE': 'INTERPRETER',
    'CUSTODIAN SON': 'NONPRIMARY BENEFICIARY',
    'CUSTODIAN DAUGHTER': 'NONPRIMARY BENEFICIARY',
    'LEGAL GUARDIAN': 'NONPRIMARY BENEFICIARY',
    'FOUNDLING': 'NONPRIMARY BENEFICIARY',
    'BENEFICIARY\'S FAMILY MEMBER': 'CF-BENEFICIARY\'S FAMILY MEMBER',
    'APPLICANT': 'CF-APPLICANT',
    'PARENT 2': 'PARENT',
    'BENEFICIARY': 'CF-BENEFICIARY',
    'PARENT 1 NAME AT BIRTH': 'PARENT'
}

def clear_terminal():
    """Clear the terminal screen based on the operating system"""
    if platform.system() == 'Windows':
        os.system('cls')
    else:
        os.system('clear')

def validate_node_existence(node_df, node_id):
    """Validate that a node exists in the node_data.csv"""
    return node_id in node_df['node_id'].values

def validate_referential_integrity(edges, node_df):
    """Validate referential integrity of edges against node data"""
    validation_results = {
        'total_edges': len(edges),
        'valid_edges': 0,
        'invalid_edges': 0,
        'missing_from_nodes': set(),
        'missing_to_nodes': set(),
        'edge_type_stats': {},
        'node_type_stats': {
            'person': {'total': 0, 'valid': 0},
            'receipt': {'total': 0, 'valid': 0}
        },
        'edges_per_person': {},  # Track edges per person
        'edges_per_receipt': {}  # Track edges per receipt
    }
    
    # Get sets of valid node IDs for quick lookup
    valid_node_ids = set(node_df['node_id'].values)
    person_node_ids = set(node_df[node_df['node_type'] == 'person']['node_id'].values)
    receipt_node_ids = set(node_df[node_df['node_type'] == 'receipt']['node_id'].values)
    
    # Initialize counters
    for person_id in person_node_ids:
        validation_results['edges_per_person'][person_id] = 0
    for receipt_id in receipt_node_ids:
        validation_results['edges_per_receipt'][receipt_id] = 0
    
    for edge in edges:
        from_node = edge['node_id_from']
        to_node = edge['node_id_to']
        edge_type = edge['edge_type']
        
        # Count edge types
        validation_results['edge_type_stats'][edge_type] = validation_results['edge_type_stats'].get(edge_type, 0) + 1
        
        # Validate node existence
        from_node_exists = from_node in valid_node_ids
        to_node_exists = to_node in valid_node_ids
        
        # Validate node types
        from_node_is_person = from_node in person_node_ids
        to_node_is_receipt = to_node in receipt_node_ids
        
        if from_node_exists and to_node_exists and from_node_is_person and to_node_is_receipt:
            validation_results['valid_edges'] += 1
            validation_results['node_type_stats']['person']['valid'] += 1
            validation_results['node_type_stats']['receipt']['valid'] += 1
            validation_results['edges_per_person'][from_node] += 1
            validation_results['edges_per_receipt'][to_node] += 1
        else:
            validation_results['invalid_edges'] += 1
            if not from_node_exists or not from_node_is_person:
                validation_results['missing_from_nodes'].add(from_node)
            if not to_node_exists or not to_node_is_receipt:
                validation_results['missing_to_nodes'].add(to_node)
    
    # Update total counts
    validation_results['node_type_stats']['person']['total'] = len(person_node_ids)
    validation_results['node_type_stats']['receipt']['total'] = len(receipt_node_ids)
    
    return validation_results

def generate_person_receipt_edges():
    try:
        clear_terminal()
        start_time = time.time()
        
        # Read node_data.csv, excluding node_name column
        print("Reading node data...")
        node_df = pd.read_csv('src/data/input/node_data.csv', usecols=['node_id', 'node_type'])
        
        # Read person data to get NAME_FULL
        print("Reading person data...")
        with open('src/data/output/gds/mock_person_data.json', 'r') as f:
            person_data = json.load(f)
        
        # Create a dictionary for quick person lookup
        person_lookup = {person['node_id']: person['node_properties']['NAME_FULL'] for person in person_data}
        
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
        
        # Get receipt nodes
        receipt_nodes = node_df[node_df['node_type'] == 'receipt']
        if receipt_nodes.empty:
            print("Warning: No receipt nodes found in node_data.csv")
            return None
        
        # Initialize edge data and counters
        edges = []
        missing_nodes = set()
        edge_type_count = 0
        
        # Track receipt usage to ensure we don't exceed the 1-4 people per receipt limit
        receipt_usage = {receipt_id: 0 for receipt_id in receipt_nodes['node_id']}
        
        # Generate edges for each person with progress bar
        print("\nGenerating person_receipt edges...")
        for _, person in tqdm(person_nodes.iterrows(), total=len(person_nodes), desc="Processing person nodes"):
            person_id = person['node_id']
            
            # Filter receipts that haven't reached their maximum usage
            available_receipts = receipt_nodes[receipt_nodes['node_id'].apply(lambda x: receipt_usage[x] < 4)]
            
            if len(available_receipts) == 0:
                print(f"Warning: No available receipts for person {person_id}")
                continue
            
            # Ensure each person has 1 or more receipt edges
            num_receipt_edges = random.randint(1, min(5, len(available_receipts)))  # Allow up to 5 receipts per person
            selected_receipts = available_receipts.sample(n=num_receipt_edges)
            
            for _, receipt in selected_receipts.iterrows():
                receipt_id = receipt['node_id']
                if validate_node_existence(node_df, receipt_id):
                    # Get random role type and its standardized version
                    role_type = random.choice(list(ROLE_TYPE_MAPPINGS.keys()))
                    role_type_std = ROLE_TYPE_MAPPINGS[role_type]
                    
                    # Get person's name
                    name_full = person_lookup.get(person_id, "UNKNOWN")
                    
                    edges.append({
                        'edge_id': str(uuid.uuid4()),
                        'node_id_from': person_id,
                        'node_id_to': receipt_id,
                        'edge_type': 'person_receipt',
                        'edge_properties': {
                            'ROLE_TYPE': role_type,
                            'ROLE_TYPE_STD': role_type_std,
                            'NAME_FULL': name_full
                        }
                    })
                    edge_type_count += 1
                    receipt_usage[receipt_id] += 1
                else:
                    missing_nodes.add(receipt_id)
        
        # Save all edges as a single JSON array
        os.makedirs('src/data/output/gds', exist_ok=True)
        with open('src/data/output/gds/mock_person-receipt_data.json', 'w') as f:
            json.dump(edges, f, indent=2)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Validate referential integrity
        validation_results = validate_referential_integrity(edges, node_df)
        
        clear_terminal()
        # Print validation results
        print("\nReferential Integrity Validation Results:")
        print(f"Total edges generated: {validation_results['total_edges']}")
        print(f"Valid edges: {validation_results['valid_edges']}")
        print(f"Invalid edges: {validation_results['invalid_edges']}")
        
        # Calculate and display edges per person distribution
        edges_per_person_dist = {}
        for person_id, count in validation_results['edges_per_person'].items():
            edges_per_person_dist[count] = edges_per_person_dist.get(count, 0) + 1
        
        print("\nDistribution of Receipt Edges per Person:")
        for count in sorted(edges_per_person_dist.keys()):
            print(f"Persons with {count} receipt edges: {edges_per_person_dist[count]}")
        
        # Calculate and display edges per receipt distribution
        edges_per_receipt_dist = {}
        for receipt_id, count in validation_results['edges_per_receipt'].items():
            edges_per_receipt_dist[count] = edges_per_receipt_dist.get(count, 0) + 1
        
        print("\nDistribution of People per Receipt:")
        for count in sorted(edges_per_receipt_dist.keys()):
            print(f"Receipts with {count} people: {edges_per_receipt_dist[count]}")
        
        if validation_results['missing_from_nodes']:
            print(f"\nMissing or invalid person nodes: {len(validation_results['missing_from_nodes'])}")
            print("Sample of missing person nodes:", list(validation_results['missing_from_nodes'])[:5])
        
        if validation_results['missing_to_nodes']:
            print(f"\nMissing or invalid receipt nodes: {len(validation_results['missing_to_nodes'])}")
            print("Sample of missing receipt nodes:", list(validation_results['missing_to_nodes'])[:5])
        
        print("\nNode Type Statistics:")
        for node_type, stats in validation_results['node_type_stats'].items():
            print(f"\n{node_type.capitalize()} Nodes:")
            print(f"  Total: {stats['total']}")
            print(f"  Used in valid edges: {stats['valid']}")
        
        print("\nEdge Generation Statistics:")
        print(f"Total number of person_receipt edges generated: {edge_type_count}")
        print(f"Processing time: {processing_time:.2f} seconds")
        print(f"Edges per second: {edge_type_count / processing_time:.2f}")
        
        # Read the final edge file to get the complete DataFrame
        with open('src/data/output/gds/mock_person-receipt_data.json', 'r') as f:
            edges_data = json.load(f)
        final_edge_df = pd.DataFrame(edges_data)
        return final_edge_df
        
    except Exception as e:
        print(f"Error generating edges: {str(e)}")
        return None

if __name__ == "__main__":
    edge_df = generate_person_receipt_edges()
    if edge_df is not None:
        print("\nSample of Generated Edges:")
        print(edge_df.head()) 