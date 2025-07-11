# To run this script, use:
#   PYTHONPATH=src python src/generate/create_neptune_gremlin_data_unified_streaming.py

import sys
import os
import glob
import platform
import time
import gc
import psutil
import multiprocessing as mp

# Import all the streaming functions directly
from generate.mock.nodes.generate_node_data import generate_node_data
from generate.mock.nodes.generate_mock_person_data_json import generate_mock_person_data
from generate.mock.nodes.generate_mock_address_data_json import generate_mock_address_data
from generate.mock.nodes.generate_mock_anumber_data_json import generate_mock_anumber_data
from generate.mock.nodes.generate_mock_building_data_json import generate_mock_building_data
from generate.mock.nodes.generate_mock_datainstance_data_json import generate_mock_datainstance_data
from generate.mock.nodes.generate_mock_email_data_json import generate_mock_email_data
from generate.mock.nodes.generate_mock_form_data_json import generate_mock_form_data
from generate.mock.nodes.generate_mock_phone_data_json import generate_mock_phone_data
from generate.mock.nodes.generate_mock_name_data_json import generate_mock_name_data
from generate.mock.nodes.generate_mock_organization_data_json import generate_mock_organization_data
from generate.mock.nodes.generate_mock_receipt_data_json import generate_mock_receipt_data

# Import streaming edge functions
from generate.mock.edges.generate_mock_person_address_edge_streaming import generate_person_address_edges_streaming
from generate.mock.edges.generate_mock_person_form_edge_streaming import generate_person_form_edges_streaming
from generate.mock.edges.generate_mock_person_receipt_edge_streaming import generate_person_receipt_edges_streaming
from generate.mock.edges.generate_mock_person_anumber_edge_streaming import generate_person_anumber_edges_streaming
from generate.mock.edges.generate_mock_person_datainstance_edge_streaming import generate_person_datainstance_edges_streaming
from generate.mock.edges.generate_mock_person_email_edge_streaming import generate_person_email_edges_streaming
from generate.mock.edges.generate_mock_person_name_edge_streaming import generate_person_name_edges_streaming
from generate.mock.edges.generate_mock_person_organization_edge_streaming import generate_person_organization_edges_streaming
from generate.mock.edges.generate_mock_person_phone_edge_streaming import generate_person_phone_edges_streaming
from generate.mock.edges.generate_mock_building_address_edge_streaming import generate_building_address_edges_streaming
from generate.mock.edges.generate_mock_organization_address_edge_streaming import generate_organization_address_edges_streaming
from generate.mock.edges.generate_mock_organization_organization_edge_streaming import generate_organization_organization_edges_streaming

# Import Neptune CSV generation functions
from generate.neptune.gremlin.generate_neptune_person_json_gremlin_csv import convert_to_gremlin as generate_neptune_person_gremlin_csv
from generate.neptune.gremlin.generate_neptune_address_json_gremlin_csv import convert_to_gremlin as generate_neptune_address_gremlin_csv
from generate.neptune.gremlin.generate_neptune_anumber_json_gremlin_csv import convert_to_gremlin as generate_neptune_anumber_gremlin_csv
from generate.neptune.gremlin.generate_neptune_datainstance_json_gremlin_csv import convert_to_gremlin as generate_neptune_datainstance_gremlin_csv
from generate.neptune.gremlin.generate_neptune_email_json_gremlin_csv import convert_to_gremlin as generate_neptune_email_gremlin_csv
from generate.neptune.gremlin.generate_neptune_form_json_gremlin_csv import convert_to_gremlin as generate_neptune_form_gremlin_csv
from generate.neptune.gremlin.generate_neptune_receipt_json_gremlin_csv import convert_to_gremlin as generate_neptune_receipt_gremlin_csv
from generate.neptune.gremlin.generate_neptune_building_json_gremlin_csv import convert_to_gremlin as generate_neptune_building_gremlin_csv
from generate.neptune.gremlin.generate_neptune_organization_json_gremlin_csv import convert_to_gremlin as generate_neptune_organization_gremlin_csv
from generate.neptune.gremlin.generate_neptune_phone_json_gremlin_csv import convert_to_gremlin as generate_neptune_phone_gremlin_csv
from generate.neptune.gremlin.generate_neptune_building_address_json_gremlin_csv import convert_to_gremlin as generate_neptune_building_address_gremlin_csv
from generate.neptune.gremlin.generate_neptune_organization_address_json_gremlin_csv import convert_to_gremlin as generate_neptune_organization_address_gremlin_csv
from generate.neptune.gremlin.generate_neptune_person_address_json_gremlin_csv import convert_to_gremlin as generate_neptune_person_address_gremlin_csv
from generate.neptune.gremlin.generate_neptune_person_anumber_json_gremlin_csv import convert_to_gremlin as generate_neptune_person_anumber_gremlin_csv
from generate.neptune.gremlin.generate_neptune_person_datainstance_json_gremlin_csv import convert_to_gremlin as generate_neptune_person_datainstance_gremlin_csv
from generate.neptune.gremlin.generate_neptune_person_email_json_gremlin_csv import convert_to_gremlin as generate_neptune_person_email_gremlin_csv
from generate.neptune.gremlin.generate_neptune_person_form_json_gremlin_csv import convert_to_gremlin as generate_neptune_person_form_gremlin_csv
from generate.neptune.gremlin.generate_neptune_person_organization_json_gremlin_csv import convert_to_gremlin as generate_neptune_person_organization_gremlin_csv
from generate.neptune.gremlin.generate_neptune_person_phone_json_gremlin_csv import convert_to_gremlin as generate_neptune_person_phone_gremlin_csv
from generate.neptune.gremlin.generate_neptune_person_receipt_json_gremlin_csv import convert_to_gremlin as generate_neptune_person_receipt_gremlin_csv

# Import validation function
from validation.validate_edges_referential_integrity_gremlin import validate_edges

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

        # Clean up Neptune directory (CSV files) - Skip existing edge files to avoid referential integrity issues
        neptune_path = "src/data/output/neptune"
        if os.path.exists(neptune_path):
            csv_files = glob.glob(os.path.join(neptune_path, "*.csv"))
            # Keep existing edge files that pass validation
            skip_files = [
                "neptune_person_address_edges_gremlin.csv",
                "neptune_person_form_edges_gremlin.csv", 
                "neptune_person_receipt_edges_gremlin.csv"
            ]
            for file in csv_files:
                filename = os.path.basename(file)
                if filename in skip_files:
                    print(f"Skipping deletion of: {file} (preserving for referential integrity)")
                    continue
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

def run_function_with_timing(func, func_name):
    """Run a function and return timing information"""
    start_time = time.time()
    try:
        print(f"\nRunning {func_name}...")
        result = func()
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"Successfully completed {func_name} in {execution_time:.2f} seconds")
        return True, execution_time, result
    except Exception as e:
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"Error running {func_name}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, execution_time, None

def main():
    # Clear terminal on startup
    clear_terminal()
    
    # Start overall timing
    total_start_time = time.time()
    
    # System resource detection
    num_cores = mp.cpu_count()
    memory_gb = psutil.virtual_memory().total // (1024**3)
    
    print("🚀 UNIFIED STREAMING NEPTUNE GREMLIN DATA GENERATION")
    print("=" * 60)
    print("This version runs all functions directly (no subprocess overhead)")
    print(f"CPU Cores: {num_cores}")
    print(f"Available Memory: {memory_gb} GB")
    print("=" * 60)
    
    print("Starting cleanup process...")
    cleanup_start_time = time.time()
    if not cleanup_output_directories():
        print("Cleanup failed. Stopping process.")
        return
    cleanup_time = time.time() - cleanup_start_time
    print(f"Cleanup completed in {cleanup_time:.2f} seconds")

    print("\nStarting UNIFIED STREAMING data generation process...")
    
    # Track timing for each phase
    phase_times = {}
    function_times = {}
    
    # Phase 1: Node Generation
    print("\nPhase 1: Generating Node Data...")
    phase_start_time = time.time()
    
    node_functions = [
        (generate_node_data, "Node Data Generation"),
        (generate_mock_person_data, "Person Data Generation"),
        (generate_mock_address_data, "Address Data Generation"),
        (generate_mock_anumber_data, "ANumber Data Generation"),
        (generate_mock_building_data, "Building Data Generation"),
        (generate_mock_datainstance_data, "Data Instance Generation"),
        (generate_mock_email_data, "Email Data Generation"),
        (generate_mock_form_data, "Form Data Generation"),
        (generate_mock_phone_data, "Phone Data Generation"),
        (generate_mock_name_data, "Name Data Generation"),
        (generate_mock_organization_data, "Organization Data Generation"),
        (generate_mock_receipt_data, "Receipt Data Generation"),
    ]
    
    for func, func_name in node_functions:
        success, execution_time, result = run_function_with_timing(func, func_name)
        function_times[func_name] = execution_time
        if not success:
            print(f"Failed to run {func_name}. Stopping process.")
            return
    
    phase_times["Node Generation"] = time.time() - phase_start_time
    
    # Force garbage collection between phases
    gc.collect()
    
    # Phase 2: Edge Generation (Streaming)
    print("\nPhase 2: Generating Edge Data (Streaming)...")
    phase_start_time = time.time()
    
    edge_functions = [
        (generate_person_address_edges_streaming, "Person-Address Edge Generation"),
        (generate_person_form_edges_streaming, "Person-Form Edge Generation"),
        (generate_person_receipt_edges_streaming, "Person-Receipt Edge Generation"),
        (generate_person_anumber_edges_streaming, "Person-ANumber Edge Generation"),
        (generate_person_datainstance_edges_streaming, "Person-DataInstance Edge Generation"),
        (generate_person_email_edges_streaming, "Person-Email Edge Generation"),
        (generate_person_name_edges_streaming, "Person-Name Edge Generation"),
        (generate_person_organization_edges_streaming, "Person-Organization Edge Generation"),
        (generate_person_phone_edges_streaming, "Person-Phone Edge Generation"),
        (generate_building_address_edges_streaming, "Building-Address Edge Generation"),
        (generate_organization_address_edges_streaming, "Organization-Address Edge Generation"),
        (generate_organization_organization_edges_streaming, "Organization-Organization Edge Generation"),
    ]
    
    for func, func_name in edge_functions:
        success, execution_time, result = run_function_with_timing(func, func_name)
        function_times[func_name] = execution_time
        if not success:
            print(f"Failed to run {func_name}. Stopping process.")
            return
    
    phase_times["Edge Generation (Streaming)"] = time.time() - phase_start_time
    
    # Force garbage collection between phases
    gc.collect()
    
    # Phase 3: Neptune CSV Generation
    print("\nPhase 3: Generating Neptune Gremlin CSV Data...")
    phase_start_time = time.time()
    
    neptune_functions = [
        (generate_neptune_person_gremlin_csv, "Neptune Person CSV Generation"),
        (generate_neptune_address_gremlin_csv, "Neptune Address CSV Generation"),
        (generate_neptune_anumber_gremlin_csv, "Neptune ANumber CSV Generation"),
        (generate_neptune_datainstance_gremlin_csv, "Neptune DataInstance CSV Generation"),
        (generate_neptune_email_gremlin_csv, "Neptune Email CSV Generation"),
        (generate_neptune_form_gremlin_csv, "Neptune Form CSV Generation"),
        (generate_neptune_receipt_gremlin_csv, "Neptune Receipt CSV Generation"),
        (generate_neptune_building_gremlin_csv, "Neptune Building CSV Generation"),
        (generate_neptune_organization_gremlin_csv, "Neptune Organization CSV Generation"),
        (generate_neptune_phone_gremlin_csv, "Neptune Phone CSV Generation"),
        (generate_neptune_building_address_gremlin_csv, "Neptune Building-Address CSV Generation"),
        (generate_neptune_organization_address_gremlin_csv, "Neptune Organization-Address CSV Generation"),
        (generate_neptune_person_address_gremlin_csv, "Neptune Person-Address CSV Generation"),
        (generate_neptune_person_anumber_gremlin_csv, "Neptune Person-ANumber CSV Generation"),
        (generate_neptune_person_datainstance_gremlin_csv, "Neptune Person-DataInstance CSV Generation"),
        (generate_neptune_person_email_gremlin_csv, "Neptune Person-Email CSV Generation"),
        (generate_neptune_person_form_gremlin_csv, "Neptune Person-Form CSV Generation"),
        (generate_neptune_person_organization_gremlin_csv, "Neptune Person-Organization CSV Generation"),
        (generate_neptune_person_phone_gremlin_csv, "Neptune Person-Phone CSV Generation"),
        (generate_neptune_person_receipt_gremlin_csv, "Neptune Person-Receipt CSV Generation"),
    ]
    
    for func, func_name in neptune_functions:
        success, execution_time, result = run_function_with_timing(func, func_name)
        function_times[func_name] = execution_time
        if not success:
            print(f"Failed to run {func_name}. Stopping process.")
            return
    
    phase_times["Neptune CSV Generation"] = time.time() - phase_start_time
    
    # Force garbage collection between phases
    gc.collect()
    
    # Phase 4: Validation
    print("\nPhase 4: Validating Edge Referential Integrity...")
    phase_start_time = time.time()
    
    validation_functions = [
        (validate_edges, "Edge Referential Integrity Validation"),
    ]
    
    for func, func_name in validation_functions:
        success, execution_time, result = run_function_with_timing(func, func_name)
        function_times[func_name] = execution_time
        if not success:
            print(f"Failed to run {func_name}. Stopping process.")
            return
    
    phase_times["Validation"] = time.time() - phase_start_time

    # Calculate total time
    total_execution_time = time.time() - total_start_time

    # Print detailed timing summary
    print("\n" + "="*80)
    print("UNIFIED STREAMING EXECUTION TIME SUMMARY")
    print("="*80)
    print(f"Total Execution Time: {total_execution_time:.2f} seconds ({total_execution_time/60:.2f} minutes)")
    print(f"Cleanup Time: {cleanup_time:.2f} seconds")
    print()
    
    # Phase timing table
    print("Phase Execution Times:")
    print("-" * 60)
    print(f"{'Phase':<30} {'Time (seconds)':<15} {'Time (minutes)':<15}")
    print("-" * 60)
    for phase, phase_time in phase_times.items():
        print(f"{phase:<30} {phase_time:<15.2f} {phase_time/60:<15.2f}")
    print()
    
    # Individual function timing tables
    print("Individual Function Execution Times:")
    print()
    
    # Node Functions Table
    print("Node Generation Functions:")
    print("-" * 70)
    print(f"{'Function Name':<50} {'Time (seconds)':<15}")
    print("-" * 70)
    for func, func_name in node_functions:
        if func_name in function_times:
            print(f"{func_name:<50} {function_times[func_name]:<15.2f}")
    print()
    
    # Edge Functions Table
    print("Edge Generation Functions (Streaming):")
    print("-" * 70)
    print(f"{'Function Name':<50} {'Time (seconds)':<15}")
    print("-" * 70)
    for func, func_name in edge_functions:
        if func_name in function_times:
            print(f"{func_name:<50} {function_times[func_name]:<15.2f}")
    print()
    
    # Neptune Functions Table
    print("Neptune CSV Generation Functions:")
    print("-" * 70)
    print(f"{'Function Name':<50} {'Time (seconds)':<15}")
    print("-" * 70)
    for func, func_name in neptune_functions:
        if func_name in function_times:
            print(f"{func_name:<50} {function_times[func_name]:<15.2f}")
    print()
    
    # Validation Functions Table
    print("Validation Functions:")
    print("-" * 70)
    print(f"{'Function Name':<50} {'Time (seconds)':<15}")
    print("-" * 70)
    for func, func_name in validation_functions:
        if func_name in function_times:
            print(f"{func_name:<50} {function_times[func_name]:<15.2f}")
    print()
    
    print("🎉 UNIFIED STREAMING data generation and validation completed successfully!")
    print("🚀 This version eliminates subprocess overhead for maximum performance!")

if __name__ == "__main__":
    main() 