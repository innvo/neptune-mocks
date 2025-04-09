# generate_mock_person_data.py

This module generates mock person data with various name formats and birth dates.

## Functions

### generate_name_list(first_name, last_name)

Generates random variations of a person's name with NAME_FIRST and NAME_LAST labels.

**Parameters:**
- `first_name` (str): The person's first name
- `last_name` (str): The person's last name

**Returns:**
- `list`: A list of name variations, each containing NAME_FIRST and NAME_LAST

**Example:**
```python
name_list = generate_name_list("WHITNEY", "THOMAS")
# Returns:
# [
#     {
#         "NAME_FIRST": "WHITNEY",
#         "NAME_LAST": "THOMAS"
#     },
#     {
#         "NAME_FIRST": "W.",
#         "NAME_LAST": "THOMAS"
#     }
# ]
```

### generate_birth_date_list(birth_date)

Generates 1-3 variations of a birth date in mm-dd-yyyy format.

**Parameters:**
- `birth_date` (str): The original birth date in YYYY-MM-DD format

**Returns:**
- `list`: A list of birth date variations

**Example:**
```python
date_list = generate_birth_date_list("1990-01-01")
# Returns: ["01-01-1990", "01-02-1990"]
```

### create_node_properties()

Creates node properties with realistic data.

**Returns:**
- `dict`: A dictionary containing:
  - NAME_FULL
  - NAME_LIST
  - BIRTH_DATE
  - BIRTH_DATE_LIST

**Example:**
```python
props = create_node_properties()
# Returns:
# {
#     "NAME_FULL": "WHITNEY THOMAS",
#     "NAME_LIST": [...],
#     "BIRTH_DATE": "1990-01-01",
#     "BIRTH_DATE_LIST": ["01-01-1990", "01-02-1990"]
# }
```

### generate_mock_person_data()

Main function to generate mock person data.

**Returns:**
- `bool`: True if successful, False otherwise

**Example:**
```python
success = generate_mock_person_data()
if success:
    print("Mock data generated successfully")
```

## Usage

```python
from generate_mock_person_data import generate_mock_person_data

# Generate mock data
success = generate_mock_person_data()
if success:
    print("Data generated successfully")
``` 