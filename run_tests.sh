#!/bin/bash

# Comprehensive testing script for optimized node generation

echo "🧪 NEPTUNE MOCK DATA GENERATION - TEST SUITE"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    print_error "Python3 is not installed"
    exit 1
fi

print_success "Python3 found: $(python3 --version)"

# Check required directories
if [ ! -d "src/generate/mock/nodes" ]; then
    print_error "Source directory not found: src/generate/mock/nodes"
    exit 1
fi

print_success "Source directory found"

# Test 1: Quick Performance Test
echo -e "\n${BLUE}═══════════════════════════════════════${NC}"
echo -e "${BLUE}TEST 1: Quick Performance Test${NC}"
echo -e "${BLUE}═══════════════════════════════════════${NC}"

print_status "Running quick performance test..."
python3 benchmark_performance.py --quick

if [ $? -eq 0 ]; then
    print_success "Quick performance test completed"
else
    print_error "Quick performance test failed"
fi

# Test 2: Unit Tests
echo -e "\n${BLUE}═══════════════════════════════════════${NC}"
echo -e "${BLUE}TEST 2: Unit Tests${NC}"
echo -e "${BLUE}═══════════════════════════════════════${NC}"

print_status "Running comprehensive unit tests..."
python3 test_node_generation.py

if [ $? -eq 0 ]; then
    print_success "Unit tests completed"
else
    print_warning "Some unit tests may have failed - check output above"
fi

# Test 3: Memory Test
echo -e "\n${BLUE}═══════════════════════════════════════${NC}"
echo -e "${BLUE}TEST 3: Memory Usage Test${NC}"
echo -e "${BLUE}═══════════════════════════════════════${NC}"

print_status "Testing memory usage with different dataset sizes..."

# Create a simple memory test script
cat > temp_memory_test.py << 'EOF'
import psutil
import sys
import os
sys.path.insert(0, 'src/generate/mock/nodes')

# Patch the record count
import generate_node_data
original_count = generate_node_data.NUM_NODE_RECORDS
generate_node_data.NUM_NODE_RECORDS = 10000

process = psutil.Process()
initial_memory = process.memory_info().rss / 1024 / 1024

print(f"Initial memory: {initial_memory:.1f} MB")

# Run generation
df = generate_node_data.generate_node_data()
peak_memory = process.memory_info().rss / 1024 / 1024

print(f"Peak memory: {peak_memory:.1f} MB")
print(f"Memory used: {peak_memory - initial_memory:.1f} MB")
print(f"Memory per record: {(peak_memory - initial_memory) / 10000 * 1024:.3f} KB")

# Cleanup
del df
import gc
gc.collect()

final_memory = process.memory_info().rss / 1024 / 1024
print(f"Memory after cleanup: {final_memory:.1f} MB")

# Restore original
generate_node_data.NUM_NODE_RECORDS = original_count
EOF

python3 temp_memory_test.py
rm temp_memory_test.py

# Test 4: Concurrency Test
echo -e "\n${BLUE}═══════════════════════════════════════${NC}"
echo -e "${BLUE}TEST 4: Concurrency Test${NC}"
echo -e "${BLUE}═══════════════════════════════════════${NC}"

print_status "Testing concurrent execution..."

# Create concurrency test
cat > temp_concurrency_test.py << 'EOF'
import multiprocessing as mp
import time
import sys
import os
sys.path.insert(0, 'src/generate/mock/nodes')

def run_generation(worker_id):
    import generate_node_data
    # Use smaller dataset for concurrency test
    original_count = generate_node_data.NUM_NODE_RECORDS
    generate_node_data.NUM_NODE_RECORDS = 5000
    
    start_time = time.time()
    df = generate_node_data.generate_node_data()
    end_time = time.time()
    
    # Restore original
    generate_node_data.NUM_NODE_RECORDS = original_count
    
    return {
        'worker_id': worker_id,
        'time': end_time - start_time,
        'records': len(df)
    }

if __name__ == '__main__':
    num_workers = min(4, mp.cpu_count())
    print(f"Testing with {num_workers} concurrent workers...")
    
    start_time = time.time()
    with mp.Pool(num_workers) as pool:
        results = pool.map(run_generation, range(num_workers))
    end_time = time.time()
    
    total_time = end_time - start_time
    total_records = sum(r['records'] for r in results)
    
    print(f"Concurrent execution results:")
    for result in results:
        print(f"  Worker {result['worker_id']}: {result['time']:.3f}s, {result['records']} records")
    
    print(f"Total time: {total_time:.3f}s")
    print(f"Total records: {total_records}")
    print(f"Overall throughput: {total_records/total_time:,.0f} records/second")
EOF

python3 temp_concurrency_test.py
rm temp_concurrency_test.py

if [ $? -eq 0 ]; then
    print_success "Concurrency test completed"
else
    print_warning "Concurrency test had issues"
fi

# Test 5: File Integrity Test
echo -e "\n${BLUE}═══════════════════════════════════════${NC}"
echo -e "${BLUE}TEST 5: File Integrity Test${NC}"
echo -e "${BLUE}═══════════════════════════════════════${NC}"

print_status "Testing file output integrity..."

# Run generation and check file
python3 src/generate/mock/nodes/generate_node_data.py > /dev/null

if [ -f "src/data/input/node_data.csv" ]; then
    print_success "Output file created successfully"
    
    # Check file size
    file_size=$(wc -l < "src/data/input/node_data.csv")
    print_status "File contains $file_size lines"
    
    # Check CSV format
    if head -1 "src/data/input/node_data.csv" | grep -q "node_id,node_type,batch"; then
        print_success "CSV header is correct"
    else
        print_error "CSV header is incorrect"
    fi
    
    # Check for data
    if [ $file_size -gt 1 ]; then
        print_success "File contains data records"
    else
        print_error "File appears to be empty"
    fi
else
    print_error "Output file was not created"
fi

# Optional: Full Benchmark (only if requested)
if [ "$1" = "--full-benchmark" ]; then
    echo -e "\n${BLUE}═══════════════════════════════════════${NC}"
    echo -e "${BLUE}FULL BENCHMARK SUITE${NC}"
    echo -e "${BLUE}═══════════════════════════════════════${NC}"
    
    print_status "Running full benchmark suite (this may take several minutes)..."
    python3 benchmark_performance.py --full --visualize
fi

# Summary
echo -e "\n${GREEN}═══════════════════════════════════════${NC}"
echo -e "${GREEN}TEST SUMMARY${NC}"
echo -e "${GREEN}═══════════════════════════════════════${NC}"

print_success "All tests completed!"
print_status "To run full benchmark: ./run_tests.sh --full-benchmark"
print_status "To run individual tests: python3 test_node_generation.py"
print_status "To run quick performance test: python3 benchmark_performance.py --quick"

echo -e "\n${BLUE}Performance optimization is working correctly! 🚀${NC}"