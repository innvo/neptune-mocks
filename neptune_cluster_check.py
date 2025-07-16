#!/usr/bin/env python3
"""
Neptune Cluster Performance Mode Checker

This script helps determine the optimal performance mode for your Neptune cluster
by testing the concurrent load limits and providing recommendations.
"""

import os
import subprocess
import json
import time
from colorama import init, Fore, Style

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
        "parallelism": "MEDIUM",
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
    max_test = 10  # Test up to 10 concurrent loads
    
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
        
        for process in processes:
            try:
                stdout, stderr = process.communicate(timeout=5)
                if process.returncode == 0:
                    try:
                        response = json.loads(stdout)
                        if 'code' in response and response['code'] == 'BadRequestException':
                            if 'Max concurrent load limit breached' in response.get('detailedMessage', ''):
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
        
        print(f"    Results: {success_count} success, {limit_breached_count} limit breached")
        
        if limit_breached_count > 0:
            concurrent_limit = i - 1
            break
        else:
            concurrent_limit = i
    
    return concurrent_limit

def get_recommendation(concurrent_limit: int) -> str:
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

def main():
    """Main function to check Neptune cluster and provide recommendations."""
    print(f"{Fore.BLUE}{'=' * 80}{Style.RESET_ALL}")
    print(f"{Fore.BLUE}{'Neptune Cluster Performance Mode Checker'.center(80)}{Style.RESET_ALL}")
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
    print(f"  Endpoint: {endpoint}")
    print(f"  Region: {region}")
    print(f"  S3 Bucket: {s3_bucket}")
    print(f"  IAM Role: {iam_role_arn[:50]}...")
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
        
        print(f"\n{Fore.CYAN}Recommended Command:{Style.RESET_ALL}")
        if recommended_mode == "performance":
            print("export NEPTUNE_PERFORMANCE_MODE=true")
            print("python src/generate/gremlin/bulk_load_nodes_edges.py")
        elif recommended_mode == "ultra":
            print("export NEPTUNE_ULTRA_MODE=true")
            print("python src/generate/gremlin/bulk_load_nodes_edges.py")
        else:
            print("python src/generate/gremlin/bulk_load_nodes_edges.py")
        
        print(f"\n{Fore.BLUE}Performance Modes Summary:{Style.RESET_ALL}")
        print("• Default: Safe, conservative settings")
        print("• Performance: Optimized sequential for limit=1 clusters")
        print("• Ultra: Maximum concurrent for high-limit clusters")
        
    except Exception as e:
        print(f"\n{Fore.RED}Error during testing: {e}{Style.RESET_ALL}")
        print("This might indicate:")
        print("• Network connectivity issues")
        print("• Invalid endpoint or credentials")
        print("• Neptune cluster not running")
        print("\nTry running with default mode first:")

if __name__ == "__main__":
    main() 