import pandas as pd
import uuid
import random
from tqdm import tqdm
import time
import os
import json
import platform
import subprocess

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
            'datainstance': {'total': 0, 'valid': 0}
        },
        'edges_per_person': {},  # New field to track edges per person
        'persons_with_no_edges': 0  # Track persons without any datainstance edges
    }
    
    # Get sets of valid node IDs for quick lookup
    valid_node_ids = set(node_df['node_id'].values)
    person_node_ids = set(node_df[node_df['node_type'] == 'person']['node_id'].values)
    datainstance_node_ids = set(node_df[node_df['node_type'] == 'datainstance']['node_id'].values)
    
    # Initialize edges_per_person counter
    for person_id in person_node_ids:
        validation_results['edges_per_person'][person_id] = 0
    
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
        to_node_is_datainstance = to_node in datainstance_node_ids
        
        if from_node_exists and to_node_exists and from_node_is_person and to_node_is_datainstance:
            validation_results['valid_edges'] += 1
            validation_results['node_type_stats']['person']['valid'] += 1
            validation_results['node_type_stats']['datainstance']['valid'] += 1
            validation_results['edges_per_person'][from_node] += 1
        else:
            validation_results['invalid_edges'] += 1
            if not from_node_exists or not from_node_is_person:
                validation_results['missing_from_nodes'].add(from_node)
            if not to_node_exists or not to_node_is_datainstance:
                validation_results['missing_to_nodes'].add(to_node)
    
    # Count persons with no edges
    for person_id in person_node_ids:
        if validation_results['edges_per_person'][person_id] == 0:
            validation_results['persons_with_no_edges'] += 1
    
    # Update total counts
    validation_results['node_type_stats']['person']['total'] = len(person_node_ids)
    validation_results['node_type_stats']['datainstance']['total'] = len(datainstance_node_ids)
    
    return validation_results

def generate_person_datainstance_edges():
    try:
        clear_terminal()
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
        
        # Get datainstance nodes
        datainstance_nodes = node_df[node_df['node_type'] == 'datainstance']
        if datainstance_nodes.empty:
            print("Warning: No datainstance nodes found in node_data.csv")
            print("Note: You may need to add 'datainstance' to NODE_TYPES in generate_node_data.py")
            return None
        
        print(f"\nFound {len(person_nodes)} person nodes and {len(datainstance_nodes)} datainstance nodes")
        
        # Check if we have enough datainstance nodes for all persons
        if len(datainstance_nodes) < len(person_nodes):
            print(f"\nWARNING: Only {len(datainstance_nodes)} datainstance nodes available for {len(person_nodes)} persons")
            print("This means some datainstance nodes will be shared across multiple persons")
        
        # Initialize edge data and counters
        edges = []
        missing_nodes = set()
        edge_type_count = 0
        datainstance_type_stats = {'SERVICEPROVIDER': 0, 'STAKEHOLDER': 0}
        
        # Track used person-datainstance pairs to avoid duplicates
        used_pairs = set()
        
        # Generate edges for each person with progress bar
        print("\nGenerating person_datainstance edges...")
        for _, person in tqdm(person_nodes.iterrows(), total=len(person_nodes), desc="Processing person nodes"):
            person_id = person['node_id']
            
            # Get available datainstances that haven't been used with this person
            available_datainstances = []
            for _, datainstance in datainstance_nodes.iterrows():
                datainstance_id = datainstance['node_id']
                pair_key = (person_id, datainstance_id)
                if pair_key not in used_pairs and validate_node_existence(node_df, datainstance_id):
                    available_datainstances.append(datainstance)
            
            # If no available datainstances, we need to reuse some (this ensures every person gets at least 1 edge)
            if len(available_datainstances) == 0:
                print(f"\nWARNING: No available datainstances for person {person_id}, reusing existing datainstances")
                # Reset used_pairs for this person to allow reuse
                for _, datainstance in datainstance_nodes.iterrows():
                    datainstance_id = datainstance['node_id']
                    if validate_node_existence(node_df, datainstance_id):
                        available_datainstances.append(datainstance)
            
            # Ensure every person has at least 1 datainstance edge
            if len(available_datainstances) > 0:
                # Most people have 1-3 datainstances, some have more
                num_datainstance_edges = random.choices([1, 2, 3, 4], weights=[0.6, 0.25, 0.1, 0.05])[0]
                
                # Limit the number of edges to available datainstances
                num_datainstance_edges = min(num_datainstance_edges, len(available_datainstances))
                
                # Randomly select datainstances without replacement
                selected_datainstances = random.sample(available_datainstances, num_datainstance_edges)
                
                for datainstance in selected_datainstances:
                    datainstance_id = datainstance['node_id']
                    
                    # Double-check validation and add to used pairs
                    if validate_node_existence(node_df, datainstance_id):
                        pair_key = (person_id, datainstance_id)
                        used_pairs.add(pair_key)
                        
                        # Determine datainstance type
                        datainstance_type = random.choice(["SERVICEPROVIDER", "STAKEHOLDER"])
                        
                        edges.append({
                            'edge_id': str(uuid.uuid4()),
                            'node_id_from': person_id,
                            'node_id_to': datainstance_id,
                            'edge_type': 'person_datainstance',
                            'edge_properties': {
                                'CONFIDENCE_SCORE': round(random.uniform(0.1, 1.0), 2)
                            }
                        })
                        edge_type_count += 1
                        datainstance_type_stats[datainstance_type] += 1
                    else:
                        missing_nodes.add(datainstance_id)
            else:
                print(f"\nERROR: No datainstance nodes available for person {person_id}")
        
        # Save all edges as a single JSON array
        os.makedirs('src/data/output/gds', exist_ok=True)
        with open('src/data/output/gds/mock_person-datainstance_data.json', 'w') as f:
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
        print(f"Persons with no datainstance edges: {validation_results['persons_with_no_edges']}")
        
        # Calculate and display edges per person distribution
        edges_per_person_dist = {}
        for person_id, count in validation_results['edges_per_person'].items():
            edges_per_person_dist[count] = edges_per_person_dist.get(count, 0) + 1
        
        print("\nDistribution of DataInstance Edges per Person:")
        for count in sorted(edges_per_person_dist.keys()):
            print(f"Persons with {count} datainstance edges: {edges_per_person_dist[count]}")
        
        # Verify that every person has at least 1 edge
        persons_with_edges = sum(1 for count in edges_per_person_dist.values() if count > 0)
        total_persons = len(person_nodes)
        print(f"\n✅ {persons_with_edges}/{total_persons} persons have at least 1 datainstance edge")
        
        if validation_results['missing_from_nodes']:
            print(f"\nMissing or invalid person nodes: {len(validation_results['missing_from_nodes'])}")
            print("Sample of missing person nodes:", list(validation_results['missing_from_nodes'])[:5])
        
        if validation_results['missing_to_nodes']:
            print(f"\nMissing or invalid datainstance nodes: {len(validation_results['missing_to_nodes'])}")
            print("Sample of missing datainstance nodes:", list(validation_results['missing_to_nodes'])[:5])
        
        print("\nNode Type Statistics:")
        for node_type, stats in validation_results['node_type_stats'].items():
            print(f"\n{node_type.capitalize()} Nodes:")
            print(f"  Total: {stats['total']}")
            print(f"  Used in valid edges: {stats['valid']}")
        
        print("\nDataInstance Type Statistics:")
        for datainstance_type, count in datainstance_type_stats.items():
            print(f"{datainstance_type}: {count} edges")
        
        print("\nEdge Generation Statistics:")
        print(f"Total number of person_datainstance edges generated: {edge_type_count}")
        print(f"Processing time: {processing_time:.2f} seconds")
        print(f"Edges per second: {edge_type_count / processing_time:.2f}")
        
        # Read the final edge file to get the complete DataFrame
        with open('src/data/output/gds/mock_person-datainstance_data.json', 'r') as f:
            edges_data = json.load(f)
        final_edge_df = pd.DataFrame(edges_data)
        return final_edge_df
        
    except Exception as e:
        print(f"Error generating edges: {str(e)}")
        return None

if __name__ == "__main__":
    edge_df = generate_person_datainstance_edges()
    if edge_df is not None:
        print("\nSample of Generated Edges:")
        print(edge_df.head())
