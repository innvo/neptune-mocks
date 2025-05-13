import boto3
import requests
from requests_aws4auth import AWS4Auth
import logging
import json

# Set logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Set your serverless endpoint and index
OPENSEARCH_ENDPOINT = 'https://utrkg13gnjqpmyz93250.us-east-1.aoss.amazonaws.com'
INDEX_NAME = 'your-index-name'  # <-- must exist!

def test_search(auth):
    url = f"{OPENSEARCH_ENDPOINT}/{INDEX_NAME}/_search"
    query = {
        "query": {
            "match_all": {}
        },
        "size": 1
    }

    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-Amz-Security-Token': auth.session_token
    }

    try:
        response = requests.get(url, auth=auth, headers=headers, data=json.dumps(query))
        response.raise_for_status()
        print("✅ Connection succeeded.")
        print(response.json())
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error {e.response.status_code}: {e.response.text}")
    except Exception as e:
        print(f"❌ Failed: {str(e)}")

def main():
    session = boto3.Session()
    credentials = session.get_credentials().get_frozen_credentials()
    region = session.region_name or 'us-east-1'

    auth = AWS4Auth(
        credentials.access_key,
        credentials.secret_key,
        region,
        'aoss',
        session_token=credentials.token
    )

    test_search(auth)

if __name__ == "__main__":
    main()
