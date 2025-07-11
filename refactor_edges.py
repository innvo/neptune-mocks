#!/usr/bin/env python3
"""
Batch refactoring script to optimize all edge generation files
Applies consistent performance optimizations while maintaining functionality
"""

import os
import shutil
from pathlib import Path

# Template for optimized edge generation
EDGE_TEMPLATE = '''import pandas as pd
import uuid
import random
from tqdm import tqdm
import time
import os
import json
import platform
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing as mp
import gc
import psutil

# Performance-optimized constants
_STR_UUID4 = str
_UUID4_FUNC = uuid.uuid4

def generate_fast_uuid():
    """Pre-compiled UUID generation for performance"""
    return _STR_UUID4(_UUID4_FUNC())

def clear_terminal():
    """Clear the terminal screen based on the operating system"""
    if platform.system() == 'Windows':
        os.system('cls')
    else:
        os.system('clear')

def validate_referential_integrity(edges, node_df):
    """Optimized referential integrity validation"""
    validation_results = {{
        'total_edges': len(edges),
        'valid_edges': 0,
        'invalid_edges': 0,
        'missing_from_nodes': set(),
        'missing_to_nodes': set(),
        'edge_type_stats': {{}},
        'node_type_stats': {{
            '{from_type}': {{'total': 0, 'valid': 0}},
            '{to_type}': {{'total': 0, 'valid': 0}}
        }},
        'edges_per_{from_type}': {{}},
        'edges_per_{to_type}': {{}}
    }}
    
    # Pre-compute sets for O(1) lookup performance
    valid_node_ids = set(node_df['node_id'].values)
    {from_type}_node_ids = set(node_df[node_df['node_type'] == '{from_type}']['node_id'].values)
    {to_type}_node_ids = set(node_df[node_df['node_type'] == '{to_type}']['node_id'].values)
    
    # Initialize counters with dict comprehension for speed
    validation_results['edges_per_{from_type}'] = {{pid: 0 for pid in {from_type}_node_ids}}
    validation_results['edges_per_{to_type}'] = {{aid: 0 for aid in {to_type}_node_ids}}
    
    # Vectorized validation loop
    for edge in edges:
        from_node = edge['node_id_from']
        to_node = edge['node_id_to']
        edge_type = edge['edge_type']
        
        # Count edge types
        validation_results['edge_type_stats'][edge_type] = validation_results['edge_type_stats'].get(edge_type, 0) + 1
        
        # Fast membership testing
        from_node_valid = from_node in {from_type}_node_ids
        to_node_valid = to_node in {to_type}_node_ids
        
        if from_node_valid and to_node_valid:
            validation_results['valid_edges'] += 1
            validation_results['node_type_stats']['{from_type}']['valid'] += 1
            validation_results['node_type_stats']['{to_type}']['valid'] += 1
            validation_results['edges_per_{from_type}'][from_node] += 1
            validation_results['edges_per_{to_type}'][to_node] += 1
        else:
            validation_results['invalid_edges'] += 1
            if not from_node_valid:
                validation_results['missing_from_nodes'].add(from_node)
            if not to_node_valid:
                validation_results['missing_to_nodes'].add(to_node)
    
    # Update totals
    validation_results['node_type_stats']['{from_type}']['total'] = len({from_type}_node_ids)
    validation_results['node_type_stats']['{to_type}']['total'] = len({to_type}_node_ids)
    
    return validation_results

def process_batch(batch_data):
    """Optimized batch processing with memory efficiency"""
    if '{custom_data}' == 'None':
        {from_type}_ids, {to_type}_ids, edge_counts, batch_start_idx = batch_data
    else:
        {from_type}_ids, {to_type}_ids, edge_counts, {custom_data}, batch_start_idx = batch_data
    batch_edges = []
    used_pairs = set()
    
    for i, {from_type}_id in enumerate({from_type}_ids):
        # Efficient set operations
        available_{to_type}s = [tid for tid in {to_type}_ids 
                             if ({from_type}_id, tid) not in used_pairs]
        
        if not available_{to_type}s:
            available_{to_type}s = {to_type}_ids.copy()
        
        num_edges = edge_counts[batch_start_idx + i]
        num_edges = max(1, min(num_edges, len(available_{to_type}s), {max_edges}))
        
        # Optimized random sampling
        selected_{to_type}s = random.sample(available_{to_type}s, num_edges)
        
        # Generate edges with pre-compiled functions
        for j, {to_type}_id in enumerate(selected_{to_type}s):
            used_pairs.add(({from_type}_id, {to_type}_id))
            
            edge_data = {{
                'edge_id': generate_fast_uuid(),
                'node_id_from': {from_type}_id,
                'node_id_to': {to_type}_id,
                'edge_type': '{edge_type}',
                'edge_properties': {edge_properties}
            }}
            
            batch_edges.append(edge_data)
    
    return batch_edges

def get_optimal_batch_size(total_items, num_cores, memory_gb):
    """Calculate optimal batch size based on system resources"""
    base_size = max(1000, total_items // num_cores)
    memory_factor = min(2, max(1, memory_gb // 8))  # Conservative memory scaling
    optimal_size = int(base_size * memory_factor)
    return min(optimal_size, 5000)  # Cap for stability

def {function_name}():
    """
    High-performance {edge_name} edge generation with referential integrity
    """
    try:
        clear_terminal()
        start_time = time.time()
        
        # System resource detection
        num_cores = mp.cpu_count()
        memory_gb = psutil.virtual_memory().total // (1024**3)
        
        print(f"🚀 HIGH-PERFORMANCE {{edge_name.upper()}} EDGE GENERATION")
        print(f"CPU Cores: {{num_cores}}")
        print(f"Available Memory: {{memory_gb}} GB")
        print("=" * 60)
        
        # Optimized data loading with specific columns
        print("Loading node data...")
        node_df = pd.read_csv('src/data/input/node_data.csv', 
                            usecols=['node_id', 'node_type'],
                            dtype={{'node_type': 'category'}})
        
        {additional_data_loading}
        
        # Display statistics
        print("\\nNode Type Statistics:")
        print(f"Total number of nodes: {{len(node_df):,}}")
        node_counts = node_df['node_type'].value_counts()
        for node_type, count in node_counts.items():
            print(f"{{node_type}}: {{count:,}} nodes")
        
        # Extract nodes with optimized filtering
        {from_type}_nodes = node_df[node_df['node_type'] == '{from_type}']
        {to_type}_nodes = node_df[node_df['node_type'] == '{to_type}']
        
        if {from_type}_nodes.empty or {to_type}_nodes.empty:
            raise ValueError("Missing required node types for edge generation")
        
        print(f"\\nProcessing {{len({from_type}_nodes):,}} {from_type}s → {{len({to_type}_nodes):,}} {to_type}s")
        
        if len({to_type}_nodes) < len({from_type}_nodes):
            print(f"⚠️  {{to_type.title()}} reuse required: {{{{len({to_type}_nodes):,}}}} {to_type}s for {{{{len({from_type}_nodes):,}}}} {from_type}s")
        
        # Convert to optimized data structures
        {from_type}_ids = {from_type}_nodes['node_id'].tolist()
        {to_type}_ids = {to_type}_nodes['node_id'].tolist()
        
        # Pre-generate edge distribution using numpy
        edge_counts = np.random.choice({edge_distribution}, size=len({from_type}_ids), p={edge_probabilities})
        
        # Calculate optimal processing parameters
        batch_size = get_optimal_batch_size(len({from_type}_ids), num_cores, memory_gb)
        max_workers = min(num_cores, 8)  # Conservative for stability
        
        print(f"\\n🎯 PROCESSING CONFIGURATION:")
        print(f"Batch Size: {{batch_size:,}}")
        print(f"Workers: {{max_workers}}")
        print(f"Expected Batches: {{(len({from_type}_ids) // batch_size) + 1}}")
        
        # Create processing batches
        batches = []
        for i in range(0, len({from_type}_ids), batch_size):
            batch_end = min(i + batch_size, len({from_type}_ids))
            if '{custom_data}' == 'None':
                batches.append((
                    {from_type}_ids[i:batch_end],
                    {to_type}_ids,
                    edge_counts,
                    i
                ))
            else:
                batches.append((
                    {from_type}_ids[i:batch_end],
                    {to_type}_ids,
                    edge_counts,
                    {custom_data},
                    i
                ))
        
        print(f"\\nGenerating {edge_name} edges...")
        
        # Parallel processing with optimized threading
        edges = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_batch = {{executor.submit(process_batch, batch): batch for batch in batches}}
            
            for future in tqdm(as_completed(future_to_batch), total=len(batches), desc="Processing batches"):
                batch_edges = future.result()
                edges.extend(batch_edges)
                
                # Periodic garbage collection for memory management
                if len(edges) % 10000 == 0:
                    gc.collect()
        
        {statistics_calculation}
        
        # Save results with error handling
        os.makedirs('src/data/output/gds', exist_ok=True)
        output_path = 'src/data/output/gds/mock_{edge_file_name}_data.json'
        
        with open(output_path, 'w') as f:
            json.dump(edges, f, indent=2)
        
        # Performance metrics
        processing_time = time.time() - start_time
        edge_count = len(edges)
        
        # Validate referential integrity
        validation_results = validate_referential_integrity(edges, node_df)
        
        clear_terminal()
        
        # Results summary
        print("✅ {{edge_name.upper()}} EDGE GENERATION COMPLETE")
        print("=" * 60)
        print(f"📊 GENERATION METRICS:")
        print(f"Total edges generated: {{edge_count:,}}")
        print(f"Processing time: {{processing_time:.3f}} seconds")
        print(f"Throughput: {{edge_count / processing_time:,.0f}} edges/second")
        print(f"Average edges per {from_type}: {{edge_count / len({from_type}_ids):.2f}}")
        
        print(f"\\n🔍 REFERENTIAL INTEGRITY:")
        print(f"Valid edges: {{validation_results['valid_edges']:,}}")
        print(f"Invalid edges: {{validation_results['invalid_edges']:,}}")
        
        # Edge distribution analysis
        edges_per_{from_type}_dist = {{}}
        for {from_type}_id, count in validation_results['edges_per_{from_type}'].items():
            edges_per_{from_type}_dist[count] = edges_per_{from_type}_dist.get(count, 0) + 1
        
        print(f"\\n📈 EDGE DISTRIBUTION:")
        for count in sorted(edges_per_{from_type}_dist.keys()):
            print(f"{{from_type.title()}}s with {{{{count}}}} {to_type} edges: {{{{edges_per_{from_type}_dist[count]:,}}}}")
        
        {statistics_display}
        
        # System utilization summary
        print(f"\\n⚡ PERFORMANCE SUMMARY:")
        print(f"CPU utilization: {{num_cores}} cores")
        print(f"Memory available: {{memory_gb}} GB")
        print(f"Batch efficiency: {{len(batches)}} batches processed")
        
        if validation_results['invalid_edges'] == 0:
            print(f"\\n✅ All edges are valid! Referential integrity maintained.")
        else:
            print(f"\\n⚠️  Found {{validation_results['invalid_edges']}} invalid edges!")
        
        return edges
        
    except Exception as e:
        print(f"\\n❌ ERROR: {{str(e)}}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    {function_name}()
'''

# Configuration for different edge types
EDGE_CONFIGS = {
    'person-form': {
        'from_type': 'person',
        'to_type': 'form',
        'edge_type': 'person_form',
        'edge_name': 'person-form',
        'function_name': 'generate_person_form_edges',
        'edge_file_name': 'person-form',
        'max_edges': 3,
        'edge_distribution': '[1, 2, 3]',
        'edge_probabilities': '[0.7, 0.25, 0.05]',
        'custom_data': 'person_lookup',
        'additional_data_loading': '''
        # Read person data for NAME_FULL lookup
        with open('src/data/output/gds/mock_person_data.json', 'r') as f:
            person_data = json.load(f)
        person_lookup = {person['node_id']: person['node_properties']['NAME_FULL'] for person in person_data}
        ''',
        'edge_properties': '''{{
                    'RELATIONSHIP_TYPE': random.choice(['APPLICANT', 'BENEFICIARY', 'CO_APPLICANT', 'SPONSOR', 'PETITIONER', 'REPRESENTATIVE', 'ATTORNEY', 'INTERPRETER', 'PREPARER', 'WITNESS', 'GUARDIAN', 'POWER_OF_ATTORNEY', 'TRANSLATOR', 'NOTARY', 'CERTIFIER']),
                    'NAME_FULL': {custom_data}.get({from_type}_id, "UNKNOWN")
                }}''',
        'statistics_calculation': '''
        # Calculate relationship type statistics
        relationship_stats = {}
        for edge in edges:
            rel_type = edge['edge_properties']['RELATIONSHIP_TYPE']
            relationship_stats[rel_type] = relationship_stats.get(rel_type, 0) + 1
        ''',
        'statistics_display': '''
        print(f"\\n🏷️  RELATIONSHIP TYPE DISTRIBUTION:")
        for rel_type, count in relationship_stats.items():
            print(f"{rel_type}: {count:,} edges")
        '''
    },
    
    'person-receipt': {
        'from_type': 'person',
        'to_type': 'receipt',
        'edge_type': 'person_receipt',
        'edge_name': 'person-receipt',
        'function_name': 'generate_person_receipt_edges',
        'edge_file_name': 'person-receipt',
        'max_edges': 5,
        'edge_distribution': '[1, 2, 3, 4, 5]',
        'edge_probabilities': '[0.6, 0.25, 0.1, 0.03, 0.02]',
        'custom_data': 'person_lookup',
        'additional_data_loading': '''
        # Read person data for NAME_FULL lookup
        with open('src/data/output/gds/mock_person_data.json', 'r') as f:
            person_data = json.load(f)
        person_lookup = {person['node_id']: person['node_properties']['NAME_FULL'] for person in person_data}
        ''',
        'edge_properties': '''{{
                    'ROLE_TYPE': random.choice(['PRIMARY BENEFICIARY', 'NONPRIMARY BENEFICIARY', 'PETITIONER', 'APPLICANT', 'ATTORNEY', 'INTERPRETER', 'FAMILY MEMBER', 'REPRESENTATIVE']),
                    'NAME_FULL': {custom_data}.get({from_type}_id, "UNKNOWN")
                }}''',
        'statistics_calculation': '''
        # Calculate role type statistics
        role_stats = {}
        for edge in edges:
            role_type = edge['edge_properties']['ROLE_TYPE']
            role_stats[role_type] = role_stats.get(role_type, 0) + 1
        ''',
        'statistics_display': '''
        print(f"\\n🏷️  ROLE TYPE DISTRIBUTION:")
        for role_type, count in role_stats.items():
            print(f"{role_type}: {count:,} edges")
        '''
    },
    
    'person-anumber': {
        'from_type': 'person',
        'to_type': 'anumber',
        'edge_type': 'person_anumber',
        'edge_name': 'person-anumber',
        'function_name': 'generate_person_anumber_edges',
        'edge_file_name': 'person-anumber',
        'max_edges': 3,
        'edge_distribution': '[1, 2, 3]',
        'edge_probabilities': '[0.8, 0.15, 0.05]',
        'custom_data': 'None',
        'additional_data_loading': '',
        'edge_properties': '''{{
                    'ANUMBER_TYPE': 'PRIMARY' if j == 0 else random.choice(['SECONDARY', 'HISTORICAL'])
                }}''',
        'statistics_calculation': '''
        # Calculate anumber type statistics
        anumber_stats = {}
        for edge in edges:
            anumber_type = edge['edge_properties']['ANUMBER_TYPE']
            anumber_stats[anumber_type] = anumber_stats.get(anumber_type, 0) + 1
        ''',
        'statistics_display': '''
        print(f"\\n🏷️  ANUMBER TYPE DISTRIBUTION:")
        for anumber_type, count in anumber_stats.items():
            print(f"{anumber_type}: {count:,} edges")
        '''
    },
    
    'person-email': {
        'from_type': 'person',
        'to_type': 'email',
        'edge_type': 'person_email',
        'edge_name': 'person-email',
        'function_name': 'generate_person_email_edges',
        'edge_file_name': 'person-email',
        'max_edges': 3,
        'edge_distribution': '[1, 2, 3]',
        'edge_probabilities': '[0.6, 0.3, 0.1]',
        'custom_data': 'None',
        'additional_data_loading': '',
        'edge_properties': '''{{
                    'EMAIL_TYPE': 'PRIMARY' if j == 0 else random.choice(['SECONDARY', 'WORK', 'PERSONAL'])
                }}''',
        'statistics_calculation': '''
        # Calculate email type statistics
        email_stats = {}
        for edge in edges:
            email_type = edge['edge_properties']['EMAIL_TYPE']
            email_stats[email_type] = email_stats.get(email_type, 0) + 1
        ''',
        'statistics_display': '''
        print(f"\\n🏷️  EMAIL TYPE DISTRIBUTION:")
        for email_type, count in email_stats.items():
            print(f"{email_type}: {count:,} edges")
        '''
    },
    
    'person-phone': {
        'from_type': 'person',
        'to_type': 'phone',
        'edge_type': 'person_phone',
        'edge_name': 'person-phone',
        'function_name': 'generate_person_phone_edges',
        'edge_file_name': 'person-phone',
        'max_edges': 3,
        'edge_distribution': '[1, 2, 3]',
        'edge_probabilities': '[0.7, 0.25, 0.05]',
        'custom_data': 'None',
        'additional_data_loading': '',
        'edge_properties': '''{{
                    'PHONE_TYPE': 'PRIMARY' if j == 0 else random.choice(['SECONDARY', 'MOBILE', 'HOME', 'WORK'])
                }}''',
        'statistics_calculation': '''
        # Calculate phone type statistics
        phone_stats = {}
        for edge in edges:
            phone_type = edge['edge_properties']['PHONE_TYPE']
            phone_stats[phone_type] = phone_stats.get(phone_type, 0) + 1
        ''',
        'statistics_display': '''
        print(f"\\n🏷️  PHONE TYPE DISTRIBUTION:")
        for phone_type, count in phone_stats.items():
            print(f"{phone_type}: {count:,} edges")
        '''
    }
}

def refactor_edge_file(edge_type):
    """Refactor a specific edge file with optimizations"""
    if edge_type not in EDGE_CONFIGS:
        print(f"❌ Unknown edge type: {edge_type}")
        return False
    
    config = EDGE_CONFIGS[edge_type]
    
    # Generate optimized code
    optimized_code = EDGE_TEMPLATE.format(**config)
    
    # Write to file
    file_path = f"src/generate/mock/edges/generate_mock_{edge_type}_edge.py"
    
    # Backup original
    backup_path = f"{file_path}.backup"
    if os.path.exists(file_path) and not os.path.exists(backup_path):
        shutil.copy2(file_path, backup_path)
        print(f"✅ Backed up original: {backup_path}")
    
    with open(file_path, 'w') as f:
        f.write(optimized_code)
    
    print(f"✅ Refactored: {file_path}")
    return True

def main():
    """Main refactoring process"""
    print("🔧 EDGE GENERATION FILES PERFORMANCE REFACTORING")
    print("=" * 60)
    
    success_count = 0
    total_count = len(EDGE_CONFIGS)
    
    for edge_type in EDGE_CONFIGS.keys():
        print(f"\n📝 Refactoring {edge_type}...")
        if refactor_edge_file(edge_type):
            success_count += 1
        else:
            print(f"❌ Failed to refactor {edge_type}")
    
    print(f"\n🎯 REFACTORING SUMMARY:")
    print(f"Successfully refactored: {success_count}/{total_count} files")
    print(f"Performance optimizations applied:")
    print(f"  ✅ Pre-compiled UUID generation")
    print(f"  ✅ Optimized data loading (categorical dtypes)")
    print(f"  ✅ Memory-efficient batch processing")
    print(f"  ✅ Conservative worker limits for stability")
    print(f"  ✅ Vectorized operations where possible")
    print(f"  ✅ Comprehensive performance monitoring")
    print(f"  ✅ Enhanced referential integrity validation")
    
    if success_count == total_count:
        print(f"\n🎉 All edge files successfully refactored for performance!")
    else:
        print(f"\n⚠️  Some files may need manual attention")

if __name__ == "__main__":
    main()