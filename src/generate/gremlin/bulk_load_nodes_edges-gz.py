#!/usr/bin/env python3
"""
Neptune Bulk Loader - Concurrent Load Manager

This script intelligently manages concurrent loads for Neptune clusters by:
1. Detecting the cluster's concurrent load limit
2. Automatically managing job queues to respect limits
3. Providing intelligent retry logic for concurrent limit errors
4. Optimizing load order and timing

Features:
- Automatic concurrent load limit detection
- Smart queue management with load balancing
- Intelligent retry logic with backoff
- Real-time load status monitoring
- Optimized file ordering by size and type
- Comprehensive error handling and recovery
- Support for both CSV and GZ (gzipped CSV) files

Environment Variables:
- NEPTUNE_ENDPOINT: Neptune cluster endpoint (default: https://localhost:8182)
- NEPTUNE_IAM_ROLE_ARN: IAM role ARN for S3 access (required)
- AWS_REGION: AWS region (default: us-east-1)
- S3_BUCKET: S3 bucket name (default: deam-neptune)
- S3_PREFIX: S3 prefix/subdirectory to load files from (default: root of bucket)
- S3_EXCLUDE_PATTERNS: Comma-separated patterns to exclude (default: archive/,backup/,old/,temp/,tmp/)
- NEPTUNE_CONCURRENT_LIMIT: Override detected concurrent limit (default: auto-detect)
- NEPTUNE_QUEUE_WAIT_TIME: Time to wait between queue checks in seconds (default: 5)
- NEPTUNE_MAX_RETRY_ATTEMPTS: Maximum retry attempts for failed loads (default: 2)
- NEPTUNE_BACKOFF_MULTIPLIER: Exponential backoff multiplier (default: 1.5)
- NEPTUNE_INITIAL_BACKOFF: Initial backoff time in seconds (default: 15)
- NEPTUNE_MAX_BACKOFF: Maximum backoff time in seconds (default: 120)
- NEPTUNE_HEALTH_CHECK_INTERVAL: Health check interval in seconds (default: 15)
- NEPTUNE_DEBUG: Enable debug logging (default: false)

Performance Modes:
- NEPTUNE_PERFORMANCE_MODE=true: Enable high-performance mode (faster retries, shorter waits)
- NEPTUNE_ULTRA_MODE=true: Enable ultra-performance mode (maximum speed, use with caution)
"""

import boto3
import subprocess
import json
import logging
import os
import sys
import time
import threading
from typing import Dict, List, Tuple, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
import traceback
from colorama import init, Fore, Style
from queue import Queue, Empty
from enum import Enum
import random

# Initialize colorama for colored output
init()

class LoadStatus(Enum):
    """Load job status enumeration."""
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    IN_PROGRESS = "LOAD_IN_PROGRESS"
    COMPLETED = "LOAD_COMPLETED"
    FAILED = "LOAD_FAILED"
    CANCELLED = "LOAD_CANCELLED"
    RETRY_REQUIRED = "RETRY_REQUIRED"
    CONCURRENT_LIMIT_EXCEEDED = "CONCURRENT_LIMIT_EXCEEDED"

@dataclass
class LoadJob:
    """Represents a single load job."""
    file_info: Dict
    file_key: str
    source: str
    size: int
    job_type: str  # 'NODE' or 'EDGE'
    status: LoadStatus = LoadStatus.PENDING
    load_id: Optional[str] = None
    submission_time: Optional[datetime] = None
    completion_time: Optional[datetime] = None
    retry_count: int = 0
    last_error: Optional[str] = None
    priority: int = 0  # Higher priority = processed first
    
    def __post_init__(self):
        """Calculate priority based on file characteristics."""
        # Prioritize smaller files and nodes over edges
        size_priority = max(0, 100 - (self.size // (1024 * 1024)))  # Smaller files first
        type_priority = 50 if self.job_type == 'NODE' else 0  # Nodes first
        self.priority = size_priority + type_priority

@dataclass
class ConcurrentLoadConfig:
    """Configuration for concurrent load management."""
    endpoint: str = "https://localhost:8182"
    iam_role_arn: str = ""
    region: str = "us-east-1"
    s3_bucket: str = "deam-neptune"
    s3_prefix: str = ""
    s3_exclude_patterns: str = "archive/,backup/,old/,temp/,tmp/"
    
    # Concurrent load management
    concurrent_limit: Optional[int] = None  # Auto-detect if None
    queue_wait_time: int = 5  # Reduced from 10 for faster processing
    max_retry_attempts: int = 2  # Reduced from 3 for faster retries
    backoff_multiplier: float = 1.5  # Reduced from 2.0 for faster recovery
    initial_backoff: int = 15  # Reduced from 30 for faster retries
    max_backoff: int = 120  # Reduced from 300 for faster recovery
    health_check_interval: int = 15  # Reduced from 30 for faster monitoring
    
    # Neptune settings - Optimized for maximum performance
    parallelism: str = "OVERSUBSCRIBE"  # Maximum throughput
    fail_on_error: bool = False  # Continue on errors
    queue_request: bool = False  # Immediate submission
    timeout: int = 3600  # Increased from 1800 for very large files
    connect_timeout: int = 30  # Reduced from 60 for faster connections
    debug_mode: bool = False
    
    @classmethod
    def from_env(cls) -> 'ConcurrentLoadConfig':
        """Create configuration from environment variables."""
        concurrent_limit = os.getenv('NEPTUNE_CONCURRENT_LIMIT')
        if concurrent_limit:
            concurrent_limit = int(concurrent_limit)
            
        return cls(
            endpoint=os.getenv('NEPTUNE_ENDPOINT', cls.endpoint),
            iam_role_arn=os.getenv('NEPTUNE_IAM_ROLE_ARN', cls.iam_role_arn),
            region=os.getenv('AWS_REGION', cls.region),
            s3_bucket=os.getenv('S3_BUCKET', cls.s3_bucket),
            s3_prefix=os.getenv('S3_PREFIX', cls.s3_prefix),
            s3_exclude_patterns=os.getenv('S3_EXCLUDE_PATTERNS', cls.s3_exclude_patterns),
            concurrent_limit=concurrent_limit,
            queue_wait_time=int(os.getenv('NEPTUNE_QUEUE_WAIT_TIME', cls.queue_wait_time)),
            max_retry_attempts=int(os.getenv('NEPTUNE_MAX_RETRY_ATTEMPTS', cls.max_retry_attempts)),
            backoff_multiplier=float(os.getenv('NEPTUNE_BACKOFF_MULTIPLIER', cls.backoff_multiplier)),
            initial_backoff=int(os.getenv('NEPTUNE_INITIAL_BACKOFF', cls.initial_backoff)),
            max_backoff=int(os.getenv('NEPTUNE_MAX_BACKOFF', cls.max_backoff)),
            health_check_interval=int(os.getenv('NEPTUNE_HEALTH_CHECK_INTERVAL', cls.health_check_interval)),
            parallelism=os.getenv('NEPTUNE_PARALLELISM', cls.parallelism),
            fail_on_error=os.getenv('NEPTUNE_FAIL_ON_ERROR', 'false').lower() == 'true',
            queue_request=os.getenv('NEPTUNE_QUEUE_REQUEST', 'false').lower() == 'true',
            timeout=int(os.getenv('NEPTUNE_TIMEOUT', cls.timeout)),
            connect_timeout=int(os.getenv('NEPTUNE_CONNECT_TIMEOUT', cls.connect_timeout)),
            debug_mode=os.getenv('NEPTUNE_DEBUG', 'false').lower() == 'true'
        )
    
    @classmethod
    def high_performance(cls) -> 'ConcurrentLoadConfig':
        """Create a high-performance configuration optimized for speed."""
        config = cls()
        # Override with high-performance settings
        config.queue_wait_time = 2  # Very fast queue processing
        config.max_retry_attempts = 1  # Minimal retries for speed
        config.backoff_multiplier = 1.2  # Fast recovery
        config.initial_backoff = 5  # Quick retries
        config.max_backoff = 30  # Fast max backoff
        config.health_check_interval = 10  # Frequent monitoring
        config.timeout = 7200  # 2 hours for very large files
        config.connect_timeout = 15  # Fast connections
        return config
    
    @classmethod
    def ultra_performance(cls) -> 'ConcurrentLoadConfig':
        """Create an ultra-performance configuration for maximum speed (use with caution)."""
        config = cls()
        # Override with ultra-performance settings
        config.queue_wait_time = 1  # Minimal wait time
        config.max_retry_attempts = 1  # Single retry attempt
        config.backoff_multiplier = 1.1  # Very fast recovery
        config.initial_backoff = 2  # Immediate retries
        config.max_backoff = 10  # Very fast max backoff
        config.health_check_interval = 5  # Very frequent monitoring
        config.timeout = 10800  # 3 hours for massive files
        config.connect_timeout = 10  # Very fast connections
        return config
    
    def validate(self) -> None:
        """Validate configuration."""
        if not self.iam_role_arn:
            raise ValueError("IAM role ARN is required. Set NEPTUNE_IAM_ROLE_ARN environment variable.")
        if not self.endpoint:
            raise ValueError("Neptune endpoint is required.")
        if not self.s3_bucket:
            raise ValueError("S3 bucket is required.")

class ConcurrentLoadManager:
    """Manages concurrent loads for Neptune with intelligent queue management."""
    
    def __init__(self, config: ConcurrentLoadConfig):
        self.config = config
        self.config.validate()
        self.logger = self._setup_logging()
        
        # Concurrent load management
        self.concurrent_limit = config.concurrent_limit
        self.active_loads: Dict[str, LoadJob] = {}  # load_id -> LoadJob
        self.pending_queue = Queue()
        self.retry_queue = Queue()
        self.completed_jobs: List[LoadJob] = []
        self.failed_jobs: List[LoadJob] = []
        
        # Thread management
        self.load_monitor_thread = None
        self.queue_processor_thread = None
        self.shutdown_event = threading.Event()
        
        # Statistics
        self.stats = {
            'total_jobs': 0,
            'submitted': 0,
            'completed': 0,
            'failed': 0,
            'retries': 0,
            'concurrent_limit_hits': 0
        }
        
        try:
            self.s3_client = boto3.client('s3')
            self.logger.info("✓ S3 client initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize S3 client: {e}")
            raise
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        level = logging.DEBUG if self.config.debug_mode else logging.INFO
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        return logging.getLogger(__name__)
    
    def detect_concurrent_limit(self) -> int:
        """Detect Neptune cluster's concurrent load limit by testing."""
        if self.concurrent_limit:
            self.logger.info(f"Using configured concurrent limit: {self.concurrent_limit}")
            return self.concurrent_limit
        
        self.logger.info("Auto-detecting Neptune concurrent load limit...")
        
        # Try to get current active loads to understand the limit
        try:
            active_loads = self._get_active_loads()
            self.logger.info(f"Found {len(active_loads)} currently active loads")
            
            # If there are already active loads, assume limit is at least that number + 1
            if active_loads:
                detected_limit = len(active_loads) + 1
                self.logger.info(f"Detected minimum concurrent limit: {detected_limit}")
            else:
                # Default to 1 for safety - most Neptune clusters have limit=1
                detected_limit = 1
                self.logger.info("No active loads found, defaulting to concurrent limit of 1")
            
            self.concurrent_limit = detected_limit
            return detected_limit
            
        except Exception as e:
            self.logger.warning(f"Could not detect concurrent limit: {e}")
            self.logger.info("Defaulting to concurrent limit of 1 for safety")
            self.concurrent_limit = 1
            return 1
    
    def _get_active_loads(self) -> List[Dict]:
        """Get list of currently active loads."""
        try:
            curl_cmd = [
                'curl', '-X', 'GET',
                f'{self.config.endpoint}/loader',
                '--connect-timeout', str(self.config.connect_timeout),
                '--max-time', str(self.config.timeout),
                '-k', '-s'
            ]
            
            result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=self.config.timeout)
            
            if result.returncode == 0:
                response_data = json.loads(result.stdout)
                # Handle different response formats
                if 'payload' in response_data:
                    loads = response_data['payload'].get('loadIds', [])
                else:
                    loads = response_data.get('loadIds', [])
                
                # Filter for active loads
                active_loads = []
                for load_info in loads:
                    if isinstance(load_info, dict):
                        status = load_info.get('status', '')
                        if status in ['LOAD_IN_PROGRESS', 'LOAD_QUEUED']:
                            active_loads.append(load_info)
                
                return active_loads
            
        except Exception as e:
            self.logger.debug(f"Error getting active loads: {e}")
        
        return []
    
    def get_files_from_s3(self) -> Tuple[List[Dict], List[Dict]]:
        """Get list of CSV and GZ files from S3 bucket, separated into nodes and edges.
        
        Note: Neptune bulk loader automatically detects compression from file extensions.
        Both .csv and .gz files use the 'csv' format parameter.
        """
        try:
            if self.config.s3_prefix:
                location = f"s3://{self.config.s3_bucket}/{self.config.s3_prefix}"
                response = self.s3_client.list_objects_v2(
                    Bucket=self.config.s3_bucket, 
                    Prefix=self.config.s3_prefix
                )
            else:
                location = f"s3://{self.config.s3_bucket}"
                response = self.s3_client.list_objects_v2(Bucket=self.config.s3_bucket)
            
            if 'Contents' not in response:
                self.logger.warning(f"No files found in {location}")
                return [], []
            
            node_files = []
            edge_files = []
            exclude_patterns = [p.strip() for p in self.config.s3_exclude_patterns.split(',') if p.strip()]
            
            for obj in response['Contents']:
                file_key = obj['Key']
                
                # Skip non-CSV and non-GZ files
                if not (file_key.lower().endswith('.csv') or file_key.lower().endswith('.gz')):
                    continue
                
                # Skip excluded files
                if any(pattern in file_key.lower() for pattern in exclude_patterns):
                    continue
                
                # Determine file format based on extension
                # Neptune bulk loader uses 'csv' format for both .csv and .gz files
                # The compression is automatically detected from the file extension
                format_type = 'csv'
                
                file_info = {
                    'source': f"s3://{self.config.s3_bucket}/{file_key}",
                    'format': format_type,
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'],
                    'key': file_key
                }
                
                # Categorize files as nodes or edges
                if self._is_edge_file(file_key):
                    edge_files.append(file_info)
                else:
                    node_files.append(file_info)
            
            self.logger.info(f"Found {len(node_files)} node files and {len(edge_files)} edge files")
            return node_files, edge_files
            
        except Exception as e:
            self.logger.error(f"Error listing S3 files: {e}")
            raise
    
    def _is_edge_file(self, file_key: str) -> bool:
        """Determine if a file is an edge file based on filename patterns.
        
        Works with both .csv and .gz files - the pattern matching is done on the base filename
        before the extension is considered.
        """
        edge_patterns = [
            'edge', 'relationship', 'link', 'connection',
            'person_address', 'person_organization', 'person_email',
            'person_phone', 'person_form', 'person_name',
            'organization_address', 'building_address'
        ]
        return any(pattern in file_key.lower() for pattern in edge_patterns)
    
    def create_load_jobs(self, node_files: List[Dict], edge_files: List[Dict]) -> List[LoadJob]:
        """Create LoadJob objects from file lists."""
        jobs = []
        
        # Create node jobs
        for file_info in node_files:
            job = LoadJob(
                file_info=file_info,
                file_key=file_info['key'],
                source=file_info['source'],
                size=file_info['size'],
                job_type='NODE'
            )
            jobs.append(job)
        
        # Create edge jobs
        for file_info in edge_files:
            job = LoadJob(
                file_info=file_info,
                file_key=file_info['key'],
                source=file_info['source'],
                size=file_info['size'],
                job_type='EDGE'
            )
            jobs.append(job)
        
        # Sort by priority (nodes first, then by size)
        jobs.sort(key=lambda x: (-x.priority, x.size))
        
        self.logger.info(f"Created {len(jobs)} load jobs")
        return jobs
    
    def build_curl_command(self, job: LoadJob) -> List[str]:
        """Build curl command for a load job."""
        payload = {
            "source": job.source,
            "format": job.file_info['format'],  # Use the format from file_info (csv or csv-gzip)
            "iamRoleArn": self.config.iam_role_arn,
            "region": self.config.region,
            "failOnError": "TRUE" if self.config.fail_on_error else "FALSE",
            "parallelism": self.config.parallelism,
            "updateSingleCardinalityProperties": "FALSE"
        }
        
        if not self.config.queue_request:
            payload["queueRequest"] = "FALSE"
        
        curl_cmd = [
            'curl', '-X', 'POST',
            f'{self.config.endpoint}/loader',
            '-H', 'Content-Type: application/json',
            '--connect-timeout', str(self.config.connect_timeout),
            '--max-time', str(self.config.timeout),
            '-k', '-s',
            '-d', json.dumps(payload)
        ]
        
        return curl_cmd
    
    def submit_load_job(self, job: LoadJob) -> bool:
        """Submit a single load job."""
        try:
            curl_cmd = self.build_curl_command(job)
            
            result = subprocess.run(
                curl_cmd,
                capture_output=True,
                text=True,
                timeout=self.config.timeout
            )
            
            if result.returncode == 0:
                response_data = json.loads(result.stdout)
                
                # Check for concurrent load limit error
                if 'code' in response_data and response_data['code'] == 'BadRequestException':
                    if 'Max concurrent load limit breached' in response_data.get('detailedMessage', ''):
                        job.status = LoadStatus.CONCURRENT_LIMIT_EXCEEDED
                        job.last_error = response_data['detailedMessage']
                        self.stats['concurrent_limit_hits'] += 1
                        self.logger.debug(f"Concurrent limit hit for {job.file_key}")
                        return False
                
                # Extract load ID
                load_id = None
                if 'payload' in response_data and 'loadId' in response_data['payload']:
                    load_id = response_data['payload']['loadId']
                elif 'loadId' in response_data:
                    load_id = response_data['loadId']
                
                if load_id:
                    job.load_id = load_id
                    job.status = LoadStatus.SUBMITTED
                    job.submission_time = datetime.now()
                    self.active_loads[load_id] = job
                    self.stats['submitted'] += 1
                    self.logger.info(f"✓ Submitted {job.file_key} with load ID: {load_id}")
                    return True
                else:
                    job.status = LoadStatus.FAILED
                    job.last_error = f"No load ID in response: {response_data}"
                    return False
            else:
                job.status = LoadStatus.FAILED
                job.last_error = f"curl failed: {result.stderr}"
                return False
                
        except Exception as e:
            job.status = LoadStatus.FAILED
            job.last_error = str(e)
            self.logger.error(f"Error submitting {job.file_key}: {e}")
            return False
    
    def check_load_status(self, load_id: str) -> str:
        """Check the status of a specific load."""
        try:
            curl_cmd = [
                'curl', '-X', 'GET',
                f'{self.config.endpoint}/loader/{load_id}',
                '--connect-timeout', str(self.config.connect_timeout),
                '--max-time', str(self.config.timeout),
                '-k', '-s'
            ]
            
            result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                response_data = json.loads(result.stdout)
                return response_data.get('payload', {}).get('overallStatus', {}).get('status', 'UNKNOWN')
            
        except Exception as e:
            self.logger.debug(f"Error checking status for {load_id}: {e}")
        
        return 'UNKNOWN'
    
    def monitor_active_loads(self):
        """Monitor active loads and update their status."""
        while not self.shutdown_event.is_set():
            try:
                current_time = datetime.now()
                completed_load_ids = []
                
                for load_id, job in self.active_loads.items():
                    status = self.check_load_status(load_id)
                    
                    if status == 'LOAD_COMPLETED':
                        job.status = LoadStatus.COMPLETED
                        job.completion_time = current_time
                        self.completed_jobs.append(job)
                        completed_load_ids.append(load_id)
                        self.stats['completed'] += 1
                        self.logger.info(f"✓ Completed: {job.file_key}")
                        
                    elif status in ['LOAD_FAILED', 'LOAD_CANCELLED']:
                        job.status = LoadStatus.FAILED
                        job.completion_time = current_time
                        job.last_error = f"Load {status.lower()}"
                        
                        # Retry if attempts remaining
                        if job.retry_count < self.config.max_retry_attempts:
                            job.status = LoadStatus.RETRY_REQUIRED
                            self.retry_queue.put(job)
                            self.logger.info(f"⚠️ Scheduling retry for {job.file_key} (attempt {job.retry_count + 1})")
                        else:
                            self.failed_jobs.append(job)
                            self.stats['failed'] += 1
                            self.logger.error(f"✗ Failed permanently: {job.file_key}")
                        
                        completed_load_ids.append(load_id)
                    
                    elif status == 'LOAD_IN_PROGRESS':
                        job.status = LoadStatus.IN_PROGRESS
                
                # Remove completed loads from active tracking
                for load_id in completed_load_ids:
                    del self.active_loads[load_id]
                
                # Sleep before next check
                self.shutdown_event.wait(self.config.health_check_interval)
                
            except Exception as e:
                self.logger.error(f"Error in load monitoring: {e}")
                self.shutdown_event.wait(5)
    
    def process_job_queue(self):
        """Process the job queue respecting concurrent limits."""
        while not self.shutdown_event.is_set():
            try:
                # Check if we can submit more jobs
                if len(self.active_loads) >= self.concurrent_limit:
                    self.logger.debug(f"At concurrent limit ({self.concurrent_limit}), waiting...")
                    self.shutdown_event.wait(self.config.queue_wait_time)
                    continue
                
                # Try to get a job from retry queue first
                job = None
                try:
                    job = self.retry_queue.get_nowait()
                    job.retry_count += 1
                    self.stats['retries'] += 1
                    
                    # Apply exponential backoff for retries
                    backoff_time = min(
                        self.config.initial_backoff * (self.config.backoff_multiplier ** (job.retry_count - 1)),
                        self.config.max_backoff
                    )
                    self.logger.info(f"Applying {backoff_time}s backoff for retry of {job.file_key}")
                    self.shutdown_event.wait(backoff_time)
                    
                except Empty:
                    # Try to get a job from pending queue
                    try:
                        job = self.pending_queue.get_nowait()
                    except Empty:
                        # No jobs available, wait and continue
                        self.shutdown_event.wait(self.config.queue_wait_time)
                        continue
                
                # Submit the job
                if job:
                    success = self.submit_load_job(job)
                    
                    if not success:
                        if job.status == LoadStatus.CONCURRENT_LIMIT_EXCEEDED:
                            # Put back in queue to try again later
                            self.pending_queue.put(job)
                            job.status = LoadStatus.PENDING
                            
                            # Wait a bit longer when hitting concurrent limits
                            wait_time = self.config.queue_wait_time * 2
                            self.logger.debug(f"Concurrent limit hit, waiting {wait_time}s before retry")
                            self.shutdown_event.wait(wait_time)
                        else:
                            # Other failure - schedule for retry if attempts remaining
                            if job.retry_count < self.config.max_retry_attempts:
                                job.status = LoadStatus.RETRY_REQUIRED
                                self.retry_queue.put(job)
                            else:
                                self.failed_jobs.append(job)
                                self.stats['failed'] += 1
                
            except Exception as e:
                self.logger.error(f"Error in queue processing: {e}")
                self.shutdown_event.wait(5)
    
    def load_all_files(self) -> Dict:
        """Load all files with intelligent concurrent management."""
        start_time = datetime.now()
        
        try:
            # Detect concurrent limit
            self.detect_concurrent_limit()
            
            # Get files and create jobs
            node_files, edge_files = self.get_files_from_s3()
            jobs = self.create_load_jobs(node_files, edge_files)
            
            if not jobs:
                self.logger.warning("No jobs to process")
                return self._create_result_summary(start_time)
            
            self.stats['total_jobs'] = len(jobs)
            
            # Add jobs to pending queue
            for job in jobs:
                self.pending_queue.put(job)
            
            self.logger.info(f"Starting concurrent load management for {len(jobs)} jobs")
            self.logger.info(f"Concurrent limit: {self.concurrent_limit}")
            
            # Start monitoring and processing threads
            self.load_monitor_thread = threading.Thread(target=self.monitor_active_loads, daemon=True)
            self.queue_processor_thread = threading.Thread(target=self.process_job_queue, daemon=True)
            
            self.load_monitor_thread.start()
            self.queue_processor_thread.start()
            
            # Wait for all jobs to complete
            self._wait_for_completion()
            
            # Shutdown threads
            self.shutdown_event.set()
            
            return self._create_result_summary(start_time)
            
        except Exception as e:
            self.logger.error(f"Error in load_all_files: {e}")
            self.shutdown_event.set()
            raise
    
    def _wait_for_completion(self):
        """Wait for all jobs to complete with progress reporting."""
        last_report_time = datetime.now()
        report_interval = 30  # Report progress every 30 seconds
        
        while True:
            # Check if all jobs are done
            total_processed = len(self.completed_jobs) + len(self.failed_jobs)
            
            if total_processed >= self.stats['total_jobs']:
                self.logger.info("All jobs completed!")
                break
            
            # Check if we should report progress
            current_time = datetime.now()
            if (current_time - last_report_time).seconds >= report_interval:
                self._report_progress()
                last_report_time = current_time
            
            # Wait before next check
            time.sleep(5)
    
    def _report_progress(self):
        """Report current progress."""
        total = self.stats['total_jobs']
        completed = len(self.completed_jobs)
        failed = len(self.failed_jobs)
        active = len(self.active_loads)
        pending = self.pending_queue.qsize()
        retry = self.retry_queue.qsize()
        
        progress = ((completed + failed) / total * 100) if total > 0 else 0
        
        self.logger.info(f"Progress: {progress:.1f}% | "
                        f"Completed: {completed} | Failed: {failed} | "
                        f"Active: {active} | Pending: {pending} | Retry: {retry}")
    
    def _create_result_summary(self, start_time: datetime) -> Dict:
        """Create a summary of the load operation."""
        duration = datetime.now() - start_time
        
        return {
            'total_jobs': self.stats['total_jobs'],
            'completed': len(self.completed_jobs),
            'failed': len(self.failed_jobs),
            'duration': duration,
            'stats': self.stats,
            'concurrent_limit': self.concurrent_limit
        }
    
    def print_final_report(self, result: Dict):
        """Print a comprehensive final report."""
        print(f"\n{Fore.BLUE}{'=' * 80}{Style.RESET_ALL}")
        print(f"{Fore.BLUE}{'Neptune Concurrent Load Report'.center(80)}{Style.RESET_ALL}")
        print(f"{Fore.BLUE}{'=' * 80}{Style.RESET_ALL}\n")
        
        print(f"{Fore.CYAN}Total Jobs:{Style.RESET_ALL} {result['total_jobs']}")
        print(f"{Fore.GREEN}Completed:{Style.RESET_ALL} {result['completed']}")
        print(f"{Fore.RED}Failed:{Style.RESET_ALL} {result['failed']}")
        print(f"{Fore.CYAN}Duration:{Style.RESET_ALL} {result['duration']}")
        print(f"{Fore.CYAN}Concurrent Limit:{Style.RESET_ALL} {result['concurrent_limit']}")
        print(f"{Fore.CYAN}Concurrent Limit Hits:{Style.RESET_ALL} {result['stats']['concurrent_limit_hits']}")
        print(f"{Fore.CYAN}Total Retries:{Style.RESET_ALL} {result['stats']['retries']}")
        
        success_rate = (result['completed'] / result['total_jobs'] * 100) if result['total_jobs'] > 0 else 0
        print(f"{Fore.CYAN}Success Rate:{Style.RESET_ALL} {success_rate:.1f}%")
        
        if self.failed_jobs:
            print(f"\n{Fore.RED}Failed Jobs:{Style.RESET_ALL}")
            for job in self.failed_jobs:
                print(f"  - {job.file_key}: {job.last_error}")

def main():
    """Main function."""
    print(f"{Fore.BLUE}{'=' * 80}{Style.RESET_ALL}")
    print(f"{Fore.BLUE}{'Neptune Concurrent Load Manager'.center(80)}{Style.RESET_ALL}")
    print(f"{Fore.BLUE}{'=' * 80}{Style.RESET_ALL}\n")
    
    try:
        # Check for performance mode flags
        performance_mode = os.getenv('NEPTUNE_PERFORMANCE_MODE', '').lower()
        ultra_mode = os.getenv('NEPTUNE_ULTRA_MODE', '').lower()
        
        # Load configuration based on performance mode
        if ultra_mode == 'true':
            print(f"{Fore.RED}🚀 ULTRA PERFORMANCE MODE ENABLED{Style.RESET_ALL}")
            config = ConcurrentLoadConfig.ultra_performance()
            print(f"{Fore.YELLOW}⚠️  Warning: This mode may overwhelm smaller Neptune clusters{Style.RESET_ALL}\n")
        elif performance_mode == 'true':
            print(f"{Fore.GREEN}⚡ HIGH PERFORMANCE MODE ENABLED{Style.RESET_ALL}\n")
            config = ConcurrentLoadConfig.high_performance()
        else:
            config = ConcurrentLoadConfig.from_env()
        
        if not config.iam_role_arn:
            print(f"{Fore.RED}Error: NEPTUNE_IAM_ROLE_ARN environment variable is required{Style.RESET_ALL}")
            print("Example: export NEPTUNE_IAM_ROLE_ARN='arn:aws:iam::123456789012:role/NeptuneLoadFromS3'")
            sys.exit(1)
        
        # Print configuration
        print(f"{Fore.CYAN}Configuration:{Style.RESET_ALL}")
        print(f"  Neptune Endpoint: {config.endpoint}")
        print(f"  AWS Region: {config.region}")
        print(f"  S3 Bucket: {config.s3_bucket}")
        if config.s3_prefix:
            print(f"  S3 Prefix: {config.s3_prefix}")
        print(f"  Concurrent Limit: {'Auto-detect' if config.concurrent_limit is None else config.concurrent_limit}")
        print(f"  Parallelism: {config.parallelism}")
        print(f"  Max Retry Attempts: {config.max_retry_attempts}")
        print(f"  Queue Wait Time: {config.queue_wait_time}s")
        print(f"  Timeout: {config.timeout}s")
        print(f"  Connect Timeout: {config.connect_timeout}s")
        print(f"  Fail on Error: {config.fail_on_error}")
        print(f"  Queue Request: {config.queue_request}")
        print()
        
        # Create and run concurrent load manager
        manager = ConcurrentLoadManager(config)
        result = manager.load_all_files()
        
        # Print final report
        manager.print_final_report(result)
        
        # Exit with appropriate code
        if result['failed'] > 0:
            print(f"\n{Fore.YELLOW}⚠️  {result['failed']} jobs failed. Check logs for details.{Style.RESET_ALL}")
            sys.exit(1)
        else:
            print(f"\n{Fore.GREEN}✅ All jobs completed successfully!{Style.RESET_ALL}")
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