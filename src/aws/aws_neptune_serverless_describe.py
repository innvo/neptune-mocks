import boto3
import requests
from requests_aws4auth import AWS4Auth
import logging

# Load environment variables
from dotenv import load_dotenv
import os

load_dotenv()
NEPTUNE_ENDPOINT = os.getenv('NEPTUNE_ENDPOINT')
if not NEPTUNE_ENDPOINT:
    raise EnvironmentError("NEPTUNE_ENDPOINT not set in environment variables")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_cluster_status(auth):
    """Get the Neptune cluster status."""
    logger.info("Retrieving Neptune cluster status...")
    status_url = f"{NEPTUNE_ENDPOINT}/status"
    
    try:
        response = requests.get(status_url, auth=auth)
        response.raise_for_status()
        
        logger.info("Successfully retrieved cluster status")
        
        # Print cluster status information
        print("\n=== Neptune Cluster Status ===")
        print(f"HTTP Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to retrieve cluster status: {str(e)}")
        print(f"\nError retrieving cluster status: {str(e)}")

def main():
    try:
        # Initialize AWS session
        session = boto3.Session(profile_name='default')
        credentials = session.get_credentials()
        
        # Create AWS4Auth instance for Neptune endpoint
        auth = AWS4Auth(
            credentials.access_key,
            credentials.secret_key,
            session.region_name,
            'neptune-db',  # Service name for Neptune DB
            session_token=credentials.token
        )
        
        # Get and display cluster status
        get_cluster_status(auth)
        
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()