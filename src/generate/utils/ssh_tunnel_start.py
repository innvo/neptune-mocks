import subprocess
import os
from pathlib import Path

def start_ssh_tunnel():
    """
    Starts an SSH tunnel to Neptune dev cluster in a new terminal window.
    """
    # Get the directory where this script is located
    script_dir = Path(__file__).parent.parent.parent
    
    # Path to the SSH key
    key_path = script_dir / "neptune-bastion-dev.pem"
    
    # Ensure the key file exists
    if not key_path.exists():
        raise FileNotFoundError(f"SSH key file not found at {key_path}")
    
    # SSH tunnel command
    ssh_command = [
        "ssh",
        "-L", "8182:neptune-dev.cluster-cz7fmvtxsrei.us-east-1.neptune.amazonaws.com:8182",
        "-i", str(key_path),
        "ec2-user@35.170.107.253"
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
        print("SSH tunnel started in new terminal window")
    except Exception as e:
        print(f"Failed to start SSH tunnel: {str(e)}")
        raise

if __name__ == "__main__":
    start_ssh_tunnel()
