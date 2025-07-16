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

# Suppress SSL warnings for localhost development
urllib3.disable_warnings(InsecureRequestWarning)
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

# Initialize colorama
init()

# Configure logging with colors
class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors"""
    
    def format(self, record):
        if record.levelno == logging.DEBUG:
            record.msg = f"{Fore.CYAN}{record.msg}{Style.RESET_ALL}"
        elif record.levelno == logging.INFO:
            record.msg = f"{Fore.GREEN}{record.msg}{Style.RESET_ALL}"
        elif record.levelno == logging.WARNING:
            record.msg = f"{Fore.YELLOW}{record.msg}{Style.RESET_ALL}"
        elif record.levelno == logging.ERROR:
            record.msg = f"{Fore.RED}{record.msg}{Style.RESET_ALL}"
        return super().format(record)

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)  # Only show warnings and errors

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

class NeptuneBulkLoader:
    def __init__(self, neptune_endpoint: str = "https://localhost:8182", max_workers: int = 10):
        self.neptune_endpoint = neptune_endpoint
        self.s3_client = boto3.client('s3')
        self.max_workers = max_workers  # Number of concurrent job submissions
        
        # Configure requests session for better SSL handling
        self.session = requests.Session()
        if 'localhost' in neptune_endpoint or '127.0.0.1' in neptune_endpoint:
            self.session.verify = False
            logger.info(f"SSL verification disabled for localhost endpoint: {neptune_endpoint}")
        else:
            logger.info(f"SSL verification enabled for endpoint: {neptune_endpoint}")
            
        logger.info(f"Initialized NeptuneBulkLoader with endpoint: {neptune_endpoint}, max_workers: {max_workers}")
        
    def get_files_from_s3(self, bucket_name: str) -> List[Dict]:
        """Get list of CSV files from S3 bucket, separated into nodes and edges."""
        try:
            response = self.s3_client.list_objects_v2(Bucket=bucket_name)
            
            if 'Contents' not in response:
                print(f"No files found in bucket {bucket_name}")
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
                    'source': f"s3://{bucket_name}/{file_key}",
                    'format': 'csv',
                    'size': file_size,
                    'last_modified': last_modified,
                    'key': file_key
                }
                
                # Categorize files as nodes or edges based on filename
                if self._is_edge_file(file_key):
                    edge_files.append(file_info)
                else:
                    node_files.append(file_info)
                    
            return node_files, edge_files
        except Exception as e:
            print(f"Error listing S3 files: {str(e)}")
            raise
    
    def _is_edge_file(self, file_key: str) -> bool:
        """Determine if a file contains edge data based on filename patterns."""
        file_lower = file_key.lower()
        
        # Check for explicit edge pattern
        if '_edges_' in file_lower:
            return True
            
        # Check for explicit node pattern
        if '_nodes_' in file_lower:
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
                return True
                
        return False
            
    def submit_load_job(self, file_info: Dict) -> Dict:
        """Submit a load job to Neptune bulk loader with optimized settings."""
        try:
            payload = {
                "source": file_info['source'],
                "format": "csv",
                "iamRoleArn": "arn:aws:iam::244081531951:role/NeptuneLoadFromS3",
                "region": "us-east-1",
                "failOnError": "TRUE",
                "parallelism": "HIGH",  # Changed from MEDIUM to HIGH for maximum speed
                "updateSingleCardinalityProperties": "FALSE",
                "queueRequest": "TRUE",
                "parserConfiguration": {
                    "namedGraphUri": "",
                    "baseUri": "",
                    "allowEmptyStrings": "FALSE",
                    "allowMultipleVertexLabels": "TRUE",
                    "allowEmptyStringsWithoutQuotes": "FALSE",
                    "trimStrings": "TRUE"
                }
            }
            
            response = self.session.post(
                f"{self.neptune_endpoint}/loader",
                json=payload,
                timeout=60  # Increased timeout for larger files
            )
            response.raise_for_status()
            
            response_data = response.json()
            load_id = response_data.get('payload', {}).get('loadId')
            if not load_id:
                raise ValueError("No load ID returned from Neptune")
                
            return {
                'file_key': file_info['key'],
                'load_id': load_id,
                'status': 'SUBMITTED',
                'type': 'NODE' if not self._is_edge_file(file_info['key']) else 'EDGE',
                'size': file_info.get('size', 0)
            }
            
        except Exception as e:
            return {
                'file_key': file_info['key'],
                'load_id': 'FAILED',
                'status': f'ERROR: {str(e)}',
                'type': 'NODE' if not self._is_edge_file(file_info['key']) else 'EDGE',
                'size': file_info.get('size', 0)
            }

    def submit_jobs_concurrent(self, files: List[Dict], job_type: str) -> List[Dict]:
        """Submit multiple jobs concurrently using ThreadPoolExecutor."""
        job_results = []
        
        print(f"\n{Fore.BLUE}Submitting {len(files)} {job_type} files concurrently (max {self.max_workers} workers)...{Style.RESET_ALL}")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all jobs
            future_to_file = {executor.submit(self.submit_load_job, file_info): file_info for file_info in files}
            
            # Process completed jobs
            completed = 0
            for future in as_completed(future_to_file):
                completed += 1
                result = future.result()
                job_results.append(result)
                
                # Update progress
                print_progress(completed, len(files), 
                             prefix=f'{job_type}:', 
                             suffix=f'({completed}/{len(files)}) - {result["file_key"]}')
                
                # Print immediate status
                if result['status'] == 'SUBMITTED':
                    print(f"\n{Fore.GREEN}✓{Style.RESET_ALL} {result['file_key']} - {result['load_id']}")
                else:
                    print(f"\n{Fore.RED}✗{Style.RESET_ALL} {result['file_key']} - {result['status']}")
        
        print()  # New line after progress bar
        return job_results
            
    def load_all_files(self, bucket_name: str):
        """Load all files from S3 bucket into Neptune - nodes first, then edges with concurrent processing."""
        start_time = datetime.now()
        
        try:
            # Get list of files separated into nodes and edges
            node_files, edge_files = self.get_files_from_s3(bucket_name)
            
            if not node_files and not edge_files:
                print("No files to load")
                return
                
            total_files = len(node_files) + len(edge_files)
            total_size = sum(f.get('size', 0) for f in node_files + edge_files)
            
            print(f"Found {len(node_files)} node files and {len(edge_files)} edge files to submit")
            print(f"Total data size: {total_size / (1024*1024*1024):.2f} GB")
            print(f"Using {self.max_workers} concurrent workers for job submission")
            
            job_results = []
            
            # Load nodes first (concurrently)
            if node_files:
                node_results = self.submit_jobs_concurrent(node_files, "NODE")
                job_results.extend(node_results)
            
            # Load edges second (concurrently)
            if edge_files:
                edge_results = self.submit_jobs_concurrent(edge_files, "EDGE")
                job_results.extend(edge_results)
            
            # Print final report
            print_header("Job Submission Report")
            print(f"{Fore.CYAN}Total Files Found:{Style.RESET_ALL} {total_files}")
            print(f"{Fore.CYAN}Total Data Size:{Style.RESET_ALL} {total_size / (1024*1024*1024):.2f} GB")
            print(f"{Fore.CYAN}Node Files:{Style.RESET_ALL} {len(node_files)}")
            print(f"{Fore.CYAN}Edge Files:{Style.RESET_ALL} {len(edge_files)}")
            print(f"{Fore.CYAN}Jobs Submitted Successfully:{Style.RESET_ALL} {len([j for j in job_results if j['status'] == 'SUBMITTED'])}")
            print(f"{Fore.CYAN}Jobs Failed:{Style.RESET_ALL} {len([j for j in job_results if j['status'] != 'SUBMITTED'])}")
            print(f"{Fore.CYAN}Submission Time:{Style.RESET_ALL} {datetime.now() - start_time}")
            print(f"{Fore.CYAN}Concurrent Workers Used:{Style.RESET_ALL} {self.max_workers}")
            
            # Print all jobs in submission order
            print(f"\n{Fore.CYAN}Job Details (in submission order):{Style.RESET_ALL}")
            print(f"{'Type':<6} {'File':<50} {'Job ID':<40} {'Size (MB)':<10} {'Status'}")
            print("-" * 116)
            
            for job in job_results:
                job_type = job['type']
                size_mb = job.get('size', 0) / (1024*1024)
                if job['status'] == 'SUBMITTED':
                    print(f"{job_type:<6} {job['file_key']:<50} {job['load_id']:<40} {size_mb:<10.1f} {Fore.GREEN}SUBMITTED{Style.RESET_ALL}")
                else:
                    print(f"{job_type:<6} {job['file_key']:<50} {'FAILED':<40} {size_mb:<10.1f} {Fore.RED}{job['status']}{Style.RESET_ALL}")
            
        except Exception as e:
            print(f"Script failed: {str(e)}")
            raise

if __name__ == "__main__":
    # Configuration
    S3_BUCKET = "deam-neptune"
    NEPTUNE_ENDPOINT = "https://localhost:8182"
    MAX_WORKERS = 10  # Adjust based on your Neptune cluster capacity
    
    try:
        loader = NeptuneBulkLoader(NEPTUNE_ENDPOINT, MAX_WORKERS)
        loader.load_all_files(S3_BUCKET)
    except KeyboardInterrupt:
        print("Process interrupted by user")
        exit(0)
    except Exception as e:
        print(f"Script failed: {str(e)}")
        exit(1)
