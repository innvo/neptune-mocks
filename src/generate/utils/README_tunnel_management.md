# SSH Tunnel Management for Neptune

This directory contains updated SSH tunnel management scripts that use environment variables for configuration and include tunnel operation checking.

## Files

- `ssh_tunnel_check.py` - Interactive SSH tunnel manager with operation checking
- `ssh_tunnel_start.py` - Start SSH tunnel in new terminal window with operation checking
- `test_neptune_connection.py` - Test Neptune connectivity

## Configuration

### Environment Variables

Create a `.env` file in the project root with the following variables:

```bash
# SSH Key Configuration
SSH_KEY_PATH=neptune-bastion-dev.pem

# Bastion Host Configuration
BASTION_HOST=35.170.107.253
BASTION_USER=ec2-user

# Neptune Endpoint Configuration
NEPTUNE_ENDPOINT=neptune-dev-instance-1.cz7fmvtxsrei.us-east-1.neptune.amazonaws.com

# Port Configuration
LOCAL_PORT=8182
REMOTE_PORT=8182

# Timeout Configuration (in seconds)
TUNNEL_TIMEOUT=30
CONNECTION_TIMEOUT=5
```

### Template File

A template file `env.template` is provided in the project root. Copy it to `.env` and update the values:

```bash
cp env.template .env
```

## Usage

### Interactive Tunnel Manager

```bash
python src/generate/utils/ssh_tunnel_check.py
```

This script:
- Loads configuration from `.env` file
- Checks if tunnel is already operational before creating a new one
- Provides interactive prompts for user decisions
- Monitors tunnel health while running
- Gracefully handles termination

### Start Tunnel in New Terminal

```bash
python src/generate/utils/ssh_tunnel_start.py
```

This script:
- Loads configuration from `.env` file
- Checks if tunnel is already operational
- Starts SSH tunnel in a new terminal window
- Verifies tunnel operation after startup

### Test Neptune Connection

```bash
python src/generate/utils/test_neptune_connection.py
```

This script tests connectivity to Neptune endpoints.

## Features

### Tunnel Operation Checking

Both scripts now include comprehensive tunnel operation checking:

1. **Port Availability Check** - Verifies if the local port is available
2. **Tunnel Health Check** - Tests actual connectivity through the tunnel
3. **Neptune Status Check** - Verifies Neptune cluster is responding
4. **Periodic Monitoring** - Continuously monitors tunnel health

### Environment-Based Configuration

- All configuration is loaded from `.env` file
- Sensible defaults if `.env` file is not found
- Clear error messages for missing configuration
- Support for different environments (dev, staging, prod)

### Error Handling

- Graceful handling of missing SSH keys
- Clear error messages for connection issues
- Troubleshooting tips for common problems
- Proper cleanup on script termination

## Troubleshooting

### Common Issues

1. **SSH Key Not Found**
   - Verify `SSH_KEY_PATH` in `.env` file
   - Ensure key file has correct permissions (400)

2. **Port Already in Use**
   - Check if another tunnel is running
   - Use different `LOCAL_PORT` in `.env`

3. **Bastion Host Unreachable**
   - Verify `BASTION_HOST` and `BASTION_USER`
   - Check network connectivity to bastion host

4. **Tunnel Not Operational**
   - Check SSH key permissions
   - Verify bastion host security groups
   - Check Neptune cluster status

### Debug Mode

For debugging, you can set additional environment variables:

```bash
# Enable verbose SSH output
SSH_VERBOSE=true

# Increase timeout values
TUNNEL_TIMEOUT=60
CONNECTION_TIMEOUT=10
```

## Security Notes

- SSH keys should have 400 permissions
- `.env` file should not be committed to version control
- Use different keys for different environments
- Regularly rotate SSH keys

## Integration

These scripts can be integrated into CI/CD pipelines or automated workflows by:

1. Setting environment variables in the pipeline
2. Running tunnel checks before data operations
3. Using the return codes for automation decisions 