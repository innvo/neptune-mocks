# Neptune Loader Status Monitor

## Overview

The `neptune_loader_status.py` script is a utility tool designed to monitor and display the status of Amazon Neptune bulk loader jobs. It provides both a summary view of all active loader jobs and detailed status information for each individual job.

## Purpose

This script helps developers and administrators:
- Monitor the progress of Neptune bulk loading operations
- Track job completion status and performance metrics
- Identify failed or stuck loader jobs
- Get detailed information about specific loader jobs

## Features

- **Summary Dashboard**: Displays all active loader jobs in a tabular format
- **Detailed Status**: Provides comprehensive JSON output for each job
- **Error Handling**: Graceful handling of connection and API errors
- **SSL Support**: Configured for localhost connections with SSL verification disabled
- **Timeout Protection**: 30-second timeout for API requests

## Prerequisites

- Python 3.x
- Required packages:
  - `requests`
  - `urllib3`
- Neptune cluster running on `localhost:8182`
- SSL certificates configured (or SSL verification disabled for local development)

## Installation

1. Ensure you have the required Python packages:
   ```bash
   pip install requests urllib3
   ```

2. The script is ready to run from the `src/generate/gremlin/tests/` directory.

## Usage

### Basic Usage

Run the script directly to get a complete status report:

```bash
python neptune_loader_status.py
```

### Programmatic Usage

You can also import and use the functions in your own code:

```python
from neptune_loader_status import get_loader_jobs, get_loader_status, print_loader_statuses

# Get all loader jobs
jobs = get_loader_jobs()

# Get status for a specific job
status = get_loader_status("your-load-id")

# Print formatted status report
print_loader_statuses()
```

## API Functions

### `get_loader_jobs()`

Retrieves all active loader jobs from Neptune.

**Returns:**
- `dict` or `None`: JSON response containing all loader job IDs, or `None` if the request fails

**Endpoint:** `GET https://localhost:8182/loader`

### `get_loader_status(load_id)`

Retrieves detailed status information for a specific loader job.

**Parameters:**
- `load_id` (str): The unique identifier of the loader job

**Returns:**
- `dict` or `None`: JSON response containing detailed job status, or `None` if the request fails

**Endpoint:** `GET https://localhost:8182/loader/{load_id}`

### `print_loader_statuses()`

Displays a formatted report of all loader jobs and their statuses.

**Output:**
- Summary table with job IDs, statuses, record counts, and durations
- Detailed JSON output for each job

## Output Format

### Summary Table

The script displays a formatted table with the following columns:

| Column | Description |
|--------|-------------|
| Load ID | Unique identifier for the loader job |
| Status | Current status (e.g., LOAD_COMPLETED, LOAD_IN_PROGRESS) |
| Records | Total number of records processed |
| Failed | Number of records that failed or were ignored |
| Duration | Time taken to complete the job (or "Running" if still in progress) |

### Detailed Status

For each job, the script also outputs the complete JSON response from Neptune, which includes:

- Overall status information
- Start and end times
- Record counts and error details
- File processing information
- Error logs (if any)

## Configuration

### SSL Settings

The script is configured for localhost development with SSL verification disabled:

```python
# Suppress SSL warnings for localhost connections
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

# SSL verification disabled for localhost
response = requests.get(url, verify=False, timeout=30)
```

### Timeout Settings

- Request timeout: 30 seconds
- This prevents the script from hanging on unresponsive Neptune endpoints

## Error Handling

The script includes comprehensive error handling:

- **Connection Errors**: Displays error messages for network issues
- **HTTP Errors**: Handles non-200 status codes
- **JSON Parsing**: Gracefully handles malformed responses
- **Missing Data**: Provides fallback values for missing fields

## Example Output

```
Getting Neptune loader jobs and statuses...
================================================================================
Found 2 loader job(s):
================================================================================
Load ID                              Status               Records   Failed     Duration    
--------------------------------------------------------------------------------
abc123-def456-ghi789                 LOAD_COMPLETED      10000     0          45.2s      
xyz789-uvw123-abc456                 LOAD_IN_PROGRESS    5000      2          Running    
--------------------------------------------------------------------------------

Detailed Status Information:
================================================================================

1. Load ID: abc123-def456-ghi789
----------------------------------------
{
  "payload": {
    "overallStatus": {
      "status": "LOAD_COMPLETED",
      "totalRecords": 10000,
      "totalRecordsFailedOrIgnored": 0,
      "startTime": 1640995200000,
      "endTime": 1640995245200
    }
  }
}
```

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Ensure Neptune is running on `localhost:8182`
   - Check if the Neptune cluster is accessible

2. **SSL Certificate Errors**
   - The script disables SSL verification for localhost
   - For production, configure proper SSL certificates

3. **Timeout Errors**
   - Increase the timeout value if Neptune is slow to respond
   - Check network connectivity

4. **No Loader Jobs Found**
   - Verify that bulk loading operations have been initiated
   - Check if jobs have been completed and removed from the queue

### Debug Mode

To enable debug output, you can modify the script to include more verbose logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Security Considerations

- **SSL Verification**: Disabled for localhost development only
- **Credentials**: No authentication required for localhost connections
- **Production Use**: Enable SSL verification and proper authentication for production environments

## Related Files

- `neptune_bulk_load_concurrency_test.py` - Tests for bulk loading performance
- `neptune_loader_metrics.py` - Additional metrics collection
- `neptune_get_active_jobs.py` - Alternative job listing utility

## Contributing

When modifying this script:

1. Maintain backward compatibility with existing API responses
2. Add appropriate error handling for new features
3. Update this documentation for any new functionality
4. Test with both successful and failed loader jobs

## License

This script is part of the Neptune Mocks project and follows the same licensing terms. 