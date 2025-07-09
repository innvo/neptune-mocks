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
            'organization': {'total': 0, 'valid': 0}
        },
        'edges_per_organization': {},  # Track edges per organization
        'organizations_per_organization': {}  # Track unique organizations per organization
    }
    
    # Get sets of valid node IDs for quick lookup
    valid_node_ids = set(node_df['node_id'].values)
    organization_node_ids = set(node_df[node_df['node_type'] == 'organization']['node_id'].values)
    
    # Initialize counters
    for org_id in organization_node_ids:
        validation_results['edges_per_organization'][org_id] = 0
        validation_results['organizations_per_organization'][org_id] = set()
    
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
        from_node_is_organization = from_node in organization_node_ids
        to_node_is_organization = to_node in organization_node_ids
        
        if from_node_exists and to_node_exists and from_node_is_organization and to_node_is_organization:
            validation_results['valid_edges'] += 1
            validation_results['node_type_stats']['organization']['valid'] += 1
            validation_results['edges_per_organization'][from_node] += 1
            validation_results['organizations_per_organization'][from_node].add(to_node)
        else:
            validation_results['invalid_edges'] += 1
            if not from_node_exists or not from_node_is_organization:
                validation_results['missing_from_nodes'].add(from_node)
            if not to_node_exists or not to_node_is_organization:
                validation_results['missing_to_nodes'].add(to_node)
    
    # Update total counts
    validation_results['node_type_stats']['organization']['total'] = len(organization_node_ids)
    
    return validation_results

def generate_organization_organization_edges():
    try:
        clear_terminal()
        start_time = time.time()
        
        # Read organization data from mock_organization_data.json to ensure consistency
        print("Reading organization data from mock_organization_data.json...")
        with open('src/data/output/gds/mock_organization_data.json', 'r') as f:
            organization_data = json.load(f)
        
        # Extract organization IDs from the JSON data
        organization_ids = [org['node_id'] for org in organization_data]
        print(f"Found {len(organization_ids)} organization IDs from mock_organization_data.json")
        
        # Read organization data from node_data.csv for validation
        print("Reading organization data from node_data.csv...")
        node_df = pd.read_csv('src/data/input/node_data.csv', usecols=['node_id', 'node_type'])
        
        # Get organization nodes
        organization_nodes = node_df[node_df['node_type'] == 'organization']
        if organization_nodes.empty:
            print("Warning: No organization nodes found in node_data.csv")
            return None
        
        print(f"Found {len(organization_nodes)} organization nodes")
        
        # Initialize edge data and counters
        edges = []
        missing_nodes = set()
        edge_type_count = 0
        
        # Configuration for edge generation
        # Probability that an organization will have relationships with other organizations (0.0 to 1.0)
        org_has_relationship_probability = 0.6  # 60% of organizations will have relationships
        
        # Maximum number of organizations an organization can be related to
        max_relationships_per_org = 5
        
        # Relationship types for organizations
        relationship_types = [
            'SUBSIDIARY', 'PARENT', 'PARTNER', 'COMPETITOR', 'SUPPLIER', 
            'CUSTOMER', 'AFFILIATE', 'JOINT_VENTURE', 'MERGER', 'ACQUISITION',
            'FRANCHISE', 'LICENSEE', 'LICENSOR', 'DISTRIBUTOR', 'CONTRACTOR'
        ]
        
        # Generate edges for each organization with progress bar
        print("\nGenerating organization_organization edges...")
        for org_id in tqdm(organization_ids, desc="Processing organization nodes"):
            # Determine if this organization will have relationships with other organizations
            if random.random() < org_has_relationship_probability:
                # Random number of relationships (1 to max_relationships_per_org)
                num_relationships = random.randint(1, min(max_relationships_per_org, len(organization_ids) - 1))
                
                # Select other organizations (excluding self)
                other_orgs = [oid for oid in organization_ids if oid != org_id]
                selected_orgs = random.sample(other_orgs, min(num_relationships, len(other_orgs)))
                
                for related_org_id in selected_orgs:
                    # Generate random relationship type
                    relationship_type = random.choice(relationship_types)
                    
                    # Generate random dates for the relationship
                    start_date = f"{random.randint(2010, 2024)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
                    end_date = None
                    if random.random() < 0.3:  # 30% chance of having an end date
                        end_date = f"{random.randint(2015, 2024)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
                    
                    # Generate random confidence score
                    confidence_score = round(random.uniform(0.1, 1.0), 2)
                    
                    edges.append({
                        'edge_id': str(uuid.uuid4()),
                        'node_id_from': org_id,
                        'node_id_to': related_org_id,
                        'edge_type': 'organization_organization',
                        'edge_name': 'relatedTo',
                        'edge_properties': {
                            'RELATIONSHIP_TYPE': relationship_type,
                            'RELATIONSHIP_START_DATE': start_date,
                            'RELATIONSHIP_END_DATE': end_date,
                            'CONFIDENCE_SCORE': confidence_score,
                            'SOURCE': 'VIBE'
                        }
                    })
                    edge_type_count += 1
        
        # Save all edges as a single JSON array
        os.makedirs('src/data/output/gds', exist_ok=True)
        with open('src/data/output/gds/mock_organization-organization_data.json', 'w') as f:
            json.dump(edges, f, indent=2)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Create a combined node dataframe for validation
        # Create organization nodes dataframe from mock_organization_data.json
        organization_nodes_data = []
        for org in organization_data:
            organization_nodes_data.append({
                'node_id': org['node_id'],
                'node_type': 'organization'
            })
        organization_nodes_df = pd.DataFrame(organization_nodes_data)
        
        # Validate referential integrity
        validation_results = validate_referential_integrity(edges, organization_nodes_df)
        
        clear_terminal()
        # Print validation results
        print("\nReferential Integrity Validation Results:")
        print(f"Total edges generated: {validation_results['total_edges']}")
        print(f"Valid edges: {validation_results['valid_edges']}")
        print(f"Invalid edges: {validation_results['invalid_edges']}")
        
        # Calculate and display edges per organization distribution
        edges_per_org_dist = {}
        for org_id, count in validation_results['edges_per_organization'].items():
            edges_per_org_dist[count] = edges_per_org_dist.get(count, 0) + 1
        
        print("\nDistribution of Organization Edges per Organization:")
        for count in sorted(edges_per_org_dist.keys()):
            print(f"Organizations with {count} relationship edges: {edges_per_org_dist[count]}")
        
        # Calculate and display unique organizations per organization distribution
        orgs_per_org_dist = {}
        for org_id, related_orgs in validation_results['organizations_per_organization'].items():
            num_related_orgs = len(related_orgs)
            orgs_per_org_dist[num_related_orgs] = orgs_per_org_dist.get(num_related_orgs, 0) + 1
        
        print("\nDistribution of Unique Related Organizations per Organization:")
        for count in sorted(orgs_per_org_dist.keys()):
            print(f"Organizations with {count} unique related organizations: {orgs_per_org_dist[count]}")
        
        if validation_results['missing_from_nodes']:
            print(f"\nMissing or invalid organization nodes (from): {len(validation_results['missing_from_nodes'])}")
            print("Sample of missing organization nodes:", list(validation_results['missing_from_nodes'])[:5])
        
        if validation_results['missing_to_nodes']:
            print(f"\nMissing or invalid organization nodes (to): {len(validation_results['missing_to_nodes'])}")
            print("Sample of missing organization nodes:", list(validation_results['missing_to_nodes'])[:5])
        
        print(f"\nProcessing time: {processing_time:.2f} seconds")
        print(f"Generated {len(edges)} organization-organization edges")
        print(f"Saved to src/data/output/gds/mock_organization-organization_data.json")
        
        # Print relationship type statistics
        relationship_type_stats = {}
        for edge in edges:
            rel_type = edge['edge_properties']['RELATIONSHIP_TYPE']
            relationship_type_stats[rel_type] = relationship_type_stats.get(rel_type, 0) + 1
        
        print("\nRelationship Type Statistics:")
        for rel_type, count in sorted(relationship_type_stats.items()):
            print(f"{rel_type}: {count} edges")
        
        return edges
        
    except Exception as e:
        print(f"Error generating organization-organization edges: {str(e)}")
        return None

if __name__ == "__main__":
    edges = generate_organization_organization_edges()
    if edges is not None:
        print("\nSample of Generated Edges:")
        print(json.dumps(edges[:2], indent=2))
