import os
import boto3
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def upload_files_to_s3(local_dir: str, s3_bucket: str, s3_prefix: str = ''):
    """
    Upload all files from a local directory to an S3 bucket.
    
    Args:
        local_dir (str): Local directory containing files to upload
        s3_bucket (str): S3 bucket name
        s3_prefix (str): Optional prefix for S3 keys
    """
    try:
        # Initialize S3 client
        s3_client = boto3.client('s3')
        
        # Get list of files in the directory
        local_path = Path(local_dir)
        if not local_path.exists():
            raise FileNotFoundError(f"Directory {local_dir} does not exist")
            
        files = [f for f in local_path.iterdir() if f.is_file()]
        
        if not files:
            logger.warning(f"No files found in {local_dir}")
            return
            
        # Upload each file
        for file_path in files:
            s3_key = os.path.join(s3_prefix, file_path.name)
            try:
                logger.info(f"Uploading {file_path} to s3://{s3_bucket}/{s3_key}")
                s3_client.upload_file(
                    str(file_path),
                    s3_bucket,
                    s3_key
                )
                logger.info(f"Successfully uploaded {file_path.name}")
            except Exception as e:
                logger.error(f"Error uploading {file_path.name}: {str(e)}")
                
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    # Configuration
    LOCAL_DIR = "src/data/output/neptune"
    S3_BUCKET = "deam-neptune"
    
    try:
        upload_files_to_s3(LOCAL_DIR, S3_BUCKET)
        logger.info("All files uploaded successfully")
    except Exception as e:
        logger.error(f"Script failed: {str(e)}")
        exit(1)
