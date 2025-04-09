# API Reference

This document provides detailed information about the Neptune Mock Data Generator's API.

## generate_mock_person_data.py

### Functions

#### `generate_mock_person_data(num_records: int) -> None`
Generates mock person data and saves it to CSV files.

**Parameters:**
- `num_records` (int): Number of person records to generate

**Output Files:**
- `mock_person_data.csv`: Contains person node data
- `node_data.csv`: Contains name node data

**Example:**
```python
generate_mock_person_data(1000)
```

#### `generate_birth_date_list(birth_date: str) -> List[str]`
Generates a list of birth dates including the original date and 1-2 variations.

**Parameters:**
- `birth_date` (str): Original birth date in mm-dd-yyyy format

**Returns:**
- `List[str]`: List of birth dates including original and variations

**Example:**
```python
dates = generate_birth_date_list("01-15-1980")
# Returns: ["01-15-1980", "01-16-1980", "01-14-1980"]
```

## upload_to_neptune.py

### Functions

#### `upload_to_neptune(csv_file: str) -> None`
Uploads CSV data to Neptune database.

**Parameters:**
- `csv_file` (str): Path to CSV file to upload

**Example:**
```python
upload_to_neptune("neptune_person_nodes.csv")
```

#### `create_ssh_tunnel(neptune_endpoint: str, ssh_host: str, ssh_user: str, ssh_key_path: str) -> None`
Creates an SSH tunnel to Neptune database.

**Parameters:**
- `neptune_endpoint` (str): Neptune database endpoint
- `ssh_host` (str): SSH host address
- `ssh_user` (str): SSH username
- `ssh_key_path` (str): Path to SSH private key

**Example:**
```python
create_ssh_tunnel(
    "your-neptune-endpoint",
    "your-ssh-host",
    "your-ssh-user",
    "path/to/your/key.pem"
)
```

## Data Formats

### Person Node Format
```csv
node_id,node_name,node_properties
"PERSON_1","Person 1","{'NAME_FULL': 'John Smith', 'BIRTH_DATE': '01-15-1980', 'NAME_LIST': ['John Smith', 'Johnny Smith'], 'BIRTH_DATE_LIST': ['01-15-1980', '01-16-1980']}"
```

### Name Node Format
```csv
node_id,node_name,node_properties
"NAME_1","Name 1","{'NAME_FULL': 'John Smith'}"
```

### Edge Format
```csv
edge_id,edge_type,node_id_from,node_id_to,edge_properties
"EDGE_1","HAS_NAME","PERSON_1","NAME_1","{}"
```

## Error Handling

### Common Exceptions

#### `SSHTunnelError`
Raised when there is an error creating or maintaining the SSH tunnel.

#### `UploadError`
Raised when there is an error uploading data to Neptune.

#### `DataGenerationError`
Raised when there is an error generating mock data.

### Error Recovery

1. For SSH tunnel errors:
   - Check SSH credentials
   - Verify network connectivity
   - Ensure Neptune endpoint is accessible

2. For upload errors:
   - Verify CSV file format
   - Check Neptune connection
   - Ensure proper permissions

3. For data generation errors:
   - Verify input parameters
   - Check file permissions
   - Ensure sufficient disk space 