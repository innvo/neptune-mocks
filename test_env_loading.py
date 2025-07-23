#!/usr/bin/env python3
"""
Test script to verify .env file loading for the Neptune bulk loader.
"""

import os
from dotenv import load_dotenv

def test_env_loading():
    """Test that environment variables are loaded from .env file."""
    print("Testing .env file loading...")
    
    # Load environment variables
    load_dotenv()
    
    # Check required variables
    s3_bucket = os.getenv('S3_BUCKET')
    iam_role_arn = os.getenv('NEPTUNE_IAM_ROLE_ARN')
    
    print(f"S3_BUCKET: {s3_bucket}")
    print(f"NEPTUNE_IAM_ROLE_ARN: {iam_role_arn}")
    
    # Check optional variables
    endpoint = os.getenv('NEPTUNE_ENDPOINT', 'https://localhost:8182')
    region = os.getenv('AWS_REGION', 'us-east-1')
    
    print(f"NEPTUNE_ENDPOINT: {endpoint}")
    print(f"AWS_REGION: {region}")
    
    # Validate required variables
    if not s3_bucket or s3_bucket == "your-s3-bucket-name":
        print("❌ S3_BUCKET is not set or is using default value")
        print("   Please set S3_BUCKET in your .env file")
        return False
    
    if not iam_role_arn or iam_role_arn == "arn:aws:iam::123456789012:role/NeptuneLoadFromS3":
        print("❌ NEPTUNE_IAM_ROLE_ARN is not set or is using default value")
        print("   Please set NEPTUNE_IAM_ROLE_ARN in your .env file")
        return False
    
    print("✅ Environment variables loaded successfully!")
    return True

if __name__ == "__main__":
    success = test_env_loading()
    if not success:
        print("\nTo fix this:")
        print("1. Copy env.template to .env: cp env.template .env")
        print("2. Edit .env and set your actual values")
        print("3. Run this test again")
        exit(1)
    else:
        print("\nEnvironment is ready for Neptune bulk loading!") 