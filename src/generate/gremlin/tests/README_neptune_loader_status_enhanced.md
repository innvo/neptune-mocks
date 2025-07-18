# Enhanced Neptune Loader Status Monitor

## Overview

The `neptune_loader_status_enhanced.py` script is an improved version of the basic Neptune loader status monitor with comprehensive parameter validation, configuration options, and enhanced functionality. It provides robust monitoring capabilities for Amazon Neptune bulk loader jobs with extensive customization options.

## Key Improvements Over Basic Version

- **Command-line parameters** for all configuration options
- **Input validation** for all parameters and load IDs
- **Retry logic** with configurable attempts and delays
- **Filtering capabilities** by job status
- **Connection validation** mode
- **Enhanced error handling** with proper exit codes
- **Type hints** for better code maintainability
- **Object-oriented design** for better extensibility

## Features

- **Flexible Configuration**: All connection and behavior parameters configurable via command-line
- **Robust Validation**: Comprehensive input validation for all parameters
- **Retry Logic**: Automatic retry with configurable attempts and delays
- **Status Filtering**: Filter jobs by status (e.g., LOAD_COMPLETED, LOAD_IN_PROGRESS)
- **Output Control**: Option to show/hide detailed JSON output
- **Specific Job Monitoring**: Check status of individual load IDs
- **Connection Testing**: Validate-only mode for testing connectivity
- **Enhanced Error Handling**: Proper error messages and exit codes

## Prerequisites

- Python 3.6+
- Required packages:
  - `requests`
  - `urllib3`
- Neptune cluster accessible via HTTPS

## Installation

1. Ensure you have the required Python packages:
   ```bash
   pip install requests urllib3
   ```

2. The script is ready to run from the `src/generate/gremlin/tests/` directory.

## Usage

### Basic Usage

Run with default settings (localhost:8182):
```bash
python neptune_loader_status_enhanced.py
```

### Command-line Parameters

#### Connection Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--host` | localhost | Neptune host address |
| `--port` | 8182 | Neptune port number |
| `--timeout` | 30 | Request timeout in seconds |
| `--verify-ssl` | False | Verify SSL certificates |

#### Retry Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--retry-attempts` | 3 | Number of retry attempts for failed requests |
| `--retry-delay` | 5 | Delay between retry attempts in seconds |

#### Output Parameters

| Parameter | Description |
|-----------|-------------|
| `--no-details` | Skip detailed JSON output |
| `--filter-status` | Filter jobs by status (e.g., LOAD_COMPLETED) |
| `--max-jobs` | Maximum number of jobs to display |

#### Special Parameters

| Parameter | Description |
|-----------|-------------|
| `--load-id` | Check status of specific load ID only |
| `--validate-only` | Only validate configuration and connection |

### Usage Examples

#### Basic Usage with Defaults
```bash
python neptune_loader_status_enhanced.py
```

#### Production Neptune Cluster
```bash
python neptune_loader_status_enhanced.py \
  --host neptune-cluster.amazonaws.com \
  --port 8182 \
  --verify-ssl \
  --timeout 60
```

#### High Reliability Configuration
```bash
python neptune_loader_status_enhanced.py \
  --timeout 60 \
  --retry-attempts 5 \
  --retry-delay 10
```

#### Filter and Limit Output
```bash
python neptune_loader_status_enhanced.py \
  --filter-status LOAD_COMPLETED \
  --max-jobs 10 \
  --no-details
```

#### Check Specific Job
```bash
python neptune_loader_status_enhanced.py \
  --load-id abc123-def456-ghi789
```

#### Validate Connection Only
```bash
python neptune_loader_status_enhanced.py \
  --validate-only \
  --host neptune-cluster.amazonaws.com
```

## API Reference

### NeptuneLoaderStatus Class

#### Constructor Parameters

```python
NeptuneLoaderStatus(
    host: str = "localhost",
    port: int = 8182,
    timeout: int = 30,
    verify_ssl: bool = False,
    retry_attempts: int = 3,
    retry_delay: int = 5
)
```

#### Methods

##### `get_loader_jobs() -> Optional[Dict[str, Any]]`
Retrieves all active loader jobs from Neptune.

##### `get_loader_status(load_id: str) -> Optional[Dict[str, Any]]`
Retrieves detailed status information for a specific loader job.

##### `validate_load_id(load_id: str) -> bool`
Validates the format of a load ID.

##### `print_loader_statuses(show_details: bool = True, filter_status: Optional[str] = None, max_jobs: Optional[int] = None) -> None`
Displays a formatted report of all loader jobs and their statuses.

## Validation Features

### Configuration Validation

The script validates all configuration parameters:

- **Host**: Cannot be empty
- **Port**: Must be between 1 and 65535
- **Timeout**: Must be positive
- **Retry Attempts**: Cannot be negative
- **Retry Delay**: Cannot be negative

### Load ID Validation

Load IDs are validated for:

- **Length**: Between 10 and 100 characters
- **Invalid Characters**: No dangerous characters (`<`, `>`, `"`, `'`, `&`, `|`, `;`, `` ` ``)
- **Format**: Basic format validation (customizable based on actual Neptune format)

### Connection Validation

The `--validate-only` mode tests:

- Configuration parameter validity
- Network connectivity to Neptune
- API endpoint accessibility

## Error Handling

### Exit Codes

| Code | Description |
|------|-------------|
| 0 | Success |
| 1 | Error (configuration, connection, or validation failure) |

### Error Types

- **Configuration Errors**: Invalid parameter values
- **Connection Errors**: Network or API failures
- **Validation Errors**: Invalid load ID format
- **User Interruption**: Ctrl+C handling

## Output Format

### Configuration Display

```
Configuration validated:
  Host: localhost
  Port: 8182
  Timeout: 30s
  SSL Verification: False
  Retry Attempts: 3
  Retry Delay: 5s
```

### Summary Table

Same format as the basic version, but with enhanced validation:

| Column | Description |
|--------|-------------|
| Load ID | Unique identifier (validated) |
| Status | Current status |
| Records | Total records processed |
| Failed | Failed/ignored records |
| Duration | Job duration or "Running" |

### Detailed Status

Complete JSON output for each job (can be disabled with `--no-details`).

## Advanced Features

### Retry Logic

The script implements intelligent retry logic:

1. **Attempt Tracking**: Shows attempt number and failure reason
2. **Configurable Delays**: User-defined delay between attempts
3. **Graceful Degradation**: Continues with partial data if some requests fail

### Status Filtering

Filter jobs by status to focus on specific job states:

```bash
# Show only completed jobs
--filter-status LOAD_COMPLETED

# Show only running jobs
--filter-status LOAD_IN_PROGRESS

# Show only failed jobs
--filter-status LOAD_FAILED
```

### Output Control

Control the verbosity and scope of output:

```bash
# Summary only (no detailed JSON)
--no-details

# Limit number of jobs shown
--max-jobs 5

# Check specific job only
--load-id abc123-def456-ghi789
```

## Security Considerations

### SSL Configuration

- **Development**: SSL verification disabled by default for localhost
- **Production**: Enable `--verify-ssl` for production environments
- **Custom Certificates**: Configure proper SSL certificates for production

### Input Validation

- **Load ID Validation**: Prevents injection attacks
- **Parameter Validation**: Ensures safe configuration values
- **Error Handling**: No sensitive information in error messages

## Performance Considerations

### Timeout Configuration

- **Default**: 30 seconds (suitable for most environments)
- **High Latency**: Increase timeout for slow networks
- **Production**: Use appropriate timeouts based on network conditions

### Retry Configuration

- **Default**: 3 attempts with 5-second delays
- **High Reliability**: Increase attempts and delays for unstable networks
- **Performance**: Reduce attempts for fast, reliable networks

## Troubleshooting

### Common Issues

1. **Configuration Errors**
   ```bash
   # Check configuration
   python neptune_loader_status_enhanced.py --validate-only
   ```

2. **Connection Timeouts**
   ```bash
   # Increase timeout and retry attempts
   python neptune_loader_status_enhanced.py --timeout 60 --retry-attempts 5
   ```

3. **SSL Certificate Issues**
   ```bash
   # Disable SSL verification (development only)
   python neptune_loader_status_enhanced.py --verify-ssl false
   ```

4. **Invalid Load IDs**
   ```bash
   # Check specific load ID format
   python neptune_loader_status_enhanced.py --load-id your-load-id
   ```

### Debug Mode

For additional debugging, you can modify the script to include verbose logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Migration from Basic Version

### Simple Migration

The enhanced version maintains backward compatibility:

```bash
# Old way
python neptune_loader_status.py

# New way (same behavior)
python neptune_loader_status_enhanced.py
```

### Enhanced Usage

Add parameters as needed:

```bash
# Basic usage
python neptune_loader_status_enhanced.py

# With production settings
python neptune_loader_status_enhanced.py \
  --host neptune-cluster.amazonaws.com \
  --verify-ssl \
  --timeout 60
```

## Related Files

- `neptune_loader_status.py` - Basic version
- `neptune_bulk_load_concurrency_test.py` - Performance testing
- `neptune_loader_metrics.py` - Additional metrics collection
- `neptune_get_active_jobs.py` - Alternative job listing utility

## Contributing

When modifying this enhanced script:

1. Maintain backward compatibility with existing API responses
2. Add validation for new parameters
3. Update this documentation for any new functionality
4. Test with various parameter combinations
5. Ensure proper error handling and exit codes

## License

This script is part of the Neptune Mocks project and follows the same licensing terms. 