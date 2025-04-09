# Neptune Mock Data Generator

A Python-based tool for generating mock person data and uploading it to Amazon Neptune.

## Features

- Generate realistic mock person data with various name formats
- Create birth date variations
- Upload data to Neptune through SSH tunnel
- Support for OpenCypher CSV format

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Generate mock data:
```bash
python generate_mock_person_data.py
```

3. Upload to Neptune:
```bash
python upload_to_neptune.py
```

## Documentation

- [Usage Guide](usage.md) - How to use the tools
- [API Reference](api/) - Detailed API documentation
- [Development](development.md) - Development guidelines

## Requirements

- Python 3.8+
- AWS credentials configured
- SSH access to Neptune bastion host
- Required Python packages (see requirements.txt) 