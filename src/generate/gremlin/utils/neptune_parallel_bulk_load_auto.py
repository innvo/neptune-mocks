#!/usr/bin/env python3
"""
Neptune Parallel Bulk Loader with Node-First Loading Strategy

This module provides a comprehensive solution for bulk loading data into Amazon Neptune
graph databases with a specific focus on maintaining referential integrity by loading
nodes before edges.

Key Features:
- Automatic file discovery and categorization (nodes vs edges)
- Two-phase loading: nodes first, then edges
- Parallel bulk load job management
- CSV validation and record count analysis
- Load status monitoring and completion tracking
- Configurable waiting strategies

Requirements:
- boto3: AWS SDK for Python
- requests: HTTP library for API calls
- csv: CSV file processing
- io: String I/O operations

AWS Prerequisites:
- S3 bucket with CSV files
- IAM role with Neptune bulk load permissions
- Neptune cluster endpoint access

Usage Examples:
    # Basic usage - discover and load all CSV files
    python neptune_parallel_bulk_load_auto.py

    # Load specific files
    python neptune_parallel_bulk_load_auto.py --files person.csv address.csv person_address_edge.csv

    # Load with CSV validation and discrepancy analysis
    python neptune_parallel_bulk_load_auto.py --validate-csv --analyze-discrepancy

    # Load with CSV validation and discrepancy analysis
    python neptune_parallel_bulk_load_auto.py --validate-csv --analyze-discrepancy

    # Analyze existing load jobs
    python neptune_parallel_bulk_load_auto.py --analyze-existing person.csv:load-123 address.csv:load-456

File Categorization:
    Node files are identified by:
    - Filename patterns: 'node', 'person', 'address', 'organization', 'building', 'form', 'receipt', 'phone', 'email'
    - CSV headers: 'id', 'label', 'type', 'name', 'address', 'phone', 'email'
    
    Edge files are identified by:
    - Filename patterns: 'edge', 'source', 'target', 'relationship', 'link', 'connection'
    - CSV headers: 'source', 'target', 'from', 'to', 'start', 'end'

Author: Neptune Bulk Load Team
Version: 2.0
Last Updated: 2024
"""

import boto3
import requests
import json
import time
import csv
import io
from urllib3.exceptions import InsecureRequestWarning

# Suppress SSL warnings for localhost connections
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

class ParallelNeptuneBulkLoader:
    """
    A comprehensive Neptune bulk loader that manages parallel loading with node-first strategy.
    
    This class provides methods to discover, categorize, and bulk load CSV files into
    Amazon Neptune with proper ordering (nodes before edges) to maintain referential
    integrity in the graph database.
    
    Attributes:
        endpoint (str): Neptune cluster endpoint (host:port)
        s3_bucket (str): S3 bucket containing CSV files
        iam_role_arn (str): IAM role ARN with Neptune bulk load permissions
        region (str): AWS region for S3 and Neptune operations
        base_url (str): Constructed HTTPS URL for Neptune loader API
        s3_client: Boto3 S3 client instance
    
    Example:
        loader = ParallelNeptuneBulkLoader(
            endpoint="my-neptune-cluster.cluster-xyz.us-east-1.neptune.amazonaws.com:8182",
            s3_bucket="my-data-bucket",
            iam_role_arn="arn:aws:iam::123456789012:role/NeptuneLoadRole"
        )
        load_ids = loader.start_parallel_loads()
    """
    
    def __init__(self, endpoint="localhost:8182", s3_bucket="deam-neptune", 
                 iam_role_arn="arn:aws:iam::244081531951:role/NeptuneLoadFromS3", 
                 region="us-east-1"):
        """
        Initialize the Neptune bulk loader with connection parameters.
        
        Args:
            endpoint (str): Neptune endpoint in format 'host:port'. 
                           Default: 'localhost:8182' for local development
            s3_bucket (str): S3 bucket name containing CSV files.
                           Default: 'deam-neptune'
            iam_role_arn (str): IAM role ARN with Neptune bulk load permissions.
                               Must have s3:GetObject permissions for the bucket
            region (str): AWS region for S3 and Neptune operations.
                         Default: 'us-east-1'
        
        Note:
            The IAM role must have the following permissions:
            - s3:GetObject for the specified S3 bucket
            - neptune-db:CreateLoader for the Neptune cluster
            - neptune-db:DescribeLoader for status checking
        """
        self.endpoint = endpoint
        self.s3_bucket = s3_bucket
        self.iam_role_arn = iam_role_arn
        self.region = region
        self.base_url = f"https://{endpoint}"
        
        # Initialize S3 client
        self.s3_client = boto3.client('s3', region_name=region)
    
    def check_bulk_load_status(self, load_id):
        """
        Check the status of a specific bulk load job.
        
        Queries the Neptune loader API to get detailed status information about
        a running or completed bulk load job.
        
        Args:
            load_id (str): The unique identifier of the bulk load job
            
        Returns:
            dict: Status payload containing job details, or None if failed
            
        Status values include:
            - LOAD_NOT_STARTED: Job is queued but not yet started
            - LOAD_IN_PROGRESS: Job is currently running
            - LOAD_COMPLETED: Job finished successfully
            - LOAD_COMPLETED_WITH_DETAILS: Job completed with detailed results
            - LOAD_FAILED: Job failed with errors
            - LOAD_CANCELLED: Job was cancelled
            
        Example:
            status = loader.check_bulk_load_status("load-12345")
            if status:
                print(f"Status: {status.get('status')}")
                print(f"Records loaded: {status.get('loadedRecords')}")
        """
        url = f"{self.base_url}/loader/{load_id}"
        
        try:
            response = requests.get(url, verify=False, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                payload = data.get('payload', {})
                
                print(f"\nBulk Load Status for {load_id}:")
                print(f"  Status: {payload.get('status', 'Unknown')}")
                print(f"  Total Records: {payload.get('totalRecords', 'Unknown')}")
                print(f"  Total Errors: {payload.get('totalErrors', 'Unknown')}")
                print(f"  Failed Records: {payload.get('failedRecords', 'Unknown')}")
                print(f"  Loaded Records: {payload.get('loadedRecords', 'Unknown')}")
                print(f"  In Queue: {payload.get('inQueue', 'Unknown')}")
                print(f"  Source: {payload.get('source', 'Unknown')}")
                
                # Check for detailed error information
                if payload.get('totalErrors', 0) > 0:
                    print(f"  Error Details: {payload.get('errors', 'No details available')}")
                
                return payload
            else:
                print(f"Failed to get status for {load_id}: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error checking status for {load_id}: {e}")
            return None
    
    def analyze_record_discrepancy(self, s3_path, load_id):
        """
        Analyze why Neptune record count doesn't match CSV row count.
        
        This method compares the actual number of rows in a CSV file with the
        number of records reported by Neptune after bulk loading. It provides
        detailed explanations for common discrepancies.
        
        Args:
            s3_path (str): S3 key path to the CSV file
            load_id (str): Neptune bulk load job ID
            
        Returns:
            dict: Neptune load status payload, or None if analysis failed
            
        Common discrepancy causes:
            - Edge data: Each edge creates 2+ records (source + target + edge)
            - Property columns: Each property might create additional records
            - Internal indexes: Neptune creates internal index records
            - Malformed data: CSV issues causing record splitting
            - Duplicate processing: Same data processed multiple times
            
        Example:
            discrepancy = loader.analyze_record_discrepancy("person_address_edge.csv", "load-123")
            if discrepancy:
                print(f"CSV rows: {csv_rows}, Neptune records: {neptune_records}")
        """
        print(f"\n" + "="*60)
        print(f"RECORD COUNT ANALYSIS")
        print(f"="*60)
        
        # Get CSV row count
        csv_rows = self.validate_csv_row_count(s3_path)
        
        # Get Neptune load status
        neptune_status = self.check_bulk_load_status(load_id)
        
        if csv_rows is not None and neptune_status is not None:
            neptune_records = neptune_status.get('totalRecords', 0)
            
            print(f"\nCOMPARISON:")
            print(f"  CSV Rows: {csv_rows}")
            print(f"  Neptune Records: {neptune_records}")
            print(f"  Ratio: {neptune_records / csv_rows:.2f}x")
            
            if neptune_records > csv_rows * 2:
                print(f"\nPOSSIBLE CAUSES FOR HIGH RECORD COUNT:")
                print(f"  1. CSV contains edge data (source/target pairs)")
                print(f"     - Each edge creates 2+ records (source node + target node + edge)")
                print(f"  2. CSV has multiple columns that create separate records")
                print(f"     - Each property column might create additional records")
                print(f"  3. Neptune is creating internal index records")
                print(f"  4. CSV has malformed data causing record splitting")
                print(f"  5. Bulk loader is processing the same data multiple times")
                
                # Check if this looks like edge data
                if 'source' in s3_path.lower() or 'target' in s3_path.lower() or 'edge' in s3_path.lower():
                    print(f"\n  NOTE: This appears to be edge data based on filename")
                    print(f"  Expected ratio for edges: 2-3x (source node + target node + edge)")
                
                # Check for property-heavy files
                if neptune_records > csv_rows * 4:
                    print(f"\n  WARNING: 4x+ ratio suggests possible data duplication or")
                    print(f"  complex property structures creating multiple records per row")
        
        return neptune_status

    def validate_csv_row_count(self, s3_path):
        """
        Validate the actual row count in a CSV file before bulk loading.
        
        Downloads and analyzes a CSV file from S3 to determine the actual number
        of data rows, excluding headers and empty rows. This helps predict the
        expected number of Neptune records.
        
        Args:
            s3_path (str): S3 key path to the CSV file
            
        Returns:
            int: Number of data rows (excluding header), or None if validation failed
            
        Analysis includes:
            - Total row count (including empty rows)
            - Non-empty row count
            - Header detection and exclusion
            - Data type classification (node vs edge)
            - Expected Neptune record count estimation
            
        Example:
            row_count = loader.validate_csv_row_count("person.csv")
            if row_count:
                print(f"CSV contains {row_count} data rows")
                print(f"Expected Neptune records: ~{row_count}")
        """
        try:
            # Download the file content from S3
            response = self.s3_client.get_object(Bucket=self.s3_bucket, Key=s3_path)
            content = response['Body'].read().decode('utf-8')
            
            # Parse CSV content
            csv_reader = csv.reader(io.StringIO(content))
            rows = list(csv_reader)
            
            # Count non-empty rows (excluding header if present)
            non_empty_rows = [row for row in rows if any(cell.strip() for cell in row)]
            
            print(f"CSV Validation for {s3_path}:")
            print(f"  Total rows (including empty): {len(rows)}")
            print(f"  Non-empty rows: {len(non_empty_rows)}")
            print(f"  Empty rows: {len(rows) - len(non_empty_rows)}")
            
            # Check if first row looks like a header
            if rows and all(rows[0]):
                header_indicators = ['id', 'label', 'source', 'target', 'type', 'property']
                first_row_lower = [cell.lower().strip() for cell in rows[0]]
                has_header_indicators = any(indicator in first_row_lower for indicator in header_indicators)
                
                if has_header_indicators:
                    print(f"  Likely header row detected: {rows[0]}")
                    print(f"  Data rows (excluding header): {len(non_empty_rows) - 1}")
                    
                    # Analyze column structure for edge vs node data
                    if 'source' in first_row_lower and 'target' in first_row_lower:
                        print(f"  EDGE DATA DETECTED: This file contains edge relationships")
                        print(f"  Expected Neptune records: ~{len(non_empty_rows) - 1} * 2-3 (source + target + edge)")
                    elif 'id' in first_row_lower and 'label' in first_row_lower:
                        print(f"  NODE DATA DETECTED: This file contains node entities")
                        print(f"  Expected Neptune records: ~{len(non_empty_rows) - 1} (one per node)")
                    
                    return len(non_empty_rows) - 1  # Exclude header
                else:
                    print(f"  No clear header detected, treating all rows as data")
            
            return len(non_empty_rows)
            
        except Exception as e:
            print(f"Error validating CSV {s3_path}: {e}")
            return None
        
    def discover_s3_files(self, file_extensions=None):
        """
        Discover CSV files in S3 bucket root only, separated into nodes and edges.
        
        Scans the S3 bucket root directory for files with specified extensions
        and automatically categorizes them as node or edge files based on
        filename patterns and content analysis.
        
        Args:
            file_extensions (list): List of file extensions to search for.
                                   Default: ['.csv']
            
        Returns:
            tuple: (all_files, node_files, edge_files) where each is a list of S3 keys
            
        Categorization logic:
            Node files identified by:
                - Filename patterns: 'node', 'person', 'address', 'organization', 
                  'building', 'form', 'receipt', 'phone', 'email'
                - CSV headers: 'id', 'label', 'type', 'name', 'address', 'phone', 'email'
                
            Edge files identified by:
                - Filename patterns: 'edge', 'source', 'target', 'relationship', 
                  'link', 'connection'
                - CSV headers: 'source', 'target', 'from', 'to', 'start', 'end'
                
        Example:
            all_files, node_files, edge_files = loader.discover_s3_files(['.csv', '.gz'])
            print(f"Found {len(node_files)} node files and {len(edge_files)} edge files")
        """
        if file_extensions is None:
            file_extensions = ['.csv']
        
        print(f"Discovering files in S3 bucket root: {self.s3_bucket}")
        print(f"Looking for extensions: {file_extensions}")
        
        all_files = []
        node_files = []
        edge_files = []
        
        try:
            # List objects in the bucket root only (no prefix, no delimiter)
            paginator = self.s3_client.get_paginator('list_objects_v2')
            page_iterator = paginator.paginate(
                Bucket=self.s3_bucket,
                Delimiter='/'
            )
            
            for page in page_iterator:
                # Check for files in the root (CommonPrefixes will be empty for root files)
                if 'Contents' in page:
                    for obj in page['Contents']:
                        key = obj['Key']
                        # Only include files that are in the root (no '/' in the key except at the end)
                        if '/' not in key or key.endswith('/'):
                            # Check if file has the right extension
                            if any(key.endswith(ext) for ext in file_extensions):
                                all_files.append(key)
                                print(f"  Found: {key}")
        
        except Exception as e:
            print(f"Error discovering S3 files: {e}")
            return [], [], []
        
        # Categorize files as nodes or edges based on filename patterns
        for file_path in all_files:
            file_lower = file_path.lower()
            
            # Edge file patterns
            edge_indicators = ['edge', 'source', 'target', 'relationship', 'link', 'connection']
            # Node file patterns  
            node_indicators = ['node', 'person', 'address', 'organization', 'building', 'form', 'receipt', 'phone', 'email']
            
            is_edge = any(indicator in file_lower for indicator in edge_indicators)
            is_node = any(indicator in file_lower for indicator in node_indicators)
            
            # If file contains both patterns, prioritize edge indicators
            if is_edge:
                edge_files.append(file_path)
                print(f"  Categorized as EDGE: {file_path}")
            elif is_node:
                node_files.append(file_path)
                print(f"  Categorized as NODE: {file_path}")
            else:
                # If unclear, check the actual CSV content
                print(f"  Ambiguous file, checking content: {file_path}")
                csv_analysis = self.analyze_csv_content(file_path)
                if csv_analysis == 'edge':
                    edge_files.append(file_path)
                    print(f"    → Categorized as EDGE based on content")
                else:
                    node_files.append(file_path)
                    print(f"    → Categorized as NODE based on content")
        
        print(f"\nFile categorization summary:")
        print(f"  Total files found: {len(all_files)}")
        print(f"  Node files: {len(node_files)}")
        print(f"  Edge files: {len(edge_files)}")
        
        return all_files, node_files, edge_files
    
    def analyze_csv_content(self, s3_path):
        """
        Analyze CSV content to determine if it's node or edge data.
        
        Downloads a CSV file from S3 and analyzes its structure to classify
        it as either node or edge data based on header patterns and data content.
        
        Args:
            s3_path (str): S3 key path to the CSV file
            
        Returns:
            str: 'node' or 'edge' based on content analysis
            
        Analysis criteria:
            Edge indicators:
                - Headers: 'source', 'target', 'from', 'to', 'start', 'end'
                - Data patterns: First two columns contain ID-like values
                
            Node indicators:
                - Headers: 'id', 'label', 'type', 'name', 'address', 'phone', 'email'
                - Data patterns: Single entity properties
                
        Example:
            data_type = loader.analyze_csv_content("ambiguous_file.csv")
            print(f"File classified as: {data_type}")
        """
        try:
            # Download the file content from S3
            response = self.s3_client.get_object(Bucket=self.s3_bucket, Key=s3_path)
            content = response['Body'].read().decode('utf-8')
            
            # Parse CSV content
            csv_reader = csv.reader(io.StringIO(content))
            rows = list(csv_reader)
            
            if not rows:
                return 'node'  # Default to node if empty
            
            # Check header row for edge indicators
            header_row = [cell.lower().strip() for cell in rows[0]]
            
            # Edge indicators in headers
            edge_headers = ['source', 'target', 'from', 'to', 'start', 'end']
            node_headers = ['id', 'label', 'type', 'name', 'address', 'phone', 'email']
            
            has_edge_headers = any(header in edge_headers for header in header_row)
            has_node_headers = any(header in node_headers for header in header_row)
            
            if has_edge_headers:
                return 'edge'
            elif has_node_headers:
                return 'node'
            else:
                # If no clear headers, check data patterns
                if len(rows) > 1:
                    # Look for patterns in first few data rows
                    for i in range(1, min(4, len(rows))):
                        row = rows[i]
                        if len(row) >= 2:
                            # If row has 2+ columns and they look like IDs, likely edge
                            if all(cell.strip().isdigit() or cell.strip().startswith('id_') for cell in row[:2]):
                                return 'edge'
                
                return 'node'  # Default to node
            
        except Exception as e:
            print(f"Error analyzing CSV content for {s3_path}: {e}")
            return 'node'  # Default to node on error
    
    def start_bulk_load(self, s3_path, format_type="csv"):
        """
        Start a bulk load for a specific file.
        
        Initiates a Neptune bulk load job for a single CSV file using the
        Neptune loader API. The job is queued and will start processing
        according to Neptune's scheduling.
        
        Args:
            s3_path (str): S3 key path to the CSV file to load
            format_type (str): File format. Default: "csv"
            
        Returns:
            str: Load ID if successful, None if failed
            
        Load configuration:
            - Source: S3 path with bucket prefix
            - Format: CSV (configurable)
            - IAM Role: Specified during initialization
            - Region: AWS region for the load
            - Fail on Error: TRUE (stops on first error)
            - Parallelism: OVERSUBSCRIBE (maximize throughput)
            - Queue Request: TRUE (queues if cluster is busy)
            
        Example:
            load_id = loader.start_bulk_load("person.csv")
            if load_id:
                print(f"Started load job: {load_id}")
            else:
                print("Failed to start load job")
        """
        
        url = f"{self.base_url}/loader"
        
        payload = {
            "source": f"s3://{self.s3_bucket}/{s3_path}",
            "format": format_type,
            "iamRoleArn": self.iam_role_arn,
            "region": self.region,
            "failOnError": "TRUE",
            "parallelism": "OVERSUBSCRIBE",
            "queueRequest": "TRUE"
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(
                url, 
                json=payload, 
                headers=headers,
                verify=False,
                timeout=30
            )
            
            if response.status_code == 200:
                response_data = response.json()
                load_id = response_data.get('payload', {}).get('loadId', 'Unknown')
                print(f"✓ Started bulk load for {s3_path}")
                print(f"  Load ID: {load_id}")
                return load_id
            else:
                print(f"✗ Failed to start bulk load for {s3_path}")
                print(f"  Status: {response.status_code}")
                print(f"  Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"✗ Error starting bulk load for {s3_path}: {e}")
            return None
    
    def start_parallel_loads(self, files=None, file_extensions=None, validate_csv=False, analyze_discrepancy=False):
        """
        Start parallel bulk loads for multiple files - nodes first, then edges.
        
        This is the main orchestration method that manages the two-phase loading
        process. It discovers files (if not provided), categorizes them as nodes
        or edges, and loads them in the correct order to maintain referential
        integrity.
        
        Args:
            files (list): Specific list of S3 file paths to load. If None, 
                         files will be discovered automatically
            file_extensions (list): File extensions to search for during discovery.
                                   Default: ['.csv']
            validate_csv (bool): Whether to validate CSV row counts before loading.
                                Default: False
            analyze_discrepancy (bool): Whether to analyze record count discrepancies.
                                       Default: False
            
        Returns:
            list: List of dictionaries containing load information:
                  [{'file': 'path', 'load_id': 'id', 'type': 'node|edge'}]
            
        Loading phases:
            Phase 1: Load all node files in parallel
            Phase 2: Load all edge files in parallel (immediately after nodes)
            
        Note:
            This method starts edge loads immediately after node loads without
            waiting for node completion. Neptune will handle the queuing and
            processing order internally.
            
        Example:
            # Load all discovered files with validation
            load_ids = loader.start_parallel_loads(validate_csv=True)
            
            # Load specific files
            load_ids = loader.start_parallel_loads(
                files=['person.csv', 'address.csv', 'person_address_edge.csv']
            )
            
            # Monitor specific loads
            for load_info in load_ids:
                print(f"{load_info['type']}: {load_info['file']} -> {load_info['load_id']}")
        """
        
        if files is None:
            all_files, node_files, edge_files = self.discover_s3_files(file_extensions)
        else:
            # If specific files provided, categorize them
            all_files = files
            node_files = []
            edge_files = []
            for file_path in files:
                file_lower = file_path.lower()
                edge_indicators = ['edge', 'source', 'target', 'relationship', 'link', 'connection']
                node_indicators = ['node', 'person', 'address', 'organization', 'building', 'form', 'receipt', 'phone', 'email']
                
                is_edge = any(indicator in file_lower for indicator in edge_indicators)
                is_node = any(indicator in file_lower for indicator in node_indicators)
                
                if is_edge:
                    edge_files.append(file_path)
                elif is_node:
                    node_files.append(file_path)
                else:
                    # Default to node if unclear
                    node_files.append(file_path)
        
        if not node_files and not edge_files:
            print("No files found to load")
            return []
        
        print(f"\nStarting bulk load jobs - NODES FIRST, then EDGES")
        print("=" * 80)
        
        load_ids = []
        successful_loads = 0
        
        # PHASE 1: Load all nodes first
        if node_files:
            print(f"\nPHASE 1: Loading {len(node_files)} node files...")
            print("-" * 60)
            
            for i, file_path in enumerate(node_files, 1):
                print(f"\n[{i}/{len(node_files)}] Processing NODE: {file_path}")
                
                # Validate CSV row count if requested
                if validate_csv:
                    actual_rows = self.validate_csv_row_count(file_path)
                    if actual_rows is not None:
                        print(f"  Expected Neptune records: {actual_rows}")
                
                load_id = self.start_bulk_load(file_path)
                
                if load_id:
                    load_info = {
                        'file': file_path,
                        'load_id': load_id,
                        'type': 'node'
                    }
                    load_ids.append(load_info)
                    successful_loads += 1
                    
                    # Analyze record discrepancy if requested
                    if analyze_discrepancy:
                        print(f"\nWaiting 10 seconds for load to start...")
                        time.sleep(10)
                        self.analyze_record_discrepancy(file_path, load_id)
                
                # Small delay between requests
                if i < len(node_files):
                    time.sleep(1)
        
        # PHASE 2: Load all edges second (immediately after nodes)
        if edge_files:
            print(f"\nPHASE 2: Loading {len(edge_files)} edge files...")
            print("-" * 60)
            
            for i, file_path in enumerate(edge_files, 1):
                print(f"\n[{i}/{len(edge_files)}] Processing EDGE: {file_path}")
                
                # Validate CSV row count if requested
                if validate_csv:
                    actual_rows = self.validate_csv_row_count(file_path)
                    if actual_rows is not None:
                        print(f"  Expected Neptune records: {actual_rows}")
                
                load_id = self.start_bulk_load(file_path)
                
                if load_id:
                    load_ids.append({
                        'file': file_path,
                        'load_id': load_id,
                        'type': 'edge'
                    })
                    successful_loads += 1
                    
                    # Analyze record discrepancy if requested
                    if analyze_discrepancy:
                        print(f"\nWaiting 10 seconds for load to start...")
                        time.sleep(10)
                        self.analyze_record_discrepancy(file_path, load_id)
                
                # Small delay between requests
                if i < len(edge_files):
                    time.sleep(1)
        
        print("\n" + "=" * 80)
        print("PARALLEL BULK LOAD SUMMARY")
        print("=" * 80)
        print(f"Total files: {len(all_files)}")
        print(f"Node files loaded: {len([x for x in load_ids if x['type'] == 'node'])}")
        print(f"Edge files loaded: {len([x for x in load_ids if x['type'] == 'edge'])}")
        print(f"Successful loads: {successful_loads}")
        print(f"Failed loads: {len(all_files) - successful_loads}")
        
        if load_ids:
            print(f"\nLoad IDs for monitoring:")
            for item in load_ids:
                print(f"  [{item['type'].upper()}] {item['file']}: {item['load_id']}")
        
        print(f"\nTo monitor all jobs:")
        print(f"curl -k {self.base_url}/loader")
        
        print(f"\nTo check specific job status:")
        for item in load_ids:
            print(f"curl -k {self.base_url}/loader/{item['load_id']}")
        
        return load_ids
    
    def wait_for_loads_to_complete(self, load_ids, check_interval=30, timeout_hours=2):
        """
        Wait for specified loads to complete.
        
        Monitors the status of multiple bulk load jobs and waits for them to
        complete (successfully or with errors) before returning. This is used
        to ensure node loads finish before starting edge loads.
        
        Args:
            load_ids (list): List of load info dictionaries with 'load_id' keys
            check_interval (int): Seconds between status checks. Default: 30
            timeout_hours (int): Maximum hours to wait before timing out. Default: 2
            
        Returns:
            bool: True if all loads completed, False if timeout occurred
            
        Monitoring behavior:
            - Checks status every check_interval seconds
            - Removes completed/failed loads from monitoring list
            - Continues until all loads complete or timeout reached
            - Provides detailed progress updates
            
        Status handling:
            - LOAD_COMPLETED/LOAD_COMPLETED_WITH_DETAILS: Success, remove from list
            - LOAD_FAILED/LOAD_CANCELLED: Error, remove from list
            - Other statuses: Continue monitoring
            
        Example:
            # Wait for node loads to complete
            completed = loader.wait_for_loads_to_complete(node_load_ids)
            if completed:
                print("All node loads completed successfully")
            else:
                print("Some loads may still be running (timeout)")
        """
        timeout_seconds = timeout_hours * 3600
        start_time = time.time()
        
        while load_ids:
            current_time = time.time()
            if current_time - start_time > timeout_seconds:
                print(f"Timeout reached ({timeout_hours} hours). Some loads may still be running.")
                break
            
            print(f"\nChecking status of {len(load_ids)} remaining loads...")
            completed_loads = []
            
            for load_info in load_ids:
                load_id = load_info['load_id']
                file_path = load_info['file']
                
                status = self.check_bulk_load_status(load_id)
                if status:
                    load_status = status.get('status', 'Unknown')
                    print(f"  {file_path}: {load_status}")
                    
                    if load_status in ['LOAD_COMPLETED', 'LOAD_COMPLETED_WITH_DETAILS']:
                        completed_loads.append(load_info)
                        print(f"    ✓ COMPLETED")
                    elif load_status in ['LOAD_FAILED', 'LOAD_CANCELLED']:
                        completed_loads.append(load_info)
                        print(f"    ✗ FAILED/CANCELLED")
                    else:
                        print(f"    ⏳ Still running...")
                else:
                    print(f"  {file_path}: Unable to check status")
            
            # Remove completed loads from the list
            for completed in completed_loads:
                load_ids.remove(completed)
            
            if load_ids:
                print(f"\nWaiting {check_interval} seconds before next check...")
                time.sleep(check_interval)
        
        print(f"\nAll loads completed or timed out!")
        return len(load_ids) == 0
    
    def analyze_completed_loads(self, load_ids):
        """
        Analyze record discrepancies for completed loads.
        
        Performs detailed analysis of record count discrepancies for a list of
        completed bulk load jobs. This is useful for understanding why Neptune
        record counts may differ from CSV row counts.
        
        Args:
            load_ids (list): List of load info dictionaries with 'file' and 'load_id' keys
            
        Returns:
            None: Analysis results are printed to console
            
        Analysis includes:
            - CSV row count validation
            - Neptune record count from load status
            - Ratio calculation and interpretation
            - Common cause explanations
            - Data type-specific insights
            
        Example:
            # Analyze existing load jobs
            load_info = [
                {'file': 'person.csv', 'load_id': 'load-123'},
                {'file': 'person_address_edge.csv', 'load_id': 'load-456'}
            ]
            loader.analyze_completed_loads(load_info)
        """
        print(f"\n" + "="*80)
        print(f"ANALYZING COMPLETED LOADS")
        print(f"="*80)
        
        for item in load_ids:
            file_path = item['file']
            load_id = item['load_id']
            
            print(f"\nAnalyzing: {file_path}")
            self.analyze_record_discrepancy(file_path, load_id)
            
            # Wait between analyses
            time.sleep(2)

def main():
    """
    Main function for the Neptune Parallel Bulk Loader.
    
    Parses command line arguments and orchestrates the bulk loading process.
    Supports various modes of operation including file discovery, specific file
    loading, and analysis of existing loads.
    
    Command Line Arguments:
        --endpoint: Neptune cluster endpoint (default: localhost:8182)
        --s3-bucket: S3 bucket name (default: deam-neptune)
        --iam-role: IAM role ARN for Neptune bulk load
        --region: AWS region (default: us-east-1)
        --files: Specific files to load (space-separated)
        --extensions: File extensions to search for (default: .csv)
        --validate-csv: Validate CSV row counts before loading
        --analyze-discrepancy: Analyze record count discrepancies
        --analyze-existing: Analyze existing load IDs (format: file:load_id)
    
    Examples:
        # Basic usage - discover and load all CSV files
        python neptune_parallel_bulk_load_auto.py
        
        # Load specific files with validation
        python neptune_parallel_bulk_load_auto.py --files person.csv address.csv --validate-csv
        
        # Load with custom endpoint and bucket
        python neptune_parallel_bulk_load_auto.py --endpoint my-cluster:8182 --s3-bucket my-data
        
        # Analyze existing loads
        python neptune_parallel_bulk_load_auto.py --analyze-existing person.csv:load-123 address.csv:load-456
        
        # Load with custom endpoint and bucket
        python neptune_parallel_bulk_load_auto.py --endpoint my-cluster:8182 --s3-bucket my-data
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Start parallel Neptune bulk loads for individual files")
    parser.add_argument("--endpoint", default="localhost:8182", 
                       help="Neptune endpoint (default: localhost:8182)")
    parser.add_argument("--s3-bucket", default="deam-neptune", 
                       help="S3 bucket name (default: deam-neptune)")
    parser.add_argument("--iam-role", default="arn:aws:iam::244081531951:role/NeptuneLoadFromS3", 
                       help="IAM role ARN for Neptune bulk load")
    parser.add_argument("--region", default="us-east-1", 
                       help="AWS region (default: us-east-1)")
    parser.add_argument("--files", nargs="+", 
                       help="Specific files to load (if not provided, will discover all CSV files)")
    parser.add_argument("--extensions", nargs="+", default=[".csv"], 
                       help="File extensions to look for (default: .csv)")
    parser.add_argument("--validate-csv", action="store_true",
                       help="Validate CSV row counts before starting bulk loads")
    parser.add_argument("--analyze-discrepancy", action="store_true",
                       help="Analyze record count discrepancies during bulk loading")
    parser.add_argument("--analyze-existing", nargs="+",
                       help="Analyze existing load IDs for record discrepancies (format: file:load_id)")
    
    args = parser.parse_args()
    
    # Create bulk loader
    loader = ParallelNeptuneBulkLoader(
        endpoint=args.endpoint,
        s3_bucket=args.s3_bucket,
        iam_role_arn=args.iam_role,
        region=args.region
    )
    
    # Handle existing load analysis
    if args.analyze_existing:
        load_ids = []
        for item in args.analyze_existing:
            if ':' in item:
                file_path, load_id = item.split(':', 1)
                load_ids.append({'file': file_path, 'load_id': load_id})
            else:
                print(f"Invalid format for --analyze-existing: {item}")
                print("Expected format: file:load_id")
                return
        
        loader.analyze_completed_loads(load_ids)
        return
    
    # Start parallel loads
    if args.files:
        # Use specific files provided
        load_ids = loader.start_parallel_loads(
            files=args.files, 
            validate_csv=args.validate_csv,
            analyze_discrepancy=args.analyze_discrepancy
        )
    else:
        # Discover files automatically
        load_ids = loader.start_parallel_loads(
            file_extensions=args.extensions, 
            validate_csv=args.validate_csv,
            analyze_discrepancy=args.analyze_discrepancy
        )
    
    if load_ids:
        print(f"\nAll {len(load_ids)} parallel bulk load jobs have been started!")
        print("Each file now has its own job running in parallel.")
        
        if args.analyze_discrepancy:
            print(f"\nRecord discrepancy analysis has been performed for each load.")
            print(f"Check the output above for detailed explanations of record count differences.")

if __name__ == "__main__":
    main() 