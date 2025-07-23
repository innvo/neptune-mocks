import boto3
import logging
import os
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def find_dotenv(start_dir):
    """Find .env file by searching up the directory tree"""
    current_dir = start_dir
    while True:
        env_path = os.path.join(current_dir, '.env')
        if os.path.isfile(env_path):
            return env_path
        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:
            break
        current_dir = parent_dir
    return None

def validate_env_variables():
    """Validate and return environment variables"""
    bucket_name = os.getenv('S3_BUCKET')
    
    if not bucket_name:
        raise ValueError("❌ ERROR: Missing environment variable S3_BUCKET. Please set it in your .env file.")
    
    return bucket_name

def delete_all_files_in_bucket(bucket_name: str):
    """
    Delete all files in the specified S3 bucket.
    
    Args:
        bucket_name (str): Name of the S3 bucket
    """
    try:
        # Initialize S3 client
        s3_client = boto3.client('s3')
        
        # List all objects in the bucket
        logger.info(f"Listing objects in bucket: {bucket_name}")
        paginator = s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=bucket_name)
        
        # Collect all object keys (only root level files)
        object_keys = []
        for page in pages:
            if 'Contents' in page:
                for obj in page['Contents']:
                    # Only include files that are in the root (no '/' in the key)
                    if '/' not in obj['Key']:
                        object_keys.append({'Key': obj['Key']})
        
        if not object_keys:
            logger.info(f"No files found in root of bucket {bucket_name}")
            return
            
        # Delete all objects in batches of 1000 (S3 API limit)
        logger.info(f"Found {len(object_keys)} objects to delete")
        for i in range(0, len(object_keys), 1000):
            batch = object_keys[i:i + 1000]
            try:
                s3_client.delete_objects(
                    Bucket=bucket_name,
                    Delete={'Objects': batch}
                )
                logger.info(f"Successfully deleted batch of {len(batch)} objects")
            except ClientError as e:
                logger.error(f"Error deleting batch: {str(e)}")
                raise
                
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        # Find and load .env file
        script_dir = os.path.dirname(os.path.abspath(__file__))
        env_path = find_dotenv(script_dir)
        if not env_path:
            raise FileNotFoundError(f"❌ ERROR: .env file not found. Please create a .env file in the project root.")
        
        logger.info(f"Using .env file at: {env_path}")
        load_dotenv(env_path)
        
        # Get bucket name from environment variables
        S3_BUCKET = validate_env_variables()
        
        delete_all_files_in_bucket(S3_BUCKET)
        logger.info("All files deleted successfully")
    except Exception as e:
        logger.error(f"Script failed: {str(e)}")
        exit(1) 