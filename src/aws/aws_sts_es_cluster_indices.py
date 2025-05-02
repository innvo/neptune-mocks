import boto3
import requests
from requests_aws4auth import AWS4Auth
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# OpenSearch endpoint
# OPENSEARCH_ENDPOINT = 'https://search-sts-deam-es-3z4qexncsuhwmwt2tdyc7cfjyq.us-east-1.es.amazonaws.com'  #User/password
OPENSEARCH_ENDPOINT = 'https://search-sts-deam-es-iam-s5lekmvl3ssmabtrxj74t5aa2i.us-east-1.es.amazonaws.com'  #IAM'

def get_indices(auth):
    """Get the list of indices from OpenSearch."""
    logger.info("Retrieving indices...")
    indices_url = f"{OPENSEARCH_ENDPOINT}/_cat/indices?format=json"
    
    try:
        # Add required headers for OpenSearch
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Amz-Security-Token': auth.session_token
        }
        
        response = requests.get(indices_url, auth=auth, headers=headers)
        response.raise_for_status()
        
        indices_data = response.json()
        logger.info(f"Successfully retrieved {len(indices_data)} indices")
        
        # Print indices in a formatted table
        print("\n=== OpenSearch Indices ===")
        print(f"Total Indices: {len(indices_data)}")
        print("\n{:<30} {:<10} {:<10} {:<15} {:<15}".format(
            "Index Name", "Health", "Status", "Docs Count", "Store Size"))
        print("-" * 80)
        
        for index in indices_data:
            print("{:<30} {:<10} {:<10} {:<15} {:<15}".format(
                index['index'],
                index['health'],
                index['status'],
                index['docs.count'],
                index['store.size']
            ))
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to retrieve indices: {str(e)}")
        print(f"\nError retrieving indices: {str(e)}")

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
            'es',  # Changed from 'aoss' to 'es' for regular OpenSearch
            session_token=credentials.token
        )
        
        # Get and display indices
        get_indices(auth)
        
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()