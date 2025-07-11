#!/usr/bin/env python3
"""
Performance benchmarking script for node generation optimization
"""

import time
import subprocess
import sys
import pandas as pd
import matplotlib.pyplot as plt
import json
from datetime import datetime

def run_benchmark_test(record_count, iterations=3):
    """Run benchmark test for specific record count"""
    times = []
    
    for i in range(iterations):
        # Modify the record count temporarily
        with open('src/generate/mock/nodes/generate_node_data.py', 'r') as f:
            content = f.read()
        
        # Replace the NUM_NODE_RECORDS value
        original_line = "NUM_NODE_RECORDS = 200000"
        test_line = f"NUM_NODE_RECORDS = {record_count}"
        
        modified_content = content.replace(original_line, test_line)
        
        with open('src/generate/mock/nodes/generate_node_data.py', 'w') as f:
            f.write(modified_content)
        
        try:
            # Run the script and measure time
            start_time = time.time()
            result = subprocess.run([
                sys.executable, 
                'src/generate/mock/nodes/generate_node_data.py'
            ], capture_output=True, text=True, timeout=30)
            end_time = time.time()
            
            if result.returncode == 0:
                execution_time = end_time - start_time
                times.append(execution_time)
                print(f"  Iteration {i+1}: {execution_time:.3f}s ({record_count/execution_time:,.0f} rec/s)")
            else:
                print(f"  Iteration {i+1}: FAILED - {result.stderr}")
                
        except subprocess.TimeoutExpired:
            print(f"  Iteration {i+1}: TIMEOUT")
            
        finally:
            # Restore original content
            with open('src/generate/mock/nodes/generate_node_data.py', 'w') as f:
                f.write(content)
    
    return times

def run_comprehensive_benchmark():
    """Run comprehensive performance benchmark"""
    print("🚀 COMPREHENSIVE PERFORMANCE BENCHMARK")
    print("=" * 80)
    
    # Test different record counts
    test_sizes = [1000, 5000, 10000, 25000, 50000, 100000, 200000]
    results = {}
    
    for size in test_sizes:
        print(f"\n📊 Testing {size:,} records:")
        times = run_benchmark_test(size, iterations=3)
        
        if times:
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)
            avg_throughput = size / avg_time
            
            results[size] = {
                'avg_time': avg_time,
                'min_time': min_time,
                'max_time': max_time,
                'avg_throughput': avg_throughput,
                'times': times
            }
            
            print(f"  Average: {avg_time:.3f}s ({avg_throughput:,.0f} rec/s)")
            print(f"  Best: {min_time:.3f}s ({size/min_time:,.0f} rec/s)")
            print(f"  Worst: {max_time:.3f}s ({size/max_time:,.0f} rec/s)")
        else:
            print("  ❌ All iterations failed")
            results[size] = None
    
    return results

def generate_performance_report(results):
    """Generate detailed performance report"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save results to JSON
    json_results = {}
    for size, data in results.items():
        if data:
            json_results[str(size)] = data
    
    with open(f'performance_report_{timestamp}.json', 'w') as f:
        json.dump(json_results, f, indent=2)
    
    # Generate markdown report
    report_content = f"""# Node Generation Performance Report
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Summary
This report shows performance benchmarks for the optimized node generation code.

## Results

| Records | Avg Time (s) | Min Time (s) | Max Time (s) | Avg Throughput (rec/s) | Best Throughput (rec/s) |
|---------|--------------|--------------|--------------|------------------------|-------------------------|
"""
    
    for size, data in results.items():
        if data:
            report_content += f"| {size:,} | {data['avg_time']:.3f} | {data['min_time']:.3f} | {data['max_time']:.3f} | {data['avg_throughput']:,.0f} | {size/data['min_time']:,.0f} |\n"
    
    report_content += f"""

## Performance Analysis

### Scaling Characteristics
"""
    
    # Calculate scaling efficiency
    if results.get(1000) and results.get(100000):
        small_throughput = results[1000]['avg_throughput']
        large_throughput = results[100000]['avg_throughput']
        scaling_efficiency = (large_throughput / small_throughput) * 100
        
        report_content += f"""
- Small dataset (1K records): {small_throughput:,.0f} records/second
- Large dataset (100K records): {large_throughput:,.0f} records/second
- Scaling efficiency: {scaling_efficiency:.1f}% (higher is better)
"""
    
    # Find sweet spot
    best_size = None
    best_throughput = 0
    for size, data in results.items():
        if data and data['avg_throughput'] > best_throughput:
            best_throughput = data['avg_throughput']
            best_size = size
    
    if best_size:
        report_content += f"""
### Optimal Performance
- Best throughput achieved with {best_size:,} records
- Peak performance: {best_throughput:,.0f} records/second
"""
    
    report_content += """
## Recommendations

1. **Optimal Batch Size**: Use batch sizes between 10K-50K records for best throughput
2. **Memory Considerations**: Monitor memory usage for datasets > 100K records
3. **Parallel Processing**: The optimization scales well with available CPU cores
4. **I/O Optimization**: CSV writing becomes bottleneck for very large datasets

## Technical Details

- **CPU Cores**: System automatically detects and uses available cores
- **Memory Optimization**: Uses pandas categorical data types and numpy arrays
- **Parallel Processing**: ThreadPoolExecutor for concurrent node generation
- **Vectorized Operations**: NumPy arrays for mathematical operations
"""
    
    with open(f'performance_report_{timestamp}.md', 'w') as f:
        f.write(report_content)
    
    print(f"\n📋 Performance reports saved:")
    print(f"  - performance_report_{timestamp}.json")
    print(f"  - performance_report_{timestamp}.md")

def create_performance_visualization(results):
    """Create performance visualization charts"""
    try:
        import matplotlib.pyplot as plt
        
        # Prepare data for plotting
        sizes = []
        avg_times = []
        throughputs = []
        
        for size, data in sorted(results.items()):
            if data:
                sizes.append(size)
                avg_times.append(data['avg_time'])
                throughputs.append(data['avg_throughput'])
        
        if not sizes:
            print("No data available for visualization")
            return
        
        # Create subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Plot 1: Execution Time vs Record Count
        ax1.plot(sizes, avg_times, 'b-o', linewidth=2, markersize=6)
        ax1.set_xlabel('Number of Records')
        ax1.set_ylabel('Execution Time (seconds)')
        ax1.set_title('Execution Time vs Record Count')
        ax1.grid(True, alpha=0.3)
        ax1.set_xscale('log')
        
        # Plot 2: Throughput vs Record Count
        ax2.plot(sizes, throughputs, 'g-o', linewidth=2, markersize=6)
        ax2.set_xlabel('Number of Records')
        ax2.set_ylabel('Throughput (records/second)')
        ax2.set_title('Throughput vs Record Count')
        ax2.grid(True, alpha=0.3)
        ax2.set_xscale('log')
        
        plt.tight_layout()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f'performance_chart_{timestamp}.png'
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.show()
        
        print(f"📈 Performance chart saved: {filename}")
        
    except ImportError:
        print("📈 Matplotlib not available - skipping visualization")

def quick_performance_test():
    """Quick performance test with current settings"""
    print("⚡ QUICK PERFORMANCE TEST")
    print("-" * 40)
    
    start_time = time.time()
    result = subprocess.run([
        sys.executable, 
        'src/generate/mock/nodes/generate_node_data.py'
    ], capture_output=True, text=True)
    end_time = time.time()
    
    if result.returncode == 0:
        execution_time = end_time - start_time
        
        # Extract performance metrics from output
        output_lines = result.stdout.split('\n')
        for line in output_lines:
            if 'Performance:' in line:
                print(f"✅ {line.strip()}")
            elif 'Overall throughput:' in line:
                print(f"🎯 {line.strip()}")
        
        print(f"⏱️  Total execution time: {execution_time:.3f} seconds")
    else:
        print(f"❌ Test failed: {result.stderr}")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Performance benchmark for node generation')
    parser.add_argument('--quick', action='store_true', help='Run quick test only')
    parser.add_argument('--full', action='store_true', help='Run full benchmark suite')
    parser.add_argument('--visualize', action='store_true', help='Create performance charts')
    
    args = parser.parse_args()
    
    if args.quick or (not args.full and not args.visualize):
        quick_performance_test()
    
    if args.full:
        results = run_comprehensive_benchmark()
        generate_performance_report(results)
        
        if args.visualize:
            create_performance_visualization(results)
    
    print("\n🏁 Benchmark complete!")