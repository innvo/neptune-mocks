#!/usr/bin/env python3
"""
Neptune Bulk Loader - Curl Command Executor

This script executes curl commands to bulk load all CSV files from s3://deam-neptune/
into Neptune. It automatically discovers files in the S3 bucket and submits them
for loading using the Neptune bulk loader API.

Features:
- Automatic file discovery in S3 bucket
- Separate handling of node and edge files
- Concurrent job submission with progress tracking
- Comprehensive error handling and logging
- Configurable timeouts and retry logic
- Support for both localhost and production endpoints

Environment Variables:
- NEPTUNE_ENDPOINT: Neptune cluster endpoint (default: https://localhost:8182)
- NEPTUNE_IAM_ROLE_ARN: IAM role ARN for S3 access (required)
- AWS_REGION: AWS region (default: us-east-1)
- S3_BUCKET: S3 bucket name (default: deam-neptune)
- NEPTUNE_MAX_WORKERS: Maximum concurrent workers (default: 10 - high performance)
- NEPTUNE_USE_SEQUENTIAL: Use sequential submission to respect Neptune's concurrent load limits (default: true)
- NEPTUNE_WAIT_FOR_COMPLETION: Wait for each load to complete before submitting next file (default: true)
- NEPTUNE_PERFORMANCE_MODE: Enable legacy performance mode (default: false - high performance is now default)
- NEPTUNE_ULTRA_MODE: Enable ultra-performance mode for Neptune clusters with high concurrent limits (default: false)
- NEPTUNE_TIMEOUT: Request timeout in seconds (default: 1800 - 30 minutes)
- NEPTUNE_CONNECT_TIMEOUT: Connection timeout in seconds (default: 60 - 1 minute)
- NEPTUNE_RETRY_ATTEMPTS: Number of retry attempts (default: 1 - minimal for speed)
- NEPTUNE_RETRY_DELAY: Delay between retries in seconds (default: 2 - short for speed)
- NEPTUNE_PARALLELISM: Neptune loader parallelism (default: OVERSUBSCRIBE - maximum)
- NEPTUNE_FAIL_ON_ERROR: Whether to fail on errors (default: false - continue on errors)
- NEPTUNE_QUEUE_REQUEST: Whether to queue requests (default: false - immediate submission)
- NEPTUNE_DEBUG: Enable debug logging (default: false)
"""

import boto3
import subprocess
import json
import logging
import os
import sys
import time
from typing import Dict, List, Tuple
from datetime import datetime
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import traceback
from colorama import init, Fore, Style

# Initialize colorama for colored output
init()

@dataclass
class NeptuneConfig:
    """Configuration for Neptune bulk loader."""
    endpoint: str = "https://localhost:8182"
    iam_role_arn: str = ""
    region: str = "us-east-1"
    s3_bucket: str = "deam-neptune"
    max_workers: int = 5
    parallelism: str = "HIGH"
    fail_on_error: bool = True
    queue_request: bool = True
    timeout: int = 300
    connect_timeout: int = 30
    retry_attempts: int = 3
    retry_delay: int = 5
    debug_mode: bool = False
    use_sequential: bool = True  # Default to sequential to respect Neptune's concurrent load limits
    wait_for_completion: bool = True  # Default to waiting for each load to complete before next submission
    
    @classmethod
    def from_env(cls) -> 'NeptuneConfig':
        """Create configuration from environment variables."""
        return cls(
            endpoint=os.getenv('NEPTUNE_ENDPOINT', cls.endpoint),
            iam_role_arn=os.getenv('NEPTUNE_IAM_ROLE_ARN', cls.iam_role_arn),
            region=os.getenv('AWS_REGION', cls.region),
            s3_bucket=os.getenv('S3_BUCKET', cls.s3_bucket),
            max_workers=int(os.getenv('NEPTUNE_MAX_WORKERS', 10)),  # Default to high performance
            parallelism=os.getenv('NEPTUNE_PARALLELISM', 'OVERSUBSCRIBE'),  # Default to maximum parallelism
            fail_on_error=os.getenv('NEPTUNE_FAIL_ON_ERROR', 'false').lower() == 'true',  # Default to not fail on errors
            queue_request=os.getenv('NEPTUNE_QUEUE_REQUEST', 'false').lower() == 'true',  # Default to immediate submission
            timeout=int(os.getenv('NEPTUNE_TIMEOUT', 1800)),  # Default to 30 minutes
            connect_timeout=int(os.getenv('NEPTUNE_CONNECT_TIMEOUT', 60)),  # Default to 1 minute
            retry_attempts=int(os.getenv('NEPTUNE_RETRY_ATTEMPTS', 1)),  # Default to minimal retries
            retry_delay=int(os.getenv('NEPTUNE_RETRY_DELAY', 2)),  # Default to short retry delay
            debug_mode=os.getenv('NEPTUNE_DEBUG', 'false').lower() == 'true',
            use_sequential=os.getenv('NEPTUNE_USE_SEQUENTIAL', 'true').lower() == 'true',  # Keep sequential for Neptune clusters with limit=1
            wait_for_completion=os.getenv('NEPTUNE_WAIT_FOR_COMPLETION', 'true').lower() == 'true'  # Wait for each load to complete
        )
    
    @classmethod
    def high_performance(cls) -> 'NeptuneConfig':
        """Create a high-performance configuration optimized for speed."""
        return cls(
            endpoint=os.getenv('NEPTUNE_ENDPOINT', cls.endpoint),
            iam_role_arn=os.getenv('NEPTUNE_IAM_ROLE_ARN', cls.iam_role_arn),
            region=os.getenv('AWS_REGION', cls.region),
            s3_bucket=os.getenv('S3_BUCKET', cls.s3_bucket),
            max_workers=10,  # Increased workers for concurrent processing
            parallelism="OVERSUBSCRIBE",  # Maximum parallelism
            fail_on_error=False,  # Don't fail on individual errors
            queue_request=False,  # Don't queue, submit immediately
            timeout=1800,  # 30 minutes for large files
            connect_timeout=60,  # 1 minute connection timeout
            retry_attempts=1,  # Minimal retries for speed
            retry_delay=2,  # Short retry delay
            debug_mode=False,  # Disable debug for performance
            use_sequential=True,  # Use sequential for Neptune clusters with limit=1
            wait_for_completion=True  # Wait for each load to complete
        )
    
    @classmethod
    def ultra_performance(cls) -> 'NeptuneConfig':
        """Create an ultra-performance configuration for Neptune clusters with higher concurrent limits."""
        return cls(
            endpoint=os.getenv('NEPTUNE_ENDPOINT', cls.endpoint),
            iam_role_arn=os.getenv('NEPTUNE_IAM_ROLE_ARN', cls.iam_role_arn),
            region=os.getenv('AWS_REGION', cls.region),
            s3_bucket=os.getenv('S3_BUCKET', cls.s3_bucket),
            max_workers=20,  # Maximum workers for concurrent processing
            parallelism="OVERSUBSCRIBE",  # Maximum parallelism
            fail_on_error=False,  # Don't fail on individual errors
            queue_request=False,  # Don't queue, submit immediately
            timeout=3600,  # 1 hour for very large files
            connect_timeout=120,  # 2 minute connection timeout
            retry_attempts=1,  # Minimal retries for speed
            retry_delay=1,  # Minimal retry delay
            debug_mode=False,  # Disable debug for performance
            use_sequential=False,  # Use concurrent processing
            wait_for_completion=False  # Don't wait for completion in ultra mode
        )
    
    def validate(self) -> None:
        """Validate configuration."""
        if not self.iam_role_arn:
            raise ValueError("IAM role ARN is required. Set NEPTUNE_IAM_ROLE_ARN environment variable.")
        if not self.endpoint:
            raise ValueError("Neptune endpoint is required.")
        if not self.s3_bucket:
            raise ValueError("S3 bucket is required.")
        if self.max_workers < 1:
            raise ValueError("Max workers must be at least 1.")
        if self.timeout < 30:
            raise ValueError("Timeout must be at least 30 seconds.")
        if self.connect_timeout < 10:
            raise ValueError("Connect timeout must be at least 10 seconds.")
        if self.retry_attempts < 0:
            raise ValueError("Retry attempts must be non-negative.")
    
    def print_performance_info(self):
        """Print performance configuration information."""
        print(f"{Fore.CYAN}HIGH PERFORMANCE Configuration:{Style.RESET_ALL}")
        print(f"  Submission Mode: {'Sequential' if self.use_sequential else 'Concurrent'}")
        print(f"  Wait for Completion: {self.wait_for_completion}")
        print(f"  Max Workers: {self.max_workers}")
        print(f"  Parallelism: {self.parallelism}")
        print(f"  Queue Requests: {self.queue_request}")
        print(f"  Fail on Error: {self.fail_on_error}")
        print(f"  Timeout: {self.timeout}s")
        print(f"  Retry Attempts: {self.retry_attempts}")
        print(f"  Retry Delay: {self.retry_delay}s")
        
        if self.use_sequential:
            print(f"{Fore.YELLOW}  ⚠️  Sequential mode may be slow for large datasets{Style.RESET_ALL}")
            print(f"  💡 Set NEPTUNE_ULTRA_MODE=true for maximum speed (if cluster supports >5 concurrent loads)")
        else:
            print(f"{Fore.GREEN}  ✅ Concurrent mode enabled for maximum performance{Style.RESET_ALL}")
        
        print(f"{Fore.GREEN}  🚀 HIGH PERFORMANCE MODE ENABLED{Style.RESET_ALL}")

# Configure logging
def setup_logging(debug_mode: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if debug_mode else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    return logging.getLogger(__name__)

def print_header(text: str):
    """Print a formatted header."""
    print(f"\n{Fore.BLUE}{'=' * 80}{Style.RESET_ALL}")
    print(f"{Fore.BLUE}{text.center(80)}{Style.RESET_ALL}")
    print(f"{Fore.BLUE}{'=' * 80}{Style.RESET_ALL}\n")

def print_progress(current: int, total: int, prefix: str = '', suffix: str = ''):
    """Print a progress bar."""
    bar_length = 50
    filled_length = int(round(bar_length * current / float(total)))
    percents = round(100.0 * current / float(total), 1)
    bar = '█' * filled_length + '░' * (bar_length - filled_length)
    sys.stdout.write(f'\r{prefix} |{bar}| {percents}% {suffix}')
    sys.stdout.flush()

class NeptuneCurlBulkLoader:
    """Neptune bulk loader using curl commands."""
    
    def __init__(self, config: NeptuneConfig):
        self.config = config
        self.config.validate()
        self.logger = setup_logging(config.debug_mode)
        
        self.logger.info(f"Initializing NeptuneCurlBulkLoader with endpoint: {config.endpoint}")
        
        try:
            self.s3_client = boto3.client('s3')
            self.logger.info("✓ S3 client initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize S3 client: {e}")
            raise
    
    def get_files_from_s3(self) -> Tuple[List[Dict], List[Dict]]:
        """Get list of CSV files from S3 bucket, separated into nodes and edges.
        
        Returns:
            Tuple of (node_files, edge_files)
        """
        try:
            self.logger.info(f"Listing objects in S3 bucket: {self.config.s3_bucket}")
            
            response = self.s3_client.list_objects_v2(Bucket=self.config.s3_bucket)
            
            if 'Contents' not in response:
                self.logger.warning(f"No files found in bucket {self.config.s3_bucket}")
                return [], []
                
            node_files = []
            edge_files = []
            
            for obj in response['Contents']:
                file_key = obj['Key']
                # Skip non-CSV files
                if not file_key.lower().endswith('.csv'):
                    continue
                    
                file_size = obj['Size']
                last_modified = obj['LastModified']
                file_info = {
                    'source': f"s3://{self.config.s3_bucket}/{file_key}",
                    'format': 'csv',
                    'size': file_size,
                    'last_modified': last_modified,
                    'key': file_key
                }
                
                # Categorize files as nodes or edges based on filename
                if self._is_edge_file(file_key):
                    edge_files.append(file_info)
                    self.logger.debug(f"Categorized as EDGE: {file_key}")
                else:
                    node_files.append(file_info)
                    self.logger.debug(f"Categorized as NODE: {file_key}")
                    
            self.logger.info(f"Found {len(node_files)} node files and {len(edge_files)} edge files")
            return node_files, edge_files
            
        except Exception as e:
            self.logger.error(f"Error listing S3 files: {str(e)}")
            raise
    
    def _is_edge_file(self, file_key: str) -> bool:
        """Determine if a file is an edge file based on filename patterns."""
        edge_patterns = [
            'edge', 'relationship', 'link', 'connection',
            'person_address', 'person_organization', 'person_email',
            'person_phone', 'person_form', 'person_name',
            'organization_address', 'building_address'
        ]
        
        file_key_lower = file_key.lower()
        return any(pattern in file_key_lower for pattern in edge_patterns)
    
    def build_curl_command(self, file_info: Dict) -> str:
        """Build curl command for a single file."""
        payload = {
            "source": file_info['source'],
            "format": "csv",
            "iamRoleArn": self.config.iam_role_arn,
            "region": self.config.region,
            "failOnError": "FALSE" if not self.config.fail_on_error else "TRUE",
            "parallelism": self.config.parallelism,
            "updateSingleCardinalityProperties": "FALSE"
        }
        
        # Only add queueRequest if explicitly set to False (to match working curl)
        if not self.config.queue_request:
            payload["queueRequest"] = "FALSE"
        
        # Build curl command as list of arguments (no shell escaping issues)
        curl_cmd = [
            'curl', '-X', 'POST',
            f'{self.config.endpoint}/loader',
            '-H', 'Content-Type: application/json',
            '--connect-timeout', str(self.config.connect_timeout),
            '--max-time', str(self.config.timeout),
            '-k',  # Disable SSL verification for localhost
            '-s',  # Silent mode
            '-d', json.dumps(payload)
        ]
        
        # For debugging, show the command as it would be executed
        curl_command = ' '.join(curl_cmd)
        
        # Log the exact curl command for debugging
        if self.config.debug_mode:
            self.logger.debug(f"Generated curl command for {file_info['key']}:")
            self.logger.debug(curl_command)
            self.logger.debug(f"Payload: {json.dumps(payload, indent=2)}")
        
        return curl_cmd
    
    def test_single_file(self, file_key: str) -> Dict:
        """Test loading a single file with minimal configuration (matching working curl)."""
        file_info = {
            'source': f"s3://{self.config.s3_bucket}/{file_key}",
            'format': 'csv',
            'key': file_key,
            'size': 0
        }
        
        # Use minimal payload matching the working curl command
        payload = {
            "source": file_info['source'],
            "format": "csv",
            "iamRoleArn": self.config.iam_role_arn,
            "region": self.config.region,
            "failOnError": "FALSE",
            "parallelism": "MEDIUM",
            "updateSingleCardinalityProperties": "FALSE",
            "queueRequest": "FALSE"
        }
        
        # Build curl command as list of arguments (no shell escaping issues)
        curl_cmd = [
            'curl', '-X', 'POST',
            f'{self.config.endpoint}/loader',
            '-H', 'Content-Type: application/json',
            '--connect-timeout', str(self.config.connect_timeout),
            '--max-time', str(self.config.timeout),
            '-k',  # Disable SSL verification for localhost
            '-s',  # Silent mode
            '-d', json.dumps(payload)
        ]
        
        # For debugging, show the command as it would be executed
        curl_command = ' '.join(curl_cmd)
        
        self.logger.info(f"Testing single file: {file_key}")
        self.logger.info(f"Test curl command: {curl_command}")
        
        try:
            result = subprocess.run(
                curl_cmd,
                shell=False,
                capture_output=True,
                text=True,
                timeout=self.config.timeout
            )
            
            self.logger.info(f"Return code: {result.returncode}")
            self.logger.info(f"stdout: {result.stdout}")
            self.logger.info(f"stderr: {result.stderr}")
            
            if result.returncode == 0:
                try:
                    response_data = json.loads(result.stdout)
                    self.logger.info(f"Response: {response_data}")
                    return {
                        'file_key': file_key,
                        'success': True,
                        'response': response_data
                    }
                except json.JSONDecodeError:
                    return {
                        'file_key': file_key,
                        'success': False,
                        'error': f"Invalid JSON: {result.stdout}"
                    }
            else:
                return {
                    'file_key': file_key,
                    'success': False,
                    'error': f"curl failed: {result.stderr}"
                }
                
        except Exception as e:
            return {
                'file_key': file_key,
                'success': False,
                'error': str(e)
            }
    
    def execute_curl_command(self, file_info: Dict) -> Dict:
        """Execute curl command for a single file with retry logic."""
        file_key = file_info['key']
        curl_cmd = self.build_curl_command(file_info)
        
        self.logger.debug(f"Executing curl command for {file_key}")
        self.logger.debug(f"Curl command: {' '.join(curl_cmd)}")
        
        last_exception = None
        for attempt in range(self.config.retry_attempts + 1):
            try:
                if attempt > 0:
                    self.logger.info(f"Retry attempt {attempt}/{self.config.retry_attempts} for file {file_key}")
                    # Use exponential backoff for retries
                    backoff_delay = self.config.retry_delay * (2 ** (attempt - 1))
                    self.logger.info(f"Waiting {backoff_delay} seconds before retry...")
                    time.sleep(backoff_delay)
                
                # Execute curl command (no shell=True to avoid escaping issues)
                result = subprocess.run(
                    curl_cmd,
                    shell=False,
                    capture_output=True,
                    text=True,
                    timeout=self.config.timeout
                )
                
                if result.returncode == 0:
                    try:
                        response_data = json.loads(result.stdout)
                        self.logger.debug(f"Response for {file_key}: {response_data}")
                        
                        # Check for concurrent load limit error
                        if 'code' in response_data and response_data['code'] == 'BadRequestException':
                            if 'Max concurrent load limit breached' in response_data.get('detailedMessage', ''):
                                self.logger.warning(f"Concurrent load limit breached for {file_key}, will retry with longer delay")
                                last_exception = f"Concurrent load limit breached: {response_data['detailedMessage']}"
                                # Use much longer delay for concurrent limit errors - Neptune needs time to process
                                wait_time = self.config.retry_delay * 10  # 20 seconds for limit=1 clusters
                                self.logger.info(f"Waiting {wait_time} seconds for Neptune to process current load...")
                                time.sleep(wait_time)
                                continue
                        
                        # Try different response structures
                        load_id = None
                        if 'payload' in response_data and 'loadId' in response_data['payload']:
                            load_id = response_data['payload']['loadId']
                        elif 'loadId' in response_data:
                            load_id = response_data['loadId']
                        elif 'status' in response_data and response_data['status'] == '200 OK':
                            # When queueRequest is FALSE, Neptune might return immediate success
                            load_id = 'IMMEDIATE_SUCCESS'
                        
                        if load_id:
                            self.logger.info(f"✓ Successfully submitted {file_key} with load ID: {load_id}")
                            return {
                                'file_key': file_key,
                                'load_id': load_id,
                                'status': 'SUBMITTED',
                                'size': file_info.get('size', 0),
                                'attempts': attempt + 1
                            }
                        else:
                            # Log the full response for debugging
                            self.logger.warning(f"Unexpected response structure for {file_key}: {response_data}")
                            raise ValueError(f"No load ID found in response: {response_data}")
                    except json.JSONDecodeError:
                        self.logger.error(f"Invalid JSON response for {file_key}: {result.stdout}")
                        raise ValueError(f"Invalid JSON response: {result.stdout[:200]}")
                else:
                    error_msg = result.stderr or result.stdout or "Unknown error"
                    self.logger.error(f"curl failed for {file_key} with return code {result.returncode}")
                    self.logger.error(f"stdout: {result.stdout}")
                    self.logger.error(f"stderr: {result.stderr}")
                    raise subprocess.CalledProcessError(result.returncode, ' '.join(curl_cmd), error_msg)
                    
            except subprocess.TimeoutExpired:
                last_exception = f"Timeout after {self.config.timeout} seconds"
                self.logger.warning(f"Timeout for {file_key} (attempt {attempt + 1})")
            except subprocess.CalledProcessError as e:
                last_exception = f"curl failed with return code {e.returncode}: {e.stderr}"
                self.logger.warning(f"curl failed for {file_key} (attempt {attempt + 1}): {e.stderr}")
            except Exception as e:
                last_exception = str(e)
                self.logger.warning(f"Error for {file_key} (attempt {attempt + 1}): {e}")
        
        # All retries failed
        self.logger.error(f"✗ Failed to submit {file_key} after {self.config.retry_attempts + 1} attempts: {last_exception}")
        return {
            'file_key': file_key,
            'load_id': 'FAILED',
            'status': f'FAILED: {last_exception}',
            'size': file_info.get('size', 0),
            'attempts': self.config.retry_attempts + 1
        }
    
    def check_load_status(self, load_id: str) -> str:
        """Check the status of a load job."""
        try:
            curl_cmd = [
                'curl', '-X', 'GET',
                f'{self.config.endpoint}/loader/{load_id}',
                '--connect-timeout', str(self.config.connect_timeout),
                '--max-time', str(self.config.timeout),
                '-k',  # Disable SSL verification for localhost
                '-s'   # Silent mode
            ]
            
            result = subprocess.run(
                curl_cmd,
                shell=False,
                capture_output=True,
                text=True,
                timeout=self.config.timeout
            )
            
            if result.returncode == 0:
                try:
                    response_data = json.loads(result.stdout)
                    return response_data.get('payload', {}).get('overallStatus', {}).get('status', 'UNKNOWN')
                except json.JSONDecodeError:
                    return 'UNKNOWN'
            else:
                return 'UNKNOWN'
                
        except Exception as e:
            self.logger.warning(f"Error checking load status for {load_id}: {e}")
            return 'UNKNOWN'
    
    def wait_for_load_completion(self, load_id: str, max_wait_time: int = 300) -> bool:
        """Wait for a load job to complete."""
        start_time = time.time()
        while time.time() - start_time < max_wait_time:
            status = self.check_load_status(load_id)
            if status in ['LOAD_COMPLETED', 'LOAD_FAILED', 'LOAD_CANCELLED']:
                self.logger.info(f"Load {load_id} completed with status: {status}")
                return status == 'LOAD_COMPLETED'
            elif status == 'LOAD_IN_PROGRESS':
                self.logger.debug(f"Load {load_id} still in progress...")
                time.sleep(5)  # Wait 5 seconds before checking again
            else:
                self.logger.debug(f"Load {load_id} status: {status}")
                time.sleep(5)
        
        self.logger.warning(f"Timeout waiting for load {load_id} to complete")
        return False
    
    def submit_jobs_sequential(self, files: List[Dict], job_type: str) -> List[Dict]:
        """Submit jobs sequentially to respect Neptune's concurrent load limits."""
        if not files:
            return []
        
        self.logger.info(f"Starting sequential submission of {len(files)} {job_type} files")
        print(f"Submitting {len(files)} {job_type} files sequentially (respecting Neptune's concurrent load limit)...")
        
        job_results = []
        completed = 0
        
        # Sort files by size (largest first) for better resource utilization
        sorted_files = sorted(files, key=lambda x: x.get('size', 0), reverse=True)
        
        for file_info in sorted_files:
            try:
                result = self.execute_curl_command(file_info)
                job_results.append(result)
                completed += 1
                print_progress(completed, len(files), f"  {job_type} Progress")
                
                # For Neptune clusters with concurrent load limit=1, wait for completion
                if self.config.wait_for_completion and result['status'] == 'SUBMITTED' and result['load_id'] != 'IMMEDIATE_SUCCESS':
                    self.logger.info(f"Waiting for load {result['load_id']} to complete before next submission...")
                    success = self.wait_for_load_completion(result['load_id'])
                    if not success:
                        self.logger.warning(f"Load {result['load_id']} may not have completed successfully")
                else:
                    # If not waiting for completion or immediate success/failed, add a small delay
                    file_size_mb = file_info.get('size', 0) / (1024 * 1024)
                    if file_size_mb > 100:  # Large files
                        delay = 3.0  # 3 seconds for large files
                    elif file_size_mb > 10:  # Medium files
                        delay = 2.0  # 2 seconds for medium files
                    else:  # Small files
                        delay = 1.0  # 1 second for small files
                    
                    self.logger.info(f"Waiting {delay} seconds before next submission (file size: {file_size_mb:.1f} MB)")
                    time.sleep(delay)
                
            except Exception as e:
                self.logger.error(f"Error processing file {file_info['key']}: {e}")
                job_results.append({
                    'file_key': file_info['key'],
                    'load_id': 'FAILED',
                    'status': f'PROCESSING_ERROR: {str(e)}',
                    'size': file_info.get('size', 0),
                    'attempts': 0
                })
        
        print()  # New line after progress bar
        self.logger.info(f"✓ Completed sequential submission of {len(job_results)} {job_type} jobs")
        return job_results
    
    def submit_jobs_concurrent(self, files: List[Dict], job_type: str) -> List[Dict]:
        """Submit jobs concurrently with progress tracking."""
        if not files:
            return []
        
        self.logger.info(f"Starting concurrent submission of {len(files)} {job_type} files")
        print(f"Submitting {len(files)} {job_type} files using {self.config.max_workers} workers...")
        
        job_results = []
        completed = 0
        
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            # Submit all jobs
            future_to_file = {
                executor.submit(self.execute_curl_command, file_info): file_info 
                for file_info in files
            }
            
            # Process completed jobs
            for future in as_completed(future_to_file):
                try:
                    result = future.result()
                    job_results.append(result)
                    completed += 1
                    print_progress(completed, len(files), f"  {job_type} Progress")
                except Exception as e:
                    self.logger.error(f"Error processing future result: {e}")
                    job_results.append({
                        'file_key': 'UNKNOWN',
                        'load_id': 'FAILED',
                        'status': f'FUTURE_ERROR: {str(e)}',
                        'size': 0,
                        'attempts': 0
                    })
        
        print()  # New line after progress bar
        self.logger.info(f"✓ Completed concurrent submission of {len(job_results)} {job_type} jobs")
        return job_results
    
    def load_all_files(self) -> Dict:
        """Load all files from S3 bucket into Neptune - nodes first, then edges."""
        start_time = datetime.now()
        self.logger.info(f"Starting load_all_files for bucket: {self.config.s3_bucket}")
        
        try:
            # Get list of files separated into nodes and edges
            self.logger.info("Retrieving file list from S3...")
            node_files, edge_files = self.get_files_from_s3()
            
            if not node_files and not edge_files:
                self.logger.warning("No files to load")
                return {
                    'total_files': 0,
                    'submitted': 0,
                    'failed': 0,
                    'duration': datetime.now() - start_time
                }
                
            total_files = len(node_files) + len(edge_files)
            total_size = sum(f.get('size', 0) for f in node_files + edge_files)
            total_size_gb = total_size / (1024*1024*1024)
            
            self.logger.info(f"Processing {total_files} files with total size {total_size_gb:.2f} GB")
            print(f"Found {len(node_files)} node files and {len(edge_files)} edge files to submit")
            print(f"Total data size: {total_size_gb:.2f} GB")
            print(f"Using {self.config.max_workers} concurrent workers for job submission")
            
            job_results = []
            
            # Load nodes first
            if node_files:
                self.logger.info(f"Starting node file submission for {len(node_files)} files...")
                if self.config.use_sequential:
                    node_results = self.submit_jobs_sequential(node_files, "NODE")
                else:
                    node_results = self.submit_jobs_concurrent(node_files, "NODE")
                job_results.extend(node_results)
                self.logger.info(f"✓ Completed node file submission, {len(node_results)} results")
            
            # Load edges second
            if edge_files:
                self.logger.info(f"Starting edge file submission for {len(edge_files)} files...")
                if self.config.use_sequential:
                    edge_results = self.submit_jobs_sequential(edge_files, "EDGE")
                else:
                    edge_results = self.submit_jobs_concurrent(edge_files, "EDGE")
                job_results.extend(edge_results)
                self.logger.info(f"✓ Completed edge file submission, {len(edge_results)} results")
            
            # Print summary
            self._print_job_report(job_results, node_files, edge_files, total_files, total_size, start_time)
            
            return {
                'total_files': total_files,
                'submitted': len([r for r in job_results if r['status'] == 'SUBMITTED']),
                'failed': len([r for r in job_results if r['status'] != 'SUBMITTED']),
                'duration': datetime.now() - start_time,
                'results': job_results
            }
            
        except Exception as e:
            self.logger.error(f"Error in load_all_files: {str(e)}")
            self.logger.debug(f"Error details: {traceback.format_exc()}")
            raise
    
    def _print_job_report(self, job_results: List[Dict], node_files: List[Dict], 
                         edge_files: List[Dict], total_files: int, total_size: int, start_time: datetime):
        """Print a detailed job report."""
        duration = datetime.now() - start_time
        total_size_gb = total_size / (1024*1024*1024)
        
        successful = [r for r in job_results if r['status'] == 'SUBMITTED']
        failed = [r for r in job_results if r['status'] != 'SUBMITTED']
        
        print_header("Neptune Bulk Load Summary")
        print(f"{Fore.CYAN}Total Files:{Style.RESET_ALL} {total_files}")
        print(f"{Fore.CYAN}Total Size:{Style.RESET_ALL} {total_size_gb:.2f} GB")
        print(f"{Fore.CYAN}Node Files:{Style.RESET_ALL} {len(node_files)}")
        print(f"{Fore.CYAN}Edge Files:{Style.RESET_ALL} {len(edge_files)}")
        print(f"{Fore.CYAN}Successful:{Style.RESET_ALL} {len(successful)}")
        print(f"{Fore.CYAN}Failed:{Style.RESET_ALL} {len(failed)}")
        print(f"{Fore.CYAN}Duration:{Style.RESET_ALL} {duration}")
        print(f"{Fore.CYAN}Success Rate:{Style.RESET_ALL} {(len(successful)/total_files*100):.1f}%")
        
        if failed:
            print(f"\n{Fore.RED}Failed Files:{Style.RESET_ALL}")
            for result in failed:
                print(f"  - {result['file_key']}: {result['status']}")
        
        if successful:
            print(f"\n{Fore.GREEN}Successful Files:{Style.RESET_ALL}")
            for result in successful[:10]:  # Show first 10
                print(f"  - {result['file_key']}: {result['load_id']}")
            if len(successful) > 10:
                print(f"  ... and {len(successful) - 10} more")

def main():
    """Main function to run the Neptune curl bulk loader."""
    print_header("Neptune Curl Bulk Loader - HIGH PERFORMANCE MODE")
    
    # Check for test mode
    test_file = os.getenv('NEPTUNE_TEST_FILE')
    
    # Check for performance mode
    performance_mode = os.getenv('NEPTUNE_PERFORMANCE_MODE', 'false').lower() == 'true'
    ultra_mode = os.getenv('NEPTUNE_ULTRA_MODE', 'false').lower() == 'true'
    
    try:
        # Load configuration from environment variables - Always use high performance
        if ultra_mode:
            print(f"{Fore.RED}Ultra Performance Mode: Using maximum performance configuration{Style.RESET_ALL}")
            print(f"{Fore.RED}⚠️  Only use this for Neptune clusters with concurrent load limit > 5{Style.RESET_ALL}")
            config = NeptuneConfig.ultra_performance()
        else:
            print(f"{Fore.GREEN}HIGH PERFORMANCE MODE: Using optimized high-performance configuration{Style.RESET_ALL}")
            config = NeptuneConfig.high_performance()
        
        if not config.iam_role_arn:
            print(f"{Fore.RED}Error: NEPTUNE_IAM_ROLE_ARN environment variable is required{Style.RESET_ALL}")
            print("Example: export NEPTUNE_IAM_ROLE_ARN='arn:aws:iam::123456789012:role/NeptuneLoadFromS3'")
            sys.exit(1)
        
        # Print configuration summary
        print(f"{Fore.CYAN}Neptune Endpoint:{Style.RESET_ALL} {config.endpoint}")
        print(f"{Fore.CYAN}AWS Region:{Style.RESET_ALL} {config.region}")
        print(f"{Fore.CYAN}S3 Bucket:{Style.RESET_ALL} {config.s3_bucket}")
        print()
        
        # Print performance information
        config.print_performance_info()
        print()
        
        # Create bulk loader and execute
        loader = NeptuneCurlBulkLoader(config)
        
        # Test mode - test a single file
        if test_file:
            print(f"{Fore.CYAN}Test Mode: Testing single file {test_file}{Style.RESET_ALL}")
            test_result = loader.test_single_file(test_file)
            if test_result['success']:
                print(f"{Fore.GREEN}✓ Test successful!{Style.RESET_ALL}")
                print(f"Response: {test_result['response']}")
                sys.exit(0)
            else:
                print(f"{Fore.RED}✗ Test failed: {test_result['error']}{Style.RESET_ALL}")
                sys.exit(1)
        
        # Normal mode - load all files
        result = loader.load_all_files()
        
        # Exit with appropriate code
        if result['failed'] > 0:
            print(f"\n{Fore.YELLOW}Warning: {result['failed']} files failed to load{Style.RESET_ALL}")
            sys.exit(1)
        else:
            print(f"\n{Fore.GREEN}✓ All files loaded successfully!{Style.RESET_ALL}")
            sys.exit(0)
            
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Operation cancelled by user{Style.RESET_ALL}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Fore.RED}Error: {str(e)}{Style.RESET_ALL}")
        if os.getenv('NEPTUNE_DEBUG', 'false').lower() == 'true':
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 