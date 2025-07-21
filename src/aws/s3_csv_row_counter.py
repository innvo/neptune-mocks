#!/usr/bin/env python3

import boto3
import csv
import tempfile
import os
import argparse
import sys
import time
from typing import Dict, List, Optional, Tuple
from botocore.exceptions import ClientError, NoCredentialsError

class S3CSVRowCounter:
    """Count rows in CSV files stored in S3 bucket"""
    
    def __init__(self, bucket_name: str = "deam-neptune", 
                 aws_region: str = None, aws_profile: str = None,
                 max_files: int = None, timeout: int = 30):
        """
        Initialize the S3 CSV row counter
        
        Args:
            bucket_name: S3 bucket name
            aws_region: AWS region for S3 access
            aws_profile: AWS profile to use
            max_files: Maximum number of files to process (None for all)
            timeout: Request timeout in seconds
        """
        self.bucket_name = bucket_name
        self.aws_region = aws_region
        self.aws_profile = aws_profile
        self.max_files = max_files
        self.timeout = timeout
        
        # Initialize S3 client
        self._init_s3_client()
    
    def _init_s3_client(self):
        """Initialize S3 client with configuration"""
        try:
            session_kwargs = {}
            if self.aws_profile:
                session_kwargs['profile_name'] = self.aws_profile
            
            if self.aws_region:
                session_kwargs['region_name'] = self.aws_region
            
            if session_kwargs:
                session = boto3.Session(**session_kwargs)
                self.s3_client = session.client('s3', config=boto3.session.Config(
                    read_timeout=self.timeout,
                    connect_timeout=self.timeout
                ))
            else:
                self.s3_client = boto3.client('s3', config=boto3.session.Config(
                    read_timeout=self.timeout,
                    connect_timeout=self.timeout
                ))
            
            # Test connection
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            print(f"✓ Successfully connected to S3 bucket: {self.bucket_name}")
            
        except NoCredentialsError:
            print("Error: No AWS credentials found. Please configure your AWS credentials.")
            sys.exit(1)
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchBucket':
                print(f"Error: S3 bucket '{self.bucket_name}' not found.")
            elif error_code == 'AccessDenied':
                print(f"Error: Access denied to S3 bucket '{self.bucket_name}'.")
            else:
                print(f"Error accessing S3 bucket '{self.bucket_name}': {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Unexpected error initializing S3 client: {e}")
            sys.exit(1)
    
    def list_csv_files(self) -> List[str]:
        """
        List all CSV files in the S3 bucket
        
        Returns:
            List of CSV file keys
        """
        csv_files = []
        
        try:
            print(f"Scanning S3 bucket '{self.bucket_name}' for CSV files...")
            
            paginator = self.s3_client.get_paginator('list_objects_v2')
            page_iterator = paginator.paginate(Bucket=self.bucket_name)
            
            for page in page_iterator:
                if 'Contents' in page:
                    for obj in page['Contents']:
                        key = obj['Key']
                        # Check if file is a CSV (case insensitive)
                        if key.lower().endswith('.csv'):
                            csv_files.append(key)
            
            print(f"Found {len(csv_files)} CSV file(s)")
            return csv_files
            
        except ClientError as e:
            print(f"Error listing CSV files: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error listing CSV files: {e}")
            return []
    
    def count_csv_rows(self, file_key: str) -> Optional[int]:
        """
        Count rows in a CSV file stored in S3
        
        Args:
            file_key: S3 object key for the CSV file
            
        Returns:
            Number of rows (excluding header) if successful, None otherwise
        """
        try:
            # Download file to temporary location
            with tempfile.NamedTemporaryFile(mode='w+b', delete=False) as temp_file:
                temp_file_path = temp_file.name
            
            try:
                # Download the file
                self.s3_client.download_file(self.bucket_name, file_key, temp_file_path)
                
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
                    
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchKey':
                print(f"Error: File not found: {file_key}")
            elif error_code == 'AccessDenied':
                print(f"Error: Access denied to file: {file_key}")
            else:
                print(f"Error accessing file {file_key}: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error counting rows in {file_key}: {e}")
            return None
    
    def get_file_size(self, file_key: str) -> Optional[int]:
        """
        Get file size in bytes
        
        Args:
            file_key: S3 object key
            
        Returns:
            File size in bytes if successful, None otherwise
        """
        try:
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=file_key)
            return response['ContentLength']
        except Exception as e:
            print(f"Error getting file size for {file_key}: {e}")
            return None
    
    def format_file_size(self, size_bytes: int) -> str:
        """
        Format file size in human-readable format
        
        Args:
            size_bytes: Size in bytes
            
        Returns:
            Formatted size string
        """
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        import math
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_names[i]}"
    
    def process_files(self, csv_files: List[str]) -> List[Dict]:
        """
        Process CSV files and count their rows
        
        Args:
            csv_files: List of CSV file keys to process
            
        Returns:
            List of dictionaries with file information and row counts
        """
        results = []
        total_files = len(csv_files)
        
        if self.max_files:
            csv_files = csv_files[:self.max_files]
            print(f"Processing first {len(csv_files)} files (limited by --max-files)")
        
        print(f"\nProcessing {len(csv_files)} CSV file(s)...")
        print("=" * 80)
        
        for i, file_key in enumerate(csv_files, 1):
            print(f"[{i}/{len(csv_files)}] Processing: {file_key}")
            
            # Get file size
            file_size = self.get_file_size(file_key)
            size_str = self.format_file_size(file_size) if file_size else "N/A"
            
            # Count rows
            start_time = time.time()
            row_count = self.count_csv_rows(file_key)
            processing_time = time.time() - start_time
            
            # Store results
            result = {
                'file_key': file_key,
                'file_size': file_size,
                'file_size_str': size_str,
                'row_count': row_count,
                'processing_time': processing_time,
                'status': 'SUCCESS' if row_count is not None else 'ERROR'
            }
            
            results.append(result)
            
            # Print progress
            if row_count is not None:
                print(f"  ✓ Rows: {row_count:,}, Size: {size_str}, Time: {processing_time:.2f}s")
            else:
                print(f"  ✗ Failed to count rows, Time: {processing_time:.2f}s")
        
        return results
    
    def print_summary(self, results: List[Dict]):
        """
        Print summary of results
        
        Args:
            results: List of processing results
        """
        print("\n" + "=" * 80)
        print("SUMMARY REPORT")
        print("=" * 80)
        
        # Calculate statistics
        successful_files = [r for r in results if r['status'] == 'SUCCESS']
        failed_files = [r for r in results if r['status'] == 'ERROR']
        
        total_rows = sum(r['row_count'] for r in successful_files if r['row_count'] is not None)
        total_size = sum(r['file_size'] for r in successful_files if r['file_size'] is not None)
        total_time = sum(r['processing_time'] for r in results)
        
        # Print file statistics
        print(f"Total Files Processed: {len(results)}")
        print(f"Successful: {len(successful_files)}")
        print(f"Failed: {len(failed_files)}")
        print(f"Success Rate: {(len(successful_files)/len(results)*100):.1f}%" if results else "N/A")
        
        print(f"\nTotal Rows: {total_rows:,}")
        print(f"Total Size: {self.format_file_size(total_size)}")
        print(f"Total Processing Time: {total_time:.2f}s")
        
        if successful_files:
            avg_rows = total_rows / len(successful_files)
            avg_size = total_size / len(successful_files)
            avg_time = total_time / len(results)
            
            print(f"Average Rows per File: {avg_rows:,.0f}")
            print(f"Average File Size: {self.format_file_size(avg_size)}")
            print(f"Average Processing Time: {avg_time:.2f}s")
        
        # Print detailed results table
        print(f"\n{'File Key':<50} {'Rows':<10} {'Size':<10} {'Time(s)':<8} {'Status':<8}")
        print("-" * 90)
        
        for result in results:
            file_key = result['file_key']
            if len(file_key) > 47:
                file_key = file_key[:44] + "..."
            
            row_count = f"{result['row_count']:,}" if result['row_count'] is not None else "N/A"
            size_str = result['file_size_str']
            time_str = f"{result['processing_time']:.2f}"
            status = result['status']
            
            print(f"{file_key:<50} {row_count:<10} {size_str:<10} {time_str:<8} {status:<8}")
        
        print("-" * 90)
        
        # Print failed files if any
        if failed_files:
            print(f"\nFailed Files ({len(failed_files)}):")
            for result in failed_files:
                print(f"  - {result['file_key']}")
    
    def run(self):
        """Main execution method"""
        # List CSV files
        csv_files = self.list_csv_files()
        
        if not csv_files:
            print("No CSV files found in the bucket.")
            return
        
        # Process files
        results = self.process_files(csv_files)
        
        # Print summary
        self.print_summary(results)

def main():
    """Main function with command-line argument parsing"""
    parser = argparse.ArgumentParser(
        description="Count rows in CSV files stored in S3 bucket",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Count rows in all CSV files in deam-neptune bucket
  %(prog)s --bucket my-bucket                 # Use different bucket
  %(prog)s --max-files 10                     # Process only first 10 files
  %(prog)s --aws-region us-east-1            # Use specific AWS region
  %(prog)s --aws-profile myprofile           # Use specific AWS profile
  %(prog)s --timeout 60                      # Set timeout to 60 seconds
        """
    )
    
    parser.add_argument("--bucket", default="deam-neptune",
                       help="S3 bucket name (default: deam-neptune)")
    parser.add_argument("--aws-region", default=None,
                       help="AWS region for S3 access")
    parser.add_argument("--aws-profile", default=None,
                       help="AWS profile to use")
    parser.add_argument("--max-files", type=int, default=None,
                       help="Maximum number of files to process")
    parser.add_argument("--timeout", type=int, default=30,
                       help="Request timeout in seconds (default: 30)")
    
    args = parser.parse_args()
    
    try:
        # Initialize counter
        counter = S3CSVRowCounter(
            bucket_name=args.bucket,
            aws_region=args.aws_region,
            aws_profile=args.aws_profile,
            max_files=args.max_files,
            timeout=args.timeout
        )
        
        # Run the counter
        counter.run()
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 