import time
import subprocess
import os
import sys
from pathlib import Path

def run_performance_comparison():
    """
    Compare performance between original and optimized edge generation scripts
    """
    print("=" * 60)
    print("PERFORMANCE COMPARISON: ORIGINAL vs OPTIMIZED")
    print("=" * 60)
    
    # Define the scripts to test
    scripts = {
        'Original Person-Address': 'src/generate/mock/edges/generate_mock_person-address_edge.py',
        'Original Person-Form': 'src/generate/mock/edges/generate_mock_person-form_edge.py', 
        'Original Person-Receipt': 'src/generate/mock/edges/generate_mock_person-receipt_edge.py',
        'Optimized All Edges': 'src/generate/mock/edges/optimized_edge_generator.py'
    }
    
    results = {}
    
    for name, script_path in scripts.items():
        if not os.path.exists(script_path):
            print(f"Warning: {script_path} not found, skipping...")
            continue
            
        print(f"\n{'='*40}")
        print(f"Testing: {name}")
        print(f"{'='*40}")
        
        start_time = time.time()
        
        try:
            # Run the script
            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            if result.returncode == 0:
                print(f"✅ SUCCESS: {name}")
                print(f"⏱️  Execution time: {execution_time:.2f} seconds")
                
                # Try to extract edge count from output
                edge_count = extract_edge_count(result.stdout)
                if edge_count:
                    print(f"📊 Edges generated: {edge_count}")
                    edges_per_second = edge_count / execution_time
                    print(f"🚀 Edges per second: {edges_per_second:.2f}")
                
                results[name] = {
                    'status': 'SUCCESS',
                    'time': execution_time,
                    'edge_count': edge_count,
                    'edges_per_second': edge_count / execution_time if edge_count else 0
                }
                
            else:
                print(f"❌ FAILED: {name}")
                print(f"Error: {result.stderr}")
                results[name] = {
                    'status': 'FAILED',
                    'time': execution_time,
                    'error': result.stderr
                }
                
        except subprocess.TimeoutExpired:
            print(f"⏰ TIMEOUT: {name} (exceeded 5 minutes)")
            results[name] = {
                'status': 'TIMEOUT',
                'time': 300
            }
        except Exception as e:
            print(f"❌ ERROR: {name} - {str(e)}")
            results[name] = {
                'status': 'ERROR',
                'error': str(e)
            }
    
    # Print summary
    print("\n" + "=" * 60)
    print("PERFORMANCE SUMMARY")
    print("=" * 60)
    
    successful_results = {k: v for k, v in results.items() if v['status'] == 'SUCCESS'}
    
    if successful_results:
        print("\n📈 Performance Comparison:")
        print(f"{'Script':<30} {'Time (s)':<10} {'Edges':<10} {'Edges/s':<10}")
        print("-" * 60)
        
        for name, result in successful_results.items():
            print(f"{name:<30} {result['time']:<10.2f} {result['edge_count']:<10} {result['edges_per_second']:<10.2f}")
        
        # Calculate improvements
        if 'Optimized All Edges' in successful_results:
            optimized_result = successful_results['Optimized All Edges']
            
            print(f"\n🚀 OPTIMIZATION IMPROVEMENTS:")
            print(f"Optimized script generates {optimized_result['edges_per_second']:.2f} edges/second")
            
            # Compare with individual scripts if available
            for name, result in successful_results.items():
                if name != 'Optimized All Edges' and result['edges_per_second'] > 0:
                    improvement = (optimized_result['edges_per_second'] / result['edges_per_second'] - 1) * 100
                    print(f"vs {name}: {improvement:+.1f}% faster")
    
    # Print failed scripts
    failed_results = {k: v for k, v in results.items() if v['status'] != 'SUCCESS'}
    if failed_results:
        print(f"\n❌ FAILED SCRIPTS:")
        for name, result in failed_results.items():
            print(f"  {name}: {result['status']}")
            if 'error' in result:
                print(f"    Error: {result['error'][:100]}...")

def extract_edge_count(output):
    """Extract edge count from script output"""
    lines = output.split('\n')
    for line in lines:
        if 'edges generated' in line.lower() or 'total edges' in line.lower():
            # Look for numbers in the line
            import re
            numbers = re.findall(r'\d+', line)
            if numbers:
                return int(numbers[-1])  # Take the last number
    return None

def check_prerequisites():
    """Check if required files exist"""
    required_files = [
        'src/data/input/node_data.csv',
        'src/data/output/gds/mock_person_data.json'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ Missing required files:")
        for file_path in missing_files:
            print(f"  - {file_path}")
        print("\nPlease ensure you have:")
        print("1. Generated node data (run generate_node_data.py)")
        print("2. Generated person data (run generate_mock_person_data_json.py)")
        return False
    
    return True

def main():
    """Main function"""
    print("🔍 Edge Generation Performance Comparison")
    print("This script will compare the performance of original vs optimized edge generation")
    
    if not check_prerequisites():
        print("\n❌ Cannot run performance comparison due to missing files")
        return
    
    print("\n✅ All prerequisites met, starting performance comparison...")
    run_performance_comparison()

if __name__ == "__main__":
    main() 