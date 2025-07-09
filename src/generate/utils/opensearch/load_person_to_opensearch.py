import json
import requests

OPENSEARCH_URL = "http://localhost:9200"
INDEX_NAME = "people"
BULK_FILE = "src/data/output/opensearch/person-bulk.json"

def create_index():
    """Create index with basic mapping if it doesn't exist."""
    url = f"{OPENSEARCH_URL}/{INDEX_NAME}"
    if requests.head(url).status_code == 404:
        print(f"Creating index: {INDEX_NAME}")
        response = requests.put(url, json={
            "mappings": {
                "properties": {
                    "names": {"type": "keyword"},
                    "aliases": {"type": "keyword"},
                    "emails": {"type": "keyword"},
                    "phones": {"type": "keyword"},
                    "addresses": {
                        "type": "nested",
                        "properties": {
                            "street": {"type": "text"},
                            "city": {"type": "keyword"},
                            "state": {"type": "keyword"},
                            "zip": {"type": "keyword"}
                        }
                    }
                }
            }
        })
        print(response.status_code, response.text)
    else:
        print(f"Index '{INDEX_NAME}' already exists.")

def load_bulk_data():
    with open(BULK_FILE, "r") as f:
        data = f.read()
    url = f"{OPENSEARCH_URL}/_bulk"
    headers = {"Content-Type": "application/x-ndjson"}
    response = requests.post(url, data=data, headers=headers)
    
    if response.status_code == 200 and not response.json().get("errors"):
        print("Bulk load successful ✅")
    else:
        print("Bulk load failed ❌")
        print(json.dumps(response.json(), indent=2))

if __name__ == "__main__":
    create_index()
    load_bulk_data()
