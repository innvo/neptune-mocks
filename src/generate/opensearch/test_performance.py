#!/usr/bin/env python3
"""
Quick Performance Test for OpenSearch CSV Loader

This script demonstrates the performance improvements by running a quick test
with different configurations and showing the results.

Usage:
    python test_performance.py
"""

import time
import logging
import sys
import os

# Add the parent directory to the path to import the loader
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from load_csv_opensearch import HighPerformanceGremlinCSVLoader, OPENSEARCH_ENDPOINT, S3_BUCKET, OPENSEARCH_ROLE_ARN

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


def test_performance_configurations():
    """Test different performance configurations."""
    logger.info("🚀 Testing OpenSearch CSV Loader Performance")
    logger.info("=" * 60)
    
    # Test configurations
    configs = [
        ("Single Worker", 1, 50000),
        ("4 Workers", 4, 50000),
        ("8 Workers", 8, 50000),
        ("16 Workers", 16, 50000),
    ]
    
    results = []
    
    for name, workers, batch_size in configs:
        logger.info(f"\n🧪 Testing {name} configuration...")
        logger.info(f"  - Workers: {workers}")
        logger.info(f"  - Batch size: {batch_size:,}")
        
        start_time = time.time()
        
        try:
            # Initialize loader
            loader = HighPerformanceGremlinCSVLoader(
                OPENSEARCH_ENDPOINT,
                'us-east-1',
                OPENSEARCH_ROLE_ARN,
                workers=workers,
                batch_size=batch_size
            )
            
            # Test with a small prefix (should be fast)
            loader.load_all_csv_files_parallel(S3_BUCKET, prefix="test/", root_only=True)
            
            end_time = time.time()
            elapsed_time = end_time - start_time
            
            # Calculate metrics
            docs_per_second = loader.stats['documents_indexed'] / elapsed_time if elapsed_time > 0 else 0
            
            result = {
                'name': name,
                'workers': workers,
                'batch_size': batch_size,
                'elapsed_time': elapsed_time,
                'documents_indexed': loader.stats['documents_indexed'],
                'docs_per_second': docs_per_second,
                'success': True
            }
            
            logger.info(f"✅ {name} completed in {elapsed_time:.2f}s")
            logger.info(f"   - Documents: {loader.stats['documents_indexed']:,}")
            logger.info(f"   - Rate: {docs_per_second:.0f} docs/sec")
            
            results.append(result)
            
        except Exception as e:
            logger.error(f"❌ {name} failed: {e}")
            result = {
                'name': name,
                'workers': workers,
                'batch_size': batch_size,
                'elapsed_time': 0,
                'documents_indexed': 0,
                'docs_per_second': 0,
                'success': False,
                'error': str(e)
            }
            results.append(result)
    
    # Print summary
    print_summary(results)


def print_summary(results):
    """Print a summary of the test results."""
    logger.info("\n" + "=" * 60)
    logger.info("📊 PERFORMANCE TEST SUMMARY")
    logger.info("=" * 60)
    
    # Filter successful results
    successful = [r for r in results if r['success']]
    
    if not successful:
        logger.error("❌ No successful test runs!")
        return
    
    # Print results table
    logger.info(f"{'Configuration':<20} {'Workers':<8} {'Time (s)':<10} {'Docs/sec':<12} {'Improvement':<12}")
    logger.info("-" * 70)
    
    baseline = None
    for result in successful:
        if baseline is None:
            baseline = result['docs_per_second']
            improvement = "1.0x"
        else:
            improvement = f"{result['docs_per_second'] / baseline:.1f}x"
        
        logger.info(f"{result['name']:<20} {result['workers']:<8} "
                   f"{result['elapsed_time']:<10.2f} {result['docs_per_second']:<12.0f} "
                   f"{improvement:<12}")
    
    logger.info("-" * 70)
    
    # Find best configuration
    best = max(successful, key=lambda x: x['docs_per_second'])
    worst = min(successful, key=lambda x: x['docs_per_second'])
    
    improvement_factor = best['docs_per_second'] / worst['docs_per_second']
    
    logger.info(f"\n🎯 Best Configuration: {best['name']}")
    logger.info(f"   - Throughput: {best['docs_per_second']:.0f} docs/sec")
    logger.info(f"   - Workers: {best['workers']}")
    logger.info(f"   - Time: {best['elapsed_time']:.2f}s")
    
    logger.info(f"\n📈 Performance Improvement: {improvement_factor:.1f}x")
    
    if improvement_factor >= 10:
        logger.info("✅ Target achieved: 10x performance improvement!")
    else:
        logger.info(f"⚠️  Target not yet achieved. Try with larger datasets or more workers.")
    
    # Recommendations
    logger.info(f"\n💡 Recommendations:")
    logger.info(f"   - Use {best['workers']} workers for optimal performance")
    logger.info(f"   - Batch size of {best['batch_size']:,} works well")
    logger.info(f"   - For production: use --performance-mode high or ultra")


def test_performance_modes():
    """Test the built-in performance modes."""
    logger.info("\n🚀 Testing Performance Modes")
    logger.info("=" * 50)
    
    modes = [
        ("Normal Mode", "normal"),
        ("High Performance", "high"),
        ("Ultra Performance", "ultra"),
    ]
    
    results = []
    
    for name, mode in modes:
        logger.info(f"\n🧪 Testing {name}...")
        
        start_time = time.time()
        
        try:
            # Initialize loader with performance mode
            if mode == 'normal':
                workers, batch_size = 4, 50000
            elif mode == 'high':
                workers, batch_size = 8, 75000
            else:  # ultra
                workers, batch_size = 16, 100000
            
            loader = HighPerformanceGremlinCSVLoader(
                OPENSEARCH_ENDPOINT,
                'us-east-1',
                OPENSEARCH_ROLE_ARN,
                workers=workers,
                batch_size=batch_size
            )
            
            # Test with small dataset
            loader.load_all_csv_files_parallel(S3_BUCKET, prefix="test/", root_only=True)
            
            end_time = time.time()
            elapsed_time = end_time - start_time
            docs_per_second = loader.stats['documents_indexed'] / elapsed_time if elapsed_time > 0 else 0
            
            result = {
                'name': name,
                'mode': mode,
                'workers': workers,
                'batch_size': batch_size,
                'elapsed_time': elapsed_time,
                'docs_per_second': docs_per_second,
                'success': True
            }
            
            logger.info(f"✅ {name} completed in {elapsed_time:.2f}s")
            logger.info(f"   - Rate: {docs_per_second:.0f} docs/sec")
            
            results.append(result)
            
        except Exception as e:
            logger.error(f"❌ {name} failed: {e}")
            results.append({
                'name': name,
                'mode': mode,
                'success': False,
                'error': str(e)
            })
    
    # Print mode comparison
    logger.info("\n📊 Performance Mode Comparison")
    logger.info("-" * 60)
    logger.info(f"{'Mode':<20} {'Workers':<8} {'Batch Size':<12} {'Docs/sec':<12}")
    logger.info("-" * 60)
    
    for result in results:
        if result['success']:
            logger.info(f"{result['name']:<20} {result['workers']:<8} "
                       f"{result['batch_size']:<12,} {result['docs_per_second']:<12.0f}")
    
    logger.info("-" * 60)


def main():
    """Main entry point."""
    logger.info("🚀 OpenSearch CSV Loader Performance Test")
    logger.info("This test demonstrates the performance improvements")
    logger.info("=" * 60)
    
    try:
        # Test basic configurations
        test_performance_configurations()
        
        # Test performance modes
        test_performance_modes()
        
        logger.info("\n✅ Performance testing completed!")
        logger.info("\n💡 To run the full benchmark:")
        logger.info("   python performance_benchmark.py --benchmark-all")
        
    except Exception as e:
        logger.error(f"Performance testing failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 