#!/usr/bin/env python3
"""
Neptune Bulk Loader Performance Comparison (GZ Version)

This script shows the performance differences between default and high-performance configurations
for the GZ-enabled Neptune bulk loader.
"""

from src.generate.gremlin.bulk_load_nodes_edges_gz import ConcurrentLoadConfig
from colorama import init, Fore, Style

# Initialize colorama for colored output
init()

def print_config_comparison():
    """Print a comparison between default and high-performance configurations."""
    print(f"{Fore.BLUE}{'=' * 80}{Style.RESET_ALL}")
    print(f"{Fore.BLUE}{'Neptune Bulk Loader Performance Comparison (GZ Version)'.center(80)}{Style.RESET_ALL}")
    print(f"{Fore.BLUE}{'=' * 80}{Style.RESET_ALL}\n")
    
    # Create configurations
    default_config = ConcurrentLoadConfig()
    perf_config = ConcurrentLoadConfig.high_performance()
    ultra_config = ConcurrentLoadConfig.ultra_performance()
    
    print(f"{Fore.CYAN}Configuration Comparison:{Style.RESET_ALL}\n")
    
    # Create comparison table
    headers = ["Setting", "Default", "High Performance", "Ultra Performance", "Impact"]
    rows = [
        ["Queue Wait Time", "5s", "2s", "1s", "🚀 5x faster"],
        ["Max Retry Attempts", "2", "1", "1", "🚀 Faster retries"],
        ["Backoff Multiplier", "1.5x", "1.2x", "1.1x", "🚀 Quicker recovery"],
        ["Initial Backoff", "15s", "5s", "2s", "🚀 7.5x faster"],
        ["Max Backoff", "120s", "30s", "10s", "🚀 12x faster"],
        ["Health Check Interval", "15s", "10s", "5s", "🚀 3x faster monitoring"],
        ["Timeout", "3600s", "7200s", "10800s", "🚀 Handle larger files"],
        ["Connect Timeout", "30s", "15s", "10s", "🚀 3x faster connections"],
        ["Parallelism", "OVERSUBSCRIBE", "OVERSUBSCRIBE", "OVERSUBSCRIBE", "🚀 Maximum throughput"],
        ["Fail on Error", "False", "False", "False", "🚀 Continue on errors"],
        ["Queue Request", "False", "False", "False", "🚀 Immediate submission"]
    ]
    
    # Print table
    print(f"{'Setting':<25} {'Default':<15} {'High Performance':<18} {'Ultra Performance':<18} {'Impact':<20}")
    print("-" * 100)
    
    for row in rows:
        setting, default, perf, ultra, impact = row
        print(f"{setting:<25} {default:<15} {perf:<18} {ultra:<18} {impact:<20}")
    
    print(f"\n{Fore.YELLOW}Performance Impact Summary:{Style.RESET_ALL}")
    print("• Faster queue processing: 5x → 2x → 1x wait times")
    print("• Quicker retry recovery: Reduced backoff times and attempts")
    print("• Faster monitoring: More frequent health checks")
    print("• Longer timeouts: Handle very large files without failures")
    print("• Faster connections: Reduced connection timeouts")
    print("• OVERSUBSCRIBE parallelism: Maximum Neptune throughput")
    print("• No queuing: Immediate job submission")
    print("• Error tolerance: Continue on errors instead of stopping")
    
    print(f"\n{Fore.GREEN}How to Enable Performance Modes:{Style.RESET_ALL}")
    print("High Performance (optimized for speed):")
    print("  export NEPTUNE_PERFORMANCE_MODE=true")
    print("  python src/generate/gremlin/bulk_load_nodes_edges-gz.py")
    print()
    print("Ultra Performance (maximum speed, use with caution):")
    print("  export NEPTUNE_ULTRA_MODE=true")
    print("  python src/generate/gremlin/bulk_load_nodes_edges-gz.py")
    
    print(f"\n{Fore.CYAN}GZ File Support:{Style.RESET_ALL}")
    print("• Automatically detects and processes .gz compressed files")
    print("• Uses 'csv' format for both .csv and .gz files")
    print("• Neptune automatically detects compression from file extension")
    print("• Significant storage savings with compressed files")
    print("• Faster S3 transfers with compressed data")
    
    print(f"\n{Fore.RED}⚠️  Important Notes:{Style.RESET_ALL}")
    print("• High-performance mode: Optimized for Neptune clusters with limit=1")
    print("• Ultra-performance mode: Requires Neptune cluster with concurrent load limit > 5")
    print("• May overwhelm smaller Neptune clusters")
    print("• Monitor cluster performance and adjust if needed")
    print("• Use default mode for production clusters with strict limits")
    print("• GZ files provide ~70-80% compression ratio for CSV data")

if __name__ == "__main__":
    print_config_comparison() 