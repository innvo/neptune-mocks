import boto3
import logging
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
        
        # Collect all object keys
        object_keys = []
        for page in pages:
            if 'Contents' in page:
                for obj in page['Contents']:
                    object_keys.append({'Key': obj['Key']})
        
        if not object_keys:
            logger.info(f"No files found in bucket {bucket_name}")
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
    # Configuration
    S3_BUCKET = "deam-neptune"
    
    try:
        delete_all_files_in_bucket(S3_BUCKET)
        logger.info("All files deleted successfully")
    except Exception as e:
        logger.error(f"Script failed: {str(e)}")
        exit(1) 