import boto3
import requests
from requests_aws4auth import AWS4Auth
import json

def get_opensearch_client():
    # Create a session using your AWS credentials
    session = boto3.Session(profile_name='default')
    credentials = session.get_credentials()
    
    # Get the credentials
    aws_access_key = credentials.access_key
    aws_secret_key = credentials.secret_key
    aws_session_token = credentials.token
    
    # Create AWS4Auth instance
    region = 'us-east-1'  # Replace with your region if different
    service = 'es'
    
    auth = AWS4Auth(
        aws_access_key,
        aws_secret_key,
        region,
        service,
        session_token=aws_session_token
    )
    
    return auth

def check_cluster_health():
    # OpenSearch endpoint
    host = 'https://search-sts-deam-es-3z4qexncsuhwmwt2tdyc7cfjyq.aos.us-east-1.on.aws'
    path = '/_cluster/health'
    
    # Get the authenticated client
    auth = get_opensearch_client()
    
    # Make the request
    url = host + path
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = requests.get(url, auth=auth, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes
        print("Cluster Health Status:")
        print(json.dumps(response.json(), indent=2))
    except requests.exceptions.RequestException as e:
        print(f"Error accessing OpenSearch: {e}")

if __name__ == "__main__":
    check_cluster_health() 