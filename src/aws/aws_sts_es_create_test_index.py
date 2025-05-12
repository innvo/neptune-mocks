import boto3
import requests
from requests_aws4auth import AWS4Auth
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ✅ Replace with your actual Serverless endpoint and test index
OPENSEARCH_ENDPOINT = 'https://utrkg13gnjqpmyz93250.us-east-1.aoss.amazonaws.com'
INDEX_NAME = 'test-index'  # Use a real or new index name
DOC_ID = 'doc-001'  # Can be anything

def put_document(auth):
    url = f"{OPENSEARCH_ENDPOINT}/{INDEX_NAME}/_doc/{DOC_ID}"

    # Sample document to insert
    document = {
        "name": "Test User",
        "email": "test@example.com",
        "timestamp": "2025-05-02T12:00:00Z"
    }

    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-Amz-Security-Token': auth.session_token
    }

    try:
        logger.info("Sending PUT request to OpenSearch Serverless...")
        response = requests.put(url, auth=auth, headers=headers, data=json.dumps(document))
        response.raise_for_status()
        logger.info("✅ Successfully inserted document into OpenSearch Serverless.")
        print(json.dumps(response.json(), indent=2))
    except requests.exceptions.HTTPError as e:
        logger.error(f"❌ HTTP Error {e.response.status_code}: {e.response.text}")
    except Exception as e:
        logger.error(f"❌ General error: {str(e)}")

def main():
    try:
        session = boto3.Session(profile_name='default')  # Or omit for default creds
        credentials = session.get_credentials().get_frozen_credentials()
        region = session.region_name or 'us-east-1'

        auth = AWS4Auth(
            credentials.access_key,
            credentials.secret_key,
            region,
            'aoss',
            session_token=credentials.token
        )

        put_document(auth)

    except Exception as e:
        logger.error(f"❌ Initialization error: {str(e)}")

if __name__ == "__main__":
    main()
