#!/usr/bin/env python3

import requests
import json
import ssl
from urllib3.exceptions import InsecureRequestWarning

# Suppress SSL warnings for localhost connections
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

def get_loader_jobs():
    """Get all loader jobs from Neptune"""
    url = "https://localhost:8182/loader"
    
    try:
        response = requests.get(url, verify=False, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting loader jobs: {e}")
        return None

def get_loader_status(load_id):
    """Get status for a specific loader job"""
    url = f"https://localhost:8182/loader/{load_id}"
    
    try:
        response = requests.get(url, verify=False, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting status for {load_id}: {e}")
        return None

def print_loader_statuses():
    """Print all loader jobs and their statuses"""
    print("Getting Neptune loader jobs and statuses...")
    print("=" * 80)
    
    # Get all loader jobs
    jobs_data = get_loader_jobs()
    
    if not jobs_data:
        print("Failed to get loader jobs")
        return
    
    payload = jobs_data.get('payload', {})
    load_ids = payload.get('loadIds', [])
    
    if not load_ids:
        print("No active loader jobs found.")
        return
    
    print(f"Found {len(load_ids)} loader job(s):")
    print("=" * 80)
    print(f"{'Load ID':<36} {'Status':<20} {'Records':<10} {'Failed':<10} {'Duration':<12}")
    print("-" * 80)
    
    for load_id in load_ids:
        status_data = get_loader_status(load_id)
        
        if not status_data:
            print(f"{load_id:<36} {'ERROR':<20} {'N/A':<10} {'N/A':<10} {'N/A':<12}")
            continue
        
        load_payload = status_data.get('payload', {})
        overall_status = load_payload.get('overallStatus', {})
        
        status = overall_status.get('status', 'UNKNOWN')
        total_records = overall_status.get('totalRecords', 0)
        failed_records = overall_status.get('totalRecordsFailedOrIgnored', 0)
        
        # Calculate duration if available
        start_time = overall_status.get('startTime', 0)
        end_time = overall_status.get('endTime', 0)
        duration = "N/A"
        if start_time and end_time:
            duration_seconds = (end_time - start_time) / 1000  # Convert from milliseconds
            duration = f"{duration_seconds:.1f}s"
        elif start_time:
            duration = "Running"
        
        print(f"{load_id:<36} {status:<20} {total_records:<10} {failed_records:<10} {duration:<12}")
    
    print("-" * 80)
    
    # Print detailed status for each job
    print("\nDetailed Status Information:")
    print("=" * 80)
    
    for i, load_id in enumerate(load_ids, 1):
        print(f"\n{i}. Load ID: {load_id}")
        print("-" * 40)
        
        status_data = get_loader_status(load_id)
        if status_data:
            print(json.dumps(status_data, indent=2))
        else:
            print("Failed to get status")
        print()

if __name__ == "__main__":
    print_loader_statuses() 