# Neptune Gremlin Converter

A Python utility to convert Neptune Gremlin results to OpenCypher format.

## Installation

```bash
pip install -e ./modules/person_converter
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