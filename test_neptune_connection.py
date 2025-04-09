import socket
import requests
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process.anonymous_traversal import traversal
from gremlin_python.structure.graph import Graph

def test_ssh_tunnel():
    """Test if the SSH tunnel is active on port 8182"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 8182))
        sock.close()
        return result == 0
    except Exception as e:
        print(f"Error testing SSH tunnel: {str(e)}")
        return False

def test_neptune_status():
    """Test Neptune status endpoint"""
    try:
        response = requests.get('http://localhost:8182/status')
        return response.status_code == 200
    except Exception as e:
        print(f"Error testing Neptune status: {str(e)}")
        return False

def test_gremlin_connection():
    """Test Gremlin connection to Neptune"""
    try:
        # Create connection to Neptune
        connection = DriverRemoteConnection(
            'ws://localhost:8182/gremlin',
            'g'
        )
        
        # Create graph traversal source
        g = traversal().withRemote(connection)
        
        # Try a simple query
        result = g.V().limit(1).toList()
        
        # Close connection
        connection.close()
        
        return True
    except Exception as e:
        print(f"Error testing Gremlin connection: {str(e)}")
        return False

def main():
    print("Testing Neptune Connection...")
    
    # Test SSH Tunnel
    print("\n1. Testing SSH Tunnel...")
    if test_ssh_tunnel():
        print("✓ SSH Tunnel is active on port 8182")
    else:
        print("✗ SSH Tunnel is not active. Please ensure the tunnel is running.")
        print("  Run: ssh -i /path/to/key.pem -L 8182:neptune-endpoint:8182 ec2-user@bastion-host")
        return
    
    # Test Neptune Status
    print("\n2. Testing Neptune Status...")
    if test_neptune_status():
        print("✓ Neptune status endpoint is accessible")
    else:
        print("✗ Could not access Neptune status endpoint")
        return
    
    # Test Gremlin Connection
    print("\n3. Testing Gremlin Connection...")
    if test_gremlin_connection():
        print("✓ Successfully connected to Neptune via Gremlin")
    else:
        print("✗ Failed to connect to Neptune via Gremlin")
        return
    
    print("\nAll tests passed! Neptune connection is working correctly.")

if __name__ == "__main__":
    main() 