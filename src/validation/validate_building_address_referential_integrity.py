#!/usr/bin/env python3
"""
Validate referential integrity of building-address edges against building and address nodes.

This script checks that:
1. All node_id_from in building-address edges exist in building_data.json
2. All node_id_to in building-address edges exist in address_data.json
3. No orphaned edges exist
"""

import json
import sys
from pathlib import Path
from typing import Dict, Set, List, Tuple


def load_json_file(file_path: str) -> List[Dict]:
    """Load and parse a JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found - {file_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {file_path} - {e}")
        sys.exit(1)


def extract_node_ids(data: List[Dict], id_field: str = "node_id") -> Set[str]:
    """Extract node IDs from a list of node dictionaries."""
    return {item[id_field] for item in data}


def validate_referential_integrity(
    edges_data: List[Dict],
    building_data: List[Dict],
    address_data: List[Dict]
) -> Tuple[bool, Dict]:
    """
    Validate referential integrity of building-address edges.
    
    Returns:
        Tuple of (is_valid, validation_results)
    """
    # Extract node IDs from building and address data
    building_ids = extract_node_ids(building_data)
    address_ids = extract_node_ids(address_data)
    
    # Extract edge information
    edge_ids = set()
    from_ids = set()
    to_ids = set()
    orphaned_edges = []
    
    for edge in edges_data:
        edge_id = edge.get("edge_id")
        node_id_from = edge.get("node_id_from")
        node_id_to = edge.get("node_id_to")
        
        edge_ids.add(edge_id)
        from_ids.add(node_id_from)
        to_ids.add(node_id_to)
        
        # Check if this edge has orphaned nodes
        if node_id_from not in building_ids or node_id_to not in address_ids:
            orphaned_edges.append({
                "edge_id": edge_id,
                "node_id_from": node_id_from,
                "node_id_to": node_id_to,
                "from_exists": node_id_from in building_ids,
                "to_exists": node_id_to in address_ids
            })
    
    # Find missing building nodes (referenced in edges but not in building data)
    missing_building_ids = from_ids - building_ids
    
    # Find missing address nodes (referenced in edges but not in address data)
    missing_address_ids = to_ids - address_ids
    
    # Check for orphaned building nodes (in building data but not referenced in edges)
    orphaned_building_ids = building_ids - from_ids
    
    # Check for orphaned address nodes (in address data but not referenced in edges)
    orphaned_address_ids = address_ids - to_ids
    
    # Compile results
    results = {
        "total_edges": len(edges_data),
        "total_buildings": len(building_data),
        "total_addresses": len(address_data),
        "unique_building_ids_in_edges": len(from_ids),
        "unique_address_ids_in_edges": len(to_ids),
        "missing_building_ids": list(missing_building_ids),
        "missing_address_ids": list(missing_address_ids),
        "orphaned_building_ids": list(orphaned_building_ids),
        "orphaned_address_ids": list(orphaned_address_ids),
        "orphaned_edges": orphaned_edges,
        "is_valid": len(missing_building_ids) == 0 and len(missing_address_ids) == 0
    }
    
    return results["is_valid"], results


def print_validation_results(results: Dict):
    """Print validation results in a formatted way."""
    print("=" * 80)
    print("BUILDING-ADDRESS REFERENTIAL INTEGRITY VALIDATION")
    print("=" * 80)
    
    print(f"\nSUMMARY:")
    print(f"  Total edges: {results['total_edges']}")
    print(f"  Total buildings: {results['total_buildings']}")
    print(f"  Total addresses: {results['total_addresses']}")
    print(f"  Unique building IDs in edges: {results['unique_building_ids_in_edges']}")
    print(f"  Unique address IDs in edges: {results['unique_address_ids_in_edges']}")
    
    print(f"\nVALIDATION STATUS: {'✅ PASSED' if results['is_valid'] else '❌ FAILED'}")
    
    if not results['is_valid']:
        print(f"\n❌ REFERENTIAL INTEGRITY ISSUES FOUND:")
        
        if results['missing_building_ids']:
            print(f"\n  Missing building IDs ({len(results['missing_building_ids'])}):")
            for building_id in results['missing_building_ids'][:10]:  # Show first 10
                print(f"    - {building_id}")
            if len(results['missing_building_ids']) > 10:
                print(f"    ... and {len(results['missing_building_ids']) - 10} more")
        
        if results['missing_address_ids']:
            print(f"\n  Missing address IDs ({len(results['missing_address_ids'])}):")
            for address_id in results['missing_address_ids'][:10]:  # Show first 10
                print(f"    - {address_id}")
            if len(results['missing_address_ids']) > 10:
                print(f"    ... and {len(results['missing_address_ids']) - 10} more")
        
        if results['orphaned_edges']:
            print(f"\n  Orphaned edges ({len(results['orphaned_edges'])}):")
            for edge in results['orphaned_edges'][:5]:  # Show first 5
                print(f"    - Edge {edge['edge_id']}:")
                print(f"      From: {edge['node_id_from']} (exists: {edge['from_exists']})")
                print(f"      To: {edge['node_id_to']} (exists: {edge['to_exists']})")
            if len(results['orphaned_edges']) > 5:
                print(f"    ... and {len(results['orphaned_edges']) - 5} more")
    
    # Show orphaned nodes (nodes that exist but aren't referenced in edges)
    if results['orphaned_building_ids']:
        print(f"\n⚠️  Orphaned building nodes ({len(results['orphaned_building_ids'])}):")
        print(f"    These building nodes exist but are not referenced in any edges")
        for building_id in results['orphaned_building_ids'][:5]:  # Show first 5
            print(f"    - {building_id}")
        if len(results['orphaned_building_ids']) > 5:
            print(f"    ... and {len(results['orphaned_building_ids']) - 5} more")
    
    if results['orphaned_address_ids']:
        print(f"\n⚠️  Orphaned address nodes ({len(results['orphaned_address_ids'])}):")
        print(f"    These address nodes exist but are not referenced in any edges")
        for address_id in results['orphaned_address_ids'][:5]:  # Show first 5
            print(f"    - {address_id}")
        if len(results['orphaned_address_ids']) > 5:
            print(f"    ... and {len(results['orphaned_address_ids']) - 5} more")
    
    print("\n" + "=" * 80)


def main():
    """Main validation function."""
    # Define file paths
    base_path = Path("src/data/output/gds")
    edges_file = base_path / "mock_building-address_data.json"
    building_file = base_path / "mock_building_data.json"
    address_file = base_path / "mock_address_data.json"
    
    print(f"Loading data files...")
    print(f"  Edges: {edges_file}")
    print(f"  Buildings: {building_file}")
    print(f"  Addresses: {address_file}")
    
    # Load data
    edges_data = load_json_file(edges_file)
    building_data = load_json_file(building_file)
    address_data = load_json_file(address_file)
    
    print(f"Loaded {len(edges_data)} edges, {len(building_data)} buildings, {len(address_data)} addresses")
    
    # Validate referential integrity
    is_valid, results = validate_referential_integrity(edges_data, building_data, address_data)
    
    # Print results
    print_validation_results(results)
    
    # Exit with appropriate code
    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main() 