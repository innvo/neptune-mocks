import boto3
import requests
from requests_aws4auth import AWS4Auth
import json
import logging
import urllib3

# Disable insecure HTTPS warnings for Neptune self-signed certs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Endpoints and index name
NEPTUNE_ENDPOINT = 'https://localhost:8182/openCypher'
OPENSEARCH_ENDPOINT = 'https://utrkg13gnjqpmyz93250.us-east-1.aoss.amazonaws.com'
INDEX_NAME = 'aws-neptune'

# HTTP headers
NEPTUNE_HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

BASE_OS_HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}


def fetch_vertices():
    """Fetch all vertices from Neptune using OpenCypher"""
    logger.info("Fetching vertices from Neptune (OpenCypher)...")
    query = {'query': 'MATCH (n) RETURN n'}
    try:
        response = requests.post(NEPTUNE_ENDPOINT, headers=NEPTUNE_HEADERS, json=query, verify=False)
        response.raise_for_status()

        body = response.json()
        results = body.get('results', [])
        if not results:
            logger.warning("No vertices returned from Neptune.")
            return []

        documents = []
        for idx, row in enumerate(results):
            record = row.get('n') or row
            if not isinstance(record, dict):
                logger.warning(f"Skipping unexpected record at index {idx}: {record}")
                continue

            doc = {}

            # Neptune OpenCypher format: { id, labels, properties }
            doc['id'] = record.get('id')
            doc['labels'] = record.get('labels', [])
            properties = record.get('properties', {})

            # Merge properties into the root document
            if isinstance(properties, dict):
                for k, v in properties.items():
                    doc[k] = v

            documents.append(doc)

        logger.info(f"Fetched {len(documents)} vertices.")
        if documents:
            logger.debug("First vertex sample: %s", json.dumps(documents[0], indent=2))
        return documents

    except requests.exceptions.RequestException as e:
        logger.error(f"Error querying Neptune OpenCypher: {str(e)}")
        raise


def create_index(auth):
    """Create the OpenSearch index if it doesn't exist"""
    url = f"{OPENSEARCH_ENDPOINT}/{INDEX_NAME}"
    headers = BASE_OS_HEADERS.copy()
    headers['X-Amz-Security-Token'] = auth.session_token
    try:
        logger.info(f"Creating index '{INDEX_NAME}'...")
        response = requests.put(url, auth=auth, headers=headers)
        logger.debug(f"Create index response: {response.status_code} - {response.text}")
        if response.status_code == 200:
            logger.info(f"Index '{INDEX_NAME}' created.")
        elif response.status_code == 400 and 'resource_already_exists_exception' in response.text:
            logger.info(f"Index '{INDEX_NAME}' already exists.")
        else:
            response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to create index '{INDEX_NAME}': {str(e)}")
        raise


def index_documents(auth, documents):
    """Index each document into OpenSearch"""
    headers = BASE_OS_HEADERS.copy()
    headers['X-Amz-Security-Token'] = auth.session_token
    total = len(documents)
    logger.info(f"Indexing {total} documents into OpenSearch...")

    success = 0
    failure = 0

    for idx, doc in enumerate(documents, start=1):
        doc_id = str(doc.get('id') or f"doc_{idx}")
        url = f"{OPENSEARCH_ENDPOINT}/{INDEX_NAME}/_doc/{doc_id}"
        try:
            response = requests.put(url, auth=auth, headers=headers, json=doc)
            response.raise_for_status()
            logger.info(f"[{idx}/{total}] Indexed document ID={doc_id}")
            success += 1
        except requests.exceptions.RequestException as e:
            logger.error(f"[{idx}/{total}] Failed to index document {doc_id}: {str(e)}")
            failure += 1

    logger.info(f"Indexing complete: {success} succeeded, {failure} failed.")


def main():
    try:
        # Set up AWS credentials
        session = boto3.Session(profile_name='default')
        creds = session.get_credentials().get_frozen_credentials()
        region = session.region_name or 'us-east-1'
        auth = AWS4Auth(creds.access_key, creds.secret_key, region, 'aoss', session_token=creds.token)

        # Run ETL
        vertices = fetch_vertices()
        create_index(auth)
        index_documents(auth, vertices)

        logger.info("ETL process completed successfully.")
    except Exception as e:
        logger.error(f"ETL process failed: {str(e)}")
        print(f"Error: {str(e)}")


if __name__ == '__main__':
    main()
