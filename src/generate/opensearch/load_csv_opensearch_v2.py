import boto3
import csv
import json
from opensearchpy import OpenSearch
from opensearchpy.helpers import bulk
import io
from typing import List, Dict, Any, Tuple
import logging
import re
import os
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class GremlinCSVToOpenSearchLoader:
    def __init__(self, opensearch_config: Dict[str, Any], aws_config: Dict[str, Any] = None):
        """
        Initialize the loader with OpenSearch and AWS configurations
        
        Args:
            opensearch_config: OpenSearch connection config
            aws_config: AWS credentials and region config (optional, will use .env if not provided)
        """
        # Initialize OpenSearch client
        self.os_client = OpenSearch(**opensearch_config)
        
        # Initialize S3 client with environment variables if no config provided
        if aws_config:
            self.s3_client = boto3.client('s3', **aws_config)
        else:
            # Use environment variables from .env file
            aws_env_config = {}
            
            if os.getenv('AWS_ACCESS_KEY_ID'):
                aws_env_config['aws_access_key_id'] = os.getenv('AWS_ACCESS_KEY_ID')
            if os.getenv('AWS_SECRET_ACCESS_KEY'):
                aws_env_config['aws_secret_access_key'] = os.getenv('AWS_SECRET_ACCESS_KEY')
            if os.getenv('AWS_REGION'):
                aws_env_config['region_name'] = os.getenv('AWS_REGION')
            if os.getenv('AWS_SESSION_TOKEN'):
                aws_env_config['aws_session_token'] = os.getenv('AWS_SESSION_TOKEN')
                
            self.s3_client = boto3.client('s3', **aws_env_config)
    
    def parse_gremlin_header(self, header_row: List[str]) -> Tuple[str, Dict[str, Dict[str, Any]]]:
        """
        Parse Gremlin CSV header to identify file type and column specifications
        
        Returns:
            tuple: (file_type, column_specs)
            file_type: 'vertex' or 'edge'
            column_specs: dict with column names and their type info
        """
        column_specs = {}
        file_type = 'vertex'  # default
        
        # Check if this is an edge file by looking for ~from and ~to columns
        has_from = any('~from' in col for col in header_row)
        has_to = any('~to' in col for col in header_row)
        
        if has_from and has_to:
            file_type = 'edge'
        elif has_from or has_to:
            raise ValueError("Edge files must have both ~from and ~to columns")
        
        for col in header_row:
            # Parse column specifications like: name:String, age:Int, scores:Int[]
            col_name = col
            col_type = 'String'  # default
            cardinality = 'single'  # default
            
            # Extract type information
            if ':' in col:
                parts = col.split(':')
                col_name = parts[0]
                type_spec = parts[1]
                
                # Check for array/list notation
                if type_spec.endswith('[]'):
                    cardinality = 'set'
                    col_type = type_spec[:-2]
                else:
                    col_type = type_spec
            
            column_specs[col_name] = {
                'type': col_type,
                'cardinality': cardinality,
                'original_header': col
            }
        
        return file_type, column_specs
    
    def convert_gremlin_value(self, value: str, col_spec: Dict[str, Any]) -> Any:
        """
        Convert Gremlin CSV value based on column specification
        """
        if not value or value.strip() == '':
            return None
        
        col_type = col_spec['type']
        cardinality = col_spec['cardinality']
        
        # Handle multiple values (semicolon-separated)
        if cardinality == 'set' and ';' in value:
            values = [v.strip() for v in value.split(';') if v.strip()]
            return [self._convert_single_value(v, col_type) for v in values]
        else:
            return self._convert_single_value(value, col_type)
    
    def _convert_single_value(self, value: str, col_type: str) -> Any:
        """Convert a single value based on type"""
        value = value.strip()
        
        if col_type.lower() in ['int', 'integer']:
            return int(value)
        elif col_type.lower() in ['float', 'double']:
            return float(value)
        elif col_type.lower() == 'boolean':
            return value.lower() in ['true', '1', 'yes']
        elif col_type.lower() == 'date':
            # Keep as string for now, could add date parsing if needed
            return value
        else:  # String or unknown types
            # Remove surrounding quotes if present
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
                # Handle escaped quotes
                value = value.replace('""', '"')
            return value
    
    def read_gremlin_csv_from_s3(self, bucket_name: str, object_key: str) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Read Gremlin CSV file from S3 and parse according to Gremlin format
        
        Returns:
            tuple: (file_type, parsed_data)
        """
        try:
            logger.info(f"Reading Gremlin CSV from s3://{bucket_name}/{object_key}")
            
            # Get object from S3
            response = self.s3_client.get_object(Bucket=bucket_name, Key=object_key)
            csv_content = response['Body'].read().decode('utf-8')
            
            # Parse CSV with proper handling of quoted fields
            csv_reader = csv.reader(io.StringIO(csv_content))
            rows = list(csv_reader)
            
            if not rows:
                raise ValueError("CSV file is empty")
            
            # Parse header
            header_row = rows[0]
            file_type, column_specs = self.parse_gremlin_header(header_row)
            
            logger.info(f"Detected {file_type} file with {len(column_specs)} columns")
            
            # Parse data rows
            parsed_data = []
            for row_idx, row in enumerate(rows[1:], 1):
                if len(row) != len(header_row):
                    logger.warning(f"Row {row_idx} has {len(row)} columns, expected {len(header_row)}")
                    continue
                
                parsed_row = {}
                for col_idx, (col_name, col_spec) in enumerate(column_specs.items()):
                    if col_idx < len(row):
                        raw_value = row[col_idx]
                        parsed_row[col_name] = self.convert_gremlin_value(raw_value, col_spec)
                
                # Add metadata about the original file type
                parsed_row['_gremlin_type'] = file_type
                parsed_data.append(parsed_row)
            
            logger.info(f"Successfully parsed {len(parsed_data)} records from Gremlin CSV")
            return file_type, parsed_data
            
        except Exception as e:
            logger.error(f"Error reading Gremlin CSV from S3: {str(e)}")
            raise
    
    def prepare_bulk_data_from_gremlin(self, file_type: str, gremlin_data: List[Dict[str, Any]], 
                                     index_strategy: str = "label") -> List[Dict[str, Any]]:
        """
        Prepare Gremlin data for bulk indexing to OpenSearch
        
        Args:
            file_type: 'vertex' or 'edge'
            gremlin_data: Parsed Gremlin CSV data
            index_strategy: How to determine index name ('label', 'type', 'fixed')
        """
        bulk_data = []
        
        for row in gremlin_data:
            # Determine index name based on strategy
            if index_strategy == "label" and "~label" in row:
                index_name = row["~label"]
            elif index_strategy == "type":
                index_name = f"{file_type}s"  # 'vertices' or 'edges'
            else:
                index_name = f"gremlin-{file_type}"
            
            if not index_name:
                logger.warning(f"No index name could be determined for row: {row}")
                continue
            
            # Prepare document
            doc = row.copy()
            
            # Add some useful metadata
            doc['_document_type'] = file_type
            
            # For edges, create readable relationship info
            if file_type == 'edge' and '~from' in doc and '~to' in doc:
                doc['_relationship'] = f"{doc['~from']} -> {doc['~to']}"
            
            # Normalize index name
            normalized_index = self.normalize_index_name(index_name)
            
            # Prepare bulk action
            action = {
                "_index": normalized_index,
                "_source": doc
            }
            
            # Use ~id as document ID if available
            if "~id" in doc and doc["~id"]:
                action["_id"] = str(doc["~id"])
            
            bulk_data.append(action)
        
        return bulk_data
    
    def normalize_index_name(self, index_name: str) -> str:
        """Normalize index name to be OpenSearch compatible"""
        if not index_name:
            return "default-index"
        
        # Convert to lowercase
        normalized = str(index_name).lower()
        
        # Replace spaces and special characters with hyphens
        normalized = re.sub(r'[^a-z0-9\-_]', '-', normalized)
        
        # Remove multiple consecutive hyphens
        normalized = re.sub(r'-+', '-', normalized)
        
        # Remove leading/trailing hyphens
        normalized = normalized.strip('-')
        
        # Ensure it doesn't start with underscore, hyphen, or plus
        if normalized.startswith(('_', '-', '+')):
            normalized = 'idx-' + normalized.lstrip('_-+')
        
        return normalized or "default-index"
    
    def bulk_index_data(self, bulk_data: List[Dict[str, Any]], chunk_size: int = 1000) -> Dict[str, Any]:
        """
        Bulk index data to OpenSearch
        """
        try:
            logger.info(f"Starting bulk indexing of {len(bulk_data)} documents")
            
            # Group by index to show statistics
            index_counts = {}
            for item in bulk_data:
                idx = item['_index']
                index_counts[idx] = index_counts.get(idx, 0) + 1
            
            logger.info(f"Documents per index: {index_counts}")
            
            # Use helpers.bulk for efficient bulk indexing
            success_count, failed_items = bulk(
                self.os_client,
                bulk_data,
                chunk_size=chunk_size,
                request_timeout=60
            )
            
            result = {
                "success_count": success_count,
                "failed_count": len(failed_items) if failed_items else 0,
                "failed_items": failed_items,
                "index_counts": index_counts
            }
            
            logger.info(f"Bulk indexing completed: {success_count} successful, {result['failed_count']} failed")
            
            if failed_items:
                logger.error(f"Failed items: {failed_items}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error during bulk indexing: {str(e)}")
            raise
    
    def process_gremlin_csv_file(self, bucket_name: str, object_key: str, 
                                index_strategy: str = "label", chunk_size: int = 1000) -> Dict[str, Any]:
        """
        Complete process: read Gremlin CSV from S3 and bulk load to OpenSearch
        
        Args:
            bucket_name: S3 bucket name
            object_key: S3 object key (file path)
            index_strategy: How to determine index name ('label', 'type', 'fixed')
            chunk_size: Bulk indexing chunk size
        """
        # Read Gremlin CSV from S3
        file_type, gremlin_data = self.read_gremlin_csv_from_s3(bucket_name, object_key)
        
        # Prepare bulk data
        bulk_data = self.prepare_bulk_data_from_gremlin(file_type, gremlin_data, index_strategy)
        
        # Bulk index to OpenSearch
        result = self.bulk_index_data(bulk_data, chunk_size)
        result['file_type'] = file_type
        result['original_file'] = f"s3://{bucket_name}/{object_key}"
        
        return result
    
    def process_multiple_gremlin_files(self, bucket_name: str, file_list: List[str], 
                                     index_strategy: str = "label", chunk_size: int = 1000) -> Dict[str, List]:
        """
        Process multiple Gremlin CSV files from S3
        """
        results = {
            "successful_files": [],
            "failed_files": []
        }
        
        for file_key in file_list:
            try:
                logger.info(f"Processing Gremlin CSV file: {file_key}")
                result = self.process_gremlin_csv_file(bucket_name, file_key, index_strategy, chunk_size)
                results["successful_files"].append({
                    "file": file_key,
                    "result": result
                })
            except Exception as e:
                logger.error(f"Failed to process file {file_key}: {str(e)}")
                results["failed_files"].append({
                    "file": file_key,
                    "error": str(e)
                })
        
        return results

# Example usage
if __name__ == "__main__":
    # OpenSearch configuration (can also be moved to .env file)
    opensearch_host = os.getenv('AWS_OPENSEARCH_HOST', 'https://localhost:9200')
    
    # Parse host and port from environment variable
    if '://' in opensearch_host:
        # Handle full URL format like https://domain.com
        use_ssl = opensearch_host.startswith('https')
        host_without_protocol = opensearch_host.split('://', 1)[1]
        if ':' in host_without_protocol:
            host, port_str = host_without_protocol.rsplit(':', 1)
            try:
                port = int(port_str)
            except ValueError:
                host = host_without_protocol
                port = 443 if use_ssl else 80
        else:
            host = host_without_protocol
            port = 443 if use_ssl else 80
    else:
        # Handle simple host:port format
        use_ssl = False
        if ':' in opensearch_host:
            host, port_str = opensearch_host.rsplit(':', 1)
            try:
                port = int(port_str)
            except ValueError:
                host = opensearch_host
                port = 9200
        else:
            host = opensearch_host
            port = 9200
    
    opensearch_config = {
        'hosts': [{'host': host, 'port': port}],
        'http_compress': True,
        'use_ssl': use_ssl,
        'verify_certs': False,
        'ssl_assert_hostname': False,
        'ssl_show_warn': False,
        # 'http_auth': ('username', 'password'),  # Uncomment for authentication
    }
    
    # Initialize loader - AWS config will be automatically loaded from .env
    loader = GremlinCSVToOpenSearchLoader(
        opensearch_config=opensearch_config
        # No aws_config needed - automatically loaded from .env file
    )
    
    # Get S3 bucket from environment
    s3_bucket = os.getenv('S3_BUCKET')
    if not s3_bucket:
        raise ValueError("S3_BUCKET environment variable not set. Please set it in your .env file.")
    
    # Process single Gremlin CSV file
    result = loader.process_gremlin_csv_file(
        bucket_name=s3_bucket,
        object_key='graph-data/vertices.csv',  # Gremlin vertex file
        index_strategy='label',  # Use ~label column to determine index
        chunk_size=1000
    )
    
    print(f"Processing result: {result}")
    
    # Process multiple Gremlin files (vertices and edges)
    file_list = [
        'graph-data/vertices.csv',
        'graph-data/edges.csv',
        'graph-data/properties.csv'
    ]
    
    batch_results = loader.process_multiple_gremlin_files(
        bucket_name=s3_bucket,
        file_list=file_list,
        index_strategy='label'
    )
    
    print(f"Batch processing results: {batch_results}")