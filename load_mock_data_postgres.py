import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import os
import json
from dotenv import load_dotenv

def validate_json(json_str):
    """Validate and escape JSON string"""
    try:
        # Try to parse the JSON
        parsed = json.loads(json_str)
        # Convert back to string with proper escaping
        return json.dumps(parsed)
    except json.JSONDecodeError:
        print(f"Invalid JSON found: {json_str[:100]}...")
        return None

def load_mock_data():
    try:
        # Load environment variables
        load_dotenv()
        
        # Database connection parameters
        db_params = {
            'dbname': os.getenv('DB_NAME', 'neptune_db'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'postgres'),
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432')
        }
        
        # Connect to PostgreSQL
        print("Connecting to PostgreSQL database...")
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()
        
        # Truncate tables
        print("\nTruncating existing data...")
        cursor.execute("TRUNCATE TABLE edges CASCADE")
        cursor.execute("TRUNCATE TABLE nodes CASCADE")
        print("Tables truncated successfully")
        
        # Load person nodes
        print("\nLoading person nodes...")
        person_df = pd.read_csv('mock_person_data.csv')
        person_data = []
        invalid_json_count = 0
        
        for _, row in person_df.iterrows():
            # Validate and escape JSON
            valid_json = validate_json(row['node_properties'])
            if valid_json is None:
                invalid_json_count += 1
                continue
                
            person_data.append((
                row['node_id'],
                'person',
                row['node_name'],
                valid_json
            ))
        
        if invalid_json_count > 0:
            print(f"Warning: Skipped {invalid_json_count} person nodes due to invalid JSON")
        
        if person_data:
            execute_values(cursor,
                "INSERT INTO nodes (node_id, node_type, node_name, node_properties) VALUES %s",
                person_data
            )
            print(f"Loaded {len(person_data)} person nodes")
        
        # Load name nodes
        print("\nLoading name nodes...")
        name_df = pd.read_csv('mock_name_data.csv')
        name_data = []
        invalid_json_count = 0
        
        for _, row in name_df.iterrows():
            # Validate and escape JSON
            valid_json = validate_json(row['node_properties'])
            if valid_json is None:
                invalid_json_count += 1
                continue
                
            name_data.append((
                row['node_id'],
                'name',
                row['node_name'],
                valid_json
            ))
        
        if invalid_json_count > 0:
            print(f"Warning: Skipped {invalid_json_count} name nodes due to invalid JSON")
        
        if name_data:
            execute_values(cursor,
                "INSERT INTO nodes (node_id, node_type, node_name, node_properties) VALUES %s",
                name_data
            )
            print(f"Loaded {len(name_data)} name nodes")
        
        # Load person edges
        print("\nLoading person edges...")
        edge_df = pd.read_csv('mock_person_name_data.csv')
        edge_data = []
        
        for _, row in edge_df.iterrows():
            edge_data.append((
                row['edge_id'],
                row['node_id_from'],
                row['node_id_to'],
                row['edge_type']
            ))
        
        if edge_data:
            execute_values(cursor,
                "INSERT INTO edges (edge_id, node_id_from, node_id_to, edge_type) VALUES %s",
                edge_data
            )
            print(f"Loaded {len(edge_data)} person edges")
        
        # Commit the transaction
        conn.commit()
        
        # Print final statistics
        print("\nData Loading Statistics:")
        cursor.execute("SELECT node_type, COUNT(*) FROM nodes GROUP BY node_type")
        print("\nNode Types Distribution:")
        for node_type, count in cursor.fetchall():
            print(f"{node_type}: {count} nodes")
            
        cursor.execute("SELECT edge_type, COUNT(*) FROM edges GROUP BY edge_type")
        print("\nEdge Types Distribution:")
        for edge_type, count in cursor.fetchall():
            print(f"{edge_type}: {count} edges")
        
        # Close the connection
        cursor.close()
        conn.close()
        
        print("\nData loading completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error loading data to PostgreSQL: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    load_mock_data() 