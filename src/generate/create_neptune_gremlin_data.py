import subprocess
import sys
import os
from pathlib import Path
import glob

def cleanup_output_directories():
    """Clean up output directories by removing JSON and CSV files."""
    try:
        # Clean up GDS directory (JSON files)
        gds_path = "src/data/output/gds"
        if os.path.exists(gds_path):
            json_files = glob.glob(os.path.join(gds_path, "*.json"))
            for file in json_files:
                try:
                    os.remove(file)
                    print(f"Deleted: {file}")
                except Exception as e:
                    print(f"Error deleting {file}: {str(e)}")

        # Clean up Neptune directory (CSV files)
        neptune_path = "src/data/output/neptune"
        if os.path.exists(neptune_path):
            csv_files = glob.glob(os.path.join(neptune_path, "*.csv"))
            for file in csv_files:
                try:
                    os.remove(file)
                    print(f"Deleted: {file}")
                except Exception as e:
                    print(f"Error deleting {file}: {str(e)}")

        print("Cleanup completed successfully")
        return True
    except Exception as e:
        print(f"Error during cleanup: {str(e)}")
        return False

def run_script(script_path):
    """Run a Python script and return True if successful, False otherwise."""
    try:
        print(f"\nRunning {script_path}...")
        result = subprocess.run([sys.executable, script_path], check=True)
        if result.returncode == 0:
            print(f"Successfully completed {script_path}")
            return True
        else:
            print(f"Error running {script_path}")
            return False
    except subprocess.CalledProcessError as e:
        print(f"Error running {script_path}: {str(e)}")
        return False
    except Exception as e:
        print(f"Unexpected error running {script_path}: {str(e)}")
        return False

def main():
    # Define the scripts to run in sequence
    node_scripts = [
        "src/generate/mock/nodes/generate_node_data.py",
        "src/generate/mock/nodes/generate_mock_person_data_json.py",
        "src/generate/mock/nodes/generate_mock_address_data_json.py",
        "src/generate/mock/nodes/generate_mock_receipt_data_json.py",
        "src/generate/mock/nodes/generate_mock_name_data_json.py"
    ]

    edge_scripts = [
        "src/generate/mock/edges/generate_mock_person-address_edge.py",
        "src/generate/mock/edges/generate_mock_person-reciept_edge.py",
        "src/generate/mock/edges/generate_mock_person-name_edge.py"
    ]

    neptune_scripts = [
        "src/generate/neptune/generate_neptune_person_json_gremlin_csv.py",
        "src/generate/neptune/generate_neptune_address_json_gremlin_csv.py",
        "src/generate/neptune/generate_neptune_person-address_json_gremlin_csv.py"
    ]

    # Combine all scripts for existence check
    all_scripts = node_scripts + edge_scripts + neptune_scripts

    # Verify all scripts exist before starting
    for script in all_scripts:
        if not os.path.exists(script):
            print(f"Error: Script {script} does not exist")
            return

    print("Starting cleanup process...")
    if not cleanup_output_directories():
        print("Cleanup failed. Stopping process.")
        return

    print("\nStarting data generation process...")
    print("\nPhase 1: Generating Node Data...")
    
    # Run node generation scripts
    for script in node_scripts:
        if not run_script(script):
            print(f"Failed to run {script}. Stopping process.")
            return

    print("\nPhase 2: Generating Edge Data...")
    
    # Run edge generation scripts
    for script in edge_scripts:
        if not run_script(script):
            print(f"Failed to run {script}. Stopping process.")
            return

    print("\nPhase 3: Generating Neptune Gremlin CSV Data...")
    
    # Run Neptune Gremlin CSV generation scripts
    for script in neptune_scripts:
        if not run_script(script):
            print(f"Failed to run {script}. Stopping process.")
            return

    print("\nAll data generation scripts completed successfully!")

if __name__ == "__main__":
    main()
