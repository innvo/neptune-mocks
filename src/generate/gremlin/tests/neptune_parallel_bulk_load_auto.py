#!/usr/bin/env python3

import boto3
import requests
import json
import time
from urllib3.exceptions import InsecureRequestWarning

# Suppress SSL warnings for localhost connections
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

class ParallelNeptuneBulkLoader:
    def __init__(self, endpoint="localhost:8182", s3_bucket="deam-neptune", 
                 iam_role_arn="arn:aws:iam::244081531951:role/NeptuneLoadFromS3", 
                 region="us-east-1"):
        self.endpoint = endpoint
        self.s3_bucket = s3_bucket
        self.iam_role_arn = iam_role_arn
        self.region = region
        self.base_url = f"https://{endpoint}"
        
        # Initialize S3 client
        self.s3_client = boto3.client('s3', region_name=region)
        
    def discover_s3_files(self, file_extensions=None):
        """Discover CSV files in S3 bucket root only"""
        if file_extensions is None:
            file_extensions = ['.csv']
        
        print(f"Discovering files in S3 bucket root: {self.s3_bucket}")
        print(f"Looking for extensions: {file_extensions}")
        
        files = []
        try:
            # List objects in the bucket root only (no prefix, no delimiter)
            paginator = self.s3_client.get_paginator('list_objects_v2')
            page_iterator = paginator.paginate(
                Bucket=self.s3_bucket,
                Delimiter='/'
            )
            
            for page in page_iterator:
                # Check for files in the root (CommonPrefixes will be empty for root files)
                if 'Contents' in page:
                    for obj in page['Contents']:
                        key = obj['Key']
                        # Only include files that are in the root (no '/' in the key except at the end)
                        if '/' not in key or key.endswith('/'):
                            # Check if file has the right extension
                            if any(key.endswith(ext) for ext in file_extensions):
                                files.append(key)
                                print(f"  Found: {key}")
        
        except Exception as e:
            print(f"Error discovering S3 files: {e}")
            return []
        
        print(f"Total files found in root: {len(files)}")
        return files
    
    def start_bulk_load(self, s3_path, format_type="csv"):
        """Start a bulk load for a specific file"""
        
        url = f"{self.base_url}/loader"
        
        payload = {
            "source": f"s3://{self.s3_bucket}/{s3_path}",
            "format": format_type,
            "iamRoleArn": self.iam_role_arn,
            "region": self.region,
            "failOnError": "FALSE",
            "parallelism": "OVERSUBSCRIBE",
            "queueRequest": "TRUE"
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(
                url, 
                json=payload, 
                headers=headers,
                verify=False,
                timeout=30
            )
            
            if response.status_code == 200:
                response_data = response.json()
                load_id = response_data.get('payload', {}).get('loadId', 'Unknown')
                print(f"✓ Started bulk load for {s3_path}")
                print(f"  Load ID: {load_id}")
                return load_id
            else:
                print(f"✗ Failed to start bulk load for {s3_path}")
                print(f"  Status: {response.status_code}")
                print(f"  Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"✗ Error starting bulk load for {s3_path}: {e}")
            return None
    
    def start_parallel_loads(self, files=None, file_extensions=None):
        """Start parallel bulk loads for multiple files"""
        
        if files is None:
            files = self.discover_s3_files(file_extensions)
        
        if not files:
            print("No files found to load")
            return []
        
        print(f"\nStarting {len(files)} parallel bulk load jobs...")
        print("=" * 80)
        
        load_ids = []
        successful_loads = 0
        
        for i, file_path in enumerate(files, 1):
            print(f"\n[{i}/{len(files)}] Processing: {file_path}")
            
            load_id = self.start_bulk_load(file_path)
            
            if load_id:
                load_ids.append({
                    'file': file_path,
                    'load_id': load_id
                })
                successful_loads += 1
            
            # Small delay between requests
            if i < len(files):
                time.sleep(1)
        
        print("\n" + "=" * 80)
        print("PARALLEL BULK LOAD SUMMARY")
        print("=" * 80)
        print(f"Total files: {len(files)}")
        print(f"Successful loads: {successful_loads}")
        print(f"Failed loads: {len(files) - successful_loads}")
        
        if load_ids:
            print(f"\nLoad IDs for monitoring:")
            for item in load_ids:
                print(f"  {item['file']}: {item['load_id']}")
        
        print(f"\nTo monitor all jobs:")
        print(f"curl -k {self.base_url}/loader")
        
        print(f"\nTo check specific job status:")
        for item in load_ids:
            print(f"curl -k {self.base_url}/loader/{item['load_id']}")
        
        return load_ids

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Start parallel Neptune bulk loads for individual files")
    parser.add_argument("--endpoint", default="localhost:8182", 
                       help="Neptune endpoint (default: localhost:8182)")
    parser.add_argument("--s3-bucket", default="deam-neptune", 
                       help="S3 bucket name (default: deam-neptune)")
    parser.add_argument("--iam-role", default="arn:aws:iam::244081531951:role/NeptuneLoadFromS3", 
                       help="IAM role ARN for Neptune bulk load")
    parser.add_argument("--region", default="us-east-1", 
                       help="AWS region (default: us-east-1)")
    parser.add_argument("--files", nargs="+", 
                       help="Specific files to load (if not provided, will discover all CSV files)")
    parser.add_argument("--extensions", nargs="+", default=[".csv"], 
                       help="File extensions to look for (default: .csv)")
    
    args = parser.parse_args()
    
    # Create bulk loader
    loader = ParallelNeptuneBulkLoader(
        endpoint=args.endpoint,
        s3_bucket=args.s3_bucket,
        iam_role_arn=args.iam_role,
        region=args.region
    )
    
    # Start parallel loads
    if args.files:
        # Use specific files provided
        load_ids = loader.start_parallel_loads(files=args.files)
    else:
        # Discover files automatically
        load_ids = loader.start_parallel_loads(file_extensions=args.extensions)
    
    if load_ids:
        print(f"\nAll {len(load_ids)} parallel bulk load jobs have been started!")
        print("Each file now has its own job running in parallel.")

if __name__ == "__main__":
    main() 