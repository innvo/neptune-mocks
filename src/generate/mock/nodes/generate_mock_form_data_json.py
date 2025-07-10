import pandas as pd
from faker import Faker
import json
from tqdm import tqdm
import os
import time
import platform
from datetime import datetime, timedelta
import random

# Define valid form numbers
FORM_NUMBERS = [
    'I-129', 'I-129F', 'I-130', 'I-131', 'I-140', 'I-360', 'I-526',
    'I-539', 'I-566', 'I-590', 'I-600', 'I-600A', 'I-730', 'I-800',
    'I-800A', 'I-821', 'I-821D', 'I-823', 'I-864', 'I-885', 'I-907',
    'I-912', 'I-130', 'I-589', 'I-765'
]

# Define valid form types
FORM_TYPES = [
    'PETITION', 'APPLICATION', 'REQUEST', 'NOTICE', 'AFFIDAVIT',
    'DECLARATION', 'STATEMENT', 'CERTIFICATE', 'WAIVER', 'APPEAL'
]

# Define valid form categories
FORM_CATEGORIES = [
    'IMMIGRATION', 'NATURALIZATION', 'ASYLUM', 'REFUGEE', 'WORK_AUTHORIZATION',
    'FAMILY_BASED', 'EMPLOYMENT_BASED', 'DIVERSITY_VISA', 'TEMPORARY_PROTECTED_STATUS',
    'DEFERRED_ACTION', 'PAROLE', 'ADJUSTMENT_OF_STATUS'
]

# Define valid form statuses
FORM_STATUSES = [
    'DRAFT', 'SUBMITTED', 'UNDER_REVIEW', 'PENDING_DOCUMENTS', 'APPROVED',
    'DENIED', 'RETURNED', 'WITHDRAWN', 'EXPIRED', 'AMENDED', 'SUPPLEMENTED'
]

def clear_terminal():
    """Clear the terminal screen"""
    if platform.system() == 'Windows':
        os.system('cls')
    else:
        os.system('clear')

def validate_referential_integrity(form_data, node_df):
    """Validate referential integrity of form data against node data"""
    validation_results = {
        'total_forms': len(form_data),
        'valid_forms': 0,
        'invalid_forms': 0,
        'missing_nodes': set(),
        'node_type_stats': {
            'form': {'total': 0, 'valid': 0}
        }
    }
    
    # Get sets of valid node IDs for quick lookup
    valid_node_ids = set(node_df['node_id'].values)
    form_node_ids = set(node_df[node_df['node_type'] == 'form']['node_id'].values)
    
    for form_entry in form_data:
        node_id = form_entry['node_id']
        
        # Validate node existence and type
        node_exists = node_id in valid_node_ids
        is_form_node = node_id in form_node_ids
        
        if node_exists and is_form_node:
            validation_results['valid_forms'] += 1
            validation_results['node_type_stats']['form']['valid'] += 1
        else:
            validation_results['invalid_forms'] += 1
            if not node_exists or not is_form_node:
                validation_results['missing_nodes'].add(node_id)
    
    # Update total counts
    validation_results['node_type_stats']['form']['total'] = len(form_node_ids)
    
    return validation_results

def generate_mock_form_data():
    try:
        # Clear terminal at start
        clear_terminal()
        
        start_time = time.time()
        
        # Initialize Faker
        fake = Faker()
        
        # Read node_data.csv to get form nodes
        print("Reading node data...")
        node_df = pd.read_csv(os.path.join('src', 'data', 'input', 'node_data.csv'), usecols=['node_id', 'node_type'])
        
        # Print node type statistics
        print("\nNode Type Statistics:")
        print(f"Total number of nodes: {len(node_df)}")
        node_counts = node_df['node_type'].value_counts()
        for node_type, count in node_counts.items():
            print(f"{node_type}: {count} nodes")
        
        # Filter for form nodes
        form_nodes = node_df[node_df['node_type'] == 'form']
        if form_nodes.empty:
            print("Warning: No form nodes found in node_data.csv")
            return None
        
        # Initialize data list
        form_data = []
        
        # Generate mock data for each form node
        print("\nGenerating mock form data...")
        for _, node in tqdm(form_nodes.iterrows(), total=len(form_nodes), desc="Processing form nodes"):
            node_id = node['node_id']
            
            # Generate random dates within the last 5 years
            end_date = datetime.now()
            start_date = end_date - timedelta(days=5*365)
            form_date = fake.date_between(start_date=start_date, end_date=end_date)
            
            # Select random form properties
            form_number = random.choice(FORM_NUMBERS)
            form_type = random.choice(FORM_TYPES)
            form_category = random.choice(FORM_CATEGORIES)
            form_status = random.choice(FORM_STATUSES)
            
            # Generate form identifier
            form_id = f"FRM-{fake.random_number(digits=8)}"
            
            # Generate version number (1-5)
            version_number = random.randint(1, 5)
            
            # Generate filing fee (common USCIS fees)
            filing_fees = [535, 575, 1170, 1225, 1440, 1600, 2050, 2250, 3250]
            filing_fee = random.choice(filing_fees)
            
            # Generate processing time estimate (30-365 days)
            processing_time_days = random.randint(30, 365)
            
            # Create node properties JSON
            node_properties = {
                "FORM_ID": form_id,
                "FORM_NUMBER": form_number,
                "FORM_TYPE": form_type,
                "FORM_CATEGORY": form_category,
                "FORM_STATUS": form_status,
                "FORM_DATE": form_date.strftime("%Y-%m-%d"),
                "VERSION_NUMBER": version_number,
                "FILING_FEE": filing_fee,
                "PROCESSING_TIME_DAYS": processing_time_days,
                "IS_ELECTRONIC": random.choice([True, False]),
                "IS_URGENT": random.choice([True, False]),
                "HAS_ATTACHMENTS": random.choice([True, False]),
                "ATTACHMENT_COUNT": random.randint(0, 10) if random.choice([True, False]) else 0
            }
            
            # Add to data list
            form_data.append({
                'node_id': node_id,
                'node_name': form_id,
                'node_properties': node_properties
            })
        
        # Save to JSON
        output_path = os.path.join('src', 'data', 'output', 'gds', 'mock_form_data.json')
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(form_data, f, indent=2)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Validate referential integrity
        validation_results = validate_referential_integrity(form_data, node_df)
        
        # Print validation results
        print("\nReferential Integrity Validation Results:")
        print(f"Total forms generated: {validation_results['total_forms']}")
        print(f"Valid forms: {validation_results['valid_forms']}")
        print(f"Invalid forms: {validation_results['invalid_forms']}")
        
        if validation_results['missing_nodes']:
            print(f"\nMissing or invalid form nodes: {len(validation_results['missing_nodes'])}")
            print("Sample of missing form nodes:", list(validation_results['missing_nodes'])[:5])
        
        print("\nNode Type Statistics:")
        for node_type, stats in validation_results['node_type_stats'].items():
            print(f"\n{node_type.capitalize()} Nodes:")
            print(f"  Total: {stats['total']}")
            print(f"  Used in valid forms: {stats['valid']}")
        
        print("\nForm Data Generation Statistics:")
        print(f"Total number of form nodes processed: {len(form_data)}")
        print(f"Processing time: {processing_time:.2f} seconds")
        print(f"Forms per second: {len(form_data) / processing_time:.2f}")
        print(f"Data saved to: {output_path}")
        
        return form_data
        
    except Exception as e:
        print(f"Error generating mock form data: {str(e)}")
        return None

if __name__ == "__main__":
    form_data = generate_mock_form_data()
    if form_data is not None:
        print("\nSample of Generated Form Data:")
        print(json.dumps(form_data[:5], indent=2))
