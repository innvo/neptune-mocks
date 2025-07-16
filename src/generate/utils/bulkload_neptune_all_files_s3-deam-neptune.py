"""
Neptune Bulk Loader with Verbose Logging

This script provides comprehensive logging for Neptune bulk loading operations.
It includes detailed progress tracking, error reporting, and debugging capabilities.

Logging Levels:
- INFO: General progress and status information
- DEBUG: Detailed technical information (when NEPTUNE_DEBUG=true)
- WARNING: Issues that don't prevent operation
- ERROR: Problems that cause failures

Environment Variables for Logging:
- NEPTUNE_DEBUG=true: Enable debug logging with detailed technical information
- NEPTUNE_VERBOSE=true: Enable verbose logging (same as NEPTUNE_DEBUG)

Features:
- Colored console output for better readability
- Detailed progress tracking for file processing
- Comprehensive error reporting with troubleshooting tips
- Network connectivity testing
- AWS credentials validation
- S3 access verification
- CSV file format validation and analysis
- Concurrent job submission with progress tracking
- Retry logic with detailed attempt logging
"""

import boto3
import requests
import logging
from typing import Dict, List
import json
from colorama import init, Fore, Style
from datetime import datetime
import sys
import urllib3
import warnings
from urllib3.exceptions import InsecureRequestWarning
import concurrent.futures
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import time
from dataclasses import dataclass
import traceback
import socket
import ssl

# Suppress SSL warnings for localhost development
urllib3.disable_warnings(InsecureRequestWarning)
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

# Initialize colorama
init()

@dataclass
class NeptuneConfig:
    """Configuration for Neptune bulk loader."""
    endpoint: str = "https://localhost:8182"
    iam_role_arn: str = ""
    region: str = "us-east-1"
    max_workers: int = 10
    parallelism: str = "HIGH"
    fail_on_error: bool = True
    queue_request: bool = True
    timeout: int = 300  # Increased from 60 to 300 seconds
    connect_timeout: int = 30  # New: separate connect timeout
    retry_attempts: int = 3  # New: number of retry attempts
    retry_delay: int = 5  # New: delay between retries in seconds
    debug_mode: bool = False  # New: enable debug mode
    
    @classmethod
    def from_env(cls) -> 'NeptuneConfig':
        """Create configuration from environment variables."""
        return cls(
            endpoint=os.getenv('NEPTUNE_ENDPOINT', cls.endpoint),
            iam_role_arn=os.getenv('NEPTUNE_IAM_ROLE_ARN', cls.iam_role_arn),
            region=os.getenv('AWS_REGION', cls.region),
            max_workers=int(os.getenv('NEPTUNE_MAX_WORKERS', cls.max_workers)),
            parallelism=os.getenv('NEPTUNE_PARALLELISM', cls.parallelism),
            fail_on_error=os.getenv('NEPTUNE_FAIL_ON_ERROR', 'true').lower() == 'true',
            queue_request=os.getenv('NEPTUNE_QUEUE_REQUEST', 'true').lower() == 'true',
            timeout=int(os.getenv('NEPTUNE_TIMEOUT', cls.timeout)),
            connect_timeout=int(os.getenv('NEPTUNE_CONNECT_TIMEOUT', cls.connect_timeout)),
            retry_attempts=int(os.getenv('NEPTUNE_RETRY_ATTEMPTS', cls.retry_attempts)),
            retry_delay=int(os.getenv('NEPTUNE_RETRY_DELAY', cls.retry_delay)),
            debug_mode=os.getenv('NEPTUNE_DEBUG', 'false').lower() == 'true'
        )
    
    def validate(self) -> None:
        """Validate configuration."""
        if not self.iam_role_arn:
            raise ValueError("IAM role ARN is required. Set NEPTUNE_IAM_ROLE_ARN environment variable.")
        if not self.endpoint:
            raise ValueError("Neptune endpoint is required.")
        if self.max_workers < 1:
            raise ValueError("Max workers must be at least 1.")
        if self.timeout < 30:
            raise ValueError("Timeout must be at least 30 seconds.")
        if self.connect_timeout < 10:
            raise ValueError("Connect timeout must be at least 10 seconds.")
        if self.retry_attempts < 0:
            raise ValueError("Retry attempts must be non-negative.")

# Configure logging with colors
class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors"""
    
    def format(self, record):
        if record.levelno == logging.DEBUG:
            record.msg = f"{Fore.CYAN}[DEBUG]{Style.RESET_ALL} {record.msg}"
        elif record.levelno == logging.INFO:
            record.msg = f"{Fore.GREEN}[INFO]{Style.RESET_ALL} {record.msg}"
        elif record.levelno == logging.WARNING:
            record.msg = f"{Fore.YELLOW}[WARN]{Style.RESET_ALL} {record.msg}"
        elif record.levelno == logging.ERROR:
            record.msg = f"{Fore.RED}[ERROR]{Style.RESET_ALL} {record.msg}"
        return super().format(record)

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG if os.getenv('NEPTUNE_DEBUG', 'false').lower() == 'true' else logging.WARNING)

# Create console handler with colored formatter
console_handler = logging.StreamHandler()
console_handler.setFormatter(ColoredFormatter(
    '%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
))
logger.addHandler(console_handler)

def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{Fore.BLUE}{'=' * 80}{Style.RESET_ALL}")
    print(f"{Fore.BLUE}{text.center(80)}{Style.RESET_ALL}")
    print(f"{Fore.BLUE}{'=' * 80}{Style.RESET_ALL}\n")

def print_progress(current: int, total: int, prefix: str = '', suffix: str = ''):
    """Print a progress bar"""
    bar_length = 50
    filled_length = int(round(bar_length * current / float(total)))
    percents = round(100.0 * current / float(total), 1)
    bar = '█' * filled_length + '░' * (bar_length - filled_length)
    sys.stdout.write(f'\r{prefix} |{bar}| {percents}% {suffix}')
    sys.stdout.flush()

def debug_network_connectivity(endpoint: str, timeout: int = 10):
    """Debug network connectivity to the endpoint."""
    logger.info(f"Debugging network connectivity to: {endpoint}")
    logger.debug(f"Timeout setting: {timeout} seconds")
    
    try:
        # Parse endpoint
        logger.debug("Parsing endpoint URL...")
        if endpoint.startswith('https://'):
            host = endpoint[8:]
            port = 443
            use_ssl = True
            logger.debug("Detected HTTPS endpoint")
        elif endpoint.startswith('http://'):
            host = endpoint[7:]
            port = 80
            use_ssl = False
            logger.debug("Detected HTTP endpoint")
        else:
            host = endpoint
            port = 443
            use_ssl = True
            logger.debug("No protocol specified, assuming HTTPS")
            
        # Remove path if present
        if '/' in host:
            host = host.split('/')[0]
            logger.debug(f"Removed path from host: {host}")
            
        # Remove port if present
        if ':' in host:
            host, port_str = host.split(':')
            port = int(port_str)
            logger.debug(f"Extracted port from host: {port}")
            
        logger.info(f"Parsed endpoint - Host: {host}, Port: {port}, SSL: {use_ssl}")
        
        # Test basic socket connection
        logger.info(f"Testing socket connection to {host}:{port}")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        logger.debug(f"Socket timeout set to {timeout} seconds")
        
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            logger.info(f"✓ Socket connection successful to {host}:{port}")
        else:
            logger.error(f"✗ Socket connection failed to {host}:{port} (error code: {result})")
            return False
            
        # Test SSL if needed
        if use_ssl:
            logger.info(f"Testing SSL connection to {host}:{port}")
            try:
                context = ssl.create_default_context()
                if 'localhost' in host or '127.0.0.1' in host:
                    context.check_hostname = False
                    context.verify_mode = ssl.CERT_NONE
                    logger.info("SSL verification disabled for localhost")
                    
                with socket.create_connection((host, port), timeout=timeout) as sock:
                    with context.wrap_socket(sock, server_hostname=host) as ssock:
                        logger.info(f"✓ SSL connection successful to {host}:{port}")
                        logger.debug(f"SSL version: {ssock.version()}")
                        logger.debug(f"Cipher: {ssock.cipher()[0]}")
            except Exception as e:
                logger.error(f"✗ SSL connection failed to {host}:{port}: {e}")
                return False
                
        logger.info("✓ Network connectivity test completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Network connectivity test failed: {e}")
        logger.debug(f"Network test error details: {traceback.format_exc()}")
        return False

def debug_aws_credentials():
    """Debug AWS credentials and configuration."""
    logger.info("Debugging AWS credentials and configuration")
    
    try:
        # Test boto3 session
        logger.debug("Creating boto3 session...")
        session = boto3.Session()
        logger.info(f"AWS region: {session.region_name}")
        
        # Get credentials
        logger.debug("Retrieving AWS credentials...")
        credentials = session.get_credentials()
        if credentials:
            logger.info(f"✓ AWS credentials found")
            logger.debug(f"Access key: {credentials.access_key[:10]}...")
            logger.debug(f"Secret key: {'*' * 20}")
            if credentials.token:
                logger.debug(f"Session token: {credentials.token[:10]}...")
                logger.info("✓ Using temporary credentials (session token)")
            else:
                logger.info("✓ Using permanent credentials")
        else:
            logger.error("✗ No AWS credentials found")
            logger.error("Please check:")
            logger.error("1. AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables")
            logger.error("2. AWS credentials file (~/.aws/credentials)")
            logger.error("3. IAM role if running on EC2")
            return False
            
        # Test STS to get account info
        logger.debug("Testing STS to get account information...")
        sts_client = boto3.client('sts')
        try:
            identity = sts_client.get_caller_identity()
            logger.info(f"✓ AWS account: {identity['Account']}")
            logger.info(f"User ARN: {identity['Arn']}")
            logger.debug(f"User ID: {identity['UserId']}")
        except Exception as e:
            logger.error(f"✗ Failed to get AWS identity: {e}")
            logger.debug(f"STS error details: {traceback.format_exc()}")
            return False
            
        logger.info("✓ AWS credentials debug completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"AWS credentials debug failed: {e}")
        logger.debug(f"AWS credentials error details: {traceback.format_exc()}")
        return False

def debug_s3_access(bucket_name: str):
    """Debug S3 bucket access."""
    logger.info(f"Debugging S3 access to bucket: {bucket_name}")
    
    try:
        logger.debug("Creating S3 client...")
        s3_client = boto3.client('s3')
        
        # Test bucket existence
        logger.info(f"Testing bucket existence: {bucket_name}")
        try:
            s3_client.head_bucket(Bucket=bucket_name)
            logger.info(f"✓ S3 bucket {bucket_name} exists and accessible")
        except Exception as e:
            logger.error(f"✗ S3 bucket {bucket_name} access failed: {e}")
            logger.debug(f"Bucket access error details: {traceback.format_exc()}")
            return False
            
        # Test listing objects
        logger.info(f"Testing object listing for bucket: {bucket_name}")
        try:
            response = s3_client.list_objects_v2(Bucket=bucket_name, MaxKeys=1)
            key_count = response.get('KeyCount', 0)
            logger.info(f"✓ S3 listing successful, found {key_count} objects")
            if key_count > 0:
                logger.debug(f"Sample object: {response['Contents'][0]['Key']}")
        except Exception as e:
            logger.error(f"✗ S3 listing failed: {e}")
            logger.debug(f"S3 listing error details: {traceback.format_exc()}")
            return False
            
        logger.info("✓ S3 access debug completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"S3 access debug failed: {e}")
        logger.debug(f"S3 access error details: {traceback.format_exc()}")
        return False

def validate_csv_format(file_info: Dict) -> Dict:
    """Validate CSV file format for Neptune bulk loader compatibility.
    
    Args:
        file_info: Dictionary containing file information
        
    Returns:
        Dictionary with validation results
    """
    logger.debug(f"Validating CSV format for file: {file_info['key']}")
    
    try:
        import csv
        import io
        
        # Download first few lines of the CSV file to validate format
        s3_client = boto3.client('s3')
        bucket_name = file_info['source'].split('/')[2]
        file_key = file_info['key']
        
        # Get first 10KB of the file to check headers and sample data
        response = s3_client.get_object(
            Bucket=bucket_name,
            Key=file_key,
            Range='bytes=0-10240'  # First 10KB
        )
        
        content = response['Body'].read().decode('utf-8')
        lines = content.split('\n')
        
        validation_result = {
            'file_key': file_key,
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'headers': [],
            'sample_rows': []
        }
        
        # Check if we have at least a header row
        if len(lines) < 1:
            validation_result['is_valid'] = False
            validation_result['errors'].append("File is empty")
            return validation_result
            
        # Parse header row
        try:
            header_reader = csv.reader([lines[0]])
            headers = next(header_reader)
            validation_result['headers'] = headers
            logger.debug(f"CSV headers: {headers}")
        except Exception as e:
            validation_result['is_valid'] = False
            validation_result['errors'].append(f"Failed to parse header row: {e}")
            return validation_result
            
        # Check for required columns
        required_columns = ['~id', '~label']
        missing_columns = [col for col in required_columns if col not in headers]
        if missing_columns:
            validation_result['is_valid'] = False
            validation_result['errors'].append(f"Missing required columns: {missing_columns}")
            
        # Check for edge-specific columns if this is an edge file
        if '_edge' in file_key.lower() or any(pattern in file_key.lower() for pattern in ['-', '_']):
            edge_required = ['~from', '~to']
            missing_edge_columns = [col for col in edge_required if col not in headers]
            if missing_edge_columns:
                validation_result['warnings'].append(f"Edge file missing edge columns: {missing_edge_columns}")
                
        # Check for data type suffixes in column names
        columns_with_suffixes = [col for col in headers if ':' in col]
        columns_without_suffixes = [col for col in headers if ':' not in col and col not in ['~id', '~label', '~from', '~to']]
        
        if columns_without_suffixes:
            validation_result['warnings'].append(f"Columns without type suffixes: {columns_without_suffixes}")
            
        # Parse sample data rows
        sample_rows = []
        for i, line in enumerate(lines[1:6]):  # Check first 5 data rows
            if line.strip():
                try:
                    row_reader = csv.reader([line])
                    row = next(row_reader)
                    sample_rows.append(row)
                    
                    # Check if row has same number of columns as header
                    if len(row) != len(headers):
                        validation_result['warnings'].append(f"Row {i+2} has {len(row)} columns, expected {len(headers)}")
                        
                except Exception as e:
                    validation_result['warnings'].append(f"Failed to parse row {i+2}: {e}")
                    
        validation_result['sample_rows'] = sample_rows
        
        # Check for common issues
        if len(headers) > 50:
            validation_result['warnings'].append(f"Large number of columns ({len(headers)}), may impact performance")
            
        # Check for empty or problematic values in sample data
        for i, row in enumerate(sample_rows):
            for j, value in enumerate(row):
                if j < len(headers):
                    if value == '':
                        validation_result['warnings'].append(f"Empty value in row {i+2}, column {headers[j]}")
                    elif len(value) > 1000:
                        validation_result['warnings'].append(f"Very long value in row {i+2}, column {headers[j]} ({len(value)} chars)")
                        
        logger.debug(f"CSV validation result: {validation_result}")
        return validation_result
        
    except Exception as e:
        logger.error(f"CSV validation failed for {file_info['key']}: {e}")
        return {
            'file_key': file_info['key'],
            'is_valid': False,
            'errors': [f"Validation failed: {str(e)}"],
            'warnings': [],
            'headers': [],
            'sample_rows': []
        }

def analyze_csv_file(file_info: Dict) -> Dict:
    """Analyze a specific CSV file to identify potential issues.
    
    Args:
        file_info: Dictionary containing file information
        
    Returns:
        Dictionary with analysis results
    """
    logger.debug(f"Analyzing CSV file: {file_info['key']}")
    
    try:
        import csv
        
        # Download the file for analysis
        s3_client = boto3.client('s3')
        bucket_name = file_info['source'].split('/')[2]
        file_key = file_info['key']
        
        # Get the entire file for analysis
        response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
        content = response['Body'].read().decode('utf-8')
        lines = content.split('\n')
        
        analysis_result = {
            'file_key': file_key,
            'total_lines': len(lines),
            'total_size_bytes': len(content.encode('utf-8')),
            'headers': [],
            'header_count': 0,
            'data_rows': 0,
            'empty_rows': 0,
            'column_analysis': {},
            'potential_issues': [],
            'sample_data': []
        }
        
        # Parse header
        if lines:
            try:
                header_reader = csv.reader([lines[0]])
                headers = next(header_reader)
                analysis_result['headers'] = headers
                analysis_result['header_count'] = len(headers)
                logger.debug(f"Headers: {headers}")
            except Exception as e:
                analysis_result['potential_issues'].append(f"Header parsing error: {e}")
                return analysis_result
                
        # Analyze data rows
        for i, line in enumerate(lines[1:], start=2):
            if not line.strip():
                analysis_result['empty_rows'] += 1
                continue
                
            try:
                row_reader = csv.reader([line])
                row = next(row_reader)
                analysis_result['data_rows'] += 1
                
                # Check column count consistency
                if len(row) != len(headers):
                    analysis_result['potential_issues'].append(
                        f"Row {i}: Expected {len(headers)} columns, got {len(row)}"
                    )
                    
                # Analyze first few rows in detail
                if analysis_result['data_rows'] <= 3:
                    analysis_result['sample_data'].append({
                        'row_number': i,
                        'data': row,
                        'column_count': len(row)
                    })
                    
                # Analyze column values
                for j, value in enumerate(row):
                    if j < len(headers):
                        col_name = headers[j]
                        if col_name not in analysis_result['column_analysis']:
                            analysis_result['column_analysis'][col_name] = {
                                'empty_count': 0,
                                'max_length': 0,
                                'sample_values': [],
                                'has_special_chars': False
                            }
                            
                        col_analysis = analysis_result['column_analysis'][col_name]
                        
                        # Count empty values
                        if not value.strip():
                            col_analysis['empty_count'] += 1
                            
                        # Track max length
                        col_analysis['max_length'] = max(col_analysis['max_length'], len(value))
                        
                        # Check for special characters
                        if any(char in value for char in ['\n', '\r', '\t', '"', "'"]):
                            col_analysis['has_special_chars'] = True
                            
                        # Store sample values
                        if len(col_analysis['sample_values']) < 3:
                            col_analysis['sample_values'].append(value[:100])  # Truncate long values
                            
            except Exception as e:
                analysis_result['potential_issues'].append(f"Row {i} parsing error: {e}")
                
        # Identify specific issues
        for col_name, analysis in analysis_result['column_analysis'].items():
            if analysis['empty_count'] > analysis_result['data_rows'] * 0.5:
                analysis_result['potential_issues'].append(
                    f"Column '{col_name}' has {analysis['empty_count']}/{analysis_result['data_rows']} empty values"
                )
                
            if analysis['max_length'] > 1000:
                analysis_result['potential_issues'].append(
                    f"Column '{col_name}' has very long values (max: {analysis['max_length']} chars)"
                )
                
            if analysis['has_special_chars']:
                analysis_result['potential_issues'].append(
                    f"Column '{col_name}' contains special characters that may need escaping"
                )
                
        # Check for Neptune-specific issues
        if '~id' in headers:
            id_col_analysis = analysis_result['column_analysis'].get('~id', {})
            if id_col_analysis['empty_count'] > 0:
                analysis_result['potential_issues'].append(
                    f"~id column has {id_col_analysis['empty_count']} empty values (should be unique and non-empty)"
                )
                
        if '~label' in headers:
            label_col_analysis = analysis_result['column_analysis'].get('~label', {})
            if label_col_analysis['empty_count'] > 0:
                analysis_result['potential_issues'].append(
                    f"~label column has {label_col_analysis['empty_count']} empty values (should be non-empty)"
                )
                
        # Check for type suffix issues
        columns_without_suffixes = [col for col in headers if ':' not in col and col not in ['~id', '~label', '~from', '~to']]
        if columns_without_suffixes:
            analysis_result['potential_issues'].append(
                f"Columns without type suffixes: {columns_without_suffixes}"
            )
            
        logger.debug(f"CSV analysis result: {analysis_result}")
        return analysis_result
        
    except Exception as e:
        logger.error(f"CSV analysis failed for {file_info['key']}: {e}")
        return {
            'file_key': file_info['key'],
            'error': str(e),
            'potential_issues': [f"Analysis failed: {e}"]
        }

class NeptuneBulkLoader:
    def __init__(self, config: NeptuneConfig):
        self.config = config
        self.config.validate()
        
        logger.debug(f"Initializing NeptuneBulkLoader with config: {config}")
        
        # Debug AWS credentials
        if self.config.debug_mode:
            debug_aws_credentials()
        
        try:
            self.s3_client = boto3.client('s3')
            logger.debug("✓ S3 client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            logger.debug(f"S3 client error details: {traceback.format_exc()}")
            raise
        
        # Configure requests session for better SSL handling and connection pooling
        self.session = requests.Session()
        
        # Configure connection pooling
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=config.max_workers * 2,
            pool_maxsize=config.max_workers * 2,
            max_retries=0  # We'll handle retries manually
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
        # Configure SSL settings
        if 'localhost' in config.endpoint or '127.0.0.1' in config.endpoint:
            self.session.verify = False
            logger.info(f"SSL verification disabled for localhost endpoint: {config.endpoint}")
        else:
            logger.info(f"SSL verification enabled for endpoint: {config.endpoint}")
            
        logger.info(f"Initialized NeptuneBulkLoader with endpoint: {config.endpoint}, max_workers: {config.max_workers}")
        
        # Debug network connectivity if in debug mode
        if self.config.debug_mode:
            debug_network_connectivity(config.endpoint, config.connect_timeout)
        
        # Test connection to Neptune endpoint
        self._test_connection()
        
    def _test_connection(self):
        """Test connection to Neptune endpoint before starting bulk load operations."""
        try:
            logger.info(f"Testing connection to Neptune endpoint: {self.config.endpoint}")
            
            # Try to get the status endpoint
            logger.debug(f"Making GET request to: {self.config.endpoint}/status")
            start_time = time.time()
            
            response = self.session.get(
                f"{self.config.endpoint}/status",
                timeout=(self.config.connect_timeout, self.config.timeout)
            )
            
            end_time = time.time()
            logger.debug(f"Response received in {end_time - start_time:.2f} seconds")
            logger.debug(f"Response status: {response.status_code}")
            logger.debug(f"Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                logger.info(f"✓ Successfully connected to Neptune endpoint")
                try:
                    response_data = response.json()
                    logger.debug(f"Response data: {json.dumps(response_data, indent=2)}")
                except Exception as e:
                    logger.debug(f"Response is not JSON: {response.text[:500]}")
            else:
                logger.warning(f"Neptune endpoint responded with status {response.status_code}")
                logger.debug(f"Response text: {response.text[:500]}")
                
        except requests.exceptions.ConnectTimeout:
            logger.error(f"Connection timeout to Neptune endpoint: {self.config.endpoint}")
            logger.error("Please check:")
            logger.error("1. Neptune cluster is running and accessible")
            logger.error("2. Network connectivity to the endpoint")
            logger.error("3. Security groups and VPC settings")
            if self.config.debug_mode:
                debug_network_connectivity(self.config.endpoint, self.config.connect_timeout)
            raise
        except requests.exceptions.Timeout:
            logger.error(f"Request timeout to Neptune endpoint: {self.config.endpoint}")
            logger.debug(f"Timeout settings - Connect: {self.config.connect_timeout}s, Read: {self.config.timeout}s")
            raise
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error to Neptune endpoint: {self.config.endpoint}")
            logger.error(f"Error details: {e}")
            if self.config.debug_mode:
                debug_network_connectivity(self.config.endpoint, self.config.connect_timeout)
            raise
        except Exception as e:
            logger.error(f"Unexpected error testing Neptune connection: {e}")
            logger.debug(f"Connection test error details: {traceback.format_exc()}")
            raise
        
    def get_files_from_s3(self, bucket_name: str) -> tuple[List[Dict], List[Dict]]:
        """Get list of CSV files from S3 bucket, separated into nodes and edges.
        
        Args:
            bucket_name: Name of the S3 bucket
            
        Returns:
            Tuple of (node_files, edge_files)
            
        Raises:
            Exception: If S3 listing fails
        """
        try:
            logger.debug(f"Listing objects in S3 bucket: {bucket_name}")
            
            # Debug S3 access if in debug mode
            if self.config.debug_mode:
                debug_s3_access(bucket_name)
            
            start_time = time.time()
            response = self.s3_client.list_objects_v2(Bucket=bucket_name)
            end_time = time.time()
            
            logger.debug(f"S3 listing completed in {end_time - start_time:.2f} seconds")
            logger.debug(f"S3 response keys: {list(response.keys())}")
            
            if 'Contents' not in response:
                logger.warning(f"No files found in bucket {bucket_name}")
                return [], []
                
            node_files = []
            edge_files = []
            
            logger.debug(f"Processing {len(response['Contents'])} objects from S3")
            
            for obj in response['Contents']:
                file_key = obj['Key']
                # Skip non-CSV files
                if not file_key.lower().endswith('.csv'):
                    logger.debug(f"Skipping non-CSV file: {file_key}")
                    continue
                    
                file_size = obj['Size']
                last_modified = obj['LastModified']
                file_info = {
                    'source': f"s3://{bucket_name}/{file_key}",
                    'format': 'csv',
                    'size': file_size,
                    'last_modified': last_modified,
                    'key': file_key
                }
                
                logger.debug(f"Processing file: {file_key} (size: {file_size} bytes)")
                
                # Categorize files as nodes or edges based on filename
                if self._is_edge_file(file_key):
                    edge_files.append(file_info)
                    logger.debug(f"Categorized as EDGE: {file_key}")
                else:
                    node_files.append(file_info)
                    logger.debug(f"Categorized as NODE: {file_key}")
                    
            logger.info(f"Found {len(node_files)} node files and {len(edge_files)} edge files in bucket {bucket_name}")
            return node_files, edge_files
        except Exception as e:
            logger.error(f"Error listing S3 files from bucket {bucket_name}: {str(e)}")
            logger.debug(f"S3 listing error details: {traceback.format_exc()}")
            raise
    
    def _is_edge_file(self, file_key: str) -> bool:
        """Determine if a file contains edge data based on filename patterns."""
        file_lower = file_key.lower()
        
        logger.debug(f"Analyzing file type for: {file_key}")
        
        # Check for explicit edge pattern
        if '_edges_' in file_lower:
            logger.debug(f"Matched explicit edge pattern '_edges_' in {file_key}")
            return True
            
        # Check for explicit node pattern
        if '_nodes_' in file_lower:
            logger.debug(f"Matched explicit node pattern '_nodes_' in {file_key}")
            return False
            
        # Fallback to common edge file patterns
        edge_patterns = [
            'edge', 'edges', 'relationship', 'relationships',
            'person-', 'person_', '-person', '_person',
            'address-', 'address_', '-address', '_address',
            'receipt-', 'receipt_', '-receipt', '_receipt',
            'name-', 'name_', '-name', '_name',
            'form-', 'form_', '-form', '_form'
        ]
        
        # Check if filename contains any edge patterns
        for pattern in edge_patterns:
            if pattern in file_lower:
                logger.debug(f"Matched edge pattern '{pattern}' in {file_key}")
                return True
                
        logger.debug(f"No edge patterns matched, categorizing as NODE: {file_key}")
        return False
            
    def submit_load_job(self, file_info: Dict) -> Dict:
        """Submit a load job to Neptune bulk loader with optimized settings and retry logic.
        
        Args:
            file_info: Dictionary containing file information
            
        Returns:
            Dictionary with job submission results
        """
        logger.debug(f"Submitting load job for file: {file_info['key']}")
        
        # Validate CSV format if in debug mode
        if self.config.debug_mode:
            validation_result = validate_csv_format(file_info)
            if not validation_result['is_valid']:
                logger.error(f"CSV validation failed for {file_info['key']}:")
                for error in validation_result['errors']:
                    logger.error(f"  - {error}")
                return {
                    'file_key': file_info['key'],
                    'load_id': 'FAILED',
                    'status': f'VALIDATION_ERROR: {"; ".join(validation_result["errors"])}',
                    'type': 'NODE' if not self._is_edge_file(file_info['key']) else 'EDGE',
                    'size': file_info.get('size', 0),
                    'attempts': 1
                }
            elif validation_result['warnings']:
                logger.warning(f"CSV validation warnings for {file_info['key']}:")
                for warning in validation_result['warnings']:
                    logger.warning(f"  - {warning}")
        
        payload = {
            "source": file_info['source'],
            "format": "csv",
            "iamRoleArn": self.config.iam_role_arn,
            "region": self.config.region,
            "failOnError": str(self.config.fail_on_error).upper(),
            "parallelism": self.config.parallelism,
            "updateSingleCardinalityProperties": "FALSE",
            "queueRequest": str(self.config.queue_request).upper(),
            "parserConfiguration": {
                "namedGraphUri": "",
                "baseUri": "",
                "allowEmptyStrings": "FALSE",
                "allowMultipleVertexLabels": "TRUE",
                "allowEmptyStringsWithoutQuotes": "FALSE",
                "trimStrings": "TRUE"
            }
        }
        
        logger.debug(f"Request payload for {file_info['key']}: {json.dumps(payload, indent=2)}")
        
        # Retry logic
        last_exception = None
        for attempt in range(self.config.retry_attempts + 1):
            try:
                if attempt > 0:
                    logger.info(f"Retry attempt {attempt}/{self.config.retry_attempts} for file {file_info['key']}")
                    time.sleep(self.config.retry_delay)
                
                logger.debug(f"Making POST request to {self.config.endpoint}/loader (attempt {attempt + 1})")
                start_time = time.time()
                
                response = self.session.post(
                    f"{self.config.endpoint}/loader",
                    json=payload,
                    timeout=(self.config.connect_timeout, self.config.timeout)
                )
                
                end_time = time.time()
                logger.debug(f"Response received in {end_time - start_time:.2f} seconds")
                logger.debug(f"Response status: {response.status_code}")
                logger.debug(f"Response headers: {dict(response.headers)}")
                
                response.raise_for_status()
                
                try:
                    response_data = response.json()
                    logger.debug(f"Response data: {json.dumps(response_data, indent=2)}")
                except Exception as e:
                    logger.debug(f"Response is not JSON: {response.text[:500]}")
                    raise ValueError(f"Invalid JSON response: {response.text[:200]}")
                
                load_id = response_data.get('payload', {}).get('loadId')
                if not load_id:
                    raise ValueError("No load ID returned from Neptune")
                    
                logger.debug(f"Successfully submitted job for {file_info['key']} with load ID: {load_id}")
                    
                return {
                    'file_key': file_info['key'],
                    'load_id': load_id,
                    'status': 'SUBMITTED',
                    'type': 'NODE' if not self._is_edge_file(file_info['key']) else 'EDGE',
                    'size': file_info.get('size', 0),
                    'attempts': attempt + 1
                }
                
            except (requests.exceptions.ConnectTimeout, requests.exceptions.Timeout) as e:
                last_exception = e
                logger.debug(f"Timeout error details: {traceback.format_exc()}")
                if attempt < self.config.retry_attempts:
                    logger.warning(f"Timeout on attempt {attempt + 1} for file {file_info['key']}: {e}")
                    continue
                else:
                    logger.error(f"All retry attempts failed for file {file_info['key']}: {e}")
                    return {
                        'file_key': file_info['key'],
                        'load_id': 'FAILED',
                        'status': f'TIMEOUT_ERROR: {str(e)}',
                        'type': 'NODE' if not self._is_edge_file(file_info['key']) else 'EDGE',
                        'size': file_info.get('size', 0),
                        'attempts': attempt + 1
                    }
                    
            except requests.exceptions.ConnectionError as e:
                last_exception = e
                logger.debug(f"Connection error details: {traceback.format_exc()}")
                if attempt < self.config.retry_attempts:
                    logger.warning(f"Connection error on attempt {attempt + 1} for file {file_key}: {e}")
                    logger.info(f"Will retry after {self.config.retry_delay} seconds...")
                    continue
                else:
                    logger.error(f"All retry attempts failed for file {file_key}: {e}")
                    logger.error(f"Total attempts made: {attempt + 1}")
                    return {
                        'file_key': file_key,
                        'load_id': 'FAILED',
                        'status': f'CONNECTION_ERROR: {str(e)}',
                        'type': 'NODE' if not self._is_edge_file(file_key) else 'EDGE',
                        'size': file_size,
                        'attempts': attempt + 1
                    }
                    
            except requests.exceptions.RequestException as e:
                last_exception = e
                logger.error(f"HTTP request failed for file {file_key}: {e}")
                logger.debug(f"HTTP error details: {traceback.format_exc()}")
                
                # Special handling for 400 Bad Request errors
                if hasattr(e, 'response') and e.response is not None:
                    if e.response.status_code == 400:
                        logger.error(f"400 Bad Request for file {file_key}")
                        logger.error(f"Response status: {e.response.status_code}")
                        logger.error(f"Response headers: {dict(e.response.headers)}")
                        
                        try:
                            error_response = e.response.json()
                            logger.error(f"Error response JSON: {json.dumps(error_response, indent=2)}")
                            
                            # Extract specific error details
                            if 'payload' in error_response:
                                payload = error_response['payload']
                                if 'errors' in payload:
                                    for error in payload['errors']:
                                        logger.error(f"Error: {error}")
                                if 'details' in payload:
                                    logger.error(f"Error details: {payload['details']}")
                                    
                        except Exception as json_error:
                            logger.error(f"Response text (not JSON): {e.response.text[:1000]}")
                            
                        # Provide specific troubleshooting for 400 errors
                        logger.error("400 Bad Request troubleshooting:")
                        logger.error("1. Check CSV file format - ensure proper column headers")
                        logger.error("2. Verify required columns: ~id, ~label for nodes")
                        logger.error("3. Check for invalid data types or malformed values")
                        logger.error("4. Ensure no empty required fields")
                        logger.error("5. Verify CSV encoding and special characters")
                        
                return {
                    'file_key': file_key,
                    'load_id': 'FAILED',
                    'status': f'HTTP_ERROR: {str(e)}',
                    'type': 'NODE' if not self._is_edge_file(file_key) else 'EDGE',
                    'size': file_size,
                    'attempts': attempt + 1
                }
                
            except Exception as e:
                last_exception = e
                logger.error(f"Unexpected error submitting job for file {file_key}: {e}")
                logger.debug(f"Unexpected error details: {traceback.format_exc()}")
                return {
                    'file_key': file_key,
                    'load_id': 'FAILED',
                    'status': f'ERROR: {str(e)}',
                    'type': 'NODE' if not self._is_edge_file(file_key) else 'EDGE',
                    'size': file_size,
                    'attempts': attempt + 1
                }
        
        # This should never be reached, but just in case
        return {
            'file_key': file_key,
            'load_id': 'FAILED',
            'status': f'UNKNOWN_ERROR: {str(last_exception)}',
            'type': 'NODE' if not self._is_edge_file(file_key) else 'EDGE',
            'size': file_size,
            'attempts': self.config.retry_attempts + 1
        }

    def submit_jobs_concurrent(self, files: List[Dict], job_type: str) -> List[Dict]:
        """Submit multiple jobs concurrently using ThreadPoolExecutor.
        
        Args:
            files: List of file information dictionaries
            job_type: Type of job (NODE or EDGE)
            
        Returns:
            List of job submission results
        """
        if not files:
            logger.info(f"No {job_type} files to submit")
            return []
            
        job_results = []
        
        logger.info(f"Starting concurrent submission of {len(files)} {job_type} files")
        logger.info(f"Using {self.config.max_workers} concurrent workers")
        print(f"\n{Fore.BLUE}Submitting {len(files)} {job_type} files concurrently (max {self.config.max_workers} workers)...{Style.RESET_ALL}")
        
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            # Submit all jobs
            logger.info(f"Submitting {len(files)} jobs to thread pool...")
            future_to_file = {executor.submit(self.submit_load_job, file_info): file_info for file_info in files}
            logger.info(f"✓ Submitted {len(future_to_file)} jobs to thread pool")
            
            # Process completed jobs
            completed = 0
            for future in as_completed(future_to_file):
                completed += 1
                try:
                    result = future.result()
                    job_results.append(result)
                    
                    logger.info(f"Job {completed}/{len(files)} completed: {result['file_key']} - {result['status']}")
                    logger.debug(f"Job {completed}/{len(files)} full result: {result}")
                    
                    # Update progress
                    print_progress(completed, len(files), 
                                 prefix=f'{job_type}:', 
                                 suffix=f'({completed}/{len(files)}) - {result["file_key"]}')
                    
                    # Print immediate status
                    if result['status'] == 'SUBMITTED':
                        print(f"\n{Fore.GREEN}✓{Style.RESET_ALL} {result['file_key']} - {result['load_id']}")
                    else:
                        print(f"\n{Fore.RED}✗{Style.RESET_ALL} {result['file_key']} - {result['status']}")
                except Exception as e:
                    logger.error(f"Error processing future result for job {completed}: {e}")
                    logger.debug(f"Future processing error details: {traceback.format_exc()}")
                    # Add a failed result if we can't get the actual result
                    job_results.append({
                        'file_key': 'UNKNOWN',
                        'load_id': 'FAILED',
                        'status': f'FUTURE_ERROR: {str(e)}',
                        'type': job_type,
                        'size': 0
                    })
        
        print()  # New line after progress bar
        logger.info(f"✓ Completed concurrent submission of {len(job_results)} {job_type} jobs")
        return job_results
            
    def load_all_files(self, bucket_name: str) -> Dict:
        """Load all files from S3 bucket into Neptune - nodes first, then edges with concurrent processing.
        
        Args:
            bucket_name: Name of the S3 bucket containing files
            
        Returns:
            Dictionary with job submission summary
            
        Raises:
            Exception: If the operation fails
        """
        start_time = datetime.now()
        logger.info(f"Starting load_all_files for bucket: {bucket_name}")
        logger.info(f"Start time: {start_time}")
        
        try:
            # Get list of files separated into nodes and edges
            logger.info("Retrieving file list from S3...")
            node_files, edge_files = self.get_files_from_s3(bucket_name)
            
            if not node_files and not edge_files:
                logger.warning("No files to load")
                return {
                    'total_files': 0,
                    'submitted': 0,
                    'failed': 0,
                    'duration': datetime.now() - start_time
                }
                
            total_files = len(node_files) + len(edge_files)
            total_size = sum(f.get('size', 0) for f in node_files + edge_files)
            total_size_gb = total_size / (1024*1024*1024)
            
            logger.info(f"Processing {total_files} files with total size {total_size_gb:.2f} GB")
            logger.info(f"Node files: {len(node_files)}, Edge files: {len(edge_files)}")
            
            print(f"Found {len(node_files)} node files and {len(edge_files)} edge files to submit")
            print(f"Total data size: {total_size_gb:.2f} GB")
            print(f"Using {self.config.max_workers} concurrent workers for job submission")
            
            job_results = []
            
            # Load nodes first (concurrently)
            if node_files:
                logger.info(f"Starting node file submission for {len(node_files)} files...")
                node_results = self.submit_jobs_concurrent(node_files, "NODE")
                job_results.extend(node_results)
                logger.info(f"✓ Completed node file submission, {len(node_results)} results")
            
            # Load edges second (concurrently)
            if edge_files:
                logger.info(f"Starting edge file submission for {len(edge_files)} files...")
                edge_results = self.submit_jobs_concurrent(edge_files, "EDGE")
                job_results.extend(edge_results)
                logger.info(f"✓ Completed edge file submission, {len(edge_results)} results")
            
            # Calculate summary
            submitted_count = len([j for j in job_results if j['status'] == 'SUBMITTED'])
            failed_count = len([j for j in job_results if j['status'] != 'SUBMITTED'])
            
            logger.info(f"Job submission summary - Submitted: {submitted_count}, Failed: {failed_count}")
            
            # Print final report
            self._print_job_report(job_results, node_files, edge_files, total_files, total_size, start_time)
            
            end_time = datetime.now()
            duration = end_time - start_time
            logger.info(f"Total execution time: {duration}")
            
            return {
                'total_files': total_files,
                'submitted': submitted_count,
                'failed': failed_count,
                'duration': duration,
                'job_results': job_results
            }
            
        except Exception as e:
            logger.error(f"Script failed: {str(e)}")
            logger.debug(f"Script failure details: {traceback.format_exc()}")
            raise
    
    def _print_job_report(self, job_results: List[Dict], node_files: List[Dict], 
                         edge_files: List[Dict], total_files: int, total_size: int, start_time: datetime):
        """Print the final job submission report."""
        submitted_count = len([j for j in job_results if j['status'] == 'SUBMITTED'])
        failed_count = len([j for j in job_results if j['status'] != 'SUBMITTED'])
        
        print_header("Job Submission Report")
        print(f"{Fore.CYAN}Total Files Found:{Style.RESET_ALL} {total_files}")
        print(f"{Fore.CYAN}Total Data Size:{Style.RESET_ALL} {total_size / (1024*1024*1024):.2f} GB")
        print(f"{Fore.CYAN}Node Files:{Style.RESET_ALL} {len(node_files)}")
        print(f"{Fore.CYAN}Edge Files:{Style.RESET_ALL} {len(edge_files)}")
        print(f"{Fore.CYAN}Jobs Submitted Successfully:{Style.RESET_ALL} {submitted_count}")
        print(f"{Fore.CYAN}Jobs Failed:{Style.RESET_ALL} {failed_count}")
        print(f"{Fore.CYAN}Submission Time:{Style.RESET_ALL} {datetime.now() - start_time}")
        print(f"{Fore.CYAN}Concurrent Workers Used:{Style.RESET_ALL} {self.config.max_workers}")
        
        # Print all jobs in submission order
        print(f"\n{Fore.CYAN}Job Details (in submission order):{Style.RESET_ALL}")
        print(f"{'Type':<6} {'File':<50} {'Job ID':<40} {'Size (MB)':<10} {'Attempts':<8} {'Status'}")
        print("-" * 124)
        
        for job in job_results:
            job_type = job['type']
            size_mb = job.get('size', 0) / (1024*1024)
            attempts = job.get('attempts', 1)
            
            if job['status'] == 'SUBMITTED':
                status_color = Fore.GREEN
                status_text = f"SUBMITTED (attempt {attempts})"
            else:
                status_color = Fore.RED
                status_text = job['status']
                
            print(f"{job_type:<6} {job['file_key']:<50} {job['load_id']:<40} {size_mb:<10.1f} {attempts:<8} {status_color}{status_text}{Style.RESET_ALL}")

def main():
    """Main function to run the Neptune bulk loader."""
    logger.info("Starting Neptune Bulk Loader...")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Working directory: {os.getcwd()}")
    
    # Configuration from environment variables with defaults
    s3_bucket = os.getenv('S3_BUCKET', 'deam-neptune')
    logger.info(f"S3 bucket from environment: {s3_bucket}")
    
    # Check for analyze flag
    analyze_file = os.getenv('ANALYZE_FILE', '')
    if analyze_file:
        logger.info(f"Analyze mode enabled for file: {analyze_file}")
    
    try:
        # Create configuration from environment variables
        logger.info("Loading configuration from environment variables...")
        config = NeptuneConfig.from_env()
        
        # If IAM role is not set, try to use a default pattern
        if not config.iam_role_arn:
            logger.error("NEPTUNE_IAM_ROLE_ARN environment variable is required")
            logger.error("Example: export NEPTUNE_IAM_ROLE_ARN='arn:aws:iam::123456789012:role/NeptuneLoadFromS3'")
            sys.exit(1)
        
        # Print configuration summary
        logger.info("Configuration loaded successfully")
        print_header("Neptune Bulk Loader Configuration")
        print(f"{Fore.CYAN}Neptune Endpoint:{Style.RESET_ALL} {config.endpoint}")
        print(f"{Fore.CYAN}AWS Region:{Style.RESET_ALL} {config.region}")
        print(f"{Fore.CYAN}S3 Bucket:{Style.RESET_ALL} {s3_bucket}")
        print(f"{Fore.CYAN}Max Workers:{Style.RESET_ALL} {config.max_workers}")
        print(f"{Fore.CYAN}Timeout:{Style.RESET_ALL} {config.timeout}s")
        print(f"{Fore.CYAN}Connect Timeout:{Style.RESET_ALL} {config.connect_timeout}s")
        print(f"{Fore.CYAN}Retry Attempts:{Style.RESET_ALL} {config.retry_attempts}")
        print(f"{Fore.CYAN}Retry Delay:{Style.RESET_ALL} {config.retry_delay}s")
        print(f"{Fore.CYAN}Parallelism:{Style.RESET_ALL} {config.parallelism}")
        print(f"{Fore.CYAN}Debug Mode:{Style.RESET_ALL} {config.debug_mode}")
        
        # Create loader
        logger.info("Creating NeptuneBulkLoader instance...")
        loader = NeptuneBulkLoader(config)
        logger.info("✓ NeptuneBulkLoader instance created successfully")
        
        # If analyze flag is set, analyze the specific file
        if analyze_file:
            logger.info(f"Starting CSV analysis for file: {analyze_file}")
            print_header(f"Analyzing CSV File: {analyze_file}")
            
            # Create a mock file_info for the specific file
            file_info = {
                'source': f"s3://{s3_bucket}/{analyze_file}",
                'key': analyze_file,
                'size': 0
            }
            
            logger.info(f"Analyzing file: {file_info['source']}")
            # Analyze the file
            analysis_result = analyze_csv_file(file_info)
            
            print(f"{Fore.CYAN}File Analysis Results:{Style.RESET_ALL}")
            print(f"File: {analysis_result['file_key']}")
            print(f"Total lines: {analysis_result.get('total_lines', 'N/A')}")
            print(f"Header count: {analysis_result.get('header_count', 'N/A')}")
            print(f"Data rows: {analysis_result.get('data_rows', 'N/A')}")
            print(f"Empty rows: {analysis_result.get('empty_rows', 'N/A')}")
            
            if 'headers' in analysis_result:
                print(f"\n{Fore.CYAN}Headers:{Style.RESET_ALL}")
                for i, header in enumerate(analysis_result['headers']):
                    print(f"  {i+1}. {header}")
                    
            if 'potential_issues' in analysis_result and analysis_result['potential_issues']:
                print(f"\n{Fore.RED}Potential Issues:{Style.RESET_ALL}")
                for issue in analysis_result['potential_issues']:
                    print(f"  • {issue}")
                    
            if 'column_analysis' in analysis_result:
                print(f"\n{Fore.CYAN}Column Analysis:{Style.RESET_ALL}")
                for col_name, analysis in analysis_result['column_analysis'].items():
                    print(f"  {col_name}:")
                    print(f"    - Empty values: {analysis['empty_count']}")
                    print(f"    - Max length: {analysis['max_length']}")
                    print(f"    - Sample values: {analysis['sample_values'][:2]}")
                    
            if 'sample_data' in analysis_result and analysis_result['sample_data']:
                print(f"\n{Fore.CYAN}Sample Data (first 3 rows):{Style.RESET_ALL}")
                for sample in analysis_result['sample_data']:
                    print(f"  Row {sample['row_number']}: {sample['data'][:5]}...")
                    
            logger.info("CSV analysis completed")
            return
            
        # Run normal bulk load operation
        logger.info("Starting bulk load operation...")
        result = loader.load_all_files(s3_bucket)
        
        # Exit with appropriate code
        if result['failed'] > 0:
            logger.warning(f"Some jobs failed: {result['failed']} out of {result['total_files']}")
            logger.info("Exiting with error code 1")
            sys.exit(1)
        else:
            logger.info(f"All {result['submitted']} jobs submitted successfully")
            logger.info("Exiting with success code 0")
            sys.exit(0)
            
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        logger.info("Exiting with SIGINT code 130")
        sys.exit(130)  # Standard exit code for SIGINT
    except Exception as e:
        logger.error(f"Script failed: {str(e)}")
        logger.debug(f"Main function error details: {traceback.format_exc()}")
        
        # Provide helpful troubleshooting information
        logger.info("Displaying troubleshooting information...")
        print_header("Troubleshooting Tips")
        print(f"{Fore.YELLOW}Common issues and solutions:{Style.RESET_ALL}")
        print("1. Connection timeout:")
        print("   - Check if Neptune cluster is running and accessible")
        print("   - Verify network connectivity and security groups")
        print("   - Try increasing NEPTUNE_CONNECT_TIMEOUT environment variable")
        print("2. Authentication issues:")
        print("   - Verify NEPTUNE_IAM_ROLE_ARN is correct")
        print("   - Check AWS credentials and permissions")
        print("3. S3 access issues:")
        print("   - Verify S3_BUCKET environment variable")
        print("   - Check S3 bucket permissions and IAM role access")
        print("4. Neptune endpoint issues:")
        print("   - Verify NEPTUNE_ENDPOINT is correct")
        print("   - Check if endpoint includes https:// prefix")
        print("   - Ensure endpoint is accessible from your network")
        print("5. Debug mode:")
        print("   - Set NEPTUNE_DEBUG=true for detailed logging")
        print("   - Set NEPTUNE_VERBOSE=true for verbose logging")
        print("   - Check network connectivity and AWS credentials")
        
        logger.info("Exiting with error code 1")
        sys.exit(1)

if __name__ == "__main__":
    main()
