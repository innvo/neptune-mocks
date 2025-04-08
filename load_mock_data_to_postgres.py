import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from tqdm import tqdm
import os
import json
from dotenv import load_dotenv

def delete_all_records(cursor):
    """Delete all records from edges and nodes tables"""
    try:
        print("Deleting existing records...")
        
        # Delete edges first (due to foreign key constraints)
        cursor.execute("DELETE FROM edges")
        print("Deleted all edge records")
        
        # Delete nodes
        cursor.execute("DELETE FROM nodes")
        print("Deleted all node records")
        
        return True
    except Exception as e:
        print(f"Error deleting records: {str(e)}")
        return False

def create_tables(cursor):
    """Create necessary tables if they don't exist"""
    try:
        print("Creating tables...")
        
        # Drop tables if they exist (optional, comment out if you want to preserve existing data)
        cursor.execute("DROP TABLE IF EXISTS edges CASCADE")
        cursor.execute("DROP TABLE IF EXISTS nodes CASCADE")
        
        # Create nodes table
        cursor.execute("""
            CREATE TABLE nodes (
                node_id VARCHAR(255) PRIMARY KEY,
                node_type VARCHAR(255),
                node_name VARCHAR(255),
                node_properties JSONB
            )
        """)
        print("Created nodes table")
        
        # Create edges table
        cursor.execute("""
            CREATE TABLE edges (
                edge_id VARCHAR(255) PRIMARY KEY,
                node_id_from VARCHAR(255),
                node_id_to VARCHAR(255),
                edge_type VARCHAR(255),
                FOREIGN KEY (node_id_from) REFERENCES nodes(node_id),
                FOREIGN KEY (node_id_to) REFERENCES nodes(node_id)
            )
        """)
        print("Created edges table")
        
        # Create indexes
        cursor.execute("CREATE INDEX idx_nodes_type ON nodes(node_type)")
        cursor.execute("CREATE INDEX idx_edges_type ON edges(edge_type)")
        cursor.execute("CREATE INDEX idx_edges_from ON edges(node_id_from)")
        cursor.execute("CREATE INDEX idx_edges_to ON edges(node_id_to)")
        print("Created indexes")
        
        return True
    except Exception as e:
        print(f"Error creating tables: {str(e)}")
        return False

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

def load_data_to_postgres():
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
        
        # Create tables
        if not create_tables(cursor):
            return False
            
        # Delete all existing records
        if not delete_all_records(cursor):
            return False
        
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
                "INSERT INTO nodes (node_id, node_type, node_name, node_properties) VALUES %s ON CONFLICT (node_id) DO NOTHING",
                person_data
            )
            print(f"Loaded {len(person_data)} person nodes")
        
        # Commit the transaction
        conn.commit()
        
        # Print final statistics
        print("\nData Loading Statistics:")
        cursor.execute("SELECT node_type, COUNT(*) FROM nodes GROUP BY node_type")
        print("\nNode Types Distribution:")
        for node_type, count in cursor.fetchall():
            print(f"{node_type}: {count} nodes")
        
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
    load_data_to_postgres() 