import os
import boto3
from botocore.config import Config
from pathlib import Path
import logging
from typing import List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define data directory path - using absolute path from workspace root
WORKSPACE_ROOT = Path(__file__).parent.parent.parent.parent
DATA_DIR = WORKSPACE_ROOT / 'src' / 'resources' / 'data'

class S3Uploader:
    def __init__(self, profile_name: str = 'default'):
        """
        Initialize S3 client with credentials from AWS config.
        
        Args:
            profile_name: AWS profile name to use (default: 'default')
        """
        try:
            # Create a session using the specified profile
            session = boto3.Session(profile_name=profile_name)
            
            # Get the region from the session
            region = session.region_name
            if not region:
                raise ValueError("AWS region not found in config")
            
            # Initialize S3 client with retry configuration
            self.s3_client = session.client(
                's3',
                config=Config(
                    retries=dict(
                        max_attempts=3
                    )
                )
            )
            
            # Get available buckets to verify credentials
            response = self.s3_client.list_buckets()
            self.available_buckets = [bucket['Name'] for bucket in response['Buckets']]
            
            logger.info(f"Successfully initialized S3 client with profile: {profile_name}")
            logger.info(f"Available buckets: {', '.join(self.available_buckets)}")
            
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {str(e)}")
            raise

    def upload_file(self, file_path: str, bucket_name: str, s3_key: Optional[str] = None) -> bool:
        """
        Upload a single file to S3.
        
        Args:
            file_path: Path to the local file
            bucket_name: Name of the S3 bucket
            s3_key: Optional S3 key (path) for the file. If not provided, uses the file name.
            
        Returns:
            bool: True if upload was successful, False otherwise
        """
        try:
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return False
                
            if bucket_name not in self.available_buckets:
                logger.error(f"Bucket not accessible: {bucket_name}")
                return False
                
            if s3_key is None:
                s3_key = os.path.basename(file_path)
                
            logger.info(f"Uploading {file_path} to s3://{bucket_name}/{s3_key}")
            self.s3_client.upload_file(file_path, bucket_name, s3_key)
            logger.info(f"Successfully uploaded {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error uploading {file_path}: {str(e)}")
            return False

    def upload_directory(self, directory_path: str, bucket_name: str, prefix: str = '') -> List[str]:
        """
        Upload all CSV files from a directory to S3.
        
        Args:
            directory_path: Path to the local directory
            bucket_name: Name of the S3 bucket
            prefix: Optional prefix to add to S3 keys
            
        Returns:
            List[str]: List of successfully uploaded files
        """
        if not os.path.isdir(directory_path):
            logger.error(f"Directory not found: {directory_path}")
            return []
            
        if bucket_name not in self.available_buckets:
            logger.error(f"Bucket not accessible: {bucket_name}")
            return []
            
        successful_uploads = []
        for file_path in Path(directory_path).glob('*.csv'):
            s3_key = f"{prefix}/{file_path.name}" if prefix else file_path.name
            if self.upload_file(str(file_path), bucket_name, s3_key):
                successful_uploads.append(str(file_path))
                
        return successful_uploads

def main():
    """Main function to handle S3 uploads."""
    try:
        # Initialize uploader with default profile
        uploader = S3Uploader()
        
        # Specify the bucket to use
        bucket_name = 'deam-neptune'
        
        # Ensure data directory exists
        if not DATA_DIR.exists():
            logger.error(f"Data directory not found: {DATA_DIR}")
            logger.info(f"Creating data directory: {DATA_DIR}")
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            
        logger.info(f"Using data directory: {DATA_DIR}")
        
        # Upload all CSV files in the directory
        csv_files = list(DATA_DIR.glob('*.csv'))
        
        if not csv_files:
            logger.warning(f"No CSV files found in {DATA_DIR}")
            return
            
        logger.info(f"Found {len(csv_files)} CSV files to upload")
        
        for file_path in csv_files:
            logger.info(f"Processing file: {file_path.name}")
            if uploader.upload_file(str(file_path), bucket_name):
                logger.info(f"Successfully processed {file_path.name}")
            else:
                logger.error(f"Failed to process {file_path.name}")
                
        logger.info("S3 upload process completed")
        
    except Exception as e:
        logger.error(f"Error in S3 upload process: {str(e)}")
        raise

if __name__ == "__main__":
    main() 