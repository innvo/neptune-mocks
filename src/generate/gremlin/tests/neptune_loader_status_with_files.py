#!/usr/bin/env python3

import requests
import json
import ssl
import argparse
import sys
import time
from urllib3.exceptions import InsecureRequestWarning
from typing import Optional, Dict, Any

# Suppress SSL warnings for localhost connections
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

class NeptuneLoaderStatusWithFiles:
    """Enhanced Neptune Loader Status Monitor with file information and rows per file"""
    
    def __init__(self, host: str = "localhost", port: int = 8182, 
                 timeout: int = 30, verify_ssl: bool = False, 
                 retry_attempts: int = 3, retry_delay: int = 5):
        """
        Initialize the Neptune Loader Status monitor
        
        Args:
            host: Neptune host address
            port: Neptune port number
            timeout: Request timeout in seconds
            verify_ssl: Whether to verify SSL certificates
            retry_attempts: Number of retry attempts for failed requests
            retry_delay: Delay between retry attempts in seconds
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        self.base_url = f"https://{host}:{port}"
        
        # Validate configuration
        self._validate_config()
    
    def _validate_config(self):
        """Validate configuration parameters"""
        if not self.host:
            raise ValueError("Host cannot be empty")
        
        if not (1 <= self.port <= 65535):
            raise ValueError("Port must be between 1 and 65535")
        
        if self.timeout <= 0:
            raise ValueError("Timeout must be positive")
        
        if self.retry_attempts < 0:
            raise ValueError("Retry attempts cannot be negative")
        
        if self.retry_delay < 0:
            raise ValueError("Retry delay cannot be negative")
    
    def _make_request(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """
        Make HTTP request with retry logic
        
        Args:
            endpoint: API endpoint path
            
        Returns:
            JSON response or None if request failed
        """
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(self.retry_attempts + 1):
            try:
                response = requests.get(
                    url, 
                    verify=self.verify_ssl, 
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.RequestException as e:
                if attempt < self.retry_attempts:
                    print(f"Attempt {attempt + 1} failed: {e}")
                    print(f"Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                else:
                    print(f"All {self.retry_attempts + 1} attempts failed: {e}")
                    return None
        
        return None
    
    def get_loader_jobs(self) -> Optional[Dict[str, Any]]:
        """Get all loader jobs from Neptune"""
        return self._make_request("/loader")
    
    def get_loader_status(self, load_id: str) -> Optional[Dict[str, Any]]:
        """Get status for a specific loader job"""
        if not load_id:
            print("Error: Load ID cannot be empty")
            return None
        
        return self._make_request(f"/loader/{load_id}")
    
    def extract_file_info(self, status_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract file information from Neptune loader status response
        
        Args:
            status_data: Complete status response from Neptune
            
        Returns:
            Dictionary containing file information
        """
        file_info = {
            'source': 'Unknown',
            'filename': 'Unknown',
            'format': 'Unknown',
            'total_rows': 0,
            'processed_rows': 0,
            'failed_rows': 0,
            'duplicate_rows': 0,
            'parsing_errors': 0,
            'datatype_errors': 0,
            'insert_errors': 0
        }
        
        try:
            payload = status_data.get('payload', {})
            overall_status = payload.get('overallStatus', {})
            
            # Extract source file information
            full_uri = overall_status.get('fullUri', '')
            if full_uri:
                file_info['source'] = full_uri
                # Extract filename from S3 URI
                if full_uri.startswith('s3://'):
                    parts = full_uri.split('/')
                    if len(parts) > 3:
                        file_info['filename'] = '/'.join(parts[3:])  # Remove s3://bucket/ prefix
                    else:
                        file_info['filename'] = full_uri
                else:
                    file_info['filename'] = full_uri
            
            # Extract format information
            format_info = payload.get('format', 'Unknown')
            file_info['format'] = format_info
            
            # Extract row counts and statistics
            file_info['total_rows'] = overall_status.get('totalRecords', 0)
            file_info['processed_rows'] = overall_status.get('totalRecords', 0) - overall_status.get('totalRecordsFailedOrIgnored', 0)
            file_info['failed_rows'] = overall_status.get('totalRecordsFailedOrIgnored', 0)
            file_info['duplicate_rows'] = overall_status.get('totalDuplicates', 0)
            file_info['parsing_errors'] = overall_status.get('parsingErrors', 0)
            file_info['datatype_errors'] = overall_status.get('datatypeMismatchErrors', 0)
            file_info['insert_errors'] = overall_status.get('insertErrors', 0)
            
        except Exception as e:
            print(f"Error extracting file info: {e}")
        
        return file_info
    
    def validate_load_id(self, load_id: str) -> bool:
        """
        Validate load ID format
        
        Args:
            load_id: Load ID to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not load_id:
            return False
        
        # Basic validation - load IDs are typically UUID-like
        if len(load_id) < 10 or len(load_id) > 100:
            return False
        
        # Check for common invalid characters
        invalid_chars = ['<', '>', '"', "'", '&', '|', ';', '`']
        if any(char in load_id for char in invalid_chars):
            return False
        
        return True
    
    def print_loader_statuses(self, show_details: bool = True, 
                            filter_status: Optional[str] = None,
                            max_jobs: Optional[int] = None,
                            show_file_info: bool = True) -> None:
        """
        Print all loader jobs and their statuses with file information
        
        Args:
            show_details: Whether to show detailed JSON output
            filter_status: Filter jobs by status (e.g., 'LOAD_COMPLETED', 'LOAD_IN_PROGRESS')
            max_jobs: Maximum number of jobs to display
            show_file_info: Whether to show file information and row counts
        """
        print(f"Getting Neptune loader jobs and statuses from {self.base_url}...")
        print("=" * 100)
        
        # Get all loader jobs
        jobs_data = self.get_loader_jobs()
        
        if not jobs_data:
            print("Failed to get loader jobs")
            return
        
        payload = jobs_data.get('payload', {})
        load_ids = payload.get('loadIds', [])
        
        if not load_ids:
            print("No active loader jobs found.")
            return
        
        # Apply filters
        if filter_status:
            print(f"Filtering jobs by status: {filter_status}")
            filtered_load_ids = []
            for load_id in load_ids:
                status_data = self.get_loader_status(load_id)
                if status_data:
                    load_payload = status_data.get('payload', {})
                    overall_status = load_payload.get('overallStatus', {})
                    status = overall_status.get('status', 'UNKNOWN')
                    if status == filter_status:
                        filtered_load_ids.append(load_id)
            load_ids = filtered_load_ids
        
        if max_jobs:
            load_ids = load_ids[:max_jobs]
            print(f"Showing first {max_jobs} jobs")
        
        if not load_ids:
            print("No jobs match the specified criteria.")
            return
        
        print(f"Found {len(load_ids)} loader job(s):")
        print("=" * 100)
        
        # Enhanced table header with file information
        if show_file_info:
            print(f"{'Load ID':<36} {'Status':<15} {'File':<30} {'Rows':<8} {'Processed':<10} {'Failed':<8} {'Duration':<12}")
            print("-" * 100)
        else:
            print(f"{'Load ID':<36} {'Status':<20} {'Records':<10} {'Failed':<10} {'Duration':<12}")
            print("-" * 80)
        
        for load_id in load_ids:
            if not self.validate_load_id(load_id):
                if show_file_info:
                    print(f"{load_id:<36} {'INVALID_ID':<15} {'N/A':<30} {'N/A':<8} {'N/A':<10} {'N/A':<8} {'N/A':<12}")
                else:
                    print(f"{load_id:<36} {'INVALID_ID':<20} {'N/A':<10} {'N/A':<10} {'N/A':<12}")
                continue
            
            status_data = self.get_loader_status(load_id)
            
            if not status_data:
                if show_file_info:
                    print(f"{load_id:<36} {'ERROR':<15} {'N/A':<30} {'N/A':<8} {'N/A':<10} {'N/A':<8} {'N/A':<12}")
                else:
                    print(f"{load_id:<36} {'ERROR':<20} {'N/A':<10} {'N/A':<10} {'N/A':<12}")
                continue
            
            load_payload = status_data.get('payload', {})
            overall_status = load_payload.get('overallStatus', {})
            
            status = overall_status.get('status', 'UNKNOWN')
            total_records = overall_status.get('totalRecords', 0)
            failed_records = overall_status.get('totalRecordsFailedOrIgnored', 0)
            processed_records = total_records - failed_records
            
            # Calculate duration if available
            start_time = overall_status.get('startTime', 0)
            end_time = overall_status.get('endTime', 0)
            duration = "N/A"
            if start_time and end_time:
                duration_seconds = (end_time - start_time) / 1000  # Convert from milliseconds
                duration = f"{duration_seconds:.1f}s"
            elif start_time:
                duration = "Running"
            
            # Extract file information
            file_info = self.extract_file_info(status_data)
            
            if show_file_info:
                # Truncate filename if too long
                filename = file_info['filename']
                if len(filename) > 28:
                    filename = filename[:25] + "..."
                
                print(f"{load_id:<36} {status:<15} {filename:<30} {total_records:<8} {processed_records:<10} {failed_records:<8} {duration:<12}")
            else:
                print(f"{load_id:<36} {status:<20} {total_records:<10} {failed_records:<10} {duration:<12}")
        
        print("-" * (100 if show_file_info else 80))
        
        # Print detailed status for each job if requested
        if show_details:
            print("\nDetailed Status Information:")
            print("=" * 100)
            
            for i, load_id in enumerate(load_ids, 1):
                print(f"\n{i}. Load ID: {load_id}")
                print("-" * 50)
                
                if not self.validate_load_id(load_id):
                    print("Invalid Load ID format")
                    continue
                
                status_data = self.get_loader_status(load_id)
                if status_data:
                    # Extract and display file information
                    file_info = self.extract_file_info(status_data)
                    
                    print("File Information:")
                    print(f"  Source: {file_info['source']}")
                    print(f"  Filename: {file_info['filename']}")
                    print(f"  Format: {file_info['format']}")
                    print(f"  Total Rows: {file_info['total_rows']:,}")
                    print(f"  Processed Rows: {file_info['processed_rows']:,}")
                    print(f"  Failed Rows: {file_info['failed_rows']:,}")
                    print(f"  Duplicate Rows: {file_info['duplicate_rows']:,}")
                    print(f"  Parsing Errors: {file_info['parsing_errors']:,}")
                    print(f"  Datatype Errors: {file_info['datatype_errors']:,}")
                    print(f"  Insert Errors: {file_info['insert_errors']:,}")
                    
                    print("\nComplete Response:")
                    print(json.dumps(status_data, indent=2))
                else:
                    print("Failed to get status")
                print()

def main():
    """Main function with command-line argument parsing"""
    parser = argparse.ArgumentParser(
        description="Enhanced Neptune Loader Status Monitor with File Information",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Basic usage with file info
  %(prog)s --no-file-info                     # Hide file information
  %(prog)s --host neptune-cluster.amazonaws.com --port 8182
  %(prog)s --filter-status LOAD_COMPLETED --max-jobs 10
  %(prog)s --load-id abc123-def456-ghi789    # Check specific job only
        """
    )
    
    # Connection parameters
    parser.add_argument("--host", default="localhost",
                       help="Neptune host address (default: localhost)")
    parser.add_argument("--port", type=int, default=8182,
                       help="Neptune port number (default: 8182)")
    parser.add_argument("--timeout", type=int, default=30,
                       help="Request timeout in seconds (default: 30)")
    parser.add_argument("--verify-ssl", action="store_true",
                       help="Verify SSL certificates (default: False)")
    
    # Retry parameters
    parser.add_argument("--retry-attempts", type=int, default=3,
                       help="Number of retry attempts (default: 3)")
    parser.add_argument("--retry-delay", type=int, default=5,
                       help="Delay between retries in seconds (default: 5)")
    
    # Output parameters
    parser.add_argument("--no-details", action="store_true",
                       help="Skip detailed JSON output")
    parser.add_argument("--no-file-info", action="store_true",
                       help="Hide file information and row counts")
    parser.add_argument("--filter-status",
                       help="Filter jobs by status (e.g., LOAD_COMPLETED)")
    parser.add_argument("--max-jobs", type=int,
                       help="Maximum number of jobs to display")
    
    # Specific job check
    parser.add_argument("--load-id",
                       help="Check status of specific load ID only")
    
    # Validation parameters
    parser.add_argument("--validate-only", action="store_true",
                       help="Only validate configuration and connection")
    
    args = parser.parse_args()
    
    try:
        # Initialize monitor
        monitor = NeptuneLoaderStatusWithFiles(
            host=args.host,
            port=args.port,
            timeout=args.timeout,
            verify_ssl=args.verify_ssl,
            retry_attempts=args.retry_attempts,
            retry_delay=args.retry_delay
        )
        
        # Validate configuration
        print(f"Configuration validated:")
        print(f"  Host: {monitor.host}")
        print(f"  Port: {monitor.port}")
        print(f"  Timeout: {monitor.timeout}s")
        print(f"  SSL Verification: {monitor.verify_ssl}")
        print(f"  Retry Attempts: {monitor.retry_attempts}")
        print(f"  Retry Delay: {monitor.retry_delay}s")
        print()
        
        if args.validate_only:
            print("Validation mode - testing connection...")
            test_response = monitor.get_loader_jobs()
            if test_response:
                print("✓ Connection successful")
                sys.exit(0)
            else:
                print("✗ Connection failed")
                sys.exit(1)
        
        # Check specific load ID if provided
        if args.load_id:
            if not monitor.validate_load_id(args.load_id):
                print(f"Error: Invalid load ID format: {args.load_id}")
                sys.exit(1)
            
            print(f"Checking status for load ID: {args.load_id}")
            status_data = monitor.get_loader_status(args.load_id)
            
            if status_data:
                # Extract and display file information
                file_info = monitor.extract_file_info(status_data)
                
                print("\nFile Information:")
                print(f"  Source: {file_info['source']}")
                print(f"  Filename: {file_info['filename']}")
                print(f"  Format: {file_info['format']}")
                print(f"  Total Rows: {file_info['total_rows']:,}")
                print(f"  Processed Rows: {file_info['processed_rows']:,}")
                print(f"  Failed Rows: {file_info['failed_rows']:,}")
                print(f"  Duplicate Rows: {file_info['duplicate_rows']:,}")
                print(f"  Parsing Errors: {file_info['parsing_errors']:,}")
                print(f"  Datatype Errors: {file_info['datatype_errors']:,}")
                print(f"  Insert Errors: {file_info['insert_errors']:,}")
                
                print("\nComplete Response:")
                print(json.dumps(status_data, indent=2))
            else:
                print(f"Failed to get status for {args.load_id}")
                sys.exit(1)
        else:
            # Print all loader statuses
            monitor.print_loader_statuses(
                show_details=not args.no_details,
                filter_status=args.filter_status,
                max_jobs=args.max_jobs,
                show_file_info=not args.no_file_info
            )
    
    except ValueError as e:
        print(f"Configuration error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 