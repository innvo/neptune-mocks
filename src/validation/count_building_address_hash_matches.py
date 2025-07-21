import json
import os
from collections import defaultdict

def count_building_address_hash_matches():
    """
    Count the number of building NODE_IDs where building ADDRESS_HASH matches address ADDRESS_HASH
    """
    try:
        # Read building data
        building_data_path = os.path.join('src', 'data', 'output', 'gds', 'mock_building_data.json')
        if not os.path.exists(building_data_path):
            print(f"Error: Building data file not found at {building_data_path}")
            return None
        
        with open(building_data_path, 'r') as f:
            building_data = json.load(f)
        
        # Read address data
        address_data_path = os.path.join('src', 'data', 'output', 'gds', 'mock_address_data.json')
        if not os.path.exists(address_data_path):
            print(f"Error: Address data file not found at {address_data_path}")
            return None
        
        with open(address_data_path, 'r') as f:
            address_data = json.load(f)
        
        print(f"Loaded {len(building_data)} building records")
        print(f"Loaded {len(address_data)} address records")
        
        # Create a mapping of ADDRESS_FULL to ADDRESS_HASH for addresses
        address_hash_map = {}
        for addr in address_data:
            address_full = addr['node_properties'].get('ADDRESS_FULL', '')
            address_hash = addr['node_properties'].get('ADDRESS_HASH', '')
            if address_full and address_hash:
                address_hash_map[address_full] = address_hash
        
        print(f"Created address hash mapping for {len(address_hash_map)} unique addresses")
        
        # Count matches and mismatches
        matches = []
        mismatches = []
        missing_addresses = []
        
        for building in building_data:
            building_id = building['node_id']
            building_address_full = building['node_properties'].get('ADDRESS_FULL', '')
            building_address_hash = building['node_properties'].get('ADDRESS_HASH', '')
            
            if building_address_full in address_hash_map:
                original_address_hash = address_hash_map[building_address_full]
                
                if building_address_hash == original_address_hash:
                    matches.append({
                        'building_id': building_id,
                        'address_full': building_address_full,
                        'address_hash': building_address_hash
                    })
                else:
                    mismatches.append({
                        'building_id': building_id,
                        'building_address_full': building_address_full,
                        'building_address_hash': building_address_hash,
                        'original_address_hash': original_address_hash
                    })
            else:
                missing_addresses.append({
                    'building_id': building_id,
                    'building_address_full': building_address_full,
                    'building_address_hash': building_address_hash
                })
        
        # Print results
        print("\n" + "="*60)
        print("BUILDING ADDRESS_HASH MATCHING RESULTS")
        print("="*60)
        print(f"Total buildings processed: {len(building_data)}")
        print(f"Buildings with matching ADDRESS_HASH: {len(matches)}")
        print(f"Buildings with mismatched ADDRESS_HASH: {len(mismatches)}")
        print(f"Buildings with missing addresses: {len(missing_addresses)}")
        print(f"Match percentage: {(len(matches) / len(building_data) * 100):.2f}%")
        
        if matches:
            print(f"\n✅ MATCHES ({len(matches)} buildings):")
            print("Building NODE_IDs with matching ADDRESS_HASH:")
            for match in matches[:10]:  # Show first 10
                print(f"  {match['building_id']} -> {match['address_hash'][:16]}...")
            if len(matches) > 10:
                print(f"  ... and {len(matches) - 10} more")
        
        if mismatches:
            print(f"\n❌ MISMATCHES ({len(mismatches)} buildings):")
            print("Building NODE_IDs with mismatched ADDRESS_HASH:")
            for mismatch in mismatches[:5]:  # Show first 5
                print(f"  {mismatch['building_id']}")
                print(f"    Building hash: {mismatch['building_address_hash']}")
                print(f"    Address hash:  {mismatch['original_address_hash']}")
                print()
            if len(mismatches) > 5:
                print(f"  ... and {len(mismatches) - 5} more mismatches")
        
        if missing_addresses:
            print(f"\n⚠️  MISSING ADDRESSES ({len(missing_addresses)} buildings):")
            print("Building NODE_IDs with addresses not found in address data:")
            for missing in missing_addresses[:5]:  # Show first 5
                print(f"  {missing['building_id']} -> {missing['building_address_full'][:50]}...")
            if len(missing_addresses) > 5:
                print(f"  ... and {len(missing_addresses) - 5} more")
        
        # Return detailed results
        return {
            'total_buildings': len(building_data),
            'matches': len(matches),
            'mismatches': len(mismatches),
            'missing_addresses': len(missing_addresses),
            'match_percentage': (len(matches) / len(building_data) * 100),
            'matching_building_ids': [m['building_id'] for m in matches],
            'mismatched_building_ids': [m['building_id'] for m in mismatches],
            'missing_building_ids': [m['building_id'] for m in missing_addresses]
        }
        
    except Exception as e:
        print(f"Error counting building address hash matches: {str(e)}")
        return None

if __name__ == "__main__":
    results = count_building_address_hash_matches()
    if results:
        print(f"\n📊 SUMMARY:")
        print(f"Total building NODE_IDs with matching ADDRESS_HASH: {results['matches']}")
        print(f"Match rate: {results['match_percentage']:.2f}%") 