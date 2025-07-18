#!/usr/bin/env python3

import requests
import json
import ssl
import argparse
import sys
import time
import csv
import os
import tempfile
from urllib3.exceptions import InsecureRequestWarning
from typing import Optional, Dict, Any

# Try to import boto3 for S3 support
try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    S3_AVAILABLE = True
except ImportError:
    S3_AVAILABLE = False
    print("Warning: boto3 not available. S3 file access will be limited.")

# Suppress SSL warnings for localhost connections
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

class NeptuneLoaderStatusWithFiles:
    """Enhanced Neptune Loader Status Monitor with file information and totalTimeSpent tracking"""
    
    def __init__(self, host: str = "localhost", port: int = 8182, 
                 timeout: int = 30, verify_ssl: bool = False, 
                 retry_attempts: int = 3, retry_delay: int = 5,
                 csv_base_dir: str = ".", aws_region: str = None, aws_profile: str = None):
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
        self.csv_base_dir = csv_base_dir
        self.aws_region = aws_region
        self.aws_profile = aws_profile
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
    
    def get_total_time_spent(self, load_id: str) -> Optional[float]:
        """
        Get the totalTimeSpent in seconds for a specific load job
        
        Args:
            load_id: Load ID to check
            
        Returns:
            TotalTimeSpent in seconds if available, None otherwise
        """
        if not self.validate_load_id(load_id):
            return None
        
        status_data = self.get_loader_status(load_id)
        if not status_data:
            return None
        
        load_payload = status_data.get('payload', {})
        overall_status = load_payload.get('overallStatus', {})
        
        total_time_spent = overall_status.get('totalTimeSpent', 0)
        
        if total_time_spent > 0:
            return total_time_spent / 1000  # Convert from milliseconds to seconds
        
        return None
    
    def print_summary_table(self, load_ids: list) -> None:
        """
        Print a summary table with job statistics
        
        Args:
            load_ids: List of load IDs to summarize
        """
        print(f"\n{'='*80}")
        print("SUMMARY TABLE")
        print(f"{'='*80}")
        
        # Collect statistics
        status_counts = {}
        total_records = 0
        total_failed_records = 0
        total_duplicates = 0
        total_errors = 0
        completed_jobs = 0
        running_jobs = 0
        failed_jobs = 0
        total_time_spent = 0
        completed_time_spent = 0
        
        for load_id in load_ids:
            if not self.validate_load_id(load_id):
                continue
                
            status_data = self.get_loader_status(load_id)
            if not status_data:
                continue
                
            load_payload = status_data.get('payload', {})
            overall_status = load_payload.get('overallStatus', {})
            
            status = overall_status.get('status', 'UNKNOWN')
            status_counts[status] = status_counts.get(status, 0) + 1
            
            # Count records and errors
            records = overall_status.get('totalRecords', 0)
            failed_records = overall_status.get('totalRecordsFailedOrIgnored', 0)
            duplicates = overall_status.get('totalDuplicates', 0)
            parsing_errors = overall_status.get('parsingErrors', 0)
            datatype_errors = overall_status.get('datatypeMismatchErrors', 0)
            insert_errors = overall_status.get('insertErrors', 0)
            
            total_records += records
            total_failed_records += failed_records
            total_duplicates += duplicates
            total_errors += parsing_errors + datatype_errors + insert_errors
            
            # Count job statuses and track time
            time_spent = overall_status.get('totalTimeSpent', 0)
            if time_spent > 0:
                time_spent_seconds = time_spent / 1000  # Convert to seconds
                total_time_spent += time_spent_seconds
                
                if status == 'LOAD_COMPLETED':
                    completed_jobs += 1
                    completed_time_spent += time_spent_seconds
                elif status == 'LOAD_IN_PROGRESS':
                    running_jobs += 1
                elif status in ['LOAD_FAILED', 'LOAD_CANCELLED']:
                    failed_jobs += 1
            else:
                if status == 'LOAD_COMPLETED':
                    completed_jobs += 1
                elif status == 'LOAD_IN_PROGRESS':
                    running_jobs += 1
                elif status in ['LOAD_FAILED', 'LOAD_CANCELLED']:
                    failed_jobs += 1
        
        # Print job status summary
        print(f"{'Job Status Summary':<30} {'Count':<10} {'Percentage':<12}")
        print("-" * 52)
        total_jobs = len(load_ids)
        
        for status, count in sorted(status_counts.items()):
            percentage = (count / total_jobs * 100) if total_jobs > 0 else 0
            print(f"{status:<30} {count:<10} {percentage:>8.1f}%")
        
        print("-" * 52)
        print(f"{'TOTAL':<30} {total_jobs:<10} {'100.0%':<12}")
        
        # Print record statistics
        print(f"\n{'Record Statistics':<30} {'Count':<15} {'Percentage':<12}")
        print("-" * 57)
        
        if total_records > 0:
            success_rate = ((total_records - total_failed_records) / total_records * 100)
            error_rate = (total_errors / total_records * 100) if total_records > 0 else 0
            duplicate_rate = (total_duplicates / total_records * 100) if total_records > 0 else 0
            
            print(f"{'Total Records Processed':<30} {total_records:<15,} {'100.0%':<12}")
            print(f"{'Successfully Processed':<30} {total_records - total_failed_records:<15,} {success_rate:>8.1f}%")
            print(f"{'Failed/Ignored Records':<30} {total_failed_records:<15,} {(total_failed_records/total_records*100):>8.1f}%")
            print(f"{'Duplicate Records':<30} {total_duplicates:<15,} {duplicate_rate:>8.1f}%")
            print(f"{'Total Errors':<30} {total_errors:<15,} {error_rate:>8.1f}%")
        else:
            print(f"{'Total Records Processed':<30} {total_records:<15,} {'N/A':<12}")
        
        # Print time statistics
        print(f"\n{'Time Statistics':<30} {'Value':<15}")
        print("-" * 45)
        
        if total_time_spent > 0:
            avg_time = total_time_spent / total_jobs if total_jobs > 0 else 0
            print(f"{'Total Time Spent':<30} {total_time_spent:<15.1f}s")
            print(f"{'Average Time per Job':<30} {avg_time:<15.1f}s")
            
            if completed_jobs > 0 and completed_time_spent > 0:
                avg_completed_time = completed_time_spent / completed_jobs
                print(f"{'Average Time (Completed)':<30} {avg_completed_time:<15.1f}s")
        else:
            print(f"{'Total Time Spent':<30} {'N/A':<15}")
            print(f"{'Average Time per Job':<30} {'N/A':<15}")
        
        # Print job counts
        print(f"\n{'Job Counts':<30} {'Count':<15}")
        print("-" * 45)
        print(f"{'Total Jobs':<30} {total_jobs:<15}")
        print(f"{'Completed Jobs':<30} {completed_jobs:<15}")
        print(f"{'Running Jobs':<30} {running_jobs:<15}")
        print(f"{'Failed Jobs':<30} {failed_jobs:<15}")
        
        print(f"\n{'='*80}")
        
        # Print detailed file row counts
        self.print_file_row_counts(load_ids)
    
    def count_csv_rows(self, file_path: str) -> Optional[int]:
        """
        Count the actual number of rows in a CSV file (local or S3)
        
        Args:
            file_path: Path to the CSV file (local path or S3 URI)
            
        Returns:
            Number of rows (excluding header) if successful, None otherwise
        """
        try:
            if file_path.startswith('s3://'):
                # return self._count_s3_csv_rows(file_path)  # Commented out S3 row counting
                return None  # Return None for S3 files since counting is disabled
            else:
                return self._count_local_csv_rows(file_path)
        except Exception as e:
            print(f"Error counting rows in {file_path}: {e}")
            return None
    
    def _count_local_csv_rows(self, file_path: str) -> Optional[int]:
        """
        Count rows in a local CSV file
        
        Args:
            file_path: Local file path
            
        Returns:
            Number of rows (excluding header) if successful, None otherwise
        """
        try:
            if not os.path.exists(file_path):
                return None
            
            with open(file_path, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                # Skip header row and count data rows
                next(reader, None)  # Skip header
                row_count = sum(1 for row in reader)
                return row_count
        except Exception as e:
            print(f"Error counting rows in local file {file_path}: {e}")
            return None
    
    def _count_s3_csv_rows(self, s3_uri: str) -> Optional[int]:
        """
        Count rows in an S3 CSV file
        
        Args:
            s3_uri: S3 URI (s3://bucket/key)
            
        Returns:
            Number of rows (excluding header) if successful, None otherwise
        """
        if not S3_AVAILABLE:
            print(f"Error: boto3 not available for S3 access to {s3_uri}")
            return None
        
        try:
            # Parse S3 URI
            if not s3_uri.startswith('s3://'):
                print(f"Invalid S3 URI: {s3_uri}")
                return None
            
            # Remove s3:// prefix and split into bucket and key
            path_parts = s3_uri[5:].split('/', 1)
            if len(path_parts) != 2:
                print(f"Invalid S3 URI format: {s3_uri}")
                return None
            
            bucket_name = path_parts[0]
            object_key = path_parts[1]
            
            # Create S3 client with configuration
            session_kwargs = {}
            if self.aws_profile:
                session_kwargs['profile_name'] = self.aws_profile
            
            if self.aws_region:
                session_kwargs['region_name'] = self.aws_region
            
            if session_kwargs:
                session = boto3.Session(**session_kwargs)
                s3_client = session.client('s3')
            else:
                s3_client = boto3.client('s3')
            
            # Download file to temporary location
            with tempfile.NamedTemporaryFile(mode='w+b', delete=False) as temp_file:
                temp_file_path = temp_file.name
            
            try:
                # Download the file
                s3_client.download_file(bucket_name, object_key, temp_file_path)
                
                # Count rows in the downloaded file
                with open(temp_file_path, 'r', encoding='utf-8') as file:
                    reader = csv.reader(file)
                    # Skip header row and count data rows
                    next(reader, None)  # Skip header
                    row_count = sum(1 for row in reader)
                    return row_count
                    
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                except OSError:
                    pass  # Ignore cleanup errors
                    
        except NoCredentialsError:
            print(f"Error: No AWS credentials found for S3 access to {s3_uri}")
            return None
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchBucket':
                print(f"Error: S3 bucket not found: {s3_uri}")
            elif error_code == 'NoSuchKey':
                print(f"Error: S3 object not found: {s3_uri}")
            elif error_code == 'AccessDenied':
                print(f"Error: Access denied to S3 object: {s3_uri}")
            else:
                print(f"Error accessing S3 object {s3_uri}: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error accessing S3 object {s3_uri}: {e}")
            return None
    
    def get_file_path_from_uri(self, full_uri: str) -> Optional[str]:
        """
        Extract local file path from S3 URI or return the URI if it's a local path
        
        Args:
            full_uri: S3 URI or local file path
            
        Returns:
            Local file path if possible, None otherwise
        """
        if full_uri.startswith('s3://'):
            # For S3 URIs, return the URI as-is for direct S3 access
            return full_uri
        else:
            # Try to construct the full path using the base directory
            if os.path.isabs(full_uri):
                return full_uri
            else:
                return os.path.join(self.csv_base_dir, full_uri)
    
    def test_s3_connection(self, s3_uri: str) -> bool:
        """
        Test S3 connectivity by attempting to access a file
        
        Args:
            s3_uri: S3 URI to test
            
        Returns:
            True if connection successful, False otherwise
        """
        if not S3_AVAILABLE:
            print("Error: boto3 not available for S3 access")
            return False
        
        try:
            # Parse S3 URI
            if not s3_uri.startswith('s3://'):
                print(f"Invalid S3 URI: {s3_uri}")
                return False
            
            path_parts = s3_uri[5:].split('/', 1)
            if len(path_parts) != 2:
                print(f"Invalid S3 URI format: {s3_uri}")
                return False
            
            bucket_name = path_parts[0]
            object_key = path_parts[1]
            
            # Create S3 client with configuration
            session_kwargs = {}
            if self.aws_profile:
                session_kwargs['profile_name'] = self.aws_profile
            
            if self.aws_region:
                session_kwargs['region_name'] = self.aws_region
            
            if session_kwargs:
                session = boto3.Session(**session_kwargs)
                s3_client = session.client('s3')
            else:
                s3_client = boto3.client('s3')
            
            # Test by getting object metadata
            s3_client.head_object(Bucket=bucket_name, Key=object_key)
            print(f"✓ S3 connection successful for {s3_uri}")
            return True
            
        except NoCredentialsError:
            print(f"Error: No AWS credentials found for S3 access to {s3_uri}")
            return False
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchBucket':
                print(f"Error: S3 bucket not found: {s3_uri}")
            elif error_code == 'NoSuchKey':
                print(f"Error: S3 object not found: {s3_uri}")
            elif error_code == 'AccessDenied':
                print(f"Error: Access denied to S3 object: {s3_uri}")
            else:
                print(f"Error accessing S3 object {s3_uri}: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error testing S3 connection to {s3_uri}: {e}")
            return False
    
    def print_file_row_counts(self, load_ids: list) -> None:
        """
        Print detailed row counts for each file
        
        Args:
            load_ids: List of load IDs to analyze
        """
        print(f"\n{'='*80}")
        print("FILE ROW COUNTS")
        print(f"{'='*80}")
        
        # Collect file information
        file_data = []
        
        for load_id in load_ids:
            if not self.validate_load_id(load_id):
                continue
                
            status_data = self.get_loader_status(load_id)
            if not status_data:
                continue
                
            load_payload = status_data.get('payload', {})
            overall_status = load_payload.get('overallStatus', {})
            
            # Extract file information
            full_uri = overall_status.get('fullUri', 'Unknown')
            filename = 'Unknown'
            if full_uri.startswith('s3://'):
                parts = full_uri.split('/')
                if len(parts) > 3:
                    filename = '/'.join(parts[3:])  # Remove s3://bucket/ prefix
                else:
                    filename = full_uri
            else:
                filename = full_uri
            
            # Extract row counts from Neptune status
            total_records = overall_status.get('totalRecords', 0)
            failed_records = overall_status.get('totalRecordsFailedOrIgnored', 0)
            successful_records = total_records - failed_records
            duplicates = overall_status.get('totalDuplicates', 0)
            parsing_errors = overall_status.get('parsingErrors', 0)
            datatype_errors = overall_status.get('datatypeMismatchErrors', 0)
            insert_errors = overall_status.get('insertErrors', 0)
            total_errors = parsing_errors + datatype_errors + insert_errors
            
            # Get actual CSV row count
            actual_csv_rows = None
            file_path = self.get_file_path_from_uri(full_uri)
            if file_path:
                actual_csv_rows = self.count_csv_rows(file_path)
            
            status = overall_status.get('status', 'UNKNOWN')
            time_spent = overall_status.get('totalTimeSpent', 0)
            time_spent_seconds = time_spent / 1000 if time_spent > 0 else 0
            
            file_data.append({
                'load_id': load_id,
                'filename': filename,
                'status': status,
                'total_records': total_records,
                'actual_csv_rows': actual_csv_rows,
                'successful_records': successful_records,
                'failed_records': failed_records,
                'duplicates': duplicates,
                'total_errors': total_errors,
                'parsing_errors': parsing_errors,
                'datatype_errors': datatype_errors,
                'insert_errors': insert_errors,
                'time_spent': time_spent_seconds
            })
        
        if not file_data:
            print("No file data available.")
            return
        
        # Sort by filename for better readability
        file_data.sort(key=lambda x: x['filename'])
        
        # Print detailed file table
        print(f"{'Filename':<35} {'Status':<12} {'CSV':<6} {'Neptune':<8} {'Success':<8} {'Failed':<8} {'Dups':<6} {'Errors':<7} {'Time(s)':<8}")
        print("-" * 110)
        
        for file_info in file_data:
            filename = file_info['filename']
            if len(filename) > 33:
                filename = filename[:30] + "..."
            
            # Format CSV row count
            csv_rows = file_info['actual_csv_rows']
            csv_str = f"{csv_rows:,}" if csv_rows is not None else "N/A"
            
            print(f"{filename:<35} {file_info['status']:<12} {csv_str:<6} {file_info['total_records']:<8,} "
                  f"{file_info['successful_records']:<8,} {file_info['failed_records']:<8,} "
                  f"{file_info['duplicates']:<6,} {file_info['total_errors']:<7,} "
                  f"{file_info['time_spent']:<8.1f}")
        
        print("-" * 110)
        
        # Print file summary statistics
        total_files = len(file_data)
        completed_files = len([f for f in file_data if f['status'] == 'LOAD_COMPLETED'])
        running_files = len([f for f in file_data if f['status'] == 'LOAD_IN_PROGRESS'])
        failed_files = len([f for f in file_data if f['status'] in ['LOAD_FAILED', 'LOAD_CANCELLED']])
        
        total_rows = sum(f['total_records'] for f in file_data)
        total_csv_rows = sum(f['actual_csv_rows'] for f in file_data if f['actual_csv_rows'] is not None)
        total_successful = sum(f['successful_records'] for f in file_data)
        total_failed = sum(f['failed_records'] for f in file_data)
        total_duplicates = sum(f['duplicates'] for f in file_data)
        total_errors = sum(f['total_errors'] for f in file_data)
        
        print(f"\nFile Summary:")
        print(f"  Total Files: {total_files}")
        print(f"  Completed: {completed_files}")
        print(f"  Running: {running_files}")
        print(f"  Failed: {failed_files}")
        print(f"  Total CSV Rows: {total_csv_rows:,}")
        print(f"  Total Neptune Rows: {total_rows:,}")
        print(f"  Successful Rows: {total_successful:,}")
        print(f"  Failed Rows: {total_failed:,}")
        print(f"  Duplicate Rows: {total_duplicates:,}")
        print(f"  Total Errors: {total_errors:,}")
        
        if total_rows > 0:
            success_rate = (total_successful / total_rows) * 100
            failure_rate = (total_failed / total_rows) * 100
            duplicate_rate = (total_duplicates / total_rows) * 100
            error_rate = (total_errors / total_rows) * 100
            
            print(f"  Success Rate: {success_rate:.1f}%")
            print(f"  Failure Rate: {failure_rate:.1f}%")
            print(f"  Duplicate Rate: {duplicate_rate:.1f}%")
            print(f"  Error Rate: {error_rate:.1f}%")
        
        print(f"\n{'='*80}")
    
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
        Print all loader jobs and their statuses with file information and totalTimeSpent
        
        Args:
            show_details: Whether to show detailed JSON output
            filter_status: Filter jobs by status (e.g., 'LOAD_COMPLETED', 'LOAD_IN_PROGRESS')
            max_jobs: Maximum number of jobs to display
            show_file_info: Whether to show file information
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
            print(f"{'Load ID':<36} {'Status':<15} {'File':<30} {'TotalTimeSpent':<15}")
            print("-" * 90)
        else:
            print(f"{'Load ID':<36} {'Status':<20} {'TotalTimeSpent':<15}")
            print("-" * 70)
        
        for load_id in load_ids:
            if not self.validate_load_id(load_id):
                if show_file_info:
                    print(f"{load_id:<36} {'INVALID_ID':<15} {'N/A':<30} {'N/A':<15}")
                else:
                    print(f"{load_id:<36} {'INVALID_ID':<20} {'N/A':<15}")
                continue
            
            status_data = self.get_loader_status(load_id)
            
            if not status_data:
                if show_file_info:
                    print(f"{load_id:<36} {'ERROR':<15} {'N/A':<30} {'N/A':<15}")
                else:
                    print(f"{load_id:<36} {'ERROR':<20} {'N/A':<15}")
                continue
            
            load_payload = status_data.get('payload', {})
            overall_status = load_payload.get('overallStatus', {})
            
            status = overall_status.get('status', 'UNKNOWN')
            
            # Get totalTimeSpent if available
            total_time_spent = overall_status.get('totalTimeSpent', 0)
            if total_time_spent:
                total_time_seconds = total_time_spent / 1000  # Convert from milliseconds
                time_spent_str = f"{total_time_seconds:.1f}s"
            else:
                time_spent_str = "N/A"
            
            # Extract file information
            file_info = self.extract_file_info(status_data)
            
            if show_file_info:
                # Truncate filename if too long
                filename = file_info['filename']
                if len(filename) > 28:
                    filename = filename[:25] + "..."
                
                print(f"{load_id:<36} {status:<15} {filename:<30} {time_spent_str:<15}")
            else:
                print(f"{load_id:<36} {status:<20} {time_spent_str:<15}")
        
        print("-" * (90 if show_file_info else 70))
        
        # Create and display summary table
        self.print_summary_table(load_ids)
        
        # Calculate and display totalTimeSpent summary
        completed_times = []
        running_jobs = 0
        
        for load_id in load_ids:
            if self.validate_load_id(load_id):
                status_data = self.get_loader_status(load_id)
                if status_data:
                    load_payload = status_data.get('payload', {})
                    overall_status = load_payload.get('overallStatus', {})
                    total_time_spent = overall_status.get('totalTimeSpent', 0)
                    end_time = overall_status.get('endTime', 0)
                    
                    if total_time_spent > 0:
                        if end_time:  # Job completed
                            completed_times.append(total_time_spent / 1000)  # Convert to seconds
                        else:  # Job still running
                            running_jobs += 1
        
        if completed_times:
            avg_time = sum(completed_times) / len(completed_times)
            min_time = min(completed_times)
            max_time = max(completed_times)
            print(f"\nTotalTimeSpent Summary (completed jobs):")
            print(f"  Average: {avg_time:.1f} seconds")
            print(f"  Minimum: {min_time:.1f} seconds")
            print(f"  Maximum: {max_time:.1f} seconds")
            print(f"  Total completed: {len(completed_times)} jobs")
        
        if running_jobs > 0:
            print(f"  Currently running: {running_jobs} jobs")
        
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
                    
                    # Display totalTimeSpent
                    total_time_spent = overall_status.get('totalTimeSpent', 0)
                    if total_time_spent:
                        total_time_seconds = total_time_spent / 1000
                        print(f"  TotalTimeSpent: {total_time_seconds:.1f} seconds")
                    else:
                        print(f"  TotalTimeSpent: Unknown")
                    
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
  %(prog)s --load-id abc123-def456-ghi789 --time-spent-only  # Get only totalTimeSpent in seconds
  %(prog)s --summary-only                     # Show only summary table
  %(prog)s --file-counts-only                 # Show only file row counts
  %(prog)s --csv-base-dir /path/to/csv/files  # Specify CSV file directory
  %(prog)s --aws-region us-east-1 --aws-profile myprofile  # Use specific AWS region and profile
  %(prog)s --test-s3 s3://mybucket/data.csv  # Test S3 connectivity
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
                       help="Hide file information")
    parser.add_argument("--filter-status",
                       help="Filter jobs by status (e.g., LOAD_COMPLETED)")
    parser.add_argument("--max-jobs", type=int,
                       help="Maximum number of jobs to display")
    
    # Specific job check
    parser.add_argument("--load-id",
                       help="Check status of specific load ID only")
    parser.add_argument("--time-spent-only", action="store_true",
                       help="Show only totalTimeSpent in seconds for the specified load ID")
    parser.add_argument("--summary-only", action="store_true",
                       help="Show only the summary table")
    parser.add_argument("--file-counts-only", action="store_true",
                       help="Show only the file row counts table")
    parser.add_argument("--csv-base-dir", default=".",
                       help="Base directory for CSV files (default: current directory)")
    
    # AWS/S3 parameters
    parser.add_argument("--aws-region", default=None,
                       help="AWS region for S3 access (default: use AWS_DEFAULT_REGION or boto3 default)")
    parser.add_argument("--aws-profile", default=None,
                       help="AWS profile to use for S3 access (default: use boto3 default)")
    
    # Validation parameters
    parser.add_argument("--validate-only", action="store_true",
                       help="Only validate configuration and connection")
    parser.add_argument("--test-s3", metavar="S3_URI",
                       help="Test S3 connectivity with the specified S3 URI")
    
    args = parser.parse_args()
    
    try:
        # Initialize monitor
        monitor = NeptuneLoaderStatusWithFiles(
            host=args.host,
            port=args.port,
            timeout=args.timeout,
            verify_ssl=args.verify_ssl,
            retry_attempts=args.retry_attempts,
            retry_delay=args.retry_delay,
            csv_base_dir=args.csv_base_dir,
            aws_region=args.aws_region,
            aws_profile=args.aws_profile
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
        
        if args.test_s3:
            print("Testing S3 connectivity...")
            if monitor.test_s3_connection(args.test_s3):
                sys.exit(0)
            else:
                sys.exit(1)
        
        # Check specific load ID if provided
        if args.load_id:
            if not monitor.validate_load_id(args.load_id):
                print(f"Error: Invalid load ID format: {args.load_id}")
                sys.exit(1)
            
            if args.time_spent_only:
                # Show only totalTimeSpent
                time_spent = monitor.get_total_time_spent(args.load_id)
                if time_spent is not None:
                    print(f"{time_spent:.1f}")
                else:
                    print("N/A")
                sys.exit(0)
            
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
                
                # Display totalTimeSpent
                load_payload = status_data.get('payload', {})
                overall_status = load_payload.get('overallStatus', {})
                total_time_spent = overall_status.get('totalTimeSpent', 0)
                if total_time_spent:
                    total_time_seconds = total_time_spent / 1000
                    print(f"  TotalTimeSpent: {total_time_seconds:.1f} seconds")
                else:
                    print(f"  TotalTimeSpent: Unknown")
                
                print("\nComplete Response:")
                print(json.dumps(status_data, indent=2))
            else:
                print(f"Failed to get status for {args.load_id}")
                sys.exit(1)
        else:
            # Print all loader statuses
            if args.summary_only:
                # Show only summary table
                jobs_data = monitor.get_loader_jobs()
                if jobs_data:
                    payload = jobs_data.get('payload', {})
                    load_ids = payload.get('loadIds', [])
                    if load_ids:
                        monitor.print_summary_table(load_ids)
                    else:
                        print("No loader jobs found.")
                else:
                    print("Failed to get loader jobs")
                    sys.exit(1)
            elif args.file_counts_only:
                # Show only file row counts
                jobs_data = monitor.get_loader_jobs()
                if jobs_data:
                    payload = jobs_data.get('payload', {})
                    load_ids = payload.get('loadIds', [])
                    if load_ids:
                        monitor.print_file_row_counts(load_ids)
                    else:
                        print("No loader jobs found.")
                else:
                    print("Failed to get loader jobs")
                    sys.exit(1)
            else:
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