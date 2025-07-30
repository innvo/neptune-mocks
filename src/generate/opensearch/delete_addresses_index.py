#!/usr/bin/env python3
"""
Delete All Records from OpenSearch Serverless Index

This script deletes all records from the specified index in OpenSearch Serverless.
Uses proper AWS authentication with IAM role assumption.

Note: OpenSearch Serverless may have limitations with delete_by_query operations.
The script will automatically fall back to delete_index if delete_by_query fails.
"""

import boto3
import logging
import argparse
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
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
            RoleSessionName='delete-records-session'
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
            timeout=60,
            max_retries=3,
            retry_on_timeout=True
        )
        
        return client
        
    except Exception as e:
        logger.error(f"Failed to create OpenSearch client: {e}")
        raise

def check_index_exists(client, index_name):
    """Check if the index exists."""
    try:
        exists = client.indices.exists(index=index_name)
        if exists:
            # Try to get document count using count API
            try:
                count_response = client.count(index=index_name)
                doc_count = count_response.get('count', 0)
                logger.info(f"Index '{index_name}' exists with {doc_count:,} documents")
                return True, doc_count
            except Exception as count_error:
                logger.warning(f"Could not get document count: {count_error}")
                # Fallback: try to get from cat indices
                try:
                    cat_response = client.cat.indices(index=index_name, format='json')
                    if cat_response:
                        doc_count = int(cat_response[0].get('docs.count', 0))
                        logger.info(f"Index '{index_name}' exists with {doc_count:,} documents (from cat)")
                        return True, doc_count
                except Exception as cat_error:
                    logger.warning(f"Could not get count from cat indices: {cat_error}")
                
                # If all else fails, assume it exists but we can't get the count
                logger.info(f"Index '{index_name}' exists (document count unknown)")
                return True, 0
        else:
            logger.warning(f"Index '{index_name}' does not exist")
            return False, 0
    except Exception as e:
        logger.error(f"Failed to check index existence: {e}")
        return False, 0

def delete_all_records(client, index_name, method='delete_by_query'):
    """
    Delete all records from the index using the specified method.
    
    Args:
        client: OpenSearch client
        index_name: Name of the index
        method: 'delete_by_query' or 'delete_index'
    """
    try:
        if method == 'delete_by_query':
            logger.info(f"Deleting all records from index '{index_name}' using delete_by_query...")
            
            try:
                # Delete all documents using a match_all query
                response = client.delete_by_query(
                    index=index_name,
                    body={
                        "query": {
                            "match_all": {}
                        }
                    },
                    timeout=60,
                    refresh=True
                )
                
                deleted_count = response.get('deleted', 0)
                logger.info(f"Successfully deleted {deleted_count:,} documents from '{index_name}'")
                return True
                
            except Exception as delete_error:
                if "404" in str(delete_error):
                    logger.warning("delete_by_query failed with 404 - OpenSearch Serverless may not support this operation")
                    logger.info("Falling back to delete_index method...")
                    return delete_all_records(client, index_name, 'delete_index')
                else:
                    raise delete_error
            
        elif method == 'delete_index':
            logger.info(f"Deleting entire index '{index_name}'...")
            
            try:
                # Delete the entire index
                response = client.indices.delete(index=index_name)
                
                if response.get('acknowledged'):
                    logger.info(f"Successfully deleted index '{index_name}'")
                    return True
                else:
                    logger.error(f"Failed to delete index '{index_name}'")
                    return False
                    
            except Exception as delete_index_error:
                if "404" in str(delete_index_error):
                    logger.error(f"Index '{index_name}' not found or already deleted")
                    return True  # Consider this a success since the goal is achieved
                else:
                    raise delete_index_error
                
    except Exception as e:
        logger.error(f"Failed to delete records from '{index_name}': {e}")
        return False

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Delete all records from OpenSearch Serverless index')
    parser.add_argument('--index', default='addresses', help='Index name to delete records from')
    parser.add_argument('--method', choices=['delete_by_query', 'delete_index'], 
                       default='delete_index', 
                       help='Method to use: delete_by_query (keeps index) or delete_index (removes entire index)')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Check what would be deleted without actually deleting')
    parser.add_argument('--confirm', action='store_true', 
                       help='Confirm deletion (required for actual deletion)')
    
    args = parser.parse_args()
    
    try:
        # Create client
        client = create_opensearch_client()
        
        # Check if index exists
        exists, doc_count = check_index_exists(client, args.index)
        
        if not exists:
            logger.info(f"Index '{args.index}' does not exist. Nothing to delete.")
            return
        
        if args.dry_run:
            logger.info(f"DRY RUN: Would delete {doc_count:,} documents from '{args.index}' using method: {args.method}")
            return
        
        if not args.confirm:
            logger.error("⚠️  SAFETY CHECK: Use --confirm flag to actually delete records")
            logger.error(f"This would delete {doc_count:,} documents from '{args.index}'")
            logger.error("Example: python delete_addresses_index.py --confirm")
            return
        
        # Confirm with user
        if doc_count > 0:
            logger.warning(f"⚠️  ABOUT TO DELETE {doc_count:,} DOCUMENTS FROM '{args.index}'")
            logger.warning("This action cannot be undone!")
            
            # For large deletions, add extra warning
            if doc_count > 100000:
                logger.error("⚠️  LARGE DELETION WARNING: This will delete over 100k documents!")
        
        # Perform deletion
        success = delete_all_records(client, args.index, args.method)
        
        if success:
            logger.info("✅ Deletion completed successfully")
            
            # Verify deletion
            if args.method == 'delete_by_query':
                exists, new_count = check_index_exists(client, args.index)
                if exists:
                    logger.info(f"Index '{args.index}' still exists with {new_count:,} documents remaining")
                else:
                    logger.info(f"Index '{args.index}' no longer exists")
        else:
            logger.error("❌ Deletion failed")
            
    except Exception as e:
        logger.error(f"Script failed: {e}")

if __name__ == "__main__":
    main() 