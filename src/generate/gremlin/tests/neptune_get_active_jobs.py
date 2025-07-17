#!/usr/bin/env python3

import requests
import json
from urllib3.exceptions import InsecureRequestWarning
from datetime import datetime

# Suppress SSL warnings for localhost connections
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

def get_active_jobs(endpoint="localhost:8182"):
    """Get active Neptune loader jobs"""
    
    base_url = f"https://{endpoint}"
    
    print(f"Getting active Neptune loader jobs from {endpoint}...")
    print("=" * 80)
    
    # Get all loader jobs
    try:
        response = requests.get(f"{base_url}/loader", verify=False, timeout=30)
        response.raise_for_status()
        jobs_data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting loader jobs: {e}")
        return
    
    payload = jobs_data.get('payload', {})
    load_ids = payload.get('loadIds', [])
    
    if not load_ids:
        print("No active loader jobs found.")
        return
    
    print(f"Found {len(load_ids)} active job(s):")
    print("=" * 80)
    print(f"{'Load ID':<36} {'Status':<20} {'Records':<10} {'Failed':<10} {'Duration':<12}")
    print("-" * 80)
    
    active_jobs = []
    
    for load_id in load_ids:
        try:
            # Get status for each job
            status_response = requests.get(f"{base_url}/loader/{load_id}", verify=False, timeout=30)
            status_response.raise_for_status()
            status_data = status_response.json()
            
            load_payload = status_data.get('payload', {})
            overall_status = load_payload.get('overallStatus', {})
            
            status = overall_status.get('status', 'UNKNOWN')
            total_records = overall_status.get('totalRecords', 0)
            failed_records = overall_status.get('totalRecordsFailedOrIgnored', 0)
            
            # Calculate duration
            start_time = overall_status.get('startTime', 0)
            end_time = overall_status.get('endTime', 0)
            duration = "N/A"
            
            if start_time and end_time:
                duration_seconds = (end_time - start_time) / 1000
                duration = f"{duration_seconds:.1f}s"
            elif start_time:
                duration = "Running"
            
            print(f"{load_id:<36} {status:<20} {total_records:<10} {failed_records:<10} {duration:<12}")
            
            # Store job info
            job_info = {
                'load_id': load_id,
                'status': status,
                'total_records': total_records,
                'failed_records': failed_records,
                'duration': duration,
                'start_time': start_time,
                'end_time': end_time
            }
            active_jobs.append(job_info)
            
        except requests.exceptions.RequestException as e:
            print(f"{load_id:<36} {'ERROR':<20} {'N/A':<10} {'N/A':<10} {'N/A':<12}")
            print(f"  Error: {e}")
    
    print("-" * 80)
    
    # Summary
    status_counts = {}
    for job in active_jobs:
        status = job['status']
        status_counts[status] = status_counts.get(status, 0) + 1
    
    print(f"\nSUMMARY:")
    print("-" * 30)
    for status, count in status_counts.items():
        print(f"{status}: {count} job(s)")
    
    # Show running jobs specifically
    running_jobs = [job for job in active_jobs if job['status'] in ['LOAD_IN_PROGRESS', 'LOAD_STARTED']]
    if running_jobs:
        print(f"\nRUNNING JOBS ({len(running_jobs)}):")
        print("-" * 30)
        for job in running_jobs:
            print(f"  {job['load_id']}: {job['total_records']} records processed")
    
    return active_jobs

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Get active Neptune loader jobs")
    parser.add_argument("--endpoint", default="localhost:8182", 
                       help="Neptune endpoint (default: localhost:8182)")
    parser.add_argument("--json", action="store_true", 
                       help="Output in JSON format")
    parser.add_argument("--save", help="Save results to JSON file")
    
    args = parser.parse_args()
    
    # Get active jobs
    active_jobs = get_active_jobs(args.endpoint)
    
    if active_jobs and (args.json or args.save):
        output_data = {
            'timestamp': datetime.now().isoformat(),
            'endpoint': args.endpoint,
            'total_jobs': len(active_jobs),
            'jobs': active_jobs
        }
        
        if args.json:
            print("\nJSON Output:")
            print(json.dumps(output_data, indent=2))
        
        if args.save:
            with open(args.save, 'w') as f:
                json.dump(output_data, f, indent=2)
            print(f"\nResults saved to: {args.save}")

if __name__ == "__main__":
    main() 