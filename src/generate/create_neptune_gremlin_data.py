import subprocess
import sys
import os
from pathlib import Path
import glob
import platform
import time
from datetime import datetime

def clear_terminal():
    """Clear the terminal screen based on the operating system."""
    try:
        if platform.system() == "Windows":
            os.system('cls')
        else:
            os.system('clear')
    except Exception as e:
        print(f"Error clearing terminal: {str(e)}")

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
    start_time = time.time()
    try:
        print(f"\nRunning {script_path}...")
        result = subprocess.run([sys.executable, script_path], check=True)
        end_time = time.time()
        execution_time = end_time - start_time
        if result.returncode == 0:
            print(f"Successfully completed {script_path} in {execution_time:.2f} seconds")
            return True, execution_time
        else:
            print(f"Error running {script_path}")
            return False, execution_time
    except subprocess.CalledProcessError as e:
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"Error running {script_path}: {str(e)}")
        return False, execution_time
    except Exception as e:
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"Unexpected error running {script_path}: {str(e)}")
        return False, execution_time

def main():
    # Clear terminal on startup
    clear_terminal()
    
    # Start overall timing
    total_start_time = time.time()
    
    # Define the scripts to run in sequence
    node_scripts = [
        "src/generate/mock/nodes/generate_node_data.py",
        "src/generate/mock/nodes/generate_mock_person_data_json.py",
        "src/generate/mock/nodes/generate_mock_address_data_json.py",
        "src/generate/mock/nodes/generate_mock_anumber_data_json.py",
        "src/generate/mock/nodes/generate_mock_building_data_json.py",
        "src/generate/mock/nodes/generate_mock_datainstance_data_json.py",
        "src/generate/mock/nodes/generate_mock_email_data_json.py",
        "src/generate/mock/nodes/generate_mock_form_data_json.py",
        "src/generate/mock/nodes/generate_mock_phone_data_json.py",
        "src/generate/mock/nodes/generate_mock_name_data_json.py",
        "src/generate/mock/nodes/generate_mock_organization_data_json.py",
        "src/generate/mock/nodes/generate_mock_receipt_data_json.py",
    ]

    edge_scripts = [
        "src/generate/mock/edges/generate_mock_building-address_edge.py",
        "src/generate/mock/edges/generate_mock_organization-address_edge.py",
        "src/generate/mock/edges/generate_mock_person-address_edge.py",
        "src/generate/mock/edges/generate_mock_person-anumber_edge.py",
        "src/generate/mock/edges/generate_mock_person-datainstance_edge.py",
        "src/generate/mock/edges/generate_mock_person-email_edge.py",
        "src/generate/mock/edges/generate_mock_person-form_edge.py",
        "src/generate/mock/edges/generate_mock_person-name_edge.py",
        "src/generate/mock/edges/generate_mock_person-organization_edge.py",
        "src/generate/mock/edges/generate_mock_person-phone_edge.py",
        "src/generate/mock/edges/generate_mock_person-receipt_edge.py",
        "src/generate/mock/edges/generate_mock_organization-organization_edge.py"
    ]

    neptune_scripts = [
        "src/generate/neptune/gremlin/generate_neptune_person_json_gremlin_csv.py",
        "src/generate/neptune/gremlin/generate_neptune_address_json_gremlin_csv.py",
        "src/generate/neptune/gremlin/generate_neptune_anumber_json_gremlin_csv.py",
        "src/generate/neptune/gremlin/generate_neptune_datainstance_json_gremlin_csv.py",
        "src/generate/neptune/gremlin/generate_neptune_email_json_gremlin_csv.py",
        "src/generate/neptune/gremlin/generate_neptune_form_json_gremlin_csv.py",
        "src/generate/neptune/gremlin/generate_neptune_receipt_json_gremlin_csv.py",
        "src/generate/neptune/gremlin/generate_neptune_building_json_gremlin_csv.py",
        "src/generate/neptune/gremlin/generate_neptune_organization_json_gremlin_csv.py",
        "src/generate/neptune/gremlin/generate_neptune_phone_json_gremlin_csv.py",
        "src/generate/neptune/gremlin/generate_neptune_building-address_json_gremlin_csv.py",
        "src/generate/neptune/gremlin/generate_neptune_organization-address_json_gremlin_csv.py",
        "src/generate/neptune/gremlin/generate_neptune_person-address_json_gremlin_csv.py",
        "src/generate/neptune/gremlin/generate_neptune_person-anumber_json_gremlin_csv.py",
        "src/generate/neptune/gremlin/generate_neptune_person-datainstance_json_gremlin_csv.py",
        "src/generate/neptune/gremlin/generate_neptune_person-email_json_gremlin_csv.py",
        "src/generate/neptune/gremlin/generate_neptune_person-form_json_gremlin_csv.py",    
        "src/generate/neptune/gremlin/generate_neptune_person-organization_json_gremlin_csv.py",
        "src/generate/neptune/gremlin/generate_neptune_person-phone_json_gremlin_csv.py",
        "src/generate/neptune/gremlin/generate_neptune_person-receipt_json_gremlin_csv.py"
    ]

    validation_scripts = [
        "src/validation/validate_edges_referential_integrity_gremlin.py"
    ]

    # Combine all scripts for existence check
    all_scripts = node_scripts + edge_scripts + neptune_scripts + validation_scripts

    # Verify all scripts exist before starting
    for script in all_scripts:
        if not os.path.exists(script):
            print(f"Error: Script {script} does not exist")
            return

    print("Starting cleanup process...")
    cleanup_start_time = time.time()
    if not cleanup_output_directories():
        print("Cleanup failed. Stopping process.")
        return
    cleanup_time = time.time() - cleanup_start_time
    print(f"Cleanup completed in {cleanup_time:.2f} seconds")

    print("\nStarting data generation process...")
    print("\nPhase 1: Generating Node Data...")
    
    # Track timing for each phase
    phase_times = {}
    script_times = {}
    
    # Run node generation scripts
    phase_start_time = time.time()
    for script in node_scripts:
        success, execution_time = run_script(script)
        script_times[script] = execution_time
        if not success:
            print(f"Failed to run {script}. Stopping process.")
            return
    phase_times["Node Generation"] = time.time() - phase_start_time

    print("\nPhase 2: Generating Edge Data...")
    
    # Run edge generation scripts
    phase_start_time = time.time()
    for script in edge_scripts:
        success, execution_time = run_script(script)
        script_times[script] = execution_time
        if not success:
            print(f"Failed to run {script}. Stopping process.")
            return
    phase_times["Edge Generation"] = time.time() - phase_start_time

    print("\nPhase 3: Generating Neptune Gremlin CSV Data...")
    
    # Run Neptune Gremlin CSV generation scripts
    phase_start_time = time.time()
    for script in neptune_scripts:
        success, execution_time = run_script(script)
        script_times[script] = execution_time
        if not success:
            print(f"Failed to run {script}. Stopping process.")
            return
    phase_times["Neptune CSV Generation"] = time.time() - phase_start_time

    print("\nPhase 4: Validating Edge Referential Integrity...")
    
    # Run validation scripts
    phase_start_time = time.time()
    for script in validation_scripts:
        success, execution_time = run_script(script)
        script_times[script] = execution_time
        if not success:
            print(f"Failed to run {script}. Stopping process.")
            return
    phase_times["Validation"] = time.time() - phase_start_time

    # Calculate total time
    total_execution_time = time.time() - total_start_time

    # Print detailed timing summary
    print("\n" + "="*80)
    print("EXECUTION TIME SUMMARY")
    print("="*80)
    print(f"Total Execution Time: {total_execution_time:.2f} seconds ({total_execution_time/60:.2f} minutes)")
    print(f"Cleanup Time: {cleanup_time:.2f} seconds")
    print()
    
    # Phase timing table
    print("Phase Execution Times:")
    print("-" * 60)
    print(f"{'Phase':<25} {'Time (seconds)':<15} {'Time (minutes)':<15}")
    print("-" * 60)
    for phase, phase_time in phase_times.items():
        print(f"{phase:<25} {phase_time:<15.2f} {phase_time/60:<15.2f}")
    print()
    
    # Individual script timing tables
    print("Individual Script Execution Times:")
    print()
    
    # Node Scripts Table
    print("Node Scripts:")
    print("-" * 70)
    print(f"{'Script Name':<50} {'Time (seconds)':<15}")
    print("-" * 70)
    for script in node_scripts:
        if script in script_times:
            script_name = os.path.basename(script)
            print(f"{script_name:<50} {script_times[script]:<15.2f}")
    print()
    
    # Edge Scripts Table
    print("Edge Scripts:")
    print("-" * 70)
    print(f"{'Script Name':<50} {'Time (seconds)':<15}")
    print("-" * 70)
    for script in edge_scripts:
        if script in script_times:
            script_name = os.path.basename(script)
            print(f"{script_name:<50} {script_times[script]:<15.2f}")
    print()
    
    # Neptune CSV Scripts Table
    print("Neptune CSV Scripts:")
    print("-" * 70)
    print(f"{'Script Name':<50} {'Time (seconds)':<15}")
    print("-" * 70)
    for script in neptune_scripts:
        if script in script_times:
            script_name = os.path.basename(script)
            print(f"{script_name:<50} {script_times[script]:<15.2f}")
    print()
    
    # Validation Scripts Table
    print("Validation Scripts:")
    print("-" * 70)
    print(f"{'Script Name':<50} {'Time (seconds)':<15}")
    print("-" * 70)
    for script in validation_scripts:
        if script in script_times:
            script_name = os.path.basename(script)
            print(f"{script_name:<50} {script_times[script]:<15.2f}")
    print()
    
    print("All data generation and validation scripts completed successfully!")

if __name__ == "__main__":
    main()
