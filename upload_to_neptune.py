import boto3
import os
import requests
import time
from botocore.config import Config
from botocore.exceptions import ClientError

class NeptuneUploader:
    def __init__(self, region='us-east-1'):
        self.neptune_status_url = 'http://localhost:8182/status'
        
    def check_neptune_status(self):
        """Check if Neptune is available through SSH tunnel"""
        try:
            response = requests.get(self.neptune_status_url, timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"Error checking Neptune status: {str(e)}")
            print("Make sure SSH tunnel is running: ssh -i /path/to/key.pem -L 8182:neptune-endpoint:8182 ec2-user@bastion-host")
            return False

    def upload_to_neptune(self, local_file_path):
        """Upload CSV file to Neptune through SSH tunnel"""
        try:
            # Get file size
            file_size = os.path.getsize(local_file_path)
            
            # Prepare headers
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            # Prepare the upload URL (using localhost due to SSH tunnel)
            upload_url = 'http://localhost:8182/loader'
            
            # Read the file
            with open(local_file_path, 'rb') as f:
                files = {'file': (os.path.basename(local_file_path), f)}
                
                # Make the request
                response = requests.post(
                    upload_url,
                    files=files,
                    headers=headers
                )
                
                if response.status_code == 200:
                    print("Upload initiated successfully")
                    return self._wait_for_upload_completion(response.json()['payload']['loadId'])
                else:
                    print(f"Error uploading to Neptune: {response.text}")
                    return False
                    
        except Exception as e:
            print(f"Error uploading to Neptune: {str(e)}")
            return False

    def _wait_for_upload_completion(self, load_id, max_retries=30, wait_interval=10):
        """Wait for the upload to complete"""
        status_url = f'http://localhost:8182/loader/{load_id}'
        
        for _ in range(max_retries):
            try:
                response = requests.get(status_url)
                if response.status_code == 200:
                    status = response.json()
                    if status['status'] == 'LOAD_COMPLETED':
                        print("Upload completed successfully")
                        return True
                    elif status['status'] == 'LOAD_FAILED':
                        print(f"Upload failed: {status.get('errorDetails', 'Unknown error')}")
                        return False
                    else:
                        print(f"Upload in progress: {status['status']}")
                        time.sleep(wait_interval)
                else:
                    print(f"Error checking upload status: {response.text}")
                    return False
            except Exception as e:
                print(f"Error checking upload status: {str(e)}")
                return False
        
        print("Upload timed out")
        return False

def main():
    # Configuration
    local_file = "neptune_person_nodes.csv"
    
    # Initialize uploader
    uploader = NeptuneUploader()
    
    # Check Neptune status
    if not uploader.check_neptune_status():
        print("Neptune is not available through SSH tunnel")
        print("Please ensure SSH tunnel is running with:")
        print("ssh -i /path/to/key.pem -L 8182:db-neptune-dev-instance-1.cz7fmvtxsrei.us-east-1.neptune.amazonaws.com:8182 ec2-user@35.170.107.253")
        return
    
    # Upload to Neptune
    if uploader.upload_to_neptune(local_file):
        print("Successfully uploaded to Neptune")
    else:
        print("Failed to upload to Neptune")

if __name__ == "__main__":
    main() 