#!/usr/bin/env python3
"""
Check OpenSearch Serverless Indices

This script uses the OpenSearch client with proper AWS authentication to check indices.
"""

import boto3
import logging
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
OPENSEARCH_ENDPOINT = "https://bw65o53nclxs1l4dpbae.us-east-1.aoss.amazonaws.com"
OPENSEARCH_ROLE_ARN = "arn:aws:iam::244081531951:role/sts-deam-opensearch-fullaccess"

def create_opensearch_client():
    """Create authenticated OpenSearch client."""
    try:
        # Assume the IAM role
        logger.info(f"Assuming IAM role: {OPENSEARCH_ROLE_ARN}")
        sts_client = boto3.client('sts')
        
        # Log current identity
        current_identity = sts_client.get_caller_identity()
        logger.info(f"Current AWS identity: {current_identity['Arn']}")
        
        # Assume the role
        assumed_role = sts_client.assume_role(
            RoleArn=OPENSEARCH_ROLE_ARN,
            RoleSessionName='check-indices-session'
        )
        
        credentials = assumed_role['Credentials']
        logger.info(f"Successfully assumed role: {assumed_role['AssumedRoleUser']['AssumedRoleId']}")
        
        # Create AWS4Auth
        auth = AWS4Auth(
            credentials['AccessKeyId'],
            credentials['SecretAccessKey'],
            'us-east-1',
            'aoss',
            session_token=credentials['SessionToken']
        )
        
        # Parse endpoint
        parsed_url = urlparse(OPENSEARCH_ENDPOINT)
        host = parsed_url.netloc
        port = 443
        
        logger.info(f"Connecting to OpenSearch at {host}:{port}")
        
        # Create client
        client = OpenSearch(
            hosts=[{'host': host, 'port': port}],
            http_auth=auth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
            timeout=30,
            max_retries=3,
            retry_on_timeout=True
        )
        
        return client
        
    except Exception as e:
        logger.error(f"Failed to create OpenSearch client: {e}")
        raise

def check_indices():
    """Check available indices."""
    try:
        client = create_opensearch_client()
        
        # Try different approaches to list indices
        logger.info("Attempting to list indices...")
        
        # Method 1: Try _cat/indices
        try:
            logger.info("Trying _cat/indices...")
            response = client.cat.indices(format='json')
            logger.info(f"Found {len(response)} indices:")
            for index in response:
                logger.info(f"  - {index['index']} (docs: {index['docs.count']}, size: {index['store.size']})")
            return
        except Exception as e:
            logger.warning(f"_cat/indices failed: {e}")
        
        # Method 2: Try _cat/indices with text format
        try:
            logger.info("Trying _cat/indices with text format...")
            response = client.cat.indices()
            logger.info("Indices (text format):")
            logger.info(response)
            return
        except Exception as e:
            logger.warning(f"_cat/indices text format failed: {e}")
        
        # Method 3: Try _cluster/state
        try:
            logger.info("Trying _cluster/state...")
            response = client.cluster.state(metric='metadata')
            indices = response.get('metadata', {}).get('indices', {})
            logger.info(f"Found {len(indices)} indices:")
            for index_name, index_info in indices.items():
                logger.info(f"  - {index_name}")
            return
        except Exception as e:
            logger.warning(f"_cluster/state failed: {e}")
        
        # Method 4: Try direct GET request
        try:
            logger.info("Trying direct GET request...")
            response = client.transport.perform_request('GET', '/_cat/indices?v')
            logger.info("Direct response:")
            logger.info(response)
            return
        except Exception as e:
            logger.warning(f"Direct GET request failed: {e}")
        
        logger.error("All methods to list indices failed")
        
    except Exception as e:
        logger.error(f"Failed to check indices: {e}")

if __name__ == "__main__":
    check_indices() 