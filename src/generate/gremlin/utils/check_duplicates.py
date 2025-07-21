#!/usr/bin/env python3
"""
Script to check for duplicate ~id values in Neptune CSV files.
"""

import csv
import sys
from collections import Counter
from pathlib import Path

def check_duplicates(file_path):
    """Check for duplicate ~id values in a CSV file."""
    file_path = Path(file_path)
    
    if not file_path.exists():
        print(f"Error: File {file_path} does not exist")
        return False
    
    print(f"Checking for duplicate ~id values in: {file_path}")
    
    ids = []
    total_rows = 0
    
    try:
        with open(file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            if '~id' not in reader.fieldnames:
                print("Error: '~id' column not found in CSV file")
                return False
            
            for row in reader:
                total_rows += 1
                ids.append(row['~id'])
                
                # Progress indicator for large files
                if total_rows % 100000 == 0:
                    print(f"Processed {total_rows:,} rows...")
    
    except Exception as e:
        print(f"Error reading file: {e}")
        return False
    
    # Count occurrences of each ID
    id_counts = Counter(ids)
    duplicates = {id_val: count for id_val, count in id_counts.items() if count > 1}
    
    print(f"\nResults:")
    print(f"Total rows processed: {total_rows:,}")
    print(f"Unique ~id values: {len(id_counts):,}")
    
    if duplicates:
        print(f"Duplicate ~id values found: {len(duplicates)}")
        print("\nDuplicate details:")
        for id_val, count in sorted(duplicates.items()):
            print(f"  {id_val}: appears {count} times")
        return False
    else:
        print("No duplicate ~id values found!")
        return True

if __name__ == "__main__":
    # Hardcoded file path to check for duplicates
    file_path = "src/data/output/neptune/nodes/neptune_person_nodes_gremlin_00001.csv"
    
    print("Checking for duplicate ~id values in Neptune person nodes CSV file...")
    success = check_duplicates(file_path)
    sys.exit(0 if success else 1)