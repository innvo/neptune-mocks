import pandas as pd

def validate_person_address_edges():
    try:
        # Read the node data
        print("Reading person nodes...")
        person_nodes_df = pd.read_csv('src/data/output/neptune/neptune_person_nodes_gremlin.csv')
        person_ids = set(person_nodes_df['~id'])
        print(f"Found {len(person_ids)} unique person nodes")
        
        print("\nReading address nodes...")
        address_nodes_df = pd.read_csv('src/data/output/neptune/neptune_address_nodes_gremlin.csv')
        address_ids = set(address_nodes_df['~id'])
        print(f"Found {len(address_ids)} unique address nodes")
        
        # Read the edge data
        print("\nReading person-address edges...")
        edges_df = pd.read_csv('src/data/output/neptune/neptune_person_address_edges_gremlin.csv')
        print(f"Found {len(edges_df)} edges to validate")
        
        # Check for missing source nodes (person IDs)
        missing_from = set(edges_df['~from']) - person_ids
        if missing_from:
            print(f"\nERROR: Found {len(missing_from)} edges with missing source nodes:")
            for node_id in missing_from:
                print(f"  - Edge source node {node_id} not found in person nodes file")
        
        # Check for missing target nodes (address IDs)
        missing_to = set(edges_df['~to']) - address_ids
        if missing_to:
            print(f"\nERROR: Found {len(missing_to)} edges with missing target nodes:")
            for node_id in missing_to:
                print(f"  - Edge target node {node_id} not found in address nodes file")
        
        # Print summary
        total_errors = len(missing_from) + len(missing_to)
        if total_errors == 0:
            print("\nSUCCESS: All person-address edges have valid source and target nodes!")
        else:
            print(f"\nFAILURE: Found {total_errors} referential integrity errors in person-address edges")
            print(f"  - {len(missing_from)} missing source nodes")
            print(f"  - {len(missing_to)} missing target nodes")
        
        return total_errors == 0
        
    except FileNotFoundError as e:
        print(f"Error: Required file not found - {str(e)}")
        return False
    except Exception as e:
        print(f"Error during validation: {str(e)}")
        return False

def validate_person_receipt_edges():
    try:
        # Read the node data
        print("\nReading person nodes...")
        person_nodes_df = pd.read_csv('src/data/output/neptune/neptune_person_nodes_gremlin.csv')
        person_ids = set(person_nodes_df['~id'])
        print(f"Found {len(person_ids)} unique person nodes")
        
        print("\nReading receipt nodes...")
        receipt_nodes_df = pd.read_csv('src/data/output/neptune/neptune_receipt_nodes_gremlin.csv')
        receipt_ids = set(receipt_nodes_df['~id'])
        print(f"Found {len(receipt_ids)} unique receipt nodes")
        
        # Read the edge data
        print("\nReading person-receipt edges...")
        edges_df = pd.read_csv('src/data/output/neptune/neptune_person_receipt_edges_gremlin.csv')
        print(f"Found {len(edges_df)} edges to validate")
        
        # Check for missing source nodes (person IDs)
        missing_from = set(edges_df['~from']) - person_ids
        if missing_from:
            print(f"\nERROR: Found {len(missing_from)} edges with missing source nodes:")
            for node_id in missing_from:
                print(f"  - Edge source node {node_id} not found in person nodes file")
        
        # Check for missing target nodes (receipt IDs)
        missing_to = set(edges_df['~to']) - receipt_ids
        if missing_to:
            print(f"\nERROR: Found {len(missing_to)} edges with missing target nodes:")
            for node_id in missing_to:
                print(f"  - Edge target node {node_id} not found in receipt nodes file")
        
        # Print summary
        total_errors = len(missing_from) + len(missing_to)
        if total_errors == 0:
            print("\nSUCCESS: All person-receipt edges have valid source and target nodes!")
        else:
            print(f"\nFAILURE: Found {total_errors} referential integrity errors in person-receipt edges")
            print(f"  - {len(missing_from)} missing source nodes")
            print(f"  - {len(missing_to)} missing target nodes")
        
        return total_errors == 0
        
    except FileNotFoundError as e:
        print(f"Error: Required file not found - {str(e)}")
        return False
    except Exception as e:
        print(f"Error during validation: {str(e)}")
        return False

def validate_building_address_edges():
    try:
        # Read the node data
        print("\nReading building nodes...")
        building_nodes_df = pd.read_csv('src/data/output/neptune/neptune_building_nodes_gremlin.csv')
        building_ids = set(building_nodes_df['~id'])
        print(f"Found {len(building_ids)} unique building nodes")
        
        print("\nReading address nodes...")
        address_nodes_df = pd.read_csv('src/data/output/neptune/neptune_address_nodes_gremlin.csv')
        address_ids = set(address_nodes_df['~id'])
        print(f"Found {len(address_ids)} unique address nodes")
        
        # Read the edge data
        print("\nReading building-address edges...")
        edges_df = pd.read_csv('src/data/output/neptune/neptune_building-address_edges_gremlin.csv')
        print(f"Found {len(edges_df)} edges to validate")
        
        # Check for missing source nodes (building IDs)
        missing_from = set(edges_df['~from']) - building_ids
        if missing_from:
            print(f"\nERROR: Found {len(missing_from)} edges with missing source nodes:")
            for node_id in missing_from:
                print(f"  - Edge source node {node_id} not found in building nodes file")
        
        # Check for missing target nodes (address IDs)
        missing_to = set(edges_df['~to']) - address_ids
        if missing_to:
            print(f"\nERROR: Found {len(missing_to)} edges with missing target nodes:")
            for node_id in missing_to:
                print(f"  - Edge target node {node_id} not found in address nodes file")
        
        # Print summary
        total_errors = len(missing_from) + len(missing_to)
        if total_errors == 0:
            print("\nSUCCESS: All building-address edges have valid source and target nodes!")
        else:
            print(f"\nFAILURE: Found {total_errors} referential integrity errors in building-address edges")
            print(f"  - {len(missing_from)} missing source nodes")
            print(f"  - {len(missing_to)} missing target nodes")
        
        return total_errors == 0
        
    except FileNotFoundError as e:
        print(f"Error: Required file not found - {str(e)}")
        return False
    except Exception as e:
        print(f"Error during validation: {str(e)}")
        return False

def validate_person_organization_edges():
    try:
        # Read the node data
        print("\nReading person nodes...")
        person_nodes_df = pd.read_csv('src/data/output/neptune/neptune_person_nodes_gremlin.csv')
        person_ids = set(person_nodes_df['~id'])
        print(f"Found {len(person_ids)} unique person nodes")
        
        print("\nReading organization nodes...")
        organization_nodes_df = pd.read_csv('src/data/output/neptune/nepture_organization_nodes_gremlin.csv')
        organization_ids = set(organization_nodes_df['~id'])
        print(f"Found {len(organization_ids)} unique organization nodes")
        
        # Read the edge data
        print("\nReading person-organization edges...")
        edges_df = pd.read_csv('src/data/output/neptune/neptune_person_organization_edges_gremlin.csv')
        print(f"Found {len(edges_df)} edges to validate")
        
        # Check for missing source nodes (person IDs)
        missing_from = set(edges_df['~from']) - person_ids
        if missing_from:
            print(f"\nERROR: Found {len(missing_from)} edges with missing source nodes:")
            for node_id in missing_from:
                print(f"  - Edge source node {node_id} not found in person nodes file")
        
        # Check for missing target nodes (organization IDs)
        missing_to = set(edges_df['~to']) - organization_ids
        if missing_to:
            print(f"\nERROR: Found {len(missing_to)} edges with missing target nodes:")
            for node_id in missing_to:
                print(f"  - Edge target node {node_id} not found in organization nodes file")
        
        # Print summary
        total_errors = len(missing_from) + len(missing_to)
        if total_errors == 0:
            print("\nSUCCESS: All person-organization edges have valid source and target nodes!")
        else:
            print(f"\nFAILURE: Found {total_errors} referential integrity errors in person-organization edges")
            print(f"  - {len(missing_from)} missing source nodes")
            print(f"  - {len(missing_to)} missing target nodes")
        
        return total_errors == 0
        
    except FileNotFoundError as e:
        print(f"Error: Required file not found - {str(e)}")
        return False
    except Exception as e:
        print(f"Error during validation: {str(e)}")
        return False

def validate_organization_address_edges():
    try:
        # Read the node data
        print("\nReading organization nodes...")
        organization_nodes_df = pd.read_csv('src/data/output/neptune/nepture_organization_nodes_gremlin.csv')
        organization_ids = set(organization_nodes_df['~id'])
        print(f"Found {len(organization_ids)} unique organization nodes")
        
        print("\nReading address nodes...")
        address_nodes_df = pd.read_csv('src/data/output/neptune/neptune_address_nodes_gremlin.csv')
        address_ids = set(address_nodes_df['~id'])
        print(f"Found {len(address_ids)} unique address nodes")
        
        # Read the edge data
        print("\nReading organization-address edges...")
        edges_df = pd.read_csv('src/data/output/neptune/neptune_organization-address_edges_gremlin.csv')
        print(f"Found {len(edges_df)} edges to validate")
        
        # Check for missing source nodes (organization IDs)
        missing_from = set(edges_df['~from']) - organization_ids
        if missing_from:
            print(f"\nERROR: Found {len(missing_from)} edges with missing source nodes:")
            for node_id in missing_from:
                print(f"  - Edge source node {node_id} not found in organization nodes file")
        
        # Check for missing target nodes (address IDs)
        missing_to = set(edges_df['~to']) - address_ids
        if missing_to:
            print(f"\nERROR: Found {len(missing_to)} edges with missing target nodes:")
            for node_id in missing_to:
                print(f"  - Edge target node {node_id} not found in address nodes file")
        
        # Print summary
        total_errors = len(missing_from) + len(missing_to)
        if total_errors == 0:
            print("\nSUCCESS: All organization-address edges have valid source and target nodes!")
        else:
            print(f"\nFAILURE: Found {total_errors} referential integrity errors in organization-address edges")
            print(f"  - {len(missing_from)} missing source nodes")
            print(f"  - {len(missing_to)} missing target nodes")
        
        return total_errors == 0
        
    except FileNotFoundError as e:
        print(f"Error: Required file not found - {str(e)}")
        return False
    except Exception as e:
        print(f"Error during validation: {str(e)}")
        return False

def validate_edges():
    print("\n=== Starting Gremlin CSV Validation ===")
    
    # Store validation results
    validation_results = {}
    
    # Run validations and store results
    validation_results['person_address'] = validate_person_address_edges()
    validation_results['person_receipt'] = validate_person_receipt_edges()
    validation_results['building_address'] = validate_building_address_edges()
    validation_results['person_organization'] = validate_person_organization_edges()
    validation_results['organization_address'] = validate_organization_address_edges()
    
    # Print comprehensive summary
    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)
    
    all_passed = True
    for edge_type, passed in validation_results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{edge_type.replace('_', '-').title()} Edges: {status}")
        if not passed:
            all_passed = False
    
    print("-" * 60)
    if all_passed:
        print("🎉 ALL VALIDATIONS PASSED - Referential integrity is maintained!")
    else:
        print("⚠️  SOME VALIDATIONS FAILED - Referential integrity issues detected!")
    
    print("="*60)
    
    return all_passed

if __name__ == "__main__":
    validate_edges() 