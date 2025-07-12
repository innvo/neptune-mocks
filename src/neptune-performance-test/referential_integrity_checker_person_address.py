#!/usr/bin/env python3
"""
Referential Integrity Checker for Person-Address Edges
Validates that all edge references point to existing nodes in CSV files
"""

import csv
import os
import time
from collections import defaultdict
from typing import Set, Dict, List, Tuple

class ReferentialIntegrityChecker:
    def __init__(self, csv_output_dir="src/neptune-performance-test/csv_output"):
        """
        Initialize the referential integrity checker
        
        Args:
            csv_output_dir (str): Directory containing CSV files
        """
        self.csv_output_dir = csv_output_dir
        self.person_ids = set()
        self.address_ids = set()
        self.validation_results = {}
        
    def load_node_ids(self):
        """Load all person and address IDs from CSV files"""
        print("📋 Loading node IDs for referential integrity check...")
        start_time = time.time()
        
        # Load person IDs
        person_count = 0
        person_files = []
        
        if os.path.exists(self.csv_output_dir):
            for file in os.listdir(self.csv_output_dir):
                if file.startswith("person-") and file.endswith(".csv"):
                    person_files.append(os.path.join(self.csv_output_dir, file))
        
        print(f"  Loading person IDs from {len(person_files)} files...")
        
        for person_file in sorted(person_files):
            try:
                with open(person_file, 'r') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        self.person_ids.add(row['~id'])
                        person_count += 1
            except Exception as e:
                print(f"    Warning: Could not read {person_file}: {e}")
        
        # Load address IDs
        address_count = 0
        address_files = []
        
        if os.path.exists(self.csv_output_dir):
            for file in os.listdir(self.csv_output_dir):
                if file.startswith("address-") and file.endswith(".csv"):
                    address_files.append(os.path.join(self.csv_output_dir, file))
        
        print(f"  Loading address IDs from {len(address_files)} files...")
        
        for address_file in sorted(address_files):
            try:
                with open(address_file, 'r') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        self.address_ids.add(row['~id'])
                        address_count += 1
            except Exception as e:
                print(f"    Warning: Could not read {address_file}: {e}")
        
        elapsed = time.time() - start_time
        
        print(f"✓ Loaded {person_count:,} person IDs from {len(person_files)} files")
        print(f"✓ Loaded {address_count:,} address IDs from {len(address_files)} files")
        print(f"✓ Total load time: {elapsed:.2f}s")
        
        return len(self.person_ids) > 0 and len(self.address_ids) > 0
    
    def validate_edge_file(self, edge_file_path: str) -> Dict:
        """
        Validate referential integrity for a single edge file
        
        Args:
            edge_file_path (str): Path to the edge CSV file
            
        Returns:
            Dict: Validation results
        """
        print(f"\n🔍 Validating {os.path.basename(edge_file_path)}...")
        
        if not os.path.exists(edge_file_path):
            return {
                'file': edge_file_path,
                'exists': False,
                'error': 'File not found'
            }
        
        start_time = time.time()
        
        # Validation counters
        total_edges = 0
        valid_edges = 0
        invalid_person_refs = []
        invalid_address_refs = []
        duplicate_edges = set()
        edge_signatures = set()
        
        # Address type distribution
        address_type_counts = defaultdict(int)
        
        # Person-address relationship stats
        person_address_counts = defaultdict(int)
        
        try:
            with open(edge_file_path, 'r') as f:
                reader = csv.DictReader(f)
                
                for row_num, row in enumerate(reader, 1):
                    total_edges += 1
                    
                    edge_id = row.get('~id', '')
                    from_id = row.get('~from', '')
                    to_id = row.get('~to', '')
                    address_type = row.get('address_type:String', '')
                    label = row.get('~label', '')
                    
                    # Check for duplicate edges (same from-to pair)
                    edge_signature = (from_id, to_id)
                    if edge_signature in edge_signatures:
                        duplicate_edges.add(edge_signature)
                    else:
                        edge_signatures.add(edge_signature)
                    
                    # Validate person ID exists
                    person_valid = from_id in self.person_ids
                    if not person_valid:
                        invalid_person_refs.append({
                            'row': row_num,
                            'edge_id': edge_id,
                            'person_id': from_id
                        })
                    
                    # Validate address ID exists
                    address_valid = to_id in self.address_ids
                    if not address_valid:
                        invalid_address_refs.append({
                            'row': row_num,
                            'edge_id': edge_id,
                            'address_id': to_id
                        })
                    
                    # Count address types
                    address_type_counts[address_type] += 1
                    
                    # Count addresses per person
                    person_address_counts[from_id] += 1
                    
                    # Edge is valid if both references are valid
                    if person_valid and address_valid:
                        valid_edges += 1
                    
                    # Progress reporting for large files
                    if total_edges % 100000 == 0:
                        print(f"    Processed {total_edges:,} edges...")
        
        except Exception as e:
            return {
                'file': edge_file_path,
                'exists': True,
                'error': f'Failed to read file: {str(e)}'
            }
        
        elapsed = time.time() - start_time
        
        # Calculate statistics
        invalid_edges = total_edges - valid_edges
        integrity_percentage = (valid_edges / total_edges * 100) if total_edges > 0 else 0
        
        # Person address distribution
        address_distribution = defaultdict(int)
        for person_id, count in person_address_counts.items():
            address_distribution[count] += 1
        
        results = {
            'file': edge_file_path,
            'exists': True,
            'processing_time': elapsed,
            'total_edges': total_edges,
            'valid_edges': valid_edges,
            'invalid_edges': invalid_edges,
            'integrity_percentage': integrity_percentage,
            'invalid_person_refs': len(invalid_person_refs),
            'invalid_address_refs': len(invalid_address_refs),
            'duplicate_edges': len(duplicate_edges),
            'address_type_distribution': dict(address_type_counts),
            'person_address_distribution': dict(address_distribution),
            'unique_persons_with_addresses': len(person_address_counts),
            'sample_invalid_persons': invalid_person_refs[:10],  # First 10 for debugging
            'sample_invalid_addresses': invalid_address_refs[:10],  # First 10 for debugging
            'error': None
        }
        
        return results
    
    def print_validation_report(self, results: Dict):
        """Print detailed validation report"""
        print(f"\n📊 REFERENTIAL INTEGRITY REPORT")
        print("=" * 60)
        print(f"File: {os.path.basename(results['file'])}")
        print(f"Processing time: {results['processing_time']:.2f}s")
        print("=" * 60)
        
        if results.get('error'):
            print(f"❌ ERROR: {results['error']}")
            return
        
        # Overall statistics
        print(f"📈 OVERALL STATISTICS")
        print(f"  Total edges:              {results['total_edges']:,}")
        print(f"  Valid edges:              {results['valid_edges']:,}")
        print(f"  Invalid edges:            {results['invalid_edges']:,}")
        print(f"  Integrity percentage:     {results['integrity_percentage']:.2f}%")
        print(f"  Duplicate edges:          {results['duplicate_edges']:,}")
        
        # Reference validation
        print(f"\n🔗 REFERENCE VALIDATION")
        print(f"  Invalid person refs:      {results['invalid_person_refs']:,}")
        print(f"  Invalid address refs:     {results['invalid_address_refs']:,}")
        
        # Address type distribution
        print(f"\n🏠 ADDRESS TYPE DISTRIBUTION")
        for addr_type, count in results['address_type_distribution'].items():
            percentage = (count / results['total_edges'] * 100) if results['total_edges'] > 0 else 0
            print(f"  {addr_type:>12}: {count:>8,} ({percentage:5.1f}%)")
        
        # Person-address relationship distribution
        print(f"\n👤 PERSON-ADDRESS RELATIONSHIP DISTRIBUTION")
        print(f"  Unique persons with addresses: {results['unique_persons_with_addresses']:,}")
        
        for num_addresses in sorted(results['person_address_distribution'].keys()):
            person_count = results['person_address_distribution'][num_addresses]
            percentage = (person_count / results['unique_persons_with_addresses'] * 100) if results['unique_persons_with_addresses'] > 0 else 0
            print(f"  {num_addresses:>2} address(es): {person_count:>8,} persons ({percentage:5.1f}%)")
        
        # Show sample errors if any
        if results['sample_invalid_persons']:
            print(f"\n❌ SAMPLE INVALID PERSON REFERENCES")
            for error in results['sample_invalid_persons'][:5]:
                print(f"  Row {error['row']:>6}: Person ID '{error['person_id']}' not found")
        
        if results['sample_invalid_addresses']:
            print(f"\n❌ SAMPLE INVALID ADDRESS REFERENCES")
            for error in results['sample_invalid_addresses'][:5]:
                print(f"  Row {error['row']:>6}: Address ID '{error['address_id']}' not found")
        
        # Status summary
        print(f"\n✅ VALIDATION SUMMARY")
        if results['integrity_percentage'] == 100.0:
            print("🎉 PERFECT! All edge references are valid.")
        elif results['integrity_percentage'] >= 99.0:
            print("✅ EXCELLENT! Nearly all edge references are valid.")
        elif results['integrity_percentage'] >= 95.0:
            print("⚠️  GOOD! Most edge references are valid, minor issues detected.")
        else:
            print("❌ ISSUES DETECTED! Significant referential integrity problems found.")
    
    def validate_first_edge_file(self):
        """Find and validate the first person-address edge file"""
        print("🔍 REFERENTIAL INTEGRITY CHECK FOR PERSON-ADDRESS EDGES")
        print("=" * 60)
        
        # Load node IDs first
        if not self.load_node_ids():
            print("❌ Failed to load node IDs. Cannot perform validation.")
            return
        
        # Find the first person-address edge file
        edge_files = []
        
        if os.path.exists(self.csv_output_dir):
            for file in os.listdir(self.csv_output_dir):
                if file.startswith("person_address_edge-") and file.endswith(".csv"):
                    edge_files.append(os.path.join(self.csv_output_dir, file))
        
        if not edge_files:
            print("❌ No person-address edge files found!")
            print(f"   Looking in: {self.csv_output_dir}")
            print("   Expected pattern: person_address_edge-*.csv")
            return
        
        # Sort and take the first file
        first_edge_file = sorted(edge_files)[0]
        print(f"📁 Found {len(edge_files)} edge file(s)")
        print(f"📄 Validating first file: {os.path.basename(first_edge_file)}")
        
        # Validate the file
        results = self.validate_edge_file(first_edge_file)
        
        # Print detailed report
        self.print_validation_report(results)
        
        return results

def main():
    """Main execution function"""
    checker = ReferentialIntegrityChecker()
    checker.validate_first_edge_file()

if __name__ == "__main__":
    main()