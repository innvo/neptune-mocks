import os
import subprocess
import time
import requests
import socket
from dotenv import load_dotenv
from pathlib import Path

def load_environment_config():
    """Load configuration from .env file"""
    # Load .env file from project root
    project_root = Path(__file__).parent.parent.parent.parent
    env_file = project_root / '.env'
    
    if env_file.exists():
        load_dotenv(env_file)
        print(f"Loaded configuration from {env_file}")
    else:
        print(f"Warning: .env file not found at {env_file}")
        print("Using default configuration values")
    
    # Configuration with defaults
    config = {
        'SSH_KEY_PATH': os.getenv('SSH_KEY_PATH', 'neptune-bastion-dev.pem'),
        'BASTION_HOST': os.getenv('BASTION_HOST', '35.170.107.253'),
        'BASTION_USER': os.getenv('BASTION_USER', 'ec2-user'),
        'NEPTUNE_ENDPOINT': os.getenv('NEPTUNE_ENDPOINT', 'neptune-dev-instance-1.cz7fmvtxsrei.us-east-1.neptune.amazonaws.com'),
        'LOCAL_PORT': int(os.getenv('LOCAL_PORT', '8182')),
        'REMOTE_PORT': int(os.getenv('REMOTE_PORT', '8182')),
        'TUNNEL_TIMEOUT': int(os.getenv('TUNNEL_TIMEOUT', '30')),
        'CONNECTION_TIMEOUT': int(os.getenv('CONNECTION_TIMEOUT', '5'))
    }
    
    return config

def is_port_in_use(port: int) -> bool:
    """Check if a port is already in use"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex(('localhost', port))
            return result == 0
    except Exception:
        return False

def check_tunnel_operation(port: int, timeout: int = 5) -> bool:
    """Check if SSH tunnel is operational by testing local port connectivity"""
    print(f"Checking if tunnel is operational on port {port}...")
    
    # Check if port is in use
    if not is_port_in_use(port):
        print(f"Port {port} is not in use - tunnel may not be established")
        return False
    
    # Test connection to local tunnel endpoint
    try:
        url = f"https://localhost:{port}/status"
        response = requests.get(url, timeout=timeout, verify=False)
        
        if response.status_code == 200:
            print(f"✓ Tunnel is operational on port {port}")
            print(f"✓ Neptune status: {response.text}")
            return True
        else:
            print(f"⚠ Tunnel port {port} is open but Neptune returned status {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"✗ Tunnel check failed: {str(e)}")
        return False

def test_neptune_connection(config: dict):
    """Test connection to Neptune instance endpoint"""
    try:
        endpoint = config['NEPTUNE_ENDPOINT']
        port = config['LOCAL_PORT']
        timeout = config['CONNECTION_TIMEOUT']
        url = f"https://{endpoint}:{port}/status"
        
        print(f"\nTesting connection to Neptune instance: {endpoint}")
        print(f"Using local tunnel port: {port}")
        
        # Try to connect with a timeout
        response = requests.get(url, timeout=timeout, verify=False)
        
        if response.status_code == 200:
            print("✓ Successfully connected to Neptune instance!")
            print(f"Response: {response.text}")
            return True
        else:
            print(f"✗ Connection failed with status code: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"✗ Error connecting to Neptune instance: {str(e)}")
        return False

def create_ssh_tunnel():
    """Create SSH tunnel with environment-based configuration"""
    try:
        # Load configuration from .env
        config = load_environment_config()
        
        print("SSH Tunnel Configuration:")
        print(f"  Key Path: {config['SSH_KEY_PATH']}")
        print(f"  Bastion Host: {config['BASTION_HOST']}")
        print(f"  Bastion User: {config['BASTION_USER']}")
        print(f"  Local Port: {config['LOCAL_PORT']}")
        print(f"  Remote Port: {config['REMOTE_PORT']}")
        print(f"  Tunnel Timeout: {config['TUNNEL_TIMEOUT']}s")
        
        # Check if tunnel is already operational
        if check_tunnel_operation(config['LOCAL_PORT']):
            print("✓ SSH tunnel is already operational!")
            return True
        
        # Check if port is already in use by another process
        if is_port_in_use(config['LOCAL_PORT']):
            print(f"⚠ Port {config['LOCAL_PORT']} is already in use")
            print("This might be another SSH tunnel or different service")
            response = input("Do you want to continue? (y/N): ")
            if response.lower() != 'y':
                return False
        
        # Ensure the key file exists and has correct permissions
        key_path = Path(config['SSH_KEY_PATH'])
        if not key_path.exists():
            print(f"✗ Error: Key file {key_path} not found")
            print("Please check your SSH_KEY_PATH in .env file")
            return False
            
        # Set proper permissions for the key file
        key_path.chmod(0o400)
        
        # SSH tunnel command
        ssh_command = [
            'ssh', '-i', str(key_path),
            '-N', '-L',
            f"{config['LOCAL_PORT']}:localhost:{config['REMOTE_PORT']}",
            f"{config['BASTION_USER']}@{config['BASTION_HOST']}"
        ]
        
        print(f"\nCreating SSH tunnel to {config['BASTION_HOST']}...")
        print(f"Local port: {config['LOCAL_PORT']}")
        print(f"Remote port: {config['REMOTE_PORT']}")
        
        # Start the SSH tunnel
        process = subprocess.Popen(ssh_command)
        
        # Wait for tunnel to establish
        print("Waiting for tunnel to establish...")
        time.sleep(3)
        
        # Check if the process is still running
        if process.poll() is None:
            print("✓ SSH tunnel process started successfully!")
            
            # Wait a bit more and check if tunnel is operational
            time.sleep(2)
            
            if check_tunnel_operation(config['LOCAL_PORT'], config['CONNECTION_TIMEOUT']):
                print("✓ SSH tunnel is fully operational!")
                print("Press Ctrl+C to terminate the tunnel")
                
                try:
                    # Keep the script running to maintain the tunnel
                    while True:
                        time.sleep(1)
                        # Periodically check if tunnel is still operational
                        if not check_tunnel_operation(config['LOCAL_PORT'], 2):
                            print("⚠ Tunnel appears to have stopped working")
                            break
                except KeyboardInterrupt:
                    print("\nTerminating SSH tunnel...")
                    process.terminate()
                    return True
            else:
                print("✗ Tunnel failed to establish properly")
                process.terminate()
                return False
        else:
            print("✗ Error: SSH tunnel failed to establish")
            return False
            
    except Exception as e:
        print(f"✗ Error creating SSH tunnel: {str(e)}")
        return False

def main():
    """Main function with tunnel operation check"""
    print("=" * 60)
    print("SSH Tunnel Manager for Neptune")
    print("=" * 60)
    
    # Load configuration
    config = load_environment_config()
    
    # Check if tunnel is already operational before creating new one
    if check_tunnel_operation(config['LOCAL_PORT']):
        print("\n✓ Tunnel is already operational!")
        response = input("Do you want to create a new tunnel anyway? (y/N): ")
        if response.lower() != 'y':
            print("Exiting...")
            return
    
    # Create tunnel
    success = create_ssh_tunnel()
    
    if success:
        print("✓ SSH tunnel operation completed successfully")
    else:
        print("✗ SSH tunnel operation failed")
        print("\nTroubleshooting tips:")
        print("1. Check your .env file configuration")
        print("2. Verify SSH key file exists and has correct permissions")
        print("3. Ensure bastion host is accessible")
        print("4. Check if port is already in use by another process")

if __name__ == "__main__":
    main() 