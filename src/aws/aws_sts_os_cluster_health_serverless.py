import boto3
import requests
from requests_aws4auth import AWS4Auth
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# OpenSearch Serverless endpoint
OPENSEARCH_ENDPOINT = 'https://utrkg13gnjqpmyz93250.us-east-1.aoss.amazonaws.com'

def get_cluster_health(auth):
    """Get the cluster health from OpenSearch Serverless."""
    logger.info("Retrieving cluster health...")
    health_url = f"{OPENSEARCH_ENDPOINT}/_search"
    
    try:
        # Add required headers for OpenSearch Serverless
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Amz-Security-Token': auth.session_token
        }
        
        response = requests.get(health_url, auth=auth, headers=headers)
        response.raise_for_status()
        
        health_data = response.json()
        logger.info("Successfully retrieved cluster health")
        
        # Print cluster health information
        print("\n=== OpenSearch Serverless Cluster Health ===")
        print(f"Status: {health_data.get('status', 'N/A')}")
        print(f"Number of Nodes: {health_data.get('number_of_nodes', 'N/A')}")
        print(f"Active Shards: {health_data.get('active_shards', 'N/A')}")
        print(f"Active Primary Shards: {health_data.get('active_primary_shards', 'N/A')}")
        print(f"Relocating Shards: {health_data.get('relocating_shards', 'N/A')}")
        print(f"Initializing Shards: {health_data.get('initializing_shards', 'N/A')}")
        print(f"Unassigned Shards: {health_data.get('unassigned_shards', 'N/A')}")
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to retrieve cluster health: {str(e)}")
        print(f"\nError retrieving cluster health: {str(e)}")

def main():
    try:
        # Initialize AWS session
        session = boto3.Session(profile_name='default')
        credentials = session.get_credentials()
        
        # Create AWS4Auth instance for OpenSearch Serverless
        auth = AWS4Auth(
            credentials.access_key,
            credentials.secret_key,
            session.region_name,
            'aoss',  # Service name for OpenSearch Serverless
            session_token=credentials.token
        )
        
        # Get and display cluster health
        get_cluster_health(auth)
        
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()