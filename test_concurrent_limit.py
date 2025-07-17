#!/usr/bin/env python3
"""
Neptune Concurrent Load Limit Tester

This script tests your Neptune cluster's concurrent load limit and provides
recommendations for optimal performance settings.
"""

import os
import subprocess
import json
import time
from colorama import init, Fore, Style
from dotenv import load_dotenv
load_dotenv()

# Initialize colorama for colored output
init()

def test_concurrent_load_limit(endpoint: str, iam_role_arn: str, s3_bucket: str, region: str = "us-east-1") -> int:
    """Test the concurrent load limit of the Neptune cluster."""
    print(f"{Fore.CYAN}Testing Neptune cluster concurrent load limit...{Style.RESET_ALL}")
    
    # Simple test payload
    test_payload = {
        "source": f"s3://{s3_bucket}/test-file.csv",
        "format": "csv",
        "iamRoleArn": iam_role_arn,
        "region": region,
        "failOnError": "FALSE",
        "parallelism": "OVERSUBSCRIBE",
        "updateSingleCardinalityProperties": "FALSE",
        "queueRequest": "FALSE"
    }
    
    curl_cmd = [
        'curl', '-X', 'POST',
        f'{endpoint}/loader',
        '-H', 'Content-Type: application/json',
        '--connect-timeout', '30',
        '--max-time', '60',
        '-k',  # Disable SSL verification for localhost
        '-s',  # Silent mode
        '-d', json.dumps(test_payload)
    ]
    
    concurrent_limit = 0
    max_test = 20  # Increased to test up to 20 concurrent loads
    
    for i in range(1, max_test + 1):
        print(f"  Testing {i} concurrent load(s)...")
        
        # Submit multiple requests
        processes = []
        for j in range(i):
            try:
                process = subprocess.Popen(
                    curl_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                processes.append(process)
            except Exception as e:
                print(f"    Error starting process {j}: {e}")
                break
        
        # Wait a moment for responses
        time.sleep(2)
        
        # Check responses
        success_count = 0
        limit_breached_count = 0
        limit_1_count = 0  # Track limit=1 responses
        
        for process in processes:
            try:
                stdout, stderr = process.communicate(timeout=5)
                if process.returncode == 0:
                    try:
                        response = json.loads(stdout)
                        if 'code' in response and response['code'] == 'BadRequestException':
                            detailed_message = response.get('detailedMessage', '')
                            if 'Max concurrent load limit breached' in detailed_message:
                                if 'Limit is 1' in detailed_message:
                                    limit_1_count += 1
                                else:
                                    limit_breached_count += 1
                            else:
                                success_count += 1
                        else:
                            success_count += 1
                    except json.JSONDecodeError:
                        success_count += 1
                else:
                    limit_breached_count += 1
            except subprocess.TimeoutExpired:
                process.kill()
                limit_breached_count += 1
            except Exception as e:
                limit_breached_count += 1
        
        # Terminate any remaining processes
        for process in processes:
            try:
                process.kill()
            except:
                pass
        
        # If we hit the limit=1, we found our concurrent limit
        if limit_1_count > 0:
            concurrent_limit = 1
            print(f"    Concurrent limit detected: 1 (cluster configured for single loads)")
            break
        # If we hit other limits, we found our concurrent limit
        elif limit_breached_count > 0:
            concurrent_limit = i - 1
            print(f"    Concurrent limit reached at {concurrent_limit}")
            break
        else:
            concurrent_limit = i
            print(f"    Successfully submitted {i} concurrent loads")
    
    return concurrent_limit

def get_recommendation(concurrent_limit: int) -> tuple:
    """Get performance mode recommendation based on concurrent limit."""
    if concurrent_limit == 0:
        return "default", "Cluster not responding or no access"
    elif concurrent_limit == 1:
        return "performance", "Use high-performance mode (optimized sequential)"
    elif concurrent_limit <= 3:
        return "performance", "Use high-performance mode (optimized sequential)"
    elif concurrent_limit <= 10:
        return "ultra", "Use ultra-performance mode (concurrent with moderate limits)"
    else:
        return "ultra", "Use ultra-performance mode (maximum concurrent)"

def setup_high_performance_environment():
    """Set up environment variables for high-performance Neptune loading."""
    print(f"\n{Fore.GREEN}Setting up High-Performance Environment for 15 Concurrent Files{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Recommended Environment Variables:{Style.RESET_ALL}")
    
    # Core settings
    print("export NEPTUNE_CONCURRENT_LIMIT=15")
    print("export NEPTUNE_ULTRA_MODE=true")
    print("export NEPTUNE_PARALLELISM=OVERSUBSCRIBE")
    print("export NEPTUNE_FAIL_ON_ERROR=false")
    print("export NEPTUNE_QUEUE_REQUEST=false")
    
    # Performance tuning
    print("export NEPTUNE_QUEUE_WAIT_TIME=1")
    print("export NEPTUNE_MAX_RETRY_ATTEMPTS=1")
    print("export NEPTUNE_BACKOFF_MULTIPLIER=1.1")
    print("export NEPTUNE_INITIAL_BACKOFF=2")
    print("export NEPTUNE_MAX_BACKOFF=10")
    print("export NEPTUNE_HEALTH_CHECK_INTERVAL=5")
    print("export NEPTUNE_TIMEOUT=10800")
    print("export NEPTUNE_CONNECT_TIMEOUT=10")
    
    # Optional debugging
    print("export NEPTUNE_DEBUG=false")
    
    print(f"\n{Fore.YELLOW}High-Performance Configuration Summary:{Style.RESET_ALL}")
    print("• Concurrent Limit: 15 files")
    print("• Mode: Ultra Performance")
    print("• Parallelism: OVERSUBSCRIBE (maximum throughput)")
    print("• Queue Wait Time: 1 second (minimal)")
    print("• Retry Attempts: 1 (fast retries)")
    print("• Timeout: 3 hours (for very large files)")
    print("• Health Check: Every 5 seconds")

def main():
    """Main function."""
    print(f"{Fore.BLUE}{'=' * 80}{Style.RESET_ALL}")
    print(f"{Fore.BLUE}{'Neptune Concurrent Load Limit Tester'.center(80)}{Style.RESET_ALL}")
    print(f"{Fore.BLUE}{'=' * 80}{Style.RESET_ALL}\n")
    
    # Get configuration from environment
    endpoint = os.getenv('NEPTUNE_ENDPOINT', 'https://localhost:8182')
    iam_role_arn = os.getenv('NEPTUNE_IAM_ROLE_ARN', '')
    s3_bucket = os.getenv('S3_BUCKET', 'deam-neptune')
    region = os.getenv('AWS_REGION', 'us-east-1')
    
    if not iam_role_arn:
        print(f"{Fore.RED}Error: NEPTUNE_IAM_ROLE_ARN environment variable is required{Style.RESET_ALL}")
        print("Example: export NEPTUNE_IAM_ROLE_ARN='arn:aws:iam::123456789012:role/NeptuneLoadFromS3'")
        return
    
    print(f"{Fore.CYAN}Configuration:{Style.RESET_ALL}")
    print(f"  Neptune Endpoint: {endpoint}")
    print(f"  AWS Region: {region}")
    print(f"  S3 Bucket: {s3_bucket}")
    print()
    
    try:
        # Test concurrent load limit
        concurrent_limit = test_concurrent_load_limit(endpoint, iam_role_arn, s3_bucket, region)
        
        print(f"\n{Fore.GREEN}Test Results:{Style.RESET_ALL}")
        print(f"  Concurrent Load Limit: {concurrent_limit}")
        
        # Get recommendation
        recommended_mode, reason = get_recommendation(concurrent_limit)
        
        print(f"\n{Fore.YELLOW}Recommendation:{Style.RESET_ALL}")
        print(f"  Mode: {recommended_mode.upper()}")
        print(f"  Reason: {reason}")
        
        # Set up high-performance environment for 15 concurrent files
        setup_high_performance_environment()
        
        print(f"\n{Fore.CYAN}Recommended Command:{Style.RESET_ALL}")
        print("python src/generate/gremlin/bulk_load_nodes_edges.py")
        
        print(f"\n{Fore.BLUE}Performance Modes Summary:{Style.RESET_ALL}")
        print("• Default: Safe, conservative settings")
        print("• Performance: Optimized sequential for limit=1 clusters")
        print("• Ultra: Maximum concurrent for high-limit clusters")
        
        # Also suggest setting the concurrent limit directly
        if concurrent_limit >= 15:
            print(f"\n{Fore.GREEN}Your cluster supports 15+ concurrent loads!{Style.RESET_ALL}")
            print("You can use the high-performance setup above.")
        elif concurrent_limit > 1:
            print(f"\n{Fore.YELLOW}Your cluster supports {concurrent_limit} concurrent loads.{Style.RESET_ALL}")
            print("Consider adjusting NEPTUNE_CONCURRENT_LIMIT to match your cluster's capability.")
            print(f"export NEPTUNE_CONCURRENT_LIMIT={concurrent_limit}")
        else:
            print(f"\n{Fore.RED}Your cluster has limited concurrent load capacity ({concurrent_limit}).{Style.RESET_ALL}")
            print("Consider using performance mode instead of ultra mode.")
        
    except Exception as e:
        print(f"\n{Fore.RED}Error during testing: {e}{Style.RESET_ALL}")
        print("This might indicate:")
        print("• Network connectivity issues")
        print("• Invalid endpoint or credentials")
        print("• Neptune cluster not running")
        print("\nTry running with default mode first:")
        print("python src/generate/gremlin/bulk_load_nodes_edges.py")

if __name__ == "__main__":
    main() 