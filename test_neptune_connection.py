#!/usr/bin/env python3
"""
Simple Neptune Connection Test

This script tests basic connectivity to Neptune and attempts a simple load operation.
"""

import os
import subprocess
import json
import requests
from colorama import init, Fore, Style

# Initialize colorama for colored output
init()

def test_neptune_status():
    """Test if Neptune cluster is responding."""
    endpoint = os.getenv('NEPTUNE_ENDPOINT', 'https://localhost:8182')
    
    print(f"{Fore.CYAN}Testing Neptune cluster status...{Style.RESET_ALL}")
    print(f"Endpoint: {endpoint}")
    
    try:
        # Test status endpoint
        status_url = f"{endpoint}/status"
        response = requests.get(status_url, timeout=10, verify=False)
        
        if response.status_code == 200:
            print(f"{Fore.GREEN}✓ Neptune cluster is responding{Style.RESET_ALL}")
            print(f"Status: {response.text[:200]}...")
            return True
        else:
            print(f"{Fore.RED}✗ Neptune returned status code: {response.status_code}{Style.RESET_ALL}")
            return False
            
    except Exception as e:
        print(f"{Fore.RED}✗ Connection failed: {e}{Style.RESET_ALL}")
        return False

def test_simple_load():
    """Test a simple load operation with minimal payload."""
    endpoint = os.getenv('NEPTUNE_ENDPOINT', 'https://localhost:8182')
    iam_role_arn = os.getenv('NEPTUNE_IAM_ROLE_ARN', '')
    s3_bucket = os.getenv('S3_BUCKET', 'deam-neptune')
    
    if not iam_role_arn:
        print(f"{Fore.RED}Error: NEPTUNE_IAM_ROLE_ARN not set{Style.RESET_ALL}")
        return False
    
    print(f"\n{Fore.CYAN}Testing simple load operation...{Style.RESET_ALL}")
    
    # Create a minimal test payload
    test_payload = {
        "source": f"s3://{s3_bucket}/test-data/test-file.csv",
        "format": "csv",
        "iamRoleArn": iam_role_arn,
        "region": "us-east-1",
        "failOnError": "FALSE",
        "parallelism": "OVERSUBSCRIBE",
        "updateSingleCardinalityProperties": "FALSE",
        "queueRequest": "FALSE"
    }
    
    print(f"Test payload: {json.dumps(test_payload, indent=2)}")
    
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
    
    try:
        print("Submitting test load request...")
        result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=30)
        
        print(f"Return code: {result.returncode}")
        print(f"Stdout: {result.stdout}")
        print(f"Stderr: {result.stderr}")
        
        if result.returncode == 0:
            try:
                response = json.loads(result.stdout)
                print(f"{Fore.GREEN}✓ Load request submitted successfully{Style.RESET_ALL}")
                print(f"Response: {json.dumps(response, indent=2)}")
                return True
            except json.JSONDecodeError:
                print(f"{Fore.YELLOW}⚠ Response is not JSON: {result.stdout}{Style.RESET_ALL}")
                return True
        else:
            print(f"{Fore.RED}✗ Load request failed{Style.RESET_ALL}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"{Fore.RED}✗ Request timed out{Style.RESET_ALL}")
        return False
    except Exception as e:
        print(f"{Fore.RED}✗ Error: {e}{Style.RESET_ALL}")
        return False

def check_s3_bucket():
    """Check if S3 bucket is accessible."""
    s3_bucket = os.getenv('S3_BUCKET', 'deam-neptune')
    
    print(f"\n{Fore.CYAN}Checking S3 bucket access...{Style.RESET_ALL}")
    print(f"S3 Bucket: {s3_bucket}")
    
    try:
        # Use AWS CLI to list bucket contents
        cmd = ['aws', 's3', 'ls', f's3://{s3_bucket}/', '--recursive', '--summarize']
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print(f"{Fore.GREEN}✓ S3 bucket is accessible{Style.RESET_ALL}")
            print("Files in bucket:")
            lines = result.stdout.strip().split('\n')
            for line in lines[:10]:  # Show first 10 files
                if line.strip():
                    print(f"  {line}")
            if len(lines) > 10:
                print(f"  ... and {len(lines) - 10} more files")
            return True
        else:
            print(f"{Fore.RED}✗ S3 bucket access failed{Style.RESET_ALL}")
            print(f"Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"{Fore.RED}✗ S3 check failed: {e}{Style.RESET_ALL}")
        return False

def main():
    """Main function."""
    print(f"{Fore.BLUE}{'=' * 60}{Style.RESET_ALL}")
    print(f"{Fore.BLUE}{'Neptune Connection Test'.center(60)}{Style.RESET_ALL}")
    print(f"{Fore.BLUE}{'=' * 60}{Style.RESET_ALL}\n")
    
    # Test Neptune status
    neptune_ok = test_neptune_status()
    
    # Check S3 bucket
    s3_ok = check_s3_bucket()
    
    # Test simple load
    load_ok = test_simple_load()
    
    # Summary
    print(f"\n{Fore.BLUE}{'Test Summary'}{Style.RESET_ALL}")
    print(f"Neptune Status: {'✓' if neptune_ok else '✗'}")
    print(f"S3 Access: {'✓' if s3_ok else '✗'}")
    print(f"Load Test: {'✓' if load_ok else '✗'}")
    
    if neptune_ok and s3_ok and load_ok:
        print(f"\n{Fore.GREEN}All tests passed! Your Neptune setup is working correctly.{Style.RESET_ALL}")
        print("You can now run the concurrent limit test:")
        print("python test_concurrent_limit.py")
    else:
        print(f"\n{Fore.RED}Some tests failed. Please check the issues above.{Style.RESET_ALL}")

if __name__ == "__main__":
    main() 