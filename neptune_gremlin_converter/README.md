# Neptune Gremlin Converter

A Python utility to convert Neptune Gremlin results to OpenCypher format.

## Installation

```bash
pip install neptune-gremlin-converter
```

## Usage

```python
from neptune_gremlin_converter import convert_gremlin_to_opencypher

# Convert a Gremlin JSON file to OpenCypher format
convert_gremlin_to_opencypher("input.json", "output_directory")
```

## Features

- Converts Gremlin JSON responses to OpenCypher format
- Handles vertex-based and count-based responses
- Properly formats date fields
- Flattens single-value lists 

To publish this package to PyPI so others can install it using pip, you would need to:
Create an account on PyPI (https://pypi.org)
Install twine: pip install twine
Build the distribution: python setup.py sdist bdist_wheel
Upload to PyPI: twine upload dist/*
Would you like me to help you with any of these additional steps, or do you have any questions about using the package?