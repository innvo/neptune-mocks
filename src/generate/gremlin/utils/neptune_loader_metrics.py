#!/usr/bin/env python3

import requests
import json
from collections import defaultdict, Counter
from urllib3.exceptions import InsecureRequestWarning
from datetime import datetime
import time

# Suppress SSL warnings for localhost connections
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

class NeptuneLoaderMetrics:
    def __init__(self, endpoint="localhost:8182"):
        self.endpoint = endpoint
        self.base_url = f"https://{endpoint}"
        
    def get_loader_jobs(self):
        """Get all loader jobs from Neptune"""
        url = f"{self.base_url}/loader"
        
        try:
            response = requests.get(url, verify=False, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error getting loader jobs: {e}")
            return None

    def get_loader_status(self, load_id):
        """Get status for a specific loader job"""
        url = f"{self.base_url}/loader/{load_id}"
        
        try:
            response = requests.get(url, verify=False, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error getting status for {load_id}: {e}")
            return None

    def collect_metrics(self):
        """Collect metrics from all loader jobs"""
        print(f"Collecting Neptune loader metrics from {self.endpoint}...")
        
        # Get all loader jobs
        jobs_data = self.get_loader_jobs()
        
        if not jobs_data:
            print("Failed to get loader jobs")
            return None
        
        payload = jobs_data.get('payload', {})
        load_ids = payload.get('loadIds', [])
        
        if not load_ids:
            print("No active loader jobs found.")
            return self.create_empty_metrics()
        
        print(f"Found {len(load_ids)} loader job(s), collecting status data...")
        
        # Initialize metrics
        metrics = {
            'summary': {
                'total_jobs': len(load_ids),
                'collection_timestamp': datetime.now().isoformat(),
                'endpoint': self.endpoint
            },
            'status_counts': Counter(),
            'status_details': defaultdict(list),
            'performance_metrics': {
                'total_records_processed': 0,
                'total_records_failed': 0,
                'avg_duration_seconds': 0,
                'completed_jobs': 0,
                'failed_jobs': 0,
                'running_jobs': 0
            },
            'job_details': []
        }
        
        total_duration = 0
        completed_count = 0
        
        # Collect data for each job
        for load_id in load_ids:
            status_data = self.get_loader_status(load_id)
            
            if not status_data:
                metrics['status_counts']['ERROR'] += 1
                metrics['status_details']['ERROR'].append({
                    'load_id': load_id,
                    'error': 'Failed to get status'
                })
                continue
            
            load_payload = status_data.get('payload', {})
            overall_status = load_payload.get('overallStatus', {})
            
            status = overall_status.get('status', 'UNKNOWN')
            total_records = overall_status.get('totalRecords', 0)
            failed_records = overall_status.get('totalRecordsFailedOrIgnored', 0)
            
            # Calculate duration
            start_time = overall_status.get('startTime', 0)
            end_time = overall_status.get('endTime', 0)
            duration_seconds = 0
            
            if start_time and end_time:
                duration_seconds = (end_time - start_time) / 1000
                total_duration += duration_seconds
                completed_count += 1
            elif start_time:
                duration_seconds = (time.time() * 1000 - start_time) / 1000
            
            # Update metrics
            metrics['status_counts'][status] += 1
            metrics['performance_metrics']['total_records_processed'] += total_records
            metrics['performance_metrics']['total_records_failed'] += failed_records
            
            # Categorize jobs
            if status in ['LOAD_COMPLETED', 'LOAD_COMPLETED_WITH_ERRORS']:
                metrics['performance_metrics']['completed_jobs'] += 1
            elif status in ['LOAD_FAILED', 'LOAD_CANCELLED']:
                metrics['performance_metrics']['failed_jobs'] += 1
            elif status in ['LOAD_IN_PROGRESS', 'LOAD_STARTED']:
                metrics['performance_metrics']['running_jobs'] += 1
            
            # Store job details
            job_detail = {
                'load_id': load_id,
                'status': status,
                'total_records': total_records,
                'failed_records': failed_records,
                'duration_seconds': duration_seconds,
                'start_time': start_time,
                'end_time': end_time
            }
            
            metrics['status_details'][status].append(job_detail)
            metrics['job_details'].append(job_detail)
        
        # Calculate averages
        if completed_count > 0:
            metrics['performance_metrics']['avg_duration_seconds'] = total_duration / completed_count
        
        return metrics

    def create_empty_metrics(self):
        """Create empty metrics structure when no jobs found"""
        return {
            'summary': {
                'total_jobs': 0,
                'collection_timestamp': datetime.now().isoformat(),
                'endpoint': self.endpoint
            },
            'status_counts': Counter(),
            'status_details': defaultdict(list),
            'performance_metrics': {
                'total_records_processed': 0,
                'total_records_failed': 0,
                'avg_duration_seconds': 0,
                'completed_jobs': 0,
                'failed_jobs': 0,
                'running_jobs': 0
            },
            'job_details': []
        }

    def print_metrics(self, metrics):
        """Print formatted metrics"""
        if not metrics:
            print("No metrics to display")
            return
        
        print("\n" + "="*80)
        print("NEPTUNE LOADER METRICS")
        print("="*80)
        
        # Summary
        summary = metrics['summary']
        print(f"Endpoint: {summary['endpoint']}")
        print(f"Total Jobs: {summary['total_jobs']}")
        print(f"Collection Time: {summary['collection_timestamp']}")
        
        # Status counts
        print(f"\nSTATUS BREAKDOWN:")
        print("-" * 50)
        if metrics['status_counts']:
            for status, count in metrics['status_counts'].most_common():
                print(f"{status:<25} {count:>5}")
        else:
            print("No jobs found")
        
        # Performance metrics
        perf = metrics['performance_metrics']
        print(f"\nPERFORMANCE METRICS:")
        print("-" * 50)
        print(f"Total Records Processed: {perf['total_records_processed']:,}")
        print(f"Total Records Failed: {perf['total_records_failed']:,}")
        print(f"Completed Jobs: {perf['completed_jobs']}")
        print(f"Failed Jobs: {perf['failed_jobs']}")
        print(f"Running Jobs: {perf['running_jobs']}")
        if perf['avg_duration_seconds'] > 0:
            print(f"Average Duration: {perf['avg_duration_seconds']:.2f} seconds")
        
        # Success rate
        total_jobs = summary['total_jobs']
        if total_jobs > 0:
            success_rate = (perf['completed_jobs'] / total_jobs) * 100
            print(f"Success Rate: {success_rate:.1f}%")
        
        # Detailed status information
        print(f"\nDETAILED STATUS INFORMATION:")
        print("-" * 50)
        for status, jobs in metrics['status_details'].items():
            if jobs:
                print(f"\n{status} ({len(jobs)} jobs):")
                for job in jobs[:5]:  # Show first 5 jobs per status
                    print(f"  - {job['load_id']}: {job['total_records']} records, "
                          f"{job['failed_records']} failed, {job['duration_seconds']:.1f}s")
                if len(jobs) > 5:
                    print(f"  ... and {len(jobs) - 5} more jobs")

    def save_metrics(self, metrics, filename=None):
        """Save metrics to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"neptune_loader_metrics_{timestamp}.json"
        
        # Convert Counter to dict for JSON serialization
        metrics_copy = metrics.copy()
        metrics_copy['status_counts'] = dict(metrics_copy['status_counts'])
        metrics_copy['status_details'] = dict(metrics_copy['status_details'])
        
        with open(filename, 'w') as f:
            json.dump(metrics_copy, f, indent=2)
        
        print(f"\nMetrics saved to: {filename}")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Collect Neptune loader metrics")
    parser.add_argument("--endpoint", default="localhost:8182", 
                       help="Neptune endpoint (default: localhost:8182)")
    parser.add_argument("--save", action="store_true", 
                       help="Save metrics to JSON file")
    parser.add_argument("--output", help="Output filename for metrics")
    
    args = parser.parse_args()
    
    # Create metrics collector
    collector = NeptuneLoaderMetrics(args.endpoint)
    
    # Collect metrics
    metrics = collector.collect_metrics()
    
    if metrics:
        # Print metrics
        collector.print_metrics(metrics)
        
        # Save if requested
        if args.save or args.output:
            collector.save_metrics(metrics, args.output)
    else:
        print("Failed to collect metrics")

if __name__ == "__main__":
    main() 