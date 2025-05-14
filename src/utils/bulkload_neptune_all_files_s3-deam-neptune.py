import boto3
import requests
import logging
from typing import Dict, List
import time
import json
from colorama import init, Fore, Style
from datetime import datetime
import sys

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
logger.setLevel(logging.DEBUG)

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
    def __init__(self, neptune_endpoint: str = "https://localhost:8182"):
        self.neptune_endpoint = neptune_endpoint
        self.s3_client = boto3.client('s3')
        logger.debug(f"Initialized NeptuneBulkLoader with endpoint: {neptune_endpoint}")
        
    def get_files_from_s3(self, bucket_name: str) -> List[Dict]:
        """Get list of CSV files from S3 bucket."""
        try:
            logger.debug(f"Listing objects in S3 bucket: {bucket_name}")
            response = self.s3_client.list_objects_v2(Bucket=bucket_name)
            
            if 'Contents' not in response:
                logger.warning(f"No files found in bucket {bucket_name}")
                return []
                
            files = []
            print_header("Found CSV Files in S3")
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
                    'last_modified': last_modified
                }
                print(f"{Fore.CYAN}• {file_key}{Style.RESET_ALL}")
                print(f"  Size: {file_size:,} bytes")
                print(f"  Last Modified: {last_modified}")
                print(f"  Format: CSV\n")
                files.append(file_info)
            return files
        except Exception as e:
            logger.error(f"Error listing S3 files: {str(e)}")
            raise
            
    def submit_load_job(self, file_info: Dict) -> str:
        """Submit a load job to Neptune bulk loader."""
        try:
            payload = {
                "source": file_info['source'],
                "format": "csv",
                "iamRoleArn": "arn:aws:iam::244081531951:role/NeptuneLoadFromS3",
                "region": "us-east-1",
                "failOnError": "TRUE",
                "parallelism": "MEDIUM",
                "updateSingleCardinalityProperties": "FALSE",
                "queueRequest": "TRUE"
            }
            
            logger.debug(f"Submitting load job for: {file_info['source']}")
            response = requests.post(
                f"{self.neptune_endpoint}/loader",
                json=payload,
                verify=False
            )
            response.raise_for_status()
            
            response_data = response.json()
            load_id = response_data.get('payload', {}).get('loadId')
            if not load_id:
                raise ValueError("No load ID returned from Neptune")
                
            logger.info(f"✓ Load job submitted successfully for {file_info['source']}")
            return load_id
            
        except Exception as e:
            logger.error(f"✗ Error submitting load job: {str(e)}")
            raise
            
    def check_load_status(self, load_id: str) -> bool:
        """Check the status of a load job."""
        try:
            response = requests.get(
                f"{self.neptune_endpoint}/loader/{load_id}",
                verify=False
            )
            response.raise_for_status()
            
            response_data = response.json()
            status = response_data.get('status')
            
            if status == "LOAD_COMPLETED":
                return True
            elif status in ["LOAD_FAILED", "LOAD_CANCELLED"]:
                error_details = response_data.get('details', {})
                logger.error(f"Load job failed. Status: {status}, Details: {json.dumps(error_details)}")
                raise Exception(f"Load job failed with status: {status}")
                
            return False
            
        except Exception as e:
            logger.error(f"Error checking load status: {str(e)}")
            raise
            
    def load_all_files(self, bucket_name: str):
        """Load all files from S3 bucket into Neptune."""
        try:
            print_header("Starting Neptune Bulk Load Process")
            start_time = datetime.now()
            
            # Get list of files
            files = self.get_files_from_s3(bucket_name)
            if not files:
                logger.warning("No files to load")
                return
                
            total_files = len(files)
            logger.info(f"Found {total_files} files to load")
            
            # Submit load jobs
            print_header("Submitting Load Jobs")
            load_ids = []
            for i, file_info in enumerate(files, 1):
                print_progress(i, total_files, prefix='Submitting:', suffix=f'({i}/{total_files})')
                load_id = self.submit_load_job(file_info)
                load_ids.append(load_id)
            print()  # New line after progress bar
            
            # Monitor load jobs
            print_header("Monitoring Load Jobs")
            completed = set()
            total_jobs = len(load_ids)
            
            while len(completed) < total_jobs:
                for i, load_id in enumerate(load_ids):
                    if load_id not in completed:
                        if self.check_load_status(load_id):
                            completed.add(load_id)
                            print_progress(
                                len(completed),
                                total_jobs,
                                prefix='Progress:',
                                suffix=f'({len(completed)}/{total_jobs})'
                            )
                if len(completed) < total_jobs:
                    time.sleep(10)
            print()  # New line after progress bar
            
            end_time = datetime.now()
            duration = end_time - start_time
            
            print_header("Load Process Completed")
            print(f"{Fore.GREEN}✓ All {total_files} files loaded successfully{Style.RESET_ALL}")
            print(f"⏱️  Total duration: {duration}")
            
        except Exception as e:
            logger.error(f"Script failed: {str(e)}")
            raise

if __name__ == "__main__":
    # Configuration
    S3_BUCKET = "deam-neptune"
    NEPTUNE_ENDPOINT = "https://localhost:8182"
    
    try:
        loader = NeptuneBulkLoader(NEPTUNE_ENDPOINT)
        loader.load_all_files(S3_BUCKET)
    except Exception as e:
        logger.error(f"Script failed: {str(e)}")
        exit(1)
