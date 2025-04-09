import os
import boto3
from botocore.config import Config
from pathlib import Path
import logging
import time
import requests
from typing import List, Dict, Optional
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define data directory path - using absolute path from workspace root
WORKSPACE_ROOT = Path(__file__).parent.parent.parent.parent
DATA_DIR = WORKSPACE_ROOT / 'src' / 'resources' / 'data'

class NeptuneBulkLoader:
    def __init__(self, profile_name: str = 'default'):
        """
        Initialize Neptune bulk loader with AWS credentials.
        
        Args:
            profile_name: AWS profile name to use (default: 'default')
        """
        try:
            # Get AWS credentials from environment
            aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
            aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
            aws_region = os.getenv('AWS_REGION')
            
            if not all([aws_access_key_id, aws_secret_access_key, aws_region]):
                raise ValueError("AWS credentials not properly configured in .env file")
            
            # Create a session using environment credentials
            session = boto3.Session(
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                region_name=aws_region
            )
            
            # Get Neptune endpoint from environment
            self.neptune_endpoint = os.getenv('NEPTUNE_ENDPOINT')
            if not self.neptune_endpoint:
                raise ValueError("NEPTUNE_ENDPOINT not set in .env file")
            
            # Initialize S3 client for source files
            self.s3_client = session.client(
                's3',
                config=Config(
                    retries=dict(
                        max_attempts=3
                    )
                )
            )
            
            logger.info(f"Successfully initialized Neptune loader with endpoint: {self.neptune_endpoint}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Neptune loader: {str(e)}")
            raise

    def start_bulk_load(self, source: str, format: str = 'csv', role_arn: str = None) -> str:
        """
        Start a Neptune bulk load job using the REST API.
        
        Args:
            source: S3 URI of the source files
            format: Format of the source files (default: 'csv')
            role_arn: IAM role ARN for Neptune to access S3
            
        Returns:
            str: Loader ID
        """
        try:
            # Prepare the request payload
            payload = {
                "source": source,
                "format": "opencypher",
                "iamRoleArn": role_arn,
                "region": os.getenv('AWS_REGION'),
                "failOnError": "FALSE",
                "parallelism": "MEDIUM",
                "updateSingleCardinalityProperties": "FALSE",
                "queueRequest": "TRUE"
            }
            
            # Make the API request
            url = f"https://{self.neptune_endpoint}:8182/loader"
            headers = {'Content-Type': 'application/json'}
            
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            # Parse the response
            result = response.json()
            loader_id = result['payload']['loadId']
            
            logger.info(f"Started bulk load job with ID: {loader_id}")
            return loader_id
            
        except Exception as e:
            logger.error(f"Failed to start bulk load job: {str(e)}")
            raise

    def get_loader_status(self, loader_id: str) -> Dict:
        """
        Get the status of a Neptune bulk load job.
        
        Args:
            loader_id: ID of the loader job
            
        Returns:
            Dict: Loader status information
        """
        try:
            url = f"https://{self.neptune_endpoint}:8182/loader/{loader_id}"
            response = requests.get(url)
            response.raise_for_status()
            
            return response.json()['payload']
            
        except Exception as e:
            logger.error(f"Failed to get loader status: {str(e)}")
            raise

    def wait_for_completion(self, loader_id: str, poll_interval: int = 30) -> bool:
        """
        Wait for a Neptune bulk load job to complete.
        
        Args:
            loader_id: ID of the loader job
            poll_interval: Time in seconds between status checks
            
        Returns:
            bool: True if job completed successfully, False otherwise
        """
        try:
            while True:
                status = self.get_loader_status(loader_id)
                current_status = status['status']
                
                logger.info(f"Loader {loader_id} status: {current_status}")
                logger.info(f"Records loaded: {status.get('recordsLoaded', 0)}")
                logger.info(f"Errors: {status.get('errors', [])}")
                
                if current_status in ['LOAD_COMPLETED', 'LOAD_COMPLETED_WITH_ERRORS']:
                    return current_status == 'LOAD_COMPLETED'
                elif current_status in ['LOAD_FAILED', 'LOAD_CANCELLED']:
                    return False
                    
                time.sleep(poll_interval)
                
        except Exception as e:
            logger.error(f"Error waiting for loader completion: {str(e)}")
            raise

def main():
    """Main function to handle Neptune bulk loading."""
    try:
        # Initialize loader
        loader = NeptuneBulkLoader()
        
        # Ensure data directory exists
        if not DATA_DIR.exists():
            logger.error(f"Data directory not found: {DATA_DIR}")
            logger.info(f"Creating data directory: {DATA_DIR}")
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            
        logger.info(f"Using data directory: {DATA_DIR}")
        
        # Get all CSV files in the directory
        csv_files = list(DATA_DIR.glob('*.csv'))
        
        if not csv_files:
            logger.warning(f"No CSV files found in {DATA_DIR}")
            return
            
        logger.info(f"Found {len(csv_files)} CSV files to load")
        
        # Upload files to S3
        bucket_name = os.getenv('S3_BUCKET_NAME')
        if not bucket_name:
            raise ValueError("S3_BUCKET_NAME not set in .env file")
            
        s3_prefix = f"neptune-load/{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        for file_path in csv_files:
            s3_key = f"{s3_prefix}/{file_path.name}"
            logger.info(f"Uploading {file_path.name} to s3://{bucket_name}/{s3_key}")
            loader.s3_client.upload_file(str(file_path), bucket_name, s3_key)
            
        # Start bulk load
        source = f"s3://{bucket_name}/{s3_prefix}/"
        role_arn = os.getenv('NEPTUNE_LOADER_ROLE_ARN')
        
        if not role_arn:
            raise ValueError("NEPTUNE_LOADER_ROLE_ARN not set in .env file")
            
        loader_id = loader.start_bulk_load(source=source, role_arn=role_arn)
        
        # Wait for completion
        success = loader.wait_for_completion(loader_id)
        
        if success:
            logger.info("Bulk load completed successfully")
        else:
            logger.error("Bulk load failed or completed with errors")
            
    except Exception as e:
        logger.error(f"Error in Neptune bulk load process: {str(e)}")
        raise

if __name__ == "__main__":
    main()
