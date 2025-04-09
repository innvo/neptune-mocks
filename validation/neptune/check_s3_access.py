import os
import boto3
import logging
from botocore.config import Config
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_s3_access():
    """
    Check if Neptune has read-only access to S3 using the loader role.
    """
    try:
        # Get required environment variables
        role_arn = os.getenv('NEPTUNE_LOADER_ROLE_ARN')
        bucket_name = os.getenv('S3_BUCKET_NAME')
        
        if not role_arn or not bucket_name:
            raise ValueError("NEPTUNE_LOADER_ROLE_ARN or S3_BUCKET_NAME not set in .env file")
        
        # Create STS client
        sts_client = boto3.client('sts')
        
        # Assume the Neptune loader role
        logger.info(f"Assuming role: {role_arn}")
        assumed_role = sts_client.assume_role(
            RoleArn=role_arn,
            RoleSessionName="NeptuneS3AccessCheck"
        )
        
        # Get temporary credentials
        credentials = assumed_role['Credentials']
        
        # Create S3 client with assumed role credentials
        s3_client = boto3.client(
            's3',
            aws_access_key_id=credentials['AccessKeyId'],
            aws_secret_access_key=credentials['SecretAccessKey'],
            aws_session_token=credentials['SessionToken'],
            config=Config(
                retries=dict(
                    max_attempts=3
                )
            )
        )
        
        # Try to list objects in the bucket
        logger.info(f"Checking access to bucket: {bucket_name}")
        response = s3_client.list_objects_v2(
            Bucket=bucket_name,
            MaxKeys=1  # Just check if we can list objects
        )
        
        if 'Contents' in response:
            logger.info("✅ Success: Neptune loader role has read access to S3 bucket")
            logger.info(f"Found {response['KeyCount']} objects in bucket")
        else:
            logger.info("ℹ️ Bucket exists but is empty")
            
        # Try to get an object's metadata (without downloading)
        try:
            # Get the first object's metadata
            if 'Contents' in response:
                object_key = response['Contents'][0]['Key']
                s3_client.head_object(
                    Bucket=bucket_name,
                    Key=object_key
                )
                logger.info("✅ Success: Neptune loader role can read object metadata")
        except Exception as e:
            logger.error(f"❌ Failed to read object metadata: {str(e)}")
            
        # Try to get an object (simulate actual read)
        try:
            if 'Contents' in response:
                object_key = response['Contents'][0]['Key']
                s3_client.get_object(
                    Bucket=bucket_name,
                    Key=object_key,
                    Range='bytes=0-0'  # Just get first byte to test access
                )
                logger.info("✅ Success: Neptune loader role can read object content")
        except Exception as e:
            logger.error(f"❌ Failed to read object content: {str(e)}")
            
    except Exception as e:
        logger.error(f"❌ Failed to check S3 access: {str(e)}")
        raise

if __name__ == "__main__":
    check_s3_access() 