import os
import subprocess
import time
import requests
from dotenv import load_dotenv

def test_neptune_connection():
    """Test connection to Neptune instance endpoint"""
    try:
        endpoint = "neptune-dev-instance-1.cz7fmvtxsrei.us-east-1.neptune.amazonaws.com"
        port = 8182
        url = f"https://{endpoint}:{port}/status"
        
        print(f"\nTesting connection to Neptune instance: {endpoint}")
        
        # Try to connect with a timeout of 5 seconds
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            print("Successfully connected to Neptune instance!")
            print("Response:", response.text)
            return True
        else:
            print(f"Connection failed with status code: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to Neptune instance: {str(e)}")
        return False

def create_ssh_tunnel():
    try:
        # Load environment variables
        load_dotenv()
        
        # SSH tunnel parameters
        key_path = 'neptune-bastion-dev.pem'
        bastion_host = '35.170.107.253'
        local_port = 8182  # Default Neptune port
        remote_port = 8182
        
        # Ensure the key file exists and has correct permissions
        if not os.path.exists(key_path):
            print(f"Error: Key file {key_path} not found")
            return False
            
        # Set proper permissions for the key file
        os.chmod(key_path, 0o400)
        
        # SSH tunnel command
        ssh_command = [
            'ssh', '-i', key_path,
            '-N', '-L',
            f'{local_port}:localhost:{remote_port}',
            f'ec2-user@{bastion_host}'
        ]
        
        print(f"Creating SSH tunnel to {bastion_host}...")
        print(f"Local port: {local_port}")
        print(f"Remote port: {remote_port}")
        
        # Start the SSH tunnel
        process = subprocess.Popen(ssh_command)
        
        # Wait a moment to ensure the tunnel is established
        time.sleep(2)
        
        # Check if the process is still running
        if process.poll() is None:
            print("SSH tunnel established successfully!")
            
            # Test connection to Neptune cluster
            if test_neptune_connection():
                print("Press Ctrl+C to terminate the tunnel")
                try:
                    # Keep the script running to maintain the tunnel
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\nTerminating SSH tunnel...")
                    process.terminate()
                    return True
            else:
                print("Terminating SSH tunnel due to connection failure...")
                process.terminate()
                return False
        else:
            print("Error: SSH tunnel failed to establish")
            return False
            
    except Exception as e:
        print(f"Error creating SSH tunnel: {str(e)}")
        return False

if __name__ == "__main__":
    create_ssh_tunnel() 