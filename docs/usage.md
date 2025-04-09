# Usage Guide

This guide explains how to use the Neptune Mock Data Generator tools.

## Prerequisites

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Configure AWS credentials:
```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_REGION=us-east-1
```

3. Set up SSH tunnel to Neptune:
```bash
ssh -i /path/to/key.pem -L 8182:neptune-endpoint:8182 ec2-user@bastion-host
```

## Generating Mock Data

1. Run the mock data generator:
```bash
python generate_mock_person_data.py
```

This will create:
- `mock_person_data.csv`: Contains person nodes with properties
- `node_data.csv`: Contains node information

## Uploading to Neptune

1. Ensure SSH tunnel is active
2. Run the upload script:
```bash
python upload_to_neptune.py
```

## Data Format

### Person Nodes

Each person node contains:
- `node_id`: Unique identifier
- `node_name`: Full name
- `node_properties`: JSON string containing:
  - NAME_FULL: Full name
  - NAME_LIST: List of name variations
  - BIRTH_DATE: Primary birth date
  - BIRTH_DATE_LIST: List of birth date variations

### Name Variations

Name variations include:
- Full name (e.g., "WHITNEY THOMAS")
- Initial first name (e.g., "W. THOMAS")
- Initial last name (e.g., "WHITNEY T.")

### Birth Date Variations

Birth dates are formatted as:
- Primary date: YYYY-MM-DD
- Variations: MM-DD-YYYY

## Troubleshooting

### Common Issues

1. **SSH Tunnel Issues**
   - Verify bastion host is accessible
   - Check key file permissions
   - Ensure port 8182 is available

2. **Data Generation Issues**
   - Check input file format
   - Verify Python version
   - Ensure all dependencies are installed

3. **Upload Issues**
   - Verify Neptune endpoint
   - Check AWS credentials
   - Ensure SSH tunnel is active

### Error Messages

- "Neptune is not available": Check SSH tunnel
- "Invalid JSON": Check data format
- "Upload failed": Check Neptune status and permissions

## Support

For additional help:
1. Check the [API Reference](api/)
2. Review the [Development Guide](development.md)
3. Open an issue on GitHub 