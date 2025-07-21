#!/usr/bin/env python3

import asyncio
import aiohttp
import time
import json
import statistics
import boto3
import ssl
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import argparse
import logging
import uuid
from urllib.parse import urljoin
import os

@dataclass
class BulkLoadResult:
    success: bool
    load_id: str
    status: str
    duration: float
    error: str = None
    records_loaded: int = 0
    records_failed: int = 0

class NeptuneBulkLoadTester:
    def __init__(self, endpoint: str, region: str, s3_bucket: str, iam_role_arn: str, port: int = 8182, insecure: bool = False):
        self.endpoint = endpoint
        self.region = region
        self.s3_bucket = s3_bucket
        self.iam_role_arn = iam_role_arn
        self.port = port
        self.insecure = insecure
        self.base_url = f"https://{endpoint}:{port}"
        
        # Initialize AWS clients
        self.s3_client = boto3.client('s3', region_name=region)
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Create SSL context for insecure connections
        self.ssl_context = None
        if insecure:
            self.ssl_context = ssl.create_default_context()
            self.ssl_context.check_hostname = False
            self.ssl_context.verify_mode = ssl.CERT_NONE
            self.logger.warning("SSL certificate verification disabled (insecure mode)")
        elif 'localhost' in endpoint or '127.0.0.1' in endpoint:
            # For localhost connections, we need to disable hostname verification
            # even if not explicitly in insecure mode
            self.ssl_context = ssl.create_default_context()
            self.ssl_context.check_hostname = False
            self.logger.info("Disabled hostname verification for localhost connection")

    async def test_connection(self) -> bool:
        """Test basic connectivity to Neptune endpoint"""
        url = f"{self.base_url}/status"
        
        connector = aiohttp.TCPConnector(ssl=self.ssl_context)
        
        try:
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        self.logger.info("✓ Successfully connected to Neptune endpoint")
                        return True
                    else:
                        self.logger.error(f"✗ Connection failed with status: {response.status}")
                        return False
        except ssl.SSLCertVerificationError as e:
            self.logger.error(f"✗ SSL certificate verification failed: {e}")
            if 'localhost' in self.endpoint or '127.0.0.1' in self.endpoint:
                self.logger.error("This is likely due to a tunneled connection. Try using the -k flag.")
            return False
        except Exception as e:
            self.logger.error(f"✗ Connection test failed: {e}")
            return False

    async def start_bulk_load(self, session: aiohttp.ClientSession, s3_path: str, 
                             format_type: str = "csv", parallelism: str = "MEDIUM",
                             timeout: int = 300) -> BulkLoadResult:
        """Start a bulk load operation"""
        
        url = f"{self.base_url}/loader"
        
        # Generate unique load ID
        load_id = str(uuid.uuid4())
        
        payload = {
            "source": f"s3://{self.s3_bucket}/{s3_path}",
            "format": format_type,
            "iamRoleArn": self.iam_role_arn,
            "region": self.region,
            "failOnError": "FALSE",
            "parallelism": parallelism,
            "queueRequest": "TRUE"  # Enable queuing for high concurrency
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        start_time = time.time()
        
        try:
            async with session.post(
                url, 
                json=payload, 
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                response_data = await response.json()
                
                if response.status == 200:
                    actual_load_id = response_data.get('payload', {}).get('loadId', load_id)
                    return BulkLoadResult(
                        success=True,
                        load_id=actual_load_id,
                        status="LOAD_STARTED",
                        duration=time.time() - start_time
                    )
                else:
                    return BulkLoadResult(
                        success=False,
                        load_id=load_id,
                        status="FAILED_TO_START",
                        duration=time.time() - start_time,
                        error=f"HTTP {response.status}: {response_data}"
                    )
                    
        except asyncio.TimeoutError:
            return BulkLoadResult(
                success=False,
                load_id=load_id,
                status="TIMEOUT",
                duration=time.time() - start_time,
                error="Request timeout"
            )
        except Exception as e:
            return BulkLoadResult(
                success=False,
                load_id=load_id,
                status="ERROR",
                duration=time.time() - start_time,
                error=str(e)
            )

    async def check_load_status(self, session: aiohttp.ClientSession, load_id: str) -> Dict[str, Any]:
        """Check the status of a bulk load operation"""
        
        url = f"{self.base_url}/loader/{load_id}"
        
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"status": "ERROR", "error": f"HTTP {response.status}"}
        except Exception as e:
            return {"status": "ERROR", "error": str(e)}

    async def cancel_load(self, session: aiohttp.ClientSession, load_id: str) -> bool:
        """Cancel a bulk load operation"""
        
        url = f"{self.base_url}/loader/{load_id}"
        
        try:
            async with session.delete(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                return response.status == 200
        except Exception as e:
            self.logger.error(f"Failed to cancel load {load_id}: {e}")
            return False

    async def monitor_load_completion(self, session: aiohttp.ClientSession, 
                                   load_result: BulkLoadResult, 
                                   max_wait_time: int = 600) -> BulkLoadResult:
        """Monitor a bulk load until completion or timeout"""
        
        if not load_result.success:
            return load_result
        
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            status_info = await self.check_load_status(session, load_result.load_id)
            
            current_status = status_info.get('payload', {}).get('overallStatus', {}).get('status', 'UNKNOWN')
            
            if current_status in ['LOAD_COMPLETED', 'LOAD_COMPLETED_WITH_ERRORS']:
                load_result.status = current_status
                load_result.duration = time.time() - start_time
                
                # Extract statistics
                stats = status_info.get('payload', {}).get('overallStatus', {})
                load_result.records_loaded = stats.get('totalRecords', 0) - stats.get('totalRecordsFailedOrIgnored', 0)
                load_result.records_failed = stats.get('totalRecordsFailedOrIgnored', 0)
                
                return load_result
            
            elif current_status in ['LOAD_FAILED', 'LOAD_CANCELLED']:
                load_result.success = False
                load_result.status = current_status
                load_result.duration = time.time() - start_time
                load_result.error = status_info.get('payload', {}).get('overallStatus', {}).get('fullStatus', 'Load failed')
                return load_result
            
            # Wait before next check
            await asyncio.sleep(10)
        
        # Timeout - cancel the load
        load_result.status = "TIMEOUT"
        load_result.duration = max_wait_time
        load_result.error = "Load monitoring timeout"
        await self.cancel_load(session, load_result.load_id)
        
        return load_result

    def create_sample_data_files(self, num_files: int = 10, records_per_file: int = 1000):
        """Create sample CSV files for testing"""
        
        self.logger.info(f"Creating {num_files} sample data files...")
        
        for i in range(num_files):
            filename = f"sample_data_{i}.csv"
            local_path = f"/tmp/{filename}"
            
            # Create CSV content
            with open(local_path, 'w') as f:
                f.write("~id,~label,name,age,city\n")  # Neptune CSV format with ~label
                for j in range(records_per_file):
                    f.write(f"person_{i}_{j},test,Person {i}-{j},{20 + (j % 50)},City{j % 10}\n")
            
            # Upload to S3
            try:
                self.s3_client.upload_file(local_path, self.s3_bucket, f"test-data/{filename}")
                self.logger.info(f"Uploaded {filename} to S3")
            except Exception as e:
                self.logger.error(f"Failed to upload {filename}: {e}")
            
            # Clean up local file
            os.remove(local_path)

    async def run_concurrent_bulk_loads(self, 
                                      s3_paths: List[str], 
                                      concurrency_level: int,
                                      parallelism: str = "MEDIUM",
                                      monitor_completion: bool = False) -> List[BulkLoadResult]:
        """Run concurrent bulk load operations"""
        
        # Create connector with SSL context
        connector = aiohttp.TCPConnector(
            limit=concurrency_level * 2,
            limit_per_host=concurrency_level * 2,
            ssl=self.ssl_context  # Use the SSL context from constructor
        )
        
        # Create session
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = []
            
            for i in range(concurrency_level):
                s3_path = s3_paths[i % len(s3_paths)]  # Cycle through files
                task = self.start_bulk_load(session, s3_path, "csv", parallelism)
                tasks.append(task)
            
            # Start all loads
            load_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Convert exceptions to failed results
            processed_results = []
            for i, result in enumerate(load_results):
                if isinstance(result, Exception):
                    processed_results.append(BulkLoadResult(
                        success=False,
                        load_id=f"error_{i}",
                        status="EXCEPTION",
                        duration=0,
                        error=str(result)
                    ))
                else:
                    processed_results.append(result)
            
            # Monitor completion if requested
            if monitor_completion:
                self.logger.info("Monitoring load completion...")
                completion_tasks = []
                for result in processed_results:
                    if result.success:
                        task = self.monitor_load_completion(session, result)
                        completion_tasks.append(task)
                
                if completion_tasks:
                    completed_results = await asyncio.gather(*completion_tasks, return_exceptions=True)
                    
                    # Update results with completion info
                    completed_idx = 0
                    for i, result in enumerate(processed_results):
                        if result.success:
                            if completed_idx < len(completed_results):
                                processed_results[i] = completed_results[completed_idx]
                            completed_idx += 1
            
            return processed_results

    def analyze_bulk_load_results(self, results: List[BulkLoadResult]) -> Dict[str, Any]:
        """Analyze bulk load test results"""
        
        successful_starts = [r for r in results if r.success]
        failed_starts = [r for r in results if not r.success]
        
        completed_loads = [r for r in results if r.status in ['LOAD_COMPLETED', 'LOAD_COMPLETED_WITH_ERRORS']]
        failed_loads = [r for r in results if r.status in ['LOAD_FAILED', 'TIMEOUT', 'LOAD_CANCELLED']]
        
        start_times = [r.duration for r in successful_starts]
        completion_times = [r.duration for r in completed_loads]
        
        analysis = {
            "total_loads": len(results),
            "successful_starts": len(successful_starts),
            "failed_starts": len(failed_starts),
            "completed_loads": len(completed_loads),
            "failed_loads": len(failed_loads),
            "start_success_rate": len(successful_starts) / len(results) * 100,
            "completion_success_rate": len(completed_loads) / len(results) * 100,
            "start_times": {
                "avg": statistics.mean(start_times) if start_times else 0,
                "min": min(start_times) if start_times else 0,
                "max": max(start_times) if start_times else 0,
                "median": statistics.median(start_times) if start_times else 0
            },
            "completion_times": {
                "avg": statistics.mean(completion_times) if completion_times else 0,
                "min": min(completion_times) if completion_times else 0,
                "max": max(completion_times) if completion_times else 0,
                "median": statistics.median(completion_times) if completion_times else 0
            },
            "status_breakdown": {},
            "errors": {},
            "total_records_processed": sum(r.records_loaded for r in completed_loads),
            "total_records_failed": sum(r.records_failed for r in completed_loads)
        }
        
        # Count status types
        for result in results:
            status = result.status
            analysis["status_breakdown"][status] = analysis["status_breakdown"].get(status, 0) + 1
        
        # Count errors
        for result in failed_starts + failed_loads:
            error = result.error or "Unknown error"
            analysis["errors"][error] = analysis["errors"].get(error, 0) + 1
        
        return analysis

    async def run_scaling_test(self, 
                              s3_paths: List[str], 
                              max_concurrency: int = 50,
                              step: int = 5,
                              parallelism: str = "MEDIUM",
                              monitor_completion: bool = False) -> Dict[int, Dict[str, Any]]:
        """Run bulk load tests with increasing concurrency levels"""
        
        results = {}
        
        for concurrency in range(step, max_concurrency + 1, step):
            self.logger.info(f"Testing bulk load concurrency level: {concurrency}")
            
            test_results = await self.run_concurrent_bulk_loads(
                s3_paths, concurrency, parallelism, monitor_completion
            )
            
            analysis = self.analyze_bulk_load_results(test_results)
            results[concurrency] = analysis
            
            self.logger.info(f"Concurrency {concurrency}: {analysis['start_success_rate']:.1f}% start success rate")
            if monitor_completion:
                self.logger.info(f"  Completion rate: {analysis['completion_success_rate']:.1f}%")
            
            # Longer delay between bulk load tests
            await asyncio.sleep(5)
        
        return results

    def print_bulk_load_results(self, results: Dict[int, Dict[str, Any]], monitor_completion: bool = False):
        """Print formatted bulk load test results"""
        
        print("\n" + "="*100)
        print("NEPTUNE BULK LOAD CONCURRENCY TEST RESULTS")
        print("="*100)
        
        if monitor_completion:
            print(f"{'Concurrency':<12} {'Start Success':<13} {'Completion':<12} {'Avg Start (s)':<13} {'Avg Complete (s)':<15} {'Records':<10}")
            print("-" * 85)
            
            for concurrency, analysis in results.items():
                records = analysis['total_records_processed']
                print(f"{concurrency:<12} {analysis['start_success_rate']:<12.1f}% "
                      f"{analysis['completion_success_rate']:<11.1f}% "
                      f"{analysis['start_times']['avg']:<12.3f}s "
                      f"{analysis['completion_times']['avg']:<14.3f}s "
                      f"{records:<10}")
        else:
            print(f"{'Concurrency':<12} {'Start Success':<13} {'Successful Starts':<16} {'Failed Starts':<13} {'Avg Start (s)':<13}")
            print("-" * 75)
            
            for concurrency, analysis in results.items():
                print(f"{concurrency:<12} {analysis['start_success_rate']:<12.1f}% "
                      f"{analysis['successful_starts']:<15} "
                      f"{analysis['failed_starts']:<12} "
                      f"{analysis['start_times']['avg']:<12.3f}s")
        
        print("\nDETAILED ANALYSIS:")
        print("-" * 50)
        
        for concurrency, analysis in results.items():
            print(f"\nConcurrency Level: {concurrency}")
            print(f"  Total Loads: {analysis['total_loads']}")
            print(f"  Successful Starts: {analysis['successful_starts']}")
            print(f"  Failed Starts: {analysis['failed_starts']}")
            
            if monitor_completion:
                print(f"  Completed Loads: {analysis['completed_loads']}")
                print(f"  Failed Loads: {analysis['failed_loads']}")
                print(f"  Total Records Processed: {analysis['total_records_processed']}")
                print(f"  Total Records Failed: {analysis['total_records_failed']}")
            
            print(f"  Status Breakdown:")
            for status, count in analysis['status_breakdown'].items():
                print(f"    {status}: {count}")
            
            if analysis['errors']:
                print(f"  Errors:")
                for error, count in analysis['errors'].items():
                    print(f"    {error}: {count}")

async def main():
    parser = argparse.ArgumentParser(description="Test AWS Neptune bulk load concurrency limits")
    parser.add_argument("endpoint", help="Neptune cluster endpoint (without https://)")
    parser.add_argument("region", help="AWS region")
    parser.add_argument("s3_bucket", help="S3 bucket for test data")
    parser.add_argument("iam_role_arn", help="IAM role ARN for Neptune bulk load")
    parser.add_argument("-k", "--insecure", action="store_true", 
                       help="Disable SSL certificate verification (equivalent to curl -k)")
    parser.add_argument("--port", type=int, default=8182, help="Neptune port (default: 8182)")
    parser.add_argument("--max-concurrency", type=int, default=15, help="Maximum concurrency level to test")
    parser.add_argument("--step", type=int, default=5, help="Concurrency step size")
    parser.add_argument("--parallelism", choices=["LOW", "MEDIUM", "HIGH", "OVERSUBSCRIBE"], 
                       default="MEDIUM", help="Bulk load parallelism setting")
    parser.add_argument("--monitor-completion", action="store_true", 
                       help="Monitor loads until completion (slower but more comprehensive)")
    parser.add_argument("--create-sample-data", action="store_true", 
                       help="Create sample data files in S3")
    parser.add_argument("--data-files", type=int, default=10, 
                       help="Number of sample data files to create")
    parser.add_argument("--records-per-file", type=int, default=1000, 
                       help="Number of records per sample file")
    
    args = parser.parse_args()
    
    # Validate endpoint format
    if args.endpoint.startswith('http://') or args.endpoint.startswith('https://'):
        print("Error: Please provide the endpoint without the protocol (http:// or https://)")
        print("Example: your-cluster.cluster-xxx.us-east-1.neptune.amazonaws.com")
        return
    
    # Check if endpoint looks like localhost and automatically enable insecure mode
    if 'localhost' in args.endpoint or '127.0.0.1' in args.endpoint:
        print("Detected localhost endpoint - this appears to be a tunnel setup.")
        if not args.insecure:
            print("Automatically enabling insecure mode (-k flag) for tunneled connections.")
            args.insecure = True
        else:
            print("Insecure mode already enabled for tunneled connection.")
    
    tester = NeptuneBulkLoadTester(
        endpoint=args.endpoint,
        region=args.region,
        s3_bucket=args.s3_bucket,
        iam_role_arn=args.iam_role_arn,
        port=args.port,
        insecure=args.insecure
    )
    
    # Create sample data if requested
    if args.create_sample_data:
        tester.create_sample_data_files(args.data_files, args.records_per_file)
    
    # Define S3 paths for test data
    s3_paths = [f"test-data/sample_data_{i}.csv" for i in range(args.data_files)]
    
    print(f"Starting Neptune bulk load concurrency test...")
    print(f"Endpoint: {args.endpoint}:{args.port}")
    print(f"S3 Bucket: {args.s3_bucket}")
    print(f"Max concurrency: {args.max_concurrency}")
    print(f"Parallelism: {args.parallelism}")
    print(f"Monitor completion: {args.monitor_completion}")
    print(f"SSL verification: {'Disabled' if args.insecure else 'Enabled'}")
    print(f"Using {len(s3_paths)} data files")
    
    # Test connection first
    print(f"\nTesting connection to Neptune...")
    if not await tester.test_connection():
        print("Connection test failed. Please check your endpoint and SSL settings.")
        if not args.insecure and ('localhost' in args.endpoint or '127.0.0.1' in args.endpoint):
            print("Hint: For tunneled connections, use the -k flag to disable SSL verification")
        return
    
    results = await tester.run_scaling_test(
        s3_paths=s3_paths,
        max_concurrency=args.max_concurrency,
        step=args.step,
        parallelism=args.parallelism,
        monitor_completion=args.monitor_completion
    )
    
    tester.print_bulk_load_results(results, args.monitor_completion)
    
    # Save results to JSON file
    filename = f"neptune_bulk_load_results_{int(time.time())}.json"
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to {filename}")

if __name__ == "__main__":
    asyncio.run(main())