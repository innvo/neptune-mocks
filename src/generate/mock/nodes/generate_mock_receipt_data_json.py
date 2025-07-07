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

# Define valid status pairs
STATUS_PAIRS = [
    ('IN PROCESS', 'APPROVED'),
    ('IN PROCESS', 'DENIED'),
    ('APPROVED', 'APPROVED'),
    ('DENIED', 'DENIED'),
    ('DENIED', 'APPROVED'),
    ('DENIED', 'ADMIN CLOSED'),
    ('DENIED', 'PENDING'),
    ('APPROVED', 'PENDING'),
    ('IN PROCESS', 'ADMIN CLOSED'),
    ('IN PROCESS', 'PENDING'),
    ('NULL', 'APPROVED'),
    ('APPROVED', 'DENIED'),
    ('NULL', 'PENDING'),
    ('NULL', 'DENIED'),
    ('UNKNOWN', 'PENDING'),
    ('ADMIN CLOSE/DISMISSAL', 'PENDING'),
    ('PENDING', 'APPROVED'),
    ('ADMIN CLOSE/DISMISSAL', 'ADMIN CLOSED'),
    ('PENDING', 'PENDING'),
    ('DENY/REFERRAL', 'ADMIN CLOSED'),
    ('PENDING', 'ADMIN CLOSED'),
    ('DENY/REFERRAL', 'DENIED'),
    ('GRANT', 'PENDING'),
    ('ADMIN CLOSE/DISMISSAL', 'APPROVED'),
    ('GRANT', 'APPROVED'),
    ('DENY/REFERRAL', 'PENDING'),
    ('PENDING', 'DENIED'),
    ('CLOSED', 'DENIED'),
    ('OPTIMIZED', 'PENDING'),
    ('OPTIMIZED', 'DENIED'),
    ('REOPENED', 'PENDING'),
    ('CLOSED', 'PENDING'),
    ('NULL', 'ADMIN CLOSED'),
    ('ACCEPTED', 'ADMIN CLOSED'),
    ('ACCEPTED', 'PENDING'),
    ('CLOSED', 'APPROVED'),
    ('HOLD', 'PENDING'),
    ('CLOSED', 'ADMIN CLOSED'),
    ('ACCEPTED', 'APPROVED'),
    ('REOPENED', 'APPROVED'),
    ('OPTIMIZED', 'APPROVED'),
    ('REOPENED', 'DENIED'),
    ('HOLD', 'DENIED')
]

def clear_terminal():
    """Clear the terminal screen"""
    if platform.system() == 'Windows':
        os.system('cls')
    else:
        os.system('clear')

def validate_referential_integrity(receipt_data, node_df):
    """Validate referential integrity of receipt data against node data"""
    validation_results = {
        'total_receipts': len(receipt_data),
        'valid_receipts': 0,
        'invalid_receipts': 0,
        'missing_nodes': set(),
        'node_type_stats': {
            'receipt': {'total': 0, 'valid': 0}
        }
    }
    
    # Get sets of valid node IDs for quick lookup
    valid_node_ids = set(node_df['node_id'].values)
    receipt_node_ids = set(node_df[node_df['node_type'] == 'receipt']['node_id'].values)
    
    for receipt_entry in receipt_data:
        node_id = receipt_entry['node_id']
        
        # Validate node existence and type
        node_exists = node_id in valid_node_ids
        is_receipt_node = node_id in receipt_node_ids
        
        if node_exists and is_receipt_node:
            validation_results['valid_receipts'] += 1
            validation_results['node_type_stats']['receipt']['valid'] += 1
        else:
            validation_results['invalid_receipts'] += 1
            if not node_exists or not is_receipt_node:
                validation_results['missing_nodes'].add(node_id)
    
    # Update total counts
    validation_results['node_type_stats']['receipt']['total'] = len(receipt_node_ids)
    
    return validation_results

def generate_mock_receipt_data():
    try:
        # Clear terminal at start
        clear_terminal()
        
        start_time = time.time()
        
        # Initialize Faker
        fake = Faker()
        
        # Read node_data.csv to get receipt nodes
        print("Reading node data...")
        node_df = pd.read_csv(os.path.join('src', 'data', 'input', 'node_data.csv'), usecols=['node_id', 'node_type'])
        
        # Print node type statistics
        print("\nNode Type Statistics:")
        print(f"Total number of nodes: {len(node_df)}")
        node_counts = node_df['node_type'].value_counts()
        for node_type, count in node_counts.items():
            print(f"{node_type}: {count} nodes")
        
        # Filter for receipt nodes
        receipt_nodes = node_df[node_df['node_type'] == 'receipt']
        if receipt_nodes.empty:
            print("Warning: No receipt nodes found in node_data.csv")
            return None
        
        # Initialize data list
        receipt_data = []
        
        # Generate mock data for each receipt node
        print("\nGenerating mock receipt data...")
        for _, node in tqdm(receipt_nodes.iterrows(), total=len(receipt_nodes), desc="Processing receipt nodes"):
            node_id = node['node_id']
            
            # Generate random dates within the last 5 years
            end_date = datetime.now()
            start_date = end_date - timedelta(days=5*365)
            receipt_date = fake.date_between(start_date=start_date, end_date=end_date)
            
            # Select random status pair
            status, status_std = random.choice(STATUS_PAIRS)
            
            # Generate receipt number and select random form number
            receipt_number = f"RCP-{fake.random_number(digits=8)}"
            form_number = random.choice(FORM_NUMBERS)
            
            # Create node properties JSON
            node_properties = {
                "RECEIPT_NUMBER": receipt_number,
                "FORM_NUMBER": form_number,
                "RECEIPT_DATE_ESTIMATED": receipt_date.strftime("%Y-%m-%d"),
                "STATUS": status,
                "STATUS_STD": status_std
            }
            
            # Add to data list
            receipt_data.append({
                'node_id': node_id,
                'node_name': receipt_number,
                'node_properties': node_properties
            })
        
        # Save to JSON
        output_path = os.path.join('src', 'data', 'output', 'gds', 'mock_receipt_data.json')
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(receipt_data, f, indent=2)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Validate referential integrity
        validation_results = validate_referential_integrity(receipt_data, node_df)
        
        # Print validation results
        print("\nReferential Integrity Validation Results:")
        print(f"Total receipts generated: {validation_results['total_receipts']}")
        print(f"Valid receipts: {validation_results['valid_receipts']}")
        print(f"Invalid receipts: {validation_results['invalid_receipts']}")
        
        if validation_results['missing_nodes']:
            print(f"\nMissing or invalid receipt nodes: {len(validation_results['missing_nodes'])}")
            print("Sample of missing receipt nodes:", list(validation_results['missing_nodes'])[:5])
        
        print("\nNode Type Statistics:")
        for node_type, stats in validation_results['node_type_stats'].items():
            print(f"\n{node_type.capitalize()} Nodes:")
            print(f"  Total: {stats['total']}")
            print(f"  Used in valid receipts: {stats['valid']}")
        
        print("\nReceipt Data Generation Statistics:")
        print(f"Total number of receipt nodes processed: {len(receipt_data)}")
        print(f"Processing time: {processing_time:.2f} seconds")
        print(f"Receipts per second: {len(receipt_data) / processing_time:.2f}")
        print(f"Data saved to: {output_path}")
        
        return receipt_data
        
    except Exception as e:
        print(f"Error generating mock receipt data: {str(e)}")
        return None

if __name__ == "__main__":
    receipt_data = generate_mock_receipt_data()
    if receipt_data is not None:
        print("\nSample of Generated Receipt Data:")
        print(json.dumps(receipt_data[:5], indent=2))
