import subprocess
import os
import socket
import time
import requests
from pathlib import Path
from dotenv import load_dotenv

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
        'NEPTUNE_ENDPOINT': os.getenv('NEPTUNE_ENDPOINT', 'neptune-dev.cluster-cz7fmvtxsrei.us-east-1.neptune.amazonaws.com'),
        'LOCAL_PORT': int(os.getenv('LOCAL_PORT', '8182')),
        'REMOTE_PORT': int(os.getenv('REMOTE_PORT', '8182')),
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

def start_ssh_tunnel():
    """
    Starts an SSH tunnel to Neptune dev cluster in a new terminal window.
    Checks if tunnel is already operational before creating a new one.
    """
    # Load configuration from .env
    config = load_environment_config()
    
    print("SSH Tunnel Configuration:")
    print(f"  Key Path: {config['SSH_KEY_PATH']}")
    print(f"  Bastion Host: {config['BASTION_HOST']}")
    print(f"  Bastion User: {config['BASTION_USER']}")
    print(f"  Local Port: {config['LOCAL_PORT']}")
    print(f"  Remote Port: {config['REMOTE_PORT']}")
    
    # Check if tunnel is already operational
    if check_tunnel_operation(config['LOCAL_PORT']):
        print("✓ SSH tunnel is already operational!")
        response = input("Do you want to start a new tunnel anyway? (y/N): ")
        if response.lower() != 'y':
            print("Exiting...")
            return True
    
    # Check if port is already in use by another process
    if is_port_in_use(config['LOCAL_PORT']):
        print(f"⚠ Port {config['LOCAL_PORT']} is already in use")
        print("This might be another SSH tunnel or different service")
        response = input("Do you want to continue? (y/N): ")
        if response.lower() != 'y':
            return False
    
    # Get the directory where this script is located
    script_dir = Path(__file__).parent.parent.parent
    
    # Path to the SSH key
    key_path = script_dir / config['SSH_KEY_PATH']
    
    # Ensure the key file exists
    if not key_path.exists():
        print(f"✗ Error: SSH key file not found at {key_path}")
        print("Please check your SSH_KEY_PATH in .env file")
        return False
    
    # SSH tunnel command
    ssh_command = [
        "ssh",
        "-L", f"{config['LOCAL_PORT']}:{config['NEPTUNE_ENDPOINT']}:{config['REMOTE_PORT']}",
        "-i", str(key_path),
        f"{config['BASTION_USER']}@{config['BASTION_HOST']}"
    ]
    
    # Command to open new terminal window with the SSH command
    terminal_command = [
        "osascript",
        "-e",
        f'tell app "Terminal" to do script "{" ".join(ssh_command)}"'
    ]
    
    try:
        # Open new terminal window with SSH command
        subprocess.run(terminal_command, check=True)
        print("✓ SSH tunnel started in new terminal window")
        
        # Wait a moment for the tunnel to establish
        print("Waiting for tunnel to establish...")
        time.sleep(5)
        
        # Check if tunnel is operational
        if check_tunnel_operation(config['LOCAL_PORT'], config['CONNECTION_TIMEOUT']):
            print("✓ SSH tunnel is fully operational!")
            return True
        else:
            print("⚠ SSH tunnel started but may not be fully operational yet")
            print("Please check the terminal window for any error messages")
            return False
            
    except Exception as e:
        print(f"✗ Failed to start SSH tunnel: {str(e)}")
        return False

def main():
    """Main function with tunnel operation check"""
    print("=" * 60)
    print("SSH Tunnel Starter for Neptune")
    print("=" * 60)
    
    success = start_ssh_tunnel()
    
    if success:
        print("✓ SSH tunnel operation completed successfully")
    else:
        print("✗ SSH tunnel operation failed")
        print("\nTroubleshooting tips:")
        print("1. Check your .env file configuration")
        print("2. Verify SSH key file exists and has correct permissions")
        print("3. Ensure bastion host is accessible")
        print("4. Check if port is already in use by another process")
        print("5. Check the terminal window for SSH error messages")

if __name__ == "__main__":
    main()
