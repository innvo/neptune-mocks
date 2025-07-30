#!/usr/bin/env python3
"""
OpenSearch Bulk Loader for Gremlin CSV Files - High Performance Version

This script loads Neptune/Gremlin format CSV files from S3 bucket into OpenSearch.
Supports both nodes and edges with proper type conversion and indexing strategies.

Performance Optimizations:
- Parallel file processing with multiple workers
- Optimized batch sizes and connection pooling
- Streaming CSV processing to reduce memory usage
- Concurrent bulk indexing operations
- Intelligent retry logic with exponential backoff
- Connection reuse and keep-alive
- Optimized OpenSearch client configuration

Requirements:
- AWS credentials configured
- OpenSearch endpoint accessible
- S3 bucket readable

Usage:
    python load_csv_opensearch.py
    python load_csv_opensearch.py --file specific_file.csv
    python load_csv_opensearch.py --prefix nodes/
    python load_csv_opensearch.py --workers 8 --batch-size 50000
"""

import argparse
import csv
import logging
import os
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Tuple, Any, Optional
from urllib.parse import urlparse
from queue import Queue
import multiprocessing as mp
from dotenv import load_dotenv

import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
from tqdm import tqdm

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('opensearch_bulk_load.log')
    ]
)
logger = logging.getLogger(__name__)

# Configuration from environment variables
OPENSEARCH_ENDPOINT = os.getenv('AWS_OPENSEARCH_HOST', 'https://localhost:9200')
S3_BUCKET = os.getenv('S3_BUCKET', 'deam-neptune')
OPENSEARCH_ROLE_ARN = os.getenv('OPENSEARCH_ROLE_ARN', 'arn:aws:iam::244081531951:role/sts-deam-opensearch-fullaccess')

# Performance configuration
DEFAULT_BATCH_SIZE = 50000  # Increased from 100000 for better memory management
DEFAULT_WORKERS = min(8, mp.cpu_count())  # Use CPU cores but cap at 8
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 1  # Reduced for faster retries
CONNECTION_POOL_SIZE = 20  # Increased connection pool
REQUEST_TIMEOUT = 120  # Increased timeout for large batches


class HighPerformanceGremlinCSVLoader:
    """High-performance loader for Gremlin format CSV files from S3 into OpenSearch."""
    
    def __init__(self, opensearch_endpoint: str, aws_region: str = 'us-east-1', 
                 role_arn: str = None, workers: int = DEFAULT_WORKERS, 
                 batch_size: int = DEFAULT_BATCH_SIZE):
        """
        Initialize the high-performance loader.
        
        Args:
            opensearch_endpoint: OpenSearch endpoint URL
            aws_region: AWS region for authentication
            role_arn: IAM role ARN to assume for OpenSearch authentication
            workers: Number of parallel workers
            batch_size: Batch size for bulk indexing
        """
        self.endpoint = opensearch_endpoint
        self.region = aws_region
        self.role_arn = role_arn
        self.workers = workers
        self.batch_size = batch_size
        
        # Performance configuration
        self.max_retries = DEFAULT_MAX_RETRIES
        self.retry_delay = DEFAULT_RETRY_DELAY
        self.connection_pool_size = CONNECTION_POOL_SIZE
        self.request_timeout = REQUEST_TIMEOUT
        
        # Thread-safe client management
        self._client_lock = threading.Lock()
        self.opensearch_clients = {}  # Thread-local clients
        self.s3_client = None
        
        # Statistics
        self.stats = {
            'files_processed': 0,
            'documents_indexed': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }
        
        # Initialize S3 client
        self._init_s3_client()
        
        # Log configuration
        logger.info(f"HighPerformanceGremlinCSVLoader initialized:")
        logger.info(f"  - Workers: {self.workers}")
        logger.info(f"  - Batch size: {self.batch_size:,}")
        logger.info(f"  - Connection pool size: {self.connection_pool_size}")
        logger.info(f"  - Request timeout: {self.request_timeout}s")
        if self.role_arn:
            logger.info(f"  - IAM role: {self.role_arn}")
    
    def _init_s3_client(self):
        """Initialize S3 client with optimized configuration."""
        try:
            # Configure S3 client for high performance
            config = boto3.session.Config(
                max_pool_connections=50,  # Increased connection pool
                retries={'max_attempts': 3, 'mode': 'adaptive'},
                read_timeout=60,
                connect_timeout=30
            )
            self.s3_client = boto3.client('s3', config=config)
            logger.info("S3 client initialized with high-performance configuration")
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            raise
    
    def _get_thread_local_client(self) -> OpenSearch:
        """Get thread-local OpenSearch client with optimized configuration."""
        thread_id = threading.get_ident()
        
        with self._client_lock:
            if thread_id not in self.opensearch_clients:
                self.opensearch_clients[thread_id] = self._create_optimized_opensearch_client()
        
        return self.opensearch_clients[thread_id]
    
    def _create_optimized_opensearch_client(self) -> OpenSearch:
        """Create optimized OpenSearch client with performance enhancements."""
        try:
            # Authentication setup
            if self.role_arn:
                logger.debug(f"Assuming IAM role: {self.role_arn}")
                sts_client = boto3.client('sts')
                
                try:
                    assumed_role = sts_client.assume_role(
                        RoleArn=self.role_arn,
                        RoleSessionName=f'opensearch-loader-{threading.get_ident()}'
                    )
                    
                    credentials = assumed_role['Credentials']
                    auth = AWS4Auth(
                        credentials['AccessKeyId'],
                        credentials['SecretAccessKey'],
                        self.region,
                        'es',
                        session_token=credentials['SessionToken']
                    )
                    
                except Exception as role_error:
                    logger.error(f"Failed to assume role {self.role_arn}: {role_error}")
                    raise Exception(f"Role assumption failed: {role_error}")
            else:
                credentials = boto3.Session().get_credentials()
                if not credentials:
                    raise Exception("AWS credentials not found.")
                
                auth = AWS4Auth(
                    credentials.access_key,
                    credentials.secret_key,
                    self.region,
                    'es',
                    session_token=credentials.token
                )
            
            parsed_url = urlparse(self.endpoint)
            host = parsed_url.netloc
            
            # Handle port in the URL
            if ':' in host:
                host, port_str = host.rsplit(':', 1)
                try:
                    port = int(port_str)
                except ValueError:
                    # If port parsing fails, use default based on scheme
                    port = 443 if parsed_url.scheme == 'https' else 80
            else:
                # No port in URL, use default based on scheme
                port = 443 if parsed_url.scheme == 'https' else 80
            
            # Determine SSL settings based on scheme
            use_ssl = parsed_url.scheme == 'https'
            verify_certs = use_ssl and not host.startswith('localhost')  # Don't verify certs for localhost
            
            logger.debug(f"OpenSearch connection config: host={host}, port={port}, use_ssl={use_ssl}, verify_certs={verify_certs}")
            
            # Create optimized client with built-in connection pooling
            client = OpenSearch(
                hosts=[{'host': host, 'port': port}],
                http_auth=auth,
                use_ssl=use_ssl,
                verify_certs=verify_certs,
                ssl_assert_hostname=False,
                ssl_show_warn=False,
                connection_class=RequestsHttpConnection,
                timeout=self.request_timeout,
                max_retries=self.max_retries,
                retry_on_timeout=True,
                http_compress=True,  # Enable compression
                http_compress_level=6,  # Balanced compression level
                pool_maxsize=self.connection_pool_size,
                pool_maxsize_per_host=self.connection_pool_size,
                keep_alive=True,
                keep_alive_timeout=30,
                max_keep_alive_requests=100
            )
            
            logger.debug(f"Created optimized OpenSearch client for thread {threading.get_ident()}")
            return client
            
        except Exception as e:
            logger.error(f"Failed to create OpenSearch client: {e}")
            raise
    
    def validate_permissions(self) -> bool:
        """Validate OpenSearch permissions."""
        try:
            client = self._get_thread_local_client()
            test_index = "test-permissions-check"
            
            try:
                client.indices.exists(index=test_index)
                logger.info("Basic OpenSearch permissions validated successfully")
                return True
            except Exception as e:
                if "403" in str(e) or "authorizationexception" in str(e).lower():
                    logger.error("Failed OpenSearch permissions check")
                    logger.error("Your IAM user/role lacks basic OpenSearch permissions")
                    return False
                else:
                    logger.warning(f"Permission check inconclusive: {e}")
                    return True
                    
        except Exception as e:
            logger.error(f"Could not validate permissions: {e}")
            return False
    
    def list_s3_csv_files(self, bucket_name: str, prefix: str = "", root_only: bool = False) -> List[str]:
        """List CSV files in S3 bucket with optimized pagination."""
        try:
            paginator = self.s3_client.get_paginator('list_objects_v2')
            csv_files = []
            
            for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix):
                if 'Contents' in page:
                    for obj in page['Contents']:
                        key = obj['Key']
                        if key.lower().endswith('.csv'):
                            if root_only:
                                if '/' not in key or key.count('/') == 0:
                                    csv_files.append(key)
                            else:
                                csv_files.append(key)
            
            location_desc = "root directory" if root_only else f"prefix '{prefix}'" if prefix else "bucket"
            logger.info(f"Found {len(csv_files)} CSV files in s3://{bucket_name} ({location_desc})")
            return sorted(csv_files)
            
        except Exception as e:
            logger.error(f"Failed to list S3 files: {e}")
            raise
    
    def _parse_gremlin_header(self, header: str) -> Tuple[str, str]:
        """Parse Gremlin CSV header to extract field name and type."""
        if ':' in header:
            field_name, field_type = header.split(':', 1)
            return field_name, field_type
        else:
            return header, 'String'
    
    def _convert_field_value(self, value: str, field_type: str) -> Any:
        """Convert CSV field value to appropriate Python type with optimized performance."""
        if not value or value.strip() == '':
            return None
            
        try:
            if field_type == 'String':
                return value.strip('"')
            elif field_type == 'Int':
                return int(value)
            elif field_type == 'Double':
                return float(value)
            elif field_type == 'Boolean':
                return value.lower() in ('true', '1', 'yes')
            elif field_type == 'Date':
                return value.strip('"')
            elif field_type.endswith('[]'):
                base_type = field_type[:-2]
                array_values = value.strip('"').split(';') if value.strip('"') else []
                return [self._convert_field_value(v, base_type) for v in array_values if v]
            else:
                return value.strip('"')
                
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to convert value '{value}' to type '{field_type}': {e}")
            return value
    
    def _determine_index_name(self, csv_filename: str, label: str = None) -> str:
        """Determine appropriate index name based on file name and label."""
        base_name = os.path.basename(csv_filename).lower()
        
        # First check the ~label field content for address or person
        if label:
            label_lower = label.lower()
            if 'address' in label_lower:
                if 'edge' in base_name or 'relationship' in base_name:
                    return 'address_relationships'
                else:
                    return 'addresses'
            elif 'person' in label_lower:
                if 'edge' in base_name or 'relationship' in base_name:
                    return 'person_relationships'
                else:
                    return 'persons'
        
        # Fallback to filename-based logic if no label match
        if 'person' in base_name:
            if 'edge' in base_name or 'relationship' in base_name:
                return 'person_relationships'
            else:
                return 'persons'
        elif 'address' in base_name:
            if 'edge' in base_name:
                return 'address_relationships'
            else:
                return 'addresses'
        elif 'form' in base_name:
            if 'edge' in base_name:
                return 'form_relationships'
            else:
                return 'forms'
        elif 'phone' in base_name:
            if 'edge' in base_name:
                return 'phone_relationships'
            else:
                return 'phones'
        elif 'email' in base_name:
            if 'edge' in base_name:
                return 'email_relationships'
            else:
                return 'emails'
        elif 'edge' in base_name or '~from' in str(label):
            return 'relationships'
        else:
            name = base_name.replace('.csv', '').replace('_', '-')
            return f"gremlin-{name}"
    
    def _create_index_mapping(self, sample_doc: Dict) -> Dict:
        """Create optimized OpenSearch index mapping."""
        properties = {}
        
        for field, value in sample_doc.items():
            if field.startswith('~'):
                if field == '~id':
                    properties[field] = {"type": "keyword"}
                elif field == '~label':
                    properties[field] = {"type": "keyword"}
                elif field in ['~from', '~to']:
                    properties[field] = {"type": "keyword"}
                else:
                    properties[field] = {"type": "keyword"}
            elif isinstance(value, str):
                if field.endswith('_date') or 'date' in field.lower():
                    properties[field] = {"type": "date", "format": "yyyy-MM-dd||yyyy-MM-dd HH:mm:ss||epoch_millis"}
                else:
                    properties[field] = {"type": "text", "fields": {"keyword": {"type": "keyword"}}}
            elif isinstance(value, int):
                properties[field] = {"type": "long"}
            elif isinstance(value, float):
                properties[field] = {"type": "double"}
            elif isinstance(value, bool):
                properties[field] = {"type": "boolean"}
            elif isinstance(value, list):
                if value:
                    first_elem = value[0]
                    if isinstance(first_elem, str):
                        properties[field] = {"type": "keyword"}
                    elif isinstance(first_elem, (int, float)):
                        properties[field] = {"type": "double"}
                    else:
                        properties[field] = {"type": "keyword"}
                else:
                    properties[field] = {"type": "keyword"}
            else:
                properties[field] = {"type": "keyword"}
        
        # Optimized settings for high-performance indexing
        mapping = {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "refresh_interval": "30s",
                "index": {
                    "max_result_window": 100000,
                    "mapping": {
                        "nested_fields": {
                            "limit": 100
                        }
                    }
                }
            },
            "mappings": {
                "properties": properties
            }
        }
        
        return mapping
    
    def create_or_update_index(self, index_name: str, mapping: Dict) -> bool:
        """Create or update OpenSearch index with optimized settings."""
        try:
            client = self._get_thread_local_client()
            
            try:
                if client.indices.exists(index=index_name):
                    logger.info(f"Index '{index_name}' already exists")
                    return True
            except Exception as check_error:
                logger.warning(f"Could not check if index exists: {check_error}")
            
            logger.info(f"Creating index '{index_name}'...")
            response = client.indices.create(
                index=index_name,
                body=mapping
            )
            
            if response.get('acknowledged'):
                logger.info(f"Created index '{index_name}' successfully")
                return True
            else:
                logger.error(f"Failed to create index '{index_name}': {response}")
                return False
                
        except Exception as e:
            if "resource_already_exists_exception" in str(e).lower():
                logger.info(f"Index '{index_name}' already exists")
                return True
            elif "authorizationexception" in str(e).lower() or "403" in str(e):
                logger.error(f"Authorization failed for index '{index_name}'. This is an IAM permissions issue.")
                logger.error("Required OpenSearch permissions:")
                logger.error("  - es:CreateIndex")
                logger.error("  - es:DescribeIndex") 
                logger.error("  - es:WriteDocument")
                logger.error("  - es:ReadDocument")
                logger.error("Please check your IAM permissions for OpenSearch access.")
                return False
            elif "security_exception" in str(e).lower():
                logger.error(f"Permission denied creating index '{index_name}'. Check IAM permissions for OpenSearch.")
                return False
            elif "invalid_index_name_exception" in str(e).lower():
                logger.error(f"Invalid index name '{index_name}'. OpenSearch has strict naming requirements.")
                return False
            else:
                logger.error(f"Error creating index '{index_name}': {e}")
                return False
    
    def _bulk_index_documents_with_retry(self, index_name: str, documents: List[Dict], 
                                       max_retries: int = 3) -> bool:
        """Bulk index documents with optimized retry logic."""
        if not documents:
            return True
        
        # Prepare bulk request body
        bulk_body = []
        for doc in documents:
            doc_id = doc.get('~id', None)
            action = {"index": {"_index": index_name}}
            if doc_id:
                action["index"]["_id"] = doc_id
            bulk_body.append(action)
            bulk_body.append(doc)
        
        for attempt in range(max_retries):
            try:
                client = self._get_thread_local_client()
                response = client.bulk(
                    body=bulk_body,
                    timeout=f"{self.request_timeout}s",
                    refresh=False,
                    request_timeout=self.request_timeout
                )
                
                # Check for errors
                if response.get('errors'):
                    error_count = 0
                    for item in response.get('items', []):
                        if 'index' in item and item['index'].get('error'):
                            error_count += 1
                            if attempt == max_retries - 1:  # Only log on final attempt
                                logger.warning(f"Index error: {item['index']['error']}")
                    
                    if error_count > 0:
                        logger.warning(f"Bulk index completed with {error_count} errors out of {len(documents)} documents")
                        if error_count > len(documents) * 0.1:  # More than 10% errors
                            raise Exception(f"Too many indexing errors: {error_count}/{len(documents)}")
                
                return True
                
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"Bulk index attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Bulk index failed after {max_retries} attempts: {e}")
                    return False
        
        return False
    
    def _process_csv_chunk(self, csv_file: str, chunk_start: int, chunk_size: int, 
                          field_info: List[Tuple[str, str]], index_name: str) -> Tuple[int, int]:
        """Process a chunk of CSV data with optimized streaming."""
        documents = []
        processed_rows = 0
        errors = 0
        
        try:
            # Download chunk from S3
            local_filename = f"/tmp/{os.path.basename(csv_file)}_chunk_{chunk_start}"
            
            # Use S3 Select for efficient chunking (if supported)
            try:
                # Try to use S3 Select for efficient chunking
                response = self.s3_client.select_object_content(
                    Bucket=S3_BUCKET,
                    Key=csv_file,
                    Expression=f"SELECT * FROM s3object s LIMIT {chunk_size} OFFSET {chunk_start}",
                    ExpressionType='SQL',
                    InputSerialization={'CSV': {'FileHeaderInfo': 'Use'}},
                    OutputSerialization={'CSV': {}}
                )
                
                # Process streaming response
                for event in response['Payload']:
                    if 'Records' in event:
                        records = event['Records']['Payload'].decode('utf-8')
                        for line in records.split('\n'):
                            if line.strip():
                                row = line.split(',')
                                doc = {}
                                for i, (field_name, field_type) in enumerate(field_info):
                                    if i < len(row):
                                        doc[field_name] = self._convert_field_value(row[i], field_type)
                                
                                documents.append(doc)
                                processed_rows += 1
                                
                                if len(documents) >= self.batch_size:
                                    if self._bulk_index_documents_with_retry(index_name, documents):
                                        self.stats['documents_indexed'] += len(documents)
                                    else:
                                        errors += len(documents)
                                    documents = []
                
            except Exception as s3_select_error:
                logger.debug(f"S3 Select not available, falling back to full download: {s3_select_error}")
                # Fallback to full download and chunk processing
                self.s3_client.download_file(S3_BUCKET, csv_file, local_filename)
                
                with open(local_filename, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    next(reader)  # Skip header
                    
                    # Skip to chunk start
                    for _ in range(chunk_start):
                        next(reader, None)
                    
                    # Process chunk
                    for _ in range(chunk_size):
                        try:
                            row = next(reader)
                            doc = {}
                            for i, (field_name, field_type) in enumerate(field_info):
                                if i < len(row):
                                    doc[field_name] = self._convert_field_value(row[i], field_type)
                            
                            documents.append(doc)
                            processed_rows += 1
                            
                            if len(documents) >= self.batch_size:
                                if self._bulk_index_documents_with_retry(index_name, documents):
                                    self.stats['documents_indexed'] += len(documents)
                                else:
                                    errors += len(documents)
                                documents = []
                                
                        except StopIteration:
                            break
                
                # Clean up
                if os.path.exists(local_filename):
                    os.remove(local_filename)
            
            # Index remaining documents
            if documents:
                if self._bulk_index_documents_with_retry(index_name, documents):
                    self.stats['documents_indexed'] += len(documents)
                else:
                    errors += len(documents)
            
            return processed_rows, errors
            
        except Exception as e:
            logger.error(f"Error processing chunk {chunk_start}-{chunk_start + chunk_size}: {e}")
            return processed_rows, len(documents) + errors
    
    def load_csv_from_s3_parallel(self, bucket_name: str, s3_key: str) -> None:
        """Load a single CSV file from S3 into OpenSearch using parallel processing."""
        logger.info(f"Processing file: s3://{bucket_name}/{s3_key}")
        
        try:
            # Get file size to determine chunking strategy
            response = self.s3_client.head_object(Bucket=bucket_name, Key=s3_key)
            file_size = response['ContentLength']
            
            # Download header to determine structure
            local_header_file = f"/tmp/{os.path.basename(s3_key)}_header"
            self.s3_client.download_file(bucket_name, s3_key, local_header_file)
            
            with open(local_header_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                headers = next(reader)
                field_info = [self._parse_gremlin_header(h) for h in headers]
            
            # Create sample document for mapping
            sample_doc = {}
            if os.path.getsize(local_header_file) > 100:  # If file has data beyond header
                with open(local_header_file, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    next(reader)  # Skip header
                    try:
                        first_row = next(reader)
                        for i, (field_name, field_type) in enumerate(field_info):
                            if i < len(first_row):
                                sample_doc[field_name] = self._convert_field_value(first_row[i], field_type)
                    except StopIteration:
                        pass
            
            # Determine index name and create mapping
            label = sample_doc.get('~label', '')
            index_name = self._determine_index_name(s3_key, label)
            mapping = self._create_index_mapping(sample_doc)
            
            if not self.create_or_update_index(index_name, mapping):
                logger.error(f"Failed to create index for {s3_key}")
                return
            
            # Clean up header file
            os.remove(local_header_file)
            
            # Calculate optimal chunk size based on file size and workers
            estimated_rows = file_size // 200  # Rough estimate: 200 bytes per row
            chunk_size = max(10000, estimated_rows // (self.workers * 4))  # Ensure reasonable chunk sizes
            
            logger.info(f"Processing {estimated_rows:,} estimated rows in chunks of {chunk_size:,}")
            
            # Process chunks in parallel
            with ThreadPoolExecutor(max_workers=self.workers) as executor:
                futures = []
                chunk_start = 0
                
                while chunk_start < estimated_rows:
                    future = executor.submit(
                        self._process_csv_chunk,
                        s3_key,
                        chunk_start,
                        chunk_size,
                        field_info,
                        index_name
                    )
                    futures.append(future)
                    chunk_start += chunk_size
                
                # Collect results
                total_processed = 0
                total_errors = 0
                
                with tqdm(total=len(futures), desc=f"Processing {os.path.basename(s3_key)}") as pbar:
                    for future in as_completed(futures):
                        try:
                            processed, errors = future.result()
                            total_processed += processed
                            total_errors += errors
                            pbar.update(1)
                        except Exception as e:
                            logger.error(f"Chunk processing failed: {e}")
                            total_errors += chunk_size
                            pbar.update(1)
                
                logger.info(f"Completed loading {total_processed:,} rows from {s3_key} into index '{index_name}'")
                if total_errors > 0:
                    logger.warning(f"Encountered {total_errors} errors during processing")
            
        except Exception as e:
            logger.error(f"Failed to process file {s3_key}: {e}")
            raise
    
    def load_all_csv_files_parallel(self, bucket_name: str, prefix: str = "", root_only: bool = False) -> None:
        """Load CSV files from S3 bucket into OpenSearch using parallel processing."""
        csv_files = self.list_s3_csv_files(bucket_name, prefix, root_only)
        
        if not csv_files:
            location_desc = "root directory" if root_only else f"prefix '{prefix}'" if prefix else "bucket"
            logger.warning(f"No CSV files found in s3://{bucket_name} ({location_desc})")
            return
        
        logger.info(f"Starting parallel bulk load of {len(csv_files)} CSV files with {self.workers} workers")
        self.stats['start_time'] = time.time()
        
        # Process files in parallel
        with ThreadPoolExecutor(max_workers=min(self.workers, len(csv_files))) as executor:
            futures = []
            
            for csv_file in csv_files:
                future = executor.submit(self.load_csv_from_s3_parallel, bucket_name, csv_file)
                futures.append((csv_file, future))
            
            # Monitor progress
            completed = 0
            failed = 0
            
            for csv_file, future in futures:
                try:
                    future.result()
                    completed += 1
                    self.stats['files_processed'] += 1
                    logger.info(f"✅ Completed {completed}/{len(csv_files)}: {csv_file}")
                except Exception as e:
                    failed += 1
                    self.stats['errors'] += 1
                    logger.error(f"❌ Failed {csv_file}: {e}")
        
        self.stats['end_time'] = time.time()
        elapsed_time = self.stats['end_time'] - self.stats['start_time']
        
        logger.info(f"🚀 Parallel bulk load completed in {elapsed_time:.2f} seconds")
        logger.info(f"📊 Statistics:")
        logger.info(f"  - Files processed: {self.stats['files_processed']}")
        logger.info(f"  - Documents indexed: {self.stats['documents_indexed']:,}")
        logger.info(f"  - Errors: {self.stats['errors']}")
        logger.info(f"  - Average rate: {self.stats['documents_indexed'] / elapsed_time:.0f} docs/sec")


def main():
    """Main entry point with performance options."""
    parser = argparse.ArgumentParser(description='High-Performance OpenSearch CSV Loader (default: processes only root directory files)')
    parser.add_argument('--prefix', default='', help='S3 prefix to filter files')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    parser.add_argument('--batch-size', type=int, default=DEFAULT_BATCH_SIZE, 
                       help=f'Batch size for bulk indexing (default: {DEFAULT_BATCH_SIZE:,})')
    parser.add_argument('--workers', type=int, default=DEFAULT_WORKERS,
                       help=f'Number of parallel workers (default: {DEFAULT_WORKERS})')
    parser.add_argument('--file', help='Process specific CSV file instead of all files')
    parser.add_argument('--test', action='store_true', help='Test mode: only list files and validate setup')
    parser.add_argument('--check-permissions', action='store_true', help='Check OpenSearch permissions and exit')
    parser.add_argument('--all-files', action='store_true', help='Process all files in bucket (not just root directory)')
    parser.add_argument('--role-arn', help='Override IAM role ARN for OpenSearch authentication')
    parser.add_argument('--performance-mode', choices=['normal', 'high', 'ultra'], default='normal',
                       help='Performance mode (default: normal)')
    
    args = parser.parse_args()
    
    # Apply performance mode settings
    if args.performance_mode == 'high':
        args.workers = min(16, mp.cpu_count())
        args.batch_size = 75000
        logger.info("🚀 High performance mode enabled")
    elif args.performance_mode == 'ultra':
        args.workers = min(32, mp.cpu_count())
        args.batch_size = 100000
        logger.info("⚡ Ultra performance mode enabled")
    
    try:
        role_arn = args.role_arn if args.role_arn else OPENSEARCH_ROLE_ARN
        logger.info(f"Using IAM role ARN: {role_arn}")
        
        # Initialize high-performance loader
        loader = HighPerformanceGremlinCSVLoader(
            OPENSEARCH_ENDPOINT, 
            args.region, 
            role_arn,
            workers=args.workers,
            batch_size=args.batch_size
        )
        
        if args.check_permissions:
            logger.info("Checking OpenSearch permissions...")
            if loader.validate_permissions():
                logger.info("✅ Permissions check passed")
            else:
                logger.error("❌ Permissions check failed")
                sys.exit(1)
            return
        
        if args.test:
            logger.info("Running in test mode...")
            # Default to root-only, use all-files flag to override
            root_only = not args.all_files
            csv_files = loader.list_s3_csv_files(S3_BUCKET, args.prefix, root_only)
            logger.info(f"Found {len(csv_files)} CSV files to process")
            for i, file in enumerate(csv_files[:5], 1):
                logger.info(f"  {i}. {file}")
            if len(csv_files) > 5:
                logger.info(f"  ... and {len(csv_files) - 5} more files")
            logger.info("Test completed successfully")
            return
        
        if args.file:
            loader.load_csv_from_s3_parallel(S3_BUCKET, args.file)
        else:
            # Default to root-only, use all-files flag to override
            root_only = not args.all_files
            if root_only:
                logger.info("🔍 Processing only files in S3 root directory (use --all-files to process all files)")
            else:
                logger.info("🔍 Processing all files in S3 bucket")
            loader.load_all_csv_files_parallel(S3_BUCKET, args.prefix, root_only)
            
        logger.info("🚀 High-performance bulk load process completed successfully")
        
    except Exception as e:
        logger.error(f"Bulk load process failed: {e}")
        if "OpenSearch" in str(e) or "endpoint" in str(e).lower():
            logger.error("Troubleshooting tips:")
            logger.error("1. Verify the OpenSearch endpoint URL")
            logger.error("2. Check IAM permissions for OpenSearch access")
            logger.error("3. Ensure IAM policies are configured correctly")
            logger.error("4. Try running with --test flag to validate S3 access first")
        sys.exit(1)


if __name__ == "__main__":
    main()