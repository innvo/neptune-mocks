import pandas as pd
import json
from tqdm import tqdm
import os

def validate_and_escape_json(json_str):
    """Validate and escape JSON string"""
    try:
        # First try to parse the JSON
        parsed = json.loads(json_str)
        # Then convert back to string with proper escaping
        return json.dumps(parsed)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON found: {json_str}")
        print(f"Error: {str(e)}")
        return None

def process_csv_file(input_file, output_file, node_type=None):
    """Process a CSV file, validate JSON, and create a new file with escaped JSON"""
    try:
        print(f"\nProcessing {input_file}...")
        
        # Read the CSV file
        df = pd.read_csv(input_file)
        
        # Initialize counters
        total_rows = len(df)
        invalid_json_count = 0
        processed_rows = 0
        
        # Process each row
        for idx, row in tqdm(df.iterrows(), total=total_rows, desc="Processing rows"):
            # Validate and escape JSON
            valid_json = validate_and_escape_json(row['node_properties'])
            if valid_json is None:
                invalid_json_count += 1
                continue
            
            # Update the row with escaped JSON
            df.at[idx, 'node_properties'] = valid_json
            processed_rows += 1
        
        # Print statistics
        print(f"\nProcessing Statistics for {input_file}:")
        print(f"Total rows: {total_rows}")
        print(f"Successfully processed: {processed_rows}")
        print(f"Invalid JSON skipped: {invalid_json_count}")
        
        # Save the processed data to a new file
        if processed_rows > 0:
            df.to_csv(output_file, index=False)
            print(f"Processed data saved to {output_file}")
            return True
        else:
            print("No valid data to save")
            return False
            
    except Exception as e:
        print(f"Error processing {input_file}: {str(e)}")
        return False

def main():
    # Process person data
    process_csv_file('mock_person_data.csv', 'mock_person_data_processed.csv')
    
    # Process name data
    process_csv_file('mock_name_data.csv', 'mock_name_data_processed.csv')
    
    print("\nJSON validation and escaping completed!")

if __name__ == "__main__":
    main() 