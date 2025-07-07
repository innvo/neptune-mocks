import os
import boto3
import logging
from pathlib import Path
from botocore.exceptions import ClientError
import math
from tqdm import tqdm
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MULTIPART_THRESHOLD = 100 * 1024 * 1024  # 100 MB
PART_SIZE = 8 * 1024 * 1024  # 8 MB

class ProgressPercentage:
    def __init__(self, filename):
        self._filename = filename
        self._size = float(os.path.getsize(filename))
        self._seen_so_far = 0
        self._lock = threading.Lock()

    def __call__(self, bytes_amount):
        with self._lock:
            self._seen_so_far += bytes_amount
            percentage = (self._seen_so_far / self._size) * 100
            logger.info(f"{self._filename} {percentage:.2f}% complete")

def upload_file_multipart(file_path: Path, s3_client, bucket: str, key: str):
    """Upload a file using multipart upload"""
    try:
        file_size = os.path.getsize(file_path)
        if file_size < MULTIPART_THRESHOLD:
            # Use regular upload for small files
            s3_client.upload_file(str(file_path), bucket, key)
            return

        # Create multipart upload
        response = s3_client.create_multipart_upload(
            Bucket=bucket,
            Key=key
        )
        upload_id = response['UploadId']

        # Calculate number of parts
        part_count = math.ceil(file_size / PART_SIZE)
        parts = []

        # Upload parts
        with tqdm(total=file_size, unit='B', unit_scale=True, desc=f"Uploading {file_path.name}") as pbar:
            with open(file_path, 'rb') as file:
                for i in range(part_count):
                    part_number = i + 1
                    start = i * PART_SIZE
                    end = min(start + PART_SIZE, file_size)
                    file.seek(start)
                    data = file.read(end - start)

                    response = s3_client.upload_part(
                        Bucket=bucket,
                        Key=key,
                        PartNumber=part_number,
                        UploadId=upload_id,
                        Body=data
                    )
                    parts.append({
                        'PartNumber': part_number,
                        'ETag': response['ETag']
                    })
                    pbar.update(len(data))

        # Complete multipart upload
        s3_client.complete_multipart_upload(
            Bucket=bucket,
            Key=key,
            UploadId=upload_id,
            MultipartUpload={'Parts': parts}
        )
    except Exception as e:
        # Abort multipart upload if it fails
        if 'upload_id' in locals():
            try:
                s3_client.abort_multipart_upload(
                    Bucket=bucket,
                    Key=key,
                    UploadId=upload_id
                )
            except:
                pass
        raise e

def upload_files_to_s3(local_dir: str, s3_bucket: str, s3_prefix: str = ''):
    """
    Upload all files from a local directory to an S3 bucket using multipart upload for large files.
    
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
                logger.info(f"Starting upload of {file_path} to s3://{s3_bucket}/{s3_key}")
                upload_file_multipart(file_path, s3_client, s3_bucket, s3_key)
                logger.info(f"Successfully uploaded {file_path.name}")
            except ClientError as e:
                logger.error(f"AWS Error uploading {file_path.name}: {str(e)}")
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
