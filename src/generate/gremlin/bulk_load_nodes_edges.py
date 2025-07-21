#!/usr/bin/env python3
"""
Neptune Bulk Loader - Simplified Concurrent Load Manager

This script manages concurrent loads for Neptune clusters with:
- Automatic concurrent load limit detection
- Smart queue management
- Retry logic for failed loads
- Progress monitoring

Environment Variables (set in .env file):
Required:
- NEPTUNE_IAM_ROLE_ARN: IAM role ARN for S3 access
- S3_BUCKET: S3 bucket name

Optional:
- NEPTUNE_ENDPOINT: Neptune cluster endpoint (default: https://localhost:8182)
- AWS_REGION: AWS region (default: us-east-1)
- S3_PREFIX: S3 prefix/subdirectory to load files from
- NEPTUNE_CONCURRENT_LIMIT: Override detected concurrent limit
- NEPTUNE_DEBUG: Enable debug logging (default: false)
"""

import boto3
import subprocess
import json
import logging
import os
import sys
import time
import threading
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass
from queue import Queue, Empty
from enum import Enum
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class LoadStatus(Enum):
    """Load job status enumeration."""
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    IN_PROGRESS = "LOAD_IN_PROGRESS"
    COMPLETED = "LOAD_COMPLETED"
    FAILED = "LOAD_FAILED"
    CANCELLED = "LOAD_CANCELLED"

@dataclass
class LoadJob:
    """Represents a single load job."""
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

@dataclass
class Config:
    """Configuration for Neptune bulk loader."""
    endpoint: str
    iam_role_arn: str
    region: str
    s3_bucket: str
    s3_prefix: str
    concurrent_limit: Optional[int]
    max_retries: int
    retry_delay: int
    check_interval: int
    debug: bool
    
    @classmethod
    def from_env(cls) -> 'Config':
        """Create configuration from environment variables."""
        concurrent_limit = os.getenv('NEPTUNE_CONCURRENT_LIMIT')
        if concurrent_limit:
            concurrent_limit = int(concurrent_limit)
            
        return cls(
            endpoint=os.getenv('NEPTUNE_ENDPOINT'),
            iam_role_arn=os.getenv('NEPTUNE_IAM_ROLE_ARN'),
            region=os.getenv('AWS_REGION'),
            s3_bucket=os.getenv('S3_BUCKET'),
            s3_prefix=os.getenv('S3_PREFIX'),
            concurrent_limit=concurrent_limit,
            max_retries=int(os.getenv('NEPTUNE_MAX_RETRIES') or '3'),
            retry_delay=int(os.getenv('NEPTUNE_RETRY_DELAY') or '30'),
            check_interval=int(os.getenv('NEPTUNE_CHECK_INTERVAL') or '15'),
            debug=(os.getenv('NEPTUNE_DEBUG') or 'false').lower() == 'true'
        )
    
    def validate(self) -> None:
        """Validate configuration."""
        if not self.iam_role_arn:
            raise ValueError("NEPTUNE_IAM_ROLE_ARN environment variable is required")
        if not self.s3_bucket:
            raise ValueError("S3_BUCKET environment variable is required")

class NeptuneBulkLoader:
    """Simplified Neptune bulk loader with concurrent load management."""
    
    def __init__(self, config: Config):
        self.config = config
        self.config.validate()
        self.logger = self._setup_logging()
        
        # Load management
        self.concurrent_limit = config.concurrent_limit or self._detect_concurrent_limit()
        self.active_loads: Dict[str, LoadJob] = {}
        self.pending_queue = Queue()
        self.completed_jobs: List[LoadJob] = []
        self.failed_jobs: List[LoadJob] = []
        
        # Thread management
        self.shutdown_event = threading.Event()
        self.monitor_thread = None
        
        # Statistics
        self.stats = {
            'total_jobs': 0,
            'submitted': 0,
            'completed': 0,
            'failed': 0,
            'retries': 0
        }
        
        # Initialize S3 client
        try:
            self.s3_client = boto3.client('s3')
            self.logger.info("S3 client initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize S3 client: {e}")
            raise
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        level = logging.DEBUG if self.config.debug else logging.INFO
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        return logging.getLogger(__name__)
    
    def _detect_concurrent_limit(self) -> int:
        """Detect Neptune cluster's concurrent load limit."""
        self.logger.info("Detecting Neptune concurrent load limit...")
        
        try:
            active_loads = self._get_active_loads()
            if active_loads:
                detected_limit = len(active_loads) + 2
                self.logger.info(f"Detected concurrent limit: {detected_limit}")
            else:
                detected_limit = 4  # Default for most Neptune clusters
                self.logger.info(f"Using default concurrent limit: {detected_limit}")
            
            return detected_limit
            
        except Exception as e:
            self.logger.warning(f"Could not detect concurrent limit: {e}")
            return 4  # Safe default
    
    def _get_active_loads(self) -> List[Dict]:
        """Get list of currently active loads."""
        try:
            curl_cmd = [
                'curl', '-X', 'GET',
                f'{self.config.endpoint}/loader',
                '--connect-timeout', '30',
                '--max-time', '60',
                '-k', '-s'
            ]
            
            result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                response_data = json.loads(result.stdout)
                loads = response_data.get('payload', {}).get('loadIds', [])
                
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
    
    def get_files_from_s3(self) -> tuple[List[Dict], List[Dict]]:
        """Get list of CSV files from S3 bucket, separated into nodes and edges."""
        try:
            if self.config.s3_prefix:
                response = self.s3_client.list_objects_v2(
                    Bucket=self.config.s3_bucket, 
                    Prefix=self.config.s3_prefix
                )
            else:
                response = self.s3_client.list_objects_v2(Bucket=self.config.s3_bucket)
            
            if 'Contents' not in response:
                self.logger.warning(f"No files found in s3://{self.config.s3_bucket}")
                return [], []
            
            node_files = []
            edge_files = []
            
            for obj in response['Contents']:
                file_key = obj['Key']
                
                # Skip non-CSV files
                if not file_key.lower().endswith('.csv'):
                    continue
                
                file_info = {
                    'source': f"s3://{self.config.s3_bucket}/{file_key}",
                    'format': 'csv',
                    'size': obj['Size'],
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
        """Determine if a file is an edge file based on filename patterns."""
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
        
        # Create node jobs first (prioritize nodes)
        for file_info in node_files:
            job = LoadJob(
                file_key=file_info['key'],
                source=file_info['source'],
                size=file_info['size'],
                job_type='NODE'
            )
            jobs.append(job)
        
        # Create edge jobs
        for file_info in edge_files:
            job = LoadJob(
                file_key=file_info['key'],
                source=file_info['source'],
                size=file_info['size'],
                job_type='EDGE'
            )
            jobs.append(job)
        
        # Sort by size (smaller files first)
        jobs.sort(key=lambda x: x.size)
        
        self.logger.info(f"Created {len(jobs)} load jobs")
        return jobs
    
    def submit_load_job(self, job: LoadJob) -> bool:
        """Submit a single load job."""
        try:
            payload = {
                "source": job.source,
                "format": "csv",
                "iamRoleArn": self.config.iam_role_arn,
                "region": self.config.region,
                "failOnError": "FALSE",
                "parallelism": "OVERSUBSCRIBE",
                "updateSingleCardinalityProperties": "FALSE"
            }
            
            curl_cmd = [
                'curl', '-X', 'POST',
                f'{self.config.endpoint}/loader',
                '-H', 'Content-Type: application/json',
                '--connect-timeout', '30',
                '--max-time', '60',
                '-k', '-s',
                '-d', json.dumps(payload)
            ]
            
            result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                response_data = json.loads(result.stdout)
                
                # Check for concurrent load limit error
                if 'code' in response_data and response_data['code'] == 'BadRequestException':
                    if 'Max concurrent load limit breached' in response_data.get('detailedMessage', ''):
                        job.last_error = response_data['detailedMessage']
                        return False
                
                # Extract load ID
                load_id = response_data.get('payload', {}).get('loadId') or response_data.get('loadId')
                
                if load_id:
                    job.load_id = load_id
                    job.status = LoadStatus.SUBMITTED
                    job.submission_time = datetime.now()
                    self.active_loads[load_id] = job
                    self.stats['submitted'] += 1
                    self.logger.info(f"Submitted {job.file_key} with load ID: {load_id}")
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
                '--connect-timeout', '30',
                '--max-time', '60',
                '-k', '-s'
            ]
            
            result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                response_data = json.loads(result.stdout)
                return response_data.get('payload', {}).get('overallStatus', {}).get('status', 'UNKNOWN')
            
        except Exception as e:
            self.logger.debug(f"Error checking status for {load_id}: {e}")
        
        return 'UNKNOWN'
    
    def monitor_loads(self):
        """Monitor active loads and update their status."""
        while not self.shutdown_event.is_set():
            try:
                completed_load_ids = []
                
                for load_id, job in self.active_loads.items():
                    status = self.check_load_status(load_id)
                    
                    if status == 'LOAD_COMPLETED':
                        job.status = LoadStatus.COMPLETED
                        job.completion_time = datetime.now()
                        self.completed_jobs.append(job)
                        completed_load_ids.append(load_id)
                        self.stats['completed'] += 1
                        self.logger.info(f"Completed: {job.file_key}")
                        
                    elif status in ['LOAD_FAILED', 'LOAD_CANCELLED']:
                        job.status = LoadStatus.FAILED
                        job.completion_time = datetime.now()
                        job.last_error = f"Load {status.lower()}"
                        
                        # Retry if attempts remaining
                        if job.retry_count < self.config.max_retries:
                            job.retry_count += 1
                            job.status = LoadStatus.PENDING
                            self.pending_queue.put(job)
                            self.stats['retries'] += 1
                            self.logger.info(f"Scheduling retry for {job.file_key} (attempt {job.retry_count})")
                        else:
                            self.failed_jobs.append(job)
                            self.stats['failed'] += 1
                            self.logger.error(f"Failed permanently: {job.file_key}")
                        
                        completed_load_ids.append(load_id)
                    
                    elif status == 'LOAD_IN_PROGRESS':
                        job.status = LoadStatus.IN_PROGRESS
                
                # Remove completed loads from active tracking
                for load_id in completed_load_ids:
                    del self.active_loads[load_id]
                
                # Sleep before next check
                self.shutdown_event.wait(self.config.check_interval)
                
            except Exception as e:
                self.logger.error(f"Error in load monitoring: {e}")
                self.shutdown_event.wait(5)
    
    def process_queue(self):
        """Process the job queue respecting concurrent limits."""
        while not self.shutdown_event.is_set():
            try:
                # Check if we can submit more jobs
                if len(self.active_loads) >= self.concurrent_limit:
                    self.shutdown_event.wait(5)
                    continue
                
                # Try to get a job from queue
                try:
                    job = self.pending_queue.get_nowait()
                except Empty:
                    self.shutdown_event.wait(5)
                    continue
                
                # Submit the job
                success = self.submit_load_job(job)
                
                if not success:
                    # Put back in queue to try again later
                    self.pending_queue.put(job)
                    time.sleep(self.config.retry_delay)
                
            except Exception as e:
                self.logger.error(f"Error in queue processing: {e}")
                self.shutdown_event.wait(5)
    
    def load_all_files(self) -> Dict:
        """Load all files with concurrent management."""
        start_time = datetime.now()
        
        try:
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
            
            # Start monitoring thread
            self.monitor_thread = threading.Thread(target=self.monitor_loads, daemon=True)
            self.monitor_thread.start()
            
            # Process queue in main thread
            self.process_queue()
            
            # Wait for monitoring thread to finish
            self.monitor_thread.join()
            
            return self._create_result_summary(start_time)
            
        except Exception as e:
            self.logger.error(f"Error in load_all_files: {e}")
            raise
    
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
    
    def print_report(self, result: Dict):
        """Print a final report."""
        print(f"\n{'=' * 60}")
        print(f"{'Neptune Bulk Load Report'.center(60)}")
        print(f"{'=' * 60}\n")
        
        print(f"Total Jobs: {result['total_jobs']}")
        print(f"Completed: {result['completed']}")
        print(f"Failed: {result['failed']}")
        print(f"Duration: {result['duration']}")
        print(f"Concurrent Limit: {result['concurrent_limit']}")
        print(f"Total Retries: {result['stats']['retries']}")
        
        success_rate = (result['completed'] / result['total_jobs'] * 100) if result['total_jobs'] > 0 else 0
        print(f"Success Rate: {success_rate:.1f}%")
        
        if self.failed_jobs:
            print(f"\nFailed Jobs:")
            for job in self.failed_jobs:
                print(f"  - {job.file_key}: {job.last_error}")

def main():
    """Main function."""
    print(f"{'=' * 60}")
    print(f"{'Neptune Bulk Loader'.center(60)}")
    print(f"{'=' * 60}\n")
    
    try:
        # Load configuration
        config = Config.from_env()
        
        if not config.iam_role_arn:
            print("Error: NEPTUNE_IAM_ROLE_ARN environment variable is required")
            print("Please set this in your .env file")
            sys.exit(1)
        
        if not config.s3_bucket:
            print("Error: S3_BUCKET environment variable is required")
            print("Please set this in your .env file")
            sys.exit(1)
        
        # Print configuration
        print("Configuration:")
        print(f"  Neptune Endpoint: {config.endpoint}")
        print(f"  AWS Region: {config.region}")
        print(f"  S3 Bucket: {config.s3_bucket}")
        if config.s3_prefix:
            print(f"  S3 Prefix: {config.s3_prefix}")
        print(f"  Concurrent Limit: {'Auto-detect' if config.concurrent_limit is None else config.concurrent_limit}")
        print(f"  Max Retries: {config.max_retries}")
        print()
        
        # Create and run bulk loader
        loader = NeptuneBulkLoader(config)
        result = loader.load_all_files()
        
        # Print final report
        loader.print_report(result)
        
        # Exit with appropriate code
        if result['failed'] > 0:
            print(f"\n⚠️  {result['failed']} jobs failed. Check logs for details.")
            sys.exit(1)
        else:
            print(f"\n✅ All jobs completed successfully!")
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {str(e)}")
        if os.getenv('NEPTUNE_DEBUG', 'false').lower() == 'true':
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()