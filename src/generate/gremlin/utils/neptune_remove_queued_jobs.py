#!/usr/bin/env python3

import requests
import json
from urllib3.exceptions import InsecureRequestWarning
from datetime import datetime

# Suppress SSL warnings for localhost connections
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

def get_loader_jobs(endpoint="localhost:8182"):
    """Get all loader jobs from Neptune"""
    base_url = f"https://{endpoint}"
    
    try:
        response = requests.get(f"{base_url}/loader", verify=False, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting loader jobs: {e}")
        return None

def get_job_status(endpoint, load_id):
    """Get status for a specific loader job"""
    base_url = f"https://{endpoint}"
    
    try:
        response = requests.get(f"{base_url}/loader/{load_id}", verify=False, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting status for {load_id}: {e}")
        return None

def cancel_job(endpoint, load_id):
    """Cancel a specific loader job"""
    base_url = f"https://{endpoint}"
    
    try:
        response = requests.delete(f"{base_url}/loader/{load_id}", verify=False, timeout=30)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error cancelling job {load_id}: {e}")
        return False

def remove_queued_jobs(endpoint="localhost:8182", dry_run=False):
    """Remove all jobs with status LOAD_IN_QUEUE"""
    
    print(f"Scanning for queued jobs on {endpoint}...")
    print("=" * 80)
    
    # Get all loader jobs
    jobs_data = get_loader_jobs(endpoint)
    
    if not jobs_data:
        print("Failed to get loader jobs")
        return
    
    payload = jobs_data.get('payload', {})
    load_ids = payload.get('loadIds', [])
    
    if not load_ids:
        print("No loader jobs found.")
        return
    
    print(f"Found {len(load_ids)} total job(s), checking status...")
    
    queued_jobs = []
    other_jobs = []
    
    # Check status of each job
    for load_id in load_ids:
        status_data = get_job_status(endpoint, load_id)
        
        if not status_data:
            print(f"  {load_id}: ERROR - Could not get status")
            continue
        
        load_payload = status_data.get('payload', {})
        overall_status = load_payload.get('overallStatus', {})
        status = overall_status.get('status', 'UNKNOWN')
        
        if status == "LOAD_IN_QUEUE":
            queued_jobs.append(load_id)
            print(f"  {load_id}: QUEUED - Will be removed")
        else:
            other_jobs.append((load_id, status))
            print(f"  {load_id}: {status} - Skipping")
    
    print("\n" + "=" * 80)
    print("SUMMARY:")
    print("-" * 30)
    print(f"Total jobs found: {len(load_ids)}")
    print(f"Queued jobs: {len(queued_jobs)}")
    print(f"Other jobs: {len(other_jobs)}")
    
    if not queued_jobs:
        print("\nNo queued jobs found to remove.")
        return
    
    print(f"\nQueued jobs to remove ({len(queued_jobs)}):")
    for job_id in queued_jobs:
        print(f"  - {job_id}")
    
    if dry_run:
        print(f"\nDRY RUN MODE: No jobs will be actually removed.")
        print("Run without --dry-run to actually remove the jobs.")
        return
    
    # Confirm removal
    print(f"\nWARNING: About to remove {len(queued_jobs)} queued job(s).")
    response = input("Continue? (y/N): ")
    
    if response.lower() != 'y':
        print("Operation cancelled.")
        return
    
    # Remove queued jobs
    print(f"\nRemoving {len(queued_jobs)} queued job(s)...")
    print("-" * 50)
    
    successful_removals = []
    failed_removals = []
    
    for job_id in queued_jobs:
        print(f"Removing {job_id}...", end=" ")
        
        if cancel_job(endpoint, job_id):
            print("SUCCESS")
            successful_removals.append(job_id)
        else:
            print("FAILED")
            failed_removals.append(job_id)
    
    # Final summary
    print("\n" + "=" * 80)
    print("REMOVAL SUMMARY:")
    print("-" * 30)
    print(f"Successfully removed: {len(successful_removals)} job(s)")
    print(f"Failed to remove: {len(failed_removals)} job(s)")
    
    if successful_removals:
        print(f"\nSuccessfully removed jobs:")
        for job_id in successful_removals:
            print(f"  - {job_id}")
    
    if failed_removals:
        print(f"\nFailed to remove jobs:")
        for job_id in failed_removals:
            print(f"  - {job_id}")
    
    return {
        'total_jobs': len(load_ids),
        'queued_jobs': len(queued_jobs),
        'successful_removals': len(successful_removals),
        'failed_removals': len(failed_removals),
        'removed_job_ids': successful_removals,
        'failed_job_ids': failed_removals
    }

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Remove Neptune loader jobs with status LOAD_IN_QUEUE")
    parser.add_argument("--endpoint", default="localhost:8182", 
                       help="Neptune endpoint (default: localhost:8182)")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Show what would be removed without actually removing")
    parser.add_argument("--json", action="store_true", 
                       help="Output results in JSON format")
    parser.add_argument("--save", help="Save results to JSON file")
    
    args = parser.parse_args()
    
    # Remove queued jobs
    results = remove_queued_jobs(args.endpoint, args.dry_run)
    
    if results and (args.json or args.save):
        output_data = {
            'timestamp': datetime.now().isoformat(),
            'endpoint': args.endpoint,
            'dry_run': args.dry_run,
            'results': results
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