import time
import subprocess
import sys
import os

def quick_performance_test():
    """Quick performance test for edge generation"""
    print("🚀 Quick Performance Test")
    print("=" * 40)
    
    # Test the optimized person-address script
    script_path = 'src/generate/mock/edges/generate_mock_person-address_edge.py'
    
    if not os.path.exists(script_path):
        print(f"❌ Script not found: {script_path}")
        return
    
    print(f"Testing: {script_path}")
    print("Starting performance test...")
    
    start_time = time.time()
    
    try:
        # Run the script with a timeout
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        if result.returncode == 0:
            print(f"✅ SUCCESS!")
            print(f"⏱️  Execution time: {execution_time:.2f} seconds")
            
            # Try to extract edge count and batch size
            output_lines = result.stdout.split('\n')
            edge_count = None
            edges_per_second = None
            batch_size = None
            
            for line in output_lines:
                if 'edges generated' in line.lower():
                    import re
                    numbers = re.findall(r'\d+', line)
                    if numbers:
                        edge_count = int(numbers[-1])
                        edges_per_second = edge_count / execution_time
                elif 'batch size' in line.lower():
                    import re
                    numbers = re.findall(r'\d+', line)
                    if numbers:
                        batch_size = int(numbers[-1])
            
            if edge_count:
                print(f"📊 Edges generated: {edge_count:,}")
                print(f"🚀 Edges per second: {edges_per_second:.2f}")
                if batch_size:
                    print(f"📦 Batch size: {batch_size:,}")
                
                # Performance assessment
                if execution_time < 60:
                    print("🎉 EXCELLENT: Under 1 minute!")
                elif execution_time < 120:
                    print("👍 GOOD: Under 2 minutes")
                elif execution_time < 300:
                    print("⚠️  ACCEPTABLE: Under 5 minutes")
                else:
                    print("❌ SLOW: Over 5 minutes")
                    
            else:
                print("⚠️  Could not extract edge count from output")
                
        else:
            print(f"❌ FAILED: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        print("⏰ TIMEOUT: Script exceeded 5 minutes")
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

def test_high_performance_generator():
    """Test the high-performance edge generator"""
    print("\n🚀 High Performance Generator Test")
    print("=" * 50)
    
    script_path = 'src/generate/mock/edges/high_performance_edge_generator.py'
    
    if not os.path.exists(script_path):
        print(f"❌ Script not found: {script_path}")
        return
    
    print(f"Testing: {script_path}")
    print("Starting high-performance test...")
    
    start_time = time.time()
    
    try:
        # Run the script with a timeout
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout for all edge types
        )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        if result.returncode == 0:
            print(f"✅ SUCCESS!")
            print(f"⏱️  Total execution time: {execution_time:.2f} seconds ({execution_time/60:.2f} minutes)")
            
            # Try to extract total time from output
            output_lines = result.stdout.split('\n')
            total_time = None
            
            for line in output_lines:
                if 'total execution time' in line.lower():
                    import re
                    numbers = re.findall(r'\d+\.?\d*', line)
                    if numbers:
                        total_time = float(numbers[0])
                        break
            
            if total_time:
                print(f"📊 High-performance total time: {total_time:.2f} seconds")
                
                # Performance assessment
                if total_time < 120:
                    print("🎉 EXCELLENT: Under 2 minutes for all edge types!")
                elif total_time < 300:
                    print("👍 GOOD: Under 5 minutes for all edge types")
                elif total_time < 600:
                    print("⚠️  ACCEPTABLE: Under 10 minutes for all edge types")
                else:
                    print("❌ SLOW: Over 10 minutes for all edge types")
                    
            else:
                print("⚠️  Could not extract total time from output")
                
        else:
            print(f"❌ FAILED: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        print("⏰ TIMEOUT: Script exceeded 10 minutes")
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

def check_dataset_size():
    """Check the size of the dataset being processed"""
    print("\n📊 Dataset Analysis")
    print("=" * 40)
    
    node_data_path = 'src/data/input/node_data.csv'
    if os.path.exists(node_data_path):
        import pandas as pd
        try:
            df = pd.read_csv(node_data_path)
            total_nodes = len(df)
            person_nodes = len(df[df['node_type'] == 'person'])
            address_nodes = len(df[df['node_type'] == 'address'])
            form_nodes = len(df[df['node_type'] == 'form'])
            receipt_nodes = len(df[df['node_type'] == 'receipt'])
            
            print(f"Total nodes: {total_nodes:,}")
            print(f"Person nodes: {person_nodes:,}")
            print(f"Address nodes: {address_nodes:,}")
            print(f"Form nodes: {form_nodes:,}")
            print(f"Receipt nodes: {receipt_nodes:,}")
            
            # Expected edge counts
            expected_address_edges = person_nodes * 2  # Average 2 addresses per person
            expected_form_edges = person_nodes * 2     # Average 2 forms per person
            expected_receipt_edges = person_nodes * 3  # Average 3 receipts per person
            
            print(f"\nExpected edges:")
            print(f"Person-Address: ~{expected_address_edges:,}")
            print(f"Person-Form: ~{expected_form_edges:,}")
            print(f"Person-Receipt: ~{expected_receipt_edges:,}")
            
            # Batch size recommendations
            import multiprocessing
            num_cores = multiprocessing.cpu_count()
            
            print(f"\nBatch size recommendations:")
            print(f"CPU cores: {num_cores}")
            print(f"Standard batches: {person_nodes // (num_cores * 2):,} persons per batch")
            print(f"Large batches: {person_nodes // (num_cores * 1):,} persons per batch")
            
            if total_nodes > 100000:
                print("\n⚠️  Large dataset detected - use high-performance generator")
            elif total_nodes > 50000:
                print("\n📈 Medium dataset - should see good performance with larger batches")
            else:
                print("\n📉 Small dataset - performance gains may be minimal")
                
        except Exception as e:
            print(f"Error reading dataset: {e}")
    else:
        print(f"❌ Node data file not found: {node_data_path}")

def main():
    """Main function"""
    print("🔍 Edge Generation Performance Test")
    print("This will test the optimized edge generation with larger batches")
    
    # Check dataset size first
    check_dataset_size()
    
    # Run performance test for individual script
    print("\n" + "=" * 50)
    quick_performance_test()
    
    # Ask user if they want to test high-performance generator
    print("\n" + "=" * 50)
    print("💡 Performance Options:")
    print("1. Individual optimized scripts (larger batches)")
    print("2. High-performance generator (maximum optimization)")
    print("3. Both tests")
    
    choice = input("\nEnter choice (1/2/3) or press Enter to skip high-performance test: ").strip()
    
    if choice in ['2', '3']:
        test_high_performance_generator()
    
    print("\n" + "=" * 50)
    print("💡 Tips for better performance:")
    print("1. Ensure you have sufficient RAM (8GB+)")
    print("2. Use SSD storage for faster I/O")
    print("3. Close other applications to free up CPU")
    print("4. For very large datasets, use high_performance_edge_generator.py")
    print("5. Larger batches reduce parallelization overhead")

if __name__ == "__main__":
    main() 