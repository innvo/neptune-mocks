#!/usr/bin/env python3
"""
CSV File Cleanup Script
Deletes all CSV files in the csv_output directory
"""

import os
import glob
import sys

def delete_csv_files():
    """Delete all CSV files in the csv_output directory"""
    csv_output_dir = "src/neptune-performance-test/csv_output"
    
    # Check if directory exists
    if not os.path.exists(csv_output_dir):
        print(f"Directory '{csv_output_dir}' does not exist.")
        return
    
    # Find all CSV files in the directory
    csv_pattern = os.path.join(csv_output_dir, "*.csv")
    csv_files = glob.glob(csv_pattern)
    
    if not csv_files:
        print(f"No CSV files found in '{csv_output_dir}' directory.")
        return
    
    print(f"Found {len(csv_files)} CSV files to delete:")
    
    # Delete each CSV file
    deleted_count = 0
    failed_count = 0
    
    for csv_file in csv_files:
        try:
            os.remove(csv_file)
            print(f"   Deleted: {os.path.basename(csv_file)}")
            deleted_count += 1
        except Exception as e:
            print(f"   Failed to delete {os.path.basename(csv_file)}: {str(e)}")
            failed_count += 1
    
    # Print summary
    print(f"\nCleanup Summary:")
    print(f"  Successfully deleted: {deleted_count} files")
    if failed_count > 0:
        print(f"  Failed to delete: {failed_count} files")
    print(f"  Total processed: {len(csv_files)} files")

def main():
    """Main execution function"""
    print("CSV File Cleanup Tool")
    print("=" * 40)
    print("This will delete ALL CSV files in csv_output/")
    print("=" * 40)
    
    # Check for --force flag
    force_delete = '--force' in sys.argv or '-f' in sys.argv
    
    if force_delete:
        print("\nForce mode enabled - deleting without confirmation...")
        delete_csv_files()
        print("\nCSV cleanup completed!")
    else:
        # Confirm deletion
        try:
            response = input("\nAre you sure you want to delete all CSV files? (y/N): ")
            
            if response.lower() in ['y', 'yes']:
                delete_csv_files()
                print("\nCSV cleanup completed!")
            else:
                print("\nOperation cancelled.")
        except (EOFError, KeyboardInterrupt):
            print("\n\nOperation cancelled.")
            sys.exit(1)

if __name__ == "__main__":
    main()