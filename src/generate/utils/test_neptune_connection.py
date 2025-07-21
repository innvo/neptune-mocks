#!/usr/bin/env python3
"""
Test script to verify Neptune connectivity before running bulk loader.
This script helps diagnose connection issues with Neptune clusters.
"""

import os
import sys
import requests
import urllib3
import warnings
from urllib3.exceptions import InsecureRequestWarning
from colorama import init, Fore, Style

# Suppress SSL warnings for localhost development
urllib3.disable_warnings(InsecureRequestWarning)
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

# Initialize colorama
init()

def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{Fore.BLUE}{'=' * 80}{Style.RESET_ALL}")
    print(f"{Fore.BLUE}{text.center(80)}{Style.RESET_ALL}")
    print(f"{Fore.BLUE}{'=' * 80}{Style.RESET_ALL}\n")

def test_neptune_connection(endpoint: str, timeout: int = 30):
    """Test connection to Neptune endpoint."""
    print(f"Testing connection to: {endpoint}")
    print(f"Timeout: {timeout} seconds")
    print("-" * 60)
    
    # Configure session
    session = requests.Session()
    if 'localhost' in endpoint or '127.0.0.1' in endpoint:
        session.verify = False
        print(f"{Fore.YELLOW}SSL verification disabled for localhost{Style.RESET_ALL}")
    
    # Test endpoints
    endpoints_to_test = [
        ('/status', 'Status endpoint'),
        ('/loader', 'Loader endpoint (GET)'),
        ('/gremlin', 'Gremlin endpoint')
    ]
    
    for path, description in endpoints_to_test:
        url = f"{endpoint}{path}"
        print(f"\n{Fore.CYAN}Testing {description}:{Style.RESET_ALL}")
        print(f"URL: {url}")
        
        try:
            response = session.get(url, timeout=timeout)
            print(f"{Fore.GREEN}✓ Status: {response.status_code}{Style.RESET_ALL}")
            
            if response.status_code == 200:
                print(f"{Fore.GREEN}✓ Connection successful{Style.RESET_ALL}")
            elif response.status_code == 405:
                print(f"{Fore.YELLOW}⚠ Method not allowed (expected for some endpoints){Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}⚠ Unexpected status code{Style.RESET_ALL}")
                
        except requests.exceptions.ConnectTimeout:
            print(f"{Fore.RED}✗ Connection timeout{Style.RESET_ALL}")
            print(f"   The endpoint is not reachable within {timeout} seconds")
            print(f"   Check network connectivity and firewall settings")
            
        except requests.exceptions.Timeout:
            print(f"{Fore.RED}✗ Request timeout{Style.RESET_ALL}")
            print(f"   The server took too long to respond")
            
        except requests.exceptions.ConnectionError as e:
            print(f"{Fore.RED}✗ Connection error{Style.RESET_ALL}")
            print(f"   Error: {e}")
            print(f"   Check if the Neptune cluster is running")
            
        except Exception as e:
            print(f"{Fore.RED}✗ Unexpected error{Style.RESET_ALL}")
            print(f"   Error: {e}")

def main():
    """Main function."""
    print_header("Neptune Connection Test")
    
    # Get endpoint from environment or use default
    endpoint = os.getenv('NEPTUNE_ENDPOINT', 'https://localhost:8182')
    timeout = int(os.getenv('NEPTUNE_CONNECT_TIMEOUT', '30'))
    
    print(f"{Fore.CYAN}Configuration:{Style.RESET_ALL}")
    print(f"Endpoint: {endpoint}")
    print(f"Timeout: {timeout}s")
    print(f"Environment variables:")
    print(f"  NEPTUNE_ENDPOINT: {os.getenv('NEPTUNE_ENDPOINT', 'Not set (using default)')}")
    print(f"  NEPTUNE_CONNECT_TIMEOUT: {os.getenv('NEPTUNE_CONNECT_TIMEOUT', 'Not set (using default)')}")
    
    # Test connection
    test_neptune_connection(endpoint, timeout)
    
    print_header("Test Complete")
    print(f"{Fore.YELLOW}If all tests show connection errors, check:{Style.RESET_ALL}")
    print("1. Neptune cluster is running and accessible")
    print("2. Network connectivity (ping, telnet, etc.)")
    print("3. Security groups and VPC settings")
    print("4. Endpoint URL is correct")
    print("5. Firewall rules allow connections to port 8182")

if __name__ == "__main__":
    main() 