import socket
import requests
import boto3
from botocore.config import Config
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process.anonymous_traversal import traversal
from gremlin_python.structure.graph import Graph

def get_neptune_endpoint():
    """Get Neptune endpoint from AWS"""
    try:
        # Initialize boto3 client
        neptune = boto3.client('neptune', config=Config(region_name='us-east-1'))
        
        # Get cluster information
        response = neptune.describe_db_clusters()
        
        # Find your cluster (modify the filter as needed)
        for cluster in response['DBClusters']:
            if 'db-neptune-1' in cluster['DBClusterIdentifier']:
                return cluster['Endpoint']
        
        return None
    except Exception as e:
        print(f"Error getting Neptune endpoint: {str(e)}")
        return None

def test_network_connectivity(endpoint, port=8182):
    """Test basic network connectivity to Neptune"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)  # 5 second timeout
        result = sock.connect_ex((endpoint, port))
        sock.close()
        return result == 0
    except Exception as e:
        print(f"Error testing network connectivity: {str(e)}")
        return False

def test_neptune_status(endpoint):
    """Test Neptune status endpoint"""
    try:
        response = requests.get(f'https://{endpoint}:8182/status', timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"Error testing Neptune status: {str(e)}")
        return False

def test_gremlin_connection(endpoint):
    """Test Gremlin connection to Neptune"""
    try:
        # Create connection to Neptune
        connection = DriverRemoteConnection(
            f'wss://{endpoint}:8182/gremlin',
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
    print("Testing Neptune Connection from EC2...")
    
    # Get Neptune endpoint
    endpoint = get_neptune_endpoint()
    if not endpoint:
        print("✗ Could not get Neptune endpoint")
        return
    
    print(f"\nNeptune endpoint: {endpoint}")
    
    # Test Network Connectivity
    print("\n1. Testing Network Connectivity...")
    if test_network_connectivity(endpoint):
        print("✓ Network connectivity to Neptune is working")
    else:
        print("✗ Cannot establish network connection to Neptune")
        print("  Check security groups and network ACLs")
        return
    
    # Test Neptune Status
    print("\n2. Testing Neptune Status...")
    if test_neptune_status(endpoint):
        print("✓ Neptune status endpoint is accessible")
    else:
        print("✗ Could not access Neptune status endpoint")
        print("  Check IAM permissions and security groups")
        return
    
    # Test Gremlin Connection
    print("\n3. Testing Gremlin Connection...")
    if test_gremlin_connection(endpoint):
        print("✓ Successfully connected to Neptune via Gremlin")
    else:
        print("✗ Failed to connect to Neptune via Gremlin")
        print("  Check IAM permissions and security groups")
        return
    
    print("\nAll tests passed! Neptune connection is working correctly.")

if __name__ == "__main__":
    main() 