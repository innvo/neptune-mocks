#!/usr/bin/env python3
"""
Comprehensive test suite for optimized node data generation
"""

import unittest
import pandas as pd
import os
import time
import sys
import tempfile
import shutil
from unittest.mock import patch
import numpy as np

# Add the source directory to the path
sys.path.insert(0, 'src/generate/mock/nodes')
from generate_node_data import generate_node_data, update_person_records, generate_batch_nodes

class TestNodeGeneration(unittest.TestCase):
    """Test suite for node data generation performance and correctness"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.original_path = 'src/data/input/node_data.csv'
        self.test_path = os.path.join(self.test_dir, 'node_data.csv')
        
        # Ensure test directories exist
        os.makedirs(os.path.dirname(self.test_path), exist_ok=True)
        
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_batch_node_generation(self):
        """Test individual batch node generation"""
        batch_info = ('person', 100, 0)
        node_ids, node_types, batches = generate_batch_nodes(batch_info)
        
        # Test correct counts
        self.assertEqual(len(node_ids), 100)
        self.assertEqual(len(node_types), 100)
        self.assertEqual(len(batches), 100)
        
        # Test data types
        self.assertTrue(all(isinstance(nid, str) for nid in node_ids))
        self.assertTrue(all(nt == 'person' for nt in node_types))
        self.assertTrue(all(isinstance(b, (int, np.integer)) for b in batches))
        
        # Test UUID format (basic check)
        self.assertTrue(all(len(nid) == 36 for nid in node_ids[:5]))  # Check first 5
        
    def test_node_data_structure(self):
        """Test the structure and integrity of generated node data"""
        with patch('src.generate.mock.nodes.generate_node_data.NUM_NODE_RECORDS', 1000):
            df = generate_node_data()
            
            # Test DataFrame structure
            self.assertIsInstance(df, pd.DataFrame)
            self.assertEqual(len(df.columns), 3)
            self.assertIn('node_id', df.columns)
            self.assertIn('node_type', df.columns)
            self.assertIn('batch', df.columns)
            
            # Test record count
            self.assertEqual(len(df), 1000)
            
            # Test node type distribution
            person_count = len(df[df['node_type'] == 'person'])
            datainstance_count = len(df[df['node_type'] == 'datainstance'])
            self.assertGreaterEqual(datainstance_count, person_count)
            
            # Test no duplicates in node_id
            self.assertEqual(len(df['node_id'].unique()), len(df))
            
    def test_performance_benchmark(self):
        """Benchmark performance against different record counts"""
        test_sizes = [1000, 5000, 10000]
        results = {}
        
        for size in test_sizes:
            with patch('src.generate.mock.nodes.generate_node_data.NUM_NODE_RECORDS', size):
                start_time = time.time()
                df = generate_node_data()
                end_time = time.time()
                
                execution_time = end_time - start_time
                records_per_second = size / execution_time
                results[size] = {
                    'time': execution_time,
                    'records_per_second': records_per_second,
                    'record_count': len(df)
                }
                
                # Performance assertions
                self.assertLess(execution_time, 5.0, f"Generation took too long for {size} records")
                self.assertGreater(records_per_second, 1000, f"Too slow: {records_per_second:.0f} records/sec")
        
        # Print performance results
        print("\n📊 PERFORMANCE BENCHMARK RESULTS:")
        print("-" * 60)
        for size, metrics in results.items():
            print(f"Records: {size:,} | Time: {metrics['time']:.3f}s | Speed: {metrics['records_per_second']:,.0f} rec/sec")
    
    def test_data_consistency(self):
        """Test data consistency across multiple runs"""
        results = []
        
        for _ in range(3):
            with patch('src.generate.mock.nodes.generate_node_data.NUM_NODE_RECORDS', 1000):
                df = generate_node_data()
                results.append({
                    'total_count': len(df),
                    'person_count': len(df[df['node_type'] == 'person']),
                    'node_types': set(df['node_type'].unique())
                })
        
        # All runs should have same structure
        for i in range(1, len(results)):
            self.assertEqual(results[0]['total_count'], results[i]['total_count'])
            self.assertEqual(results[0]['person_count'], results[i]['person_count'])
            self.assertEqual(results[0]['node_types'], results[i]['node_types'])
    
    def test_memory_efficiency(self):
        """Test memory usage with different record counts"""
        import psutil
        import gc
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        with patch('src.generate.mock.nodes.generate_node_data.NUM_NODE_RECORDS', 50000):
            df = generate_node_data()
            peak_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Clean up
            del df
            gc.collect()
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        memory_used = peak_memory - initial_memory
        memory_per_record = memory_used / 50000 * 1024  # KB per record
        
        print(f"\n💾 MEMORY USAGE ANALYSIS:")
        print(f"Initial memory: {initial_memory:.1f} MB")
        print(f"Peak memory: {peak_memory:.1f} MB")
        print(f"Memory used: {memory_used:.1f} MB")
        print(f"Memory per record: {memory_per_record:.3f} KB")
        
        # Memory efficiency assertions
        self.assertLess(memory_per_record, 1.0, "Memory usage too high per record")
    
    def test_parallel_processing(self):
        """Test that parallel processing works correctly"""
        import multiprocessing as mp
        
        # Test with different worker counts
        original_cpu_count = mp.cpu_count()
        
        with patch('multiprocessing.cpu_count', return_value=2):
            with patch('src.generate.mock.nodes.generate_node_data.NUM_NODE_RECORDS', 2000):
                start_time = time.time()
                df = generate_node_data()
                parallel_time = time.time() - start_time
        
        # Test should complete and produce correct results
        self.assertEqual(len(df), 2000)
        self.assertLess(parallel_time, 3.0, "Parallel processing took too long")
    
    def test_edge_cases(self):
        """Test edge cases and error handling"""
        
        # Test very small record count
        with patch('src.generate.mock.nodes.generate_node_data.NUM_NODE_RECORDS', 10):
            df = generate_node_data()
            self.assertEqual(len(df), 10)
            self.assertGreater(len(df['node_type'].unique()), 1)
        
        # Test batch size larger than total records
        with patch('src.generate.mock.nodes.generate_node_data.NUM_NODE_RECORDS', 100):
            with patch('src.generate.mock.nodes.generate_node_data.NUM_NODE_RECORDS_PER_BATCH', 200):
                df = generate_node_data()
                self.assertEqual(len(df), 100)
                # All records should be in batch 1
                self.assertTrue(all(df['batch'] == 1))


class TestLoadTesting(unittest.TestCase):
    """Load testing for high-volume scenarios"""
    
    def test_stress_test_large_dataset(self):
        """Stress test with large dataset"""
        large_size = 100000
        
        with patch('src.generate.mock.nodes.generate_node_data.NUM_NODE_RECORDS', large_size):
            start_time = time.time()
            df = generate_node_data()
            end_time = time.time()
            
            execution_time = end_time - start_time
            records_per_second = large_size / execution_time
            
            print(f"\n🔥 STRESS TEST RESULTS:")
            print(f"Records: {large_size:,}")
            print(f"Time: {execution_time:.3f} seconds")
            print(f"Throughput: {records_per_second:,.0f} records/second")
            
            # Stress test assertions
            self.assertEqual(len(df), large_size)
            self.assertLess(execution_time, 10.0, "Stress test took too long")
            self.assertGreater(records_per_second, 10000, "Throughput too low under stress")


def run_performance_comparison():
    """Compare performance with different optimization levels"""
    print("\n🏁 PERFORMANCE COMPARISON")
    print("=" * 80)
    
    test_sizes = [1000, 10000, 50000]
    
    for size in test_sizes:
        print(f"\nTesting with {size:,} records:")
        
        # Run multiple iterations for average
        times = []
        for i in range(3):
            with patch('src.generate.mock.nodes.generate_node_data.NUM_NODE_RECORDS', size):
                start = time.time()
                df = generate_node_data()
                end = time.time()
                times.append(end - start)
        
        avg_time = sum(times) / len(times)
        avg_throughput = size / avg_time
        
        print(f"  Average time: {avg_time:.3f}s")
        print(f"  Average throughput: {avg_throughput:,.0f} records/sec")
        print(f"  Min time: {min(times):.3f}s")
        print(f"  Max time: {max(times):.3f}s")


if __name__ == '__main__':
    # Run unit tests
    print("🧪 RUNNING COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Run performance comparison
    run_performance_comparison()
    
    # Print summary
    print("\n" + "=" * 80)
    if result.wasSuccessful():
        print("✅ ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED!")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
    
    print(f"Tests run: {result.testsRun}")
    print("=" * 80)