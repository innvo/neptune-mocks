# Development Guide

This guide provides information for developers working on the Neptune Mock Data Generator.

## Project Structure

```
neptune-mocks/
├── docs/                  # Documentation
├── src/                   # Source code
│   ├── generate_mock_person_data.py
│   └── upload_to_neptune.py
├── requirements.txt       # Python dependencies
└── README.md             # Project overview
```

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/neptune-mocks.git
cd neptune-mocks
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install development dependencies:
```bash
pip install -r requirements.txt
```

## Code Style

- Follow PEP 8 guidelines
- Use type hints for function parameters and return values
- Document all public functions and classes
- Keep functions focused and small
- Use meaningful variable names

## Testing

1. Run unit tests:
```bash
python -m pytest tests/
```

2. Run linting:
```bash
flake8 src/
```

3. Run type checking:
```bash
mypy src/
```

## Documentation

1. Build documentation:
```bash
mkdocs build
```

2. Serve documentation locally:
```bash
mkdocs serve
```

3. Deploy documentation:
```bash
mkdocs gh-deploy
```

## Adding New Features

1. Create a new branch:
```bash
git checkout -b feature/your-feature-name
```

2. Make your changes
3. Add tests for new functionality
4. Update documentation
5. Submit a pull request

## Release Process

1. Update version number
2. Update CHANGELOG.md
3. Create a release tag
4. Build and test
5. Deploy documentation
6. Create GitHub release

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Support

For development support:
1. Check the [API Reference](api/)
2. Review the [Usage Guide](usage.md)
3. Open an issue on GitHub 