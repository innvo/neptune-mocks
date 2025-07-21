#!/usr/bin/env python3

import boto3
import argparse
import json
import os
from collections import defaultdict
from datetime import datetime
from dotenv import load_dotenv

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

class S3FileLister:
    def __init__(self, s3_bucket=None, region="us-east-1"):
        # Load .env file if s3_bucket is not provided
        if s3_bucket is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            env_path = find_dotenv(script_dir)
            if env_path:
                print(f"Using .env file at: {env_path}")
                load_dotenv(env_path)
                self.s3_bucket = validate_env_variables()
            else:
                print("Warning: .env file not found, using default bucket 'deam-neptune'")
                self.s3_bucket = "deam-neptune"
        else:
            self.s3_bucket = s3_bucket
            
        self.region = region
        
        # Initialize S3 client
        self.s3_client = boto3.client('s3', region_name=region)
        
    def discover_s3_files(self, file_extensions=None):
        """Discover files in S3 bucket with detailed information"""
        if file_extensions is None:
            file_extensions = ['.csv']
        
        print(f"🔍 Discovering files in S3 bucket: {self.s3_bucket}")
        print(f"📁 Looking for extensions: {file_extensions}")
        print("=" * 80)
        
        files = []
        folder_structure = defaultdict(list)
        file_sizes = {}
        
        try:
            # List objects in the bucket
            paginator = self.s3_client.get_paginator('list_objects_v2')
            page_iterator = paginator.paginate(Bucket=self.s3_bucket)
            
            for page in page_iterator:
                if 'Contents' in page:
                    for obj in page['Contents']:
                        key = obj['Key']
                        size = obj['Size']
                        last_modified = obj['LastModified']
                        
                        # Check if file has the right extension
                        if any(key.endswith(ext) for ext in file_extensions):
                            files.append({
                                'key': key,
                                'size': size,
                                'last_modified': last_modified,
                                'size_mb': round(size / (1024 * 1024), 2)
                            })
                            
                            # Organize by folder structure
                            if '/' in key:
                                folder = key.rsplit('/', 1)[0] + '/'
                            else:
                                folder = 'root/'
                            
                            folder_structure[folder].append(key)
                            file_sizes[key] = size
                            
                            print(f"✅ Found: {key}")
                            print(f"   📊 Size: {size:,} bytes ({round(size / (1024 * 1024), 2)} MB)")
                            print(f"   📅 Modified: {last_modified}")
        
        except Exception as e:
            print(f"❌ Error discovering S3 files: {e}")
            return [], {}, {}
        
        print(f"\n📈 Total files found: {len(files)}")
        return files, folder_structure, file_sizes
    
    def print_summary(self, files, folder_structure, file_sizes):
        """Print a detailed summary of discovered files"""
        if not files:
            print("❌ No files found matching the criteria")
            return
        
        print("\n" + "=" * 80)
        print("📋 S3 BUCKET FILE PROCESSING SUMMARY")
        print("=" * 80)
        
        # Overall statistics
        total_size = sum(file['size'] for file in files)
        total_size_mb = round(total_size / (1024 * 1024), 2)
        total_size_gb = round(total_size / (1024 * 1024 * 1024), 2)
        
        print(f"📊 Total Files: {len(files)}")
        print(f"💾 Total Size: {total_size:,} bytes ({total_size_mb} MB / {total_size_gb} GB)")
        print(f"📁 Folders: {len(folder_structure)}")
        
        # Folder breakdown
        print(f"\n📂 FOLDER BREAKDOWN:")
        print("-" * 40)
        for folder, file_list in sorted(folder_structure.items()):
            folder_size = sum(file_sizes.get(f, 0) for f in file_list)
            folder_size_mb = round(folder_size / (1024 * 1024), 2)
            print(f"📁 {folder}")
            print(f"   Files: {len(file_list)}")
            print(f"   Size: {folder_size_mb} MB")
            for file in sorted(file_list):
                file_size_mb = round(file_sizes.get(file, 0) / (1024 * 1024), 2)
                print(f"     📄 {file} ({file_size_mb} MB)")
            print()
        
        # File list for processing
        print(f"\n🔄 FILES TO BE PROCESSED BY NEPTUNE BULK LOADER:")
        print("-" * 60)
        for i, file_info in enumerate(files, 1):
            print(f"{i:3d}. {file_info['key']}")
            print(f"     Size: {file_info['size_mb']} MB | Modified: {file_info['last_modified']}")
        
        # Generate processing commands
        print(f"\n🚀 PROCESSING COMMANDS:")
        print("-" * 40)
        print("To process all files with the Neptune bulk loader:")
        print(f"python neptune_parallel_bulk_load_auto.py --s3-bucket {self.s3_bucket}")
        
        print(f"\nTo process specific file types:")
        for ext in ['.csv', '.json', '.txt']:
            print(f"python neptune_parallel_bulk_load_auto.py --s3-bucket {self.s3_bucket} --extensions {ext}")
        
        print(f"\nTo process specific files:")
        for file_info in files[:3]:  # Show first 3 as examples
            print(f"python neptune_parallel_bulk_load_auto.py --s3-bucket {self.s3_bucket} --files '{file_info['key']}'")
    
    def export_file_list(self, files, output_file=None):
        """Export the file list to JSON for further processing"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"s3_files_list_{timestamp}.json"
        
        export_data = {
            'bucket': self.s3_bucket,
            'region': self.region,
            'discovery_time': datetime.now().isoformat(),
            'total_files': len(files),
            'total_size_bytes': sum(file['size'] for file in files),
            'files': files
        }
        
        try:
            with open(output_file, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            print(f"\n💾 File list exported to: {output_file}")
            return output_file
        except Exception as e:
            print(f"❌ Error exporting file list: {e}")
            return None

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="List files in S3 bucket that would be processed by Neptune bulk loader")
    parser.add_argument("--s3-bucket", 
                       help="S3 bucket name (will use S3_BUCKET from .env file if not provided)")
    parser.add_argument("--region", default="us-east-1", 
                       help="AWS region (default: us-east-1)")
    parser.add_argument("--extensions", nargs="+", default=[".csv"], 
                       help="File extensions to look for (default: .csv)")
    parser.add_argument("--export", 
                       help="Export file list to JSON file")
    parser.add_argument("--quiet", action="store_true",
                       help="Suppress detailed output, show only summary")
    
    args = parser.parse_args()
    
    # Create file lister
    lister = S3FileLister(
        s3_bucket=args.s3_bucket,
        region=args.region
    )
    
    # Discover files
    files, folder_structure, file_sizes = lister.discover_s3_files(args.extensions)
    
    # Print summary
    if not args.quiet:
        lister.print_summary(files, folder_structure, file_sizes)
    else:
        print(f"Found {len(files)} files in {lister.s3_bucket}")
        total_size_mb = sum(file['size'] for file in files) / (1024 * 1024)
        print(f"Total size: {total_size_mb:.2f} MB")
    
    # Export if requested
    if args.export:
        lister.export_file_list(files, args.export)
    elif not args.quiet:
        # Auto-export if not quiet mode
        lister.export_file_list(files)

if __name__ == "__main__":
    main() 