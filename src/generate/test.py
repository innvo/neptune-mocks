import pandas as pd
import os
import glob
import subprocess
import json
import shutil


def execute_node_data_generation():
    try:
        result = subprocess.run(['python', 'src/generate/mock/nodes/generate_node_data.py'], 
                              check=True, capture_output=True, text=True)
        print("Node data generation completed successfully")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error in node data generation: {e.stderr}")
        return False


def main():
    # Execute the node data generation script
    if not execute_node_data_generation():
        print("Failed to generate node data. Exiting...")
        exit(1)

    # Read the CSV file
    df = pd.read_csv('src/data/input/node_data.csv')

    # Get the max batch value
    max_batch = df['batch'].max()
    print(f"Max batch value: {max_batch}")

    # Remove all JSON files in the output directory before each loop
    json_files = glob.glob('src/data/output/gds/*.json')
    for file_path in json_files:
        try:
            os.remove(file_path)
            print(f"Removed: {file_path}")
        except Exception as e:
            print(f"Error removing {file_path}: {e}")

    # Loop through each batch
    for i, batch_num in enumerate(range(1, max_batch + 1), start=1):
        print(f"\n{'='*50}")
        print(f"Processing Loop {i}: Batch {batch_num}")
        print(f"{'='*50}")
        
        # Execute the mock person data generation script
        try:
            result = subprocess.run(['python', 'src/generate/mock/nodes/generate_mock_person_data_json.py'], 
                                  check=True, capture_output=True, text=True)
            print("Person data generation completed successfully")
            if result.stdout:
                print(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"Error in person data generation: {e.stderr}")
            continue  # Skip to next iteration if critical step fails
        
        # Execute the mock address data generation script
        try:
            result = subprocess.run(['python', 'src/generate/mock/nodes/generate_mock_address_data_json.py'], 
                                  check=True, capture_output=True, text=True)
            print("Address data generation completed successfully")
            if result.stdout:
                print(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"Error in address data generation: {e.stderr}")
            continue
        
        # Execute the mock receipt data generation script
        try:
            result = subprocess.run(['python', 'src/generate/mock/nodes/generate_mock_receipt_data_json.py'], 
                                  check=True, capture_output=True, text=True)
            print("Receipt data generation completed successfully")
            if result.stdout:
                print(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"Error in receipt data generation: {e.stderr}")
            continue
        
        # Execute the mock person-address edge generation script
        try:
            result = subprocess.run(['python', 'src/generate/mock/edges/generate_mock_person-address_edge.py'], 
                                  check=True, capture_output=True, text=True)
            print("Person-address edge generation completed successfully")
            if result.stdout:
                print(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"Error in person-address edge generation: {e.stderr}")
            continue
        
        # Execute the mock person-receipt edge generation script
        try:
            result = subprocess.run(['python', 'src/generate/mock/edges/generate_mock_person-receipt_edge.py'], 
                                  check=True, capture_output=True, text=True)
            print("Person-receipt edge generation completed successfully")
            if result.stdout:
                print(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"Error in person-receipt edge generation: {e.stderr}")
            continue
        
        # Display sample records from generated files
        files_to_check = [
            ('src/data/output/gds/mock_person_data.json', 'person'),
            ('src/data/output/gds/mock_address_data.json', 'address'),
            ('src/data/output/gds/mock_receipt_data.json', 'receipt'),
            ('src/data/output/gds/mock_person-address_edge.json', 'person-address edge'),
            ('src/data/output/gds/mock_person-receipt_edge.json', 'person-receipt edge')
        ]
        
        for file_path, file_type in files_to_check:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    if data:
                        print(f"\nFirst record in the generated {file_type} JSON file:")
                        print(json.dumps(data[0], indent=2))
                    else:
                        print(f"No records found in the generated {file_type} JSON file.")
            except FileNotFoundError:
                print(f"File not found: {file_path}")
            except json.JSONDecodeError:
                print(f"Invalid JSON in file: {file_path}")
            except Exception as e:
                print(f"Error reading the generated {file_type} JSON file: {e}")
        
        # Move and rename files with batch prefix
        file_mappings = [
            ('src/data/output/gds/mock_person_data.json', f'src/data/output/gds/batch_{batch_num}_mock_person_data.json'),
            ('src/data/output/gds/mock_address_data.json', f'src/data/output/gds/batch_{batch_num}_mock_address_data.json'),
            ('src/data/output/gds/mock_receipt_data.json', f'src/data/output/gds/batch_{batch_num}_mock_receipt_data.json'),
            ('src/data/output/gds/mock_person-address_edge.json', f'src/data/output/gds/batch_{batch_num}_mock_person_address_edge.json'),
            ('src/data/output/gds/mock_person-receipt_edge.json', f'src/data/output/gds/batch_{batch_num}_mock_person_receipt_edge.json')
        ]
        
        for source_file, dest_file in file_mappings:
            try:
                if os.path.exists(source_file):
                    shutil.move(source_file, dest_file)
                    print(f"Moved: {source_file} -> {dest_file}")
                else:
                    print(f"Warning: Source file not found: {source_file}")
            except Exception as e:
                print(f"Error moving {source_file} to {dest_file}: {e}")
        
        print(f"Completed processing Loop {i}: Batch {batch_num}")

    print(f"\nAll {max_batch} batches processed successfully!")


if __name__ == "__main__":
    main()