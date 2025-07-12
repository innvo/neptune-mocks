#!/usr/bin/env python3
"""
Test script for high-performance parallel CSV generation
Smaller dataset for quick testing
"""

# Import the high-performance generator
from graph_parallel import HighPerformanceGremlinCSVGenerator
import time

def main():
    """Test with smaller dataset"""
    # Configuration for testing
    FILE_SIZE_LIMIT = 100000  # 100K records per file
    OUTPUT_DIR = "src/neptune-performance-test/csv_output"
    MAX_WORKERS = 14  # Up to 14 CPUs
    MAX_MEMORY_GB = 48  # Up to 48GB RAM
    
    # Test generation counts
    GENERATION_COUNTS = {
        'person': 500000,    # 500K person records 
        'address': 300000,   # 300K address records
        'building': 150000,  # 150K building records
        'form': 200000,      # 200K form records
        'name': 400000,      # 400K name records
        'email': 350000,     # 350K email records
        'phone': 450000      # 450K phone records
    }
    
    print("🧪 TESTING HIGH-PERFORMANCE PARALLEL CSV GENERATION")
    print("=" * 60)
    print(f"Target: {sum(GENERATION_COUNTS.values()):,} total records")
    print(f"Resources: {MAX_WORKERS} CPUs, {MAX_MEMORY_GB}GB RAM")
    print(f"File size limit: {FILE_SIZE_LIMIT:,} records per file")
    print("=" * 60)
    
    # Initialize generator
    generator = HighPerformanceGremlinCSVGenerator(
        file_size_limit=FILE_SIZE_LIMIT,
        output_dir=OUTPUT_DIR,
        max_workers=MAX_WORKERS,
        max_memory_gb=MAX_MEMORY_GB
    )
    
    # Track total execution time
    total_start_time = time.time()
    
    # Generate data for each node type
    for node_type, count in GENERATION_COUNTS.items():
        generator.generate_node_data(node_type, count)
    
    total_time = time.time() - total_start_time
    total_records = sum(GENERATION_COUNTS.values())
    overall_rate = total_records / total_time if total_time > 0 else 0
    
    # Print final summary
    generator.print_summary()
    print(f"\n⚡ TEST PERFORMANCE SUMMARY")
    print(f"Total execution time: {total_time:.2f} seconds ({total_time/60:.1f} minutes)")
    print(f"Overall generation rate: {overall_rate:,.0f} records/second")
    print("\n🎉 High-performance test completed successfully!")

if __name__ == "__main__":
    main()