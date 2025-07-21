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
    """Load bulk data by splitting the file into chunks to avoid size limits."""
    url = f"{OPENSEARCH_URL}/_bulk"
    headers = {"Content-Type": "application/x-ndjson"}
    
    total_records = 0
    total_errors = 0
    CHUNK_SIZE = 5000  # Smaller chunks to avoid circuit breaker
    
    print(f"📦 Loading bulk data in chunks of {CHUNK_SIZE} records...")
    print(f"🌐 Using cluster endpoint: {OPENSEARCH_URL}")
    
    with open(BULK_FILE, "r") as f:
        chunk_lines = []
        chunk_count = 0
        
        for line_num, line in enumerate(f, 1):
            chunk_lines.append(line.strip())
            
            # When we have enough lines for a chunk (2 lines per record: action + data)
            if len(chunk_lines) >= CHUNK_SIZE * 2:
                chunk_count += 1
                print(f"Processing chunk {chunk_count}...")
                
                # Send the chunk
                chunk_data = "\n".join(chunk_lines) + "\n"
                response = requests.post(url, data=chunk_data, headers=headers)
                
                if response.status_code == 200:
                    result = response.json()
                    chunk_records = len(result.get('items', []))
                    chunk_errors = sum(1 for item in result.get('items', []) 
                                     if 'index' in item and item['index'].get('error'))
                    
                    total_records += chunk_records
                    total_errors += chunk_errors
                    
                    print(f"  Chunk {chunk_count}: {chunk_records} records, {chunk_errors} errors")
                else:
                    print(f"  Chunk {chunk_count} failed: {response.status_code}")
                    print(f"  Response: {response.text}")
                    return
                
                # Clear the chunk for the next iteration
                chunk_lines = []
        
        # Send the remaining lines as the final chunk
        if chunk_lines:
            chunk_count += 1
            print(f"Processing final chunk {chunk_count}...")
            
            chunk_data = "\n".join(chunk_lines) + "\n"
            response = requests.post(url, data=chunk_data, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                chunk_records = len(result.get('items', []))
                chunk_errors = sum(1 for item in result.get('items', []) 
                                 if 'index' in item and item['index'].get('error'))
                
                total_records += chunk_records
                total_errors += chunk_errors
                
                print(f"  Final chunk: {chunk_records} records, {chunk_errors} errors")
            else:
                print(f"  Final chunk failed: {response.status_code}")
                print(f"  Response: {response.text}")
                return
    
    # Summary
    print(f"\n✅ Bulk load completed!")
    print(f"📊 Total records indexed: {total_records}")
    print(f"❌ Total errors: {total_errors}")
    
    if total_errors > 0:
        print(f"⚠️  {total_errors} records failed to index")

if __name__ == "__main__":
    create_index()
    load_bulk_data()
