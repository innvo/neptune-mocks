import boto3
import requests
from requests_aws4auth import AWS4Auth
import json

def check_cluster_health():
    # OpenSearch endpoint
    host = 'https://search-sts-deam-es-iam-s5lekmvl3ssmabtrxj74t5aa2i.us-east-1.es.amazonaws.com'
    path = '/_cluster/health'
    
    # Get AWS credentials using default profile
    session = boto3.Session()
    credentials = session.get_credentials()
    
    # Create AWS4Auth instance
    auth = AWS4Auth(
        credentials.access_key,
        credentials.secret_key,
        session.region_name,
        'es',
        session_token=credentials.token
    )
    
    # Make the request
    url = host + path
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = requests.get(url, auth=auth, headers=headers)
        response.raise_for_status()
        print("Cluster Health Status:")
        print(json.dumps(response.json(), indent=2))
    except requests.exceptions.RequestException as e:
        print(f"Error accessing OpenSearch: {e}")

if __name__ == "__main__":
    check_cluster_health() 