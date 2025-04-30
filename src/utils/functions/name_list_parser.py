# name_parser.py

def parse_name_string(input_string: str) -> dict:
    result = {"NAME_LIST": []}
    
    # Split the input by ';' to separate different name records
    name_entries = input_string.strip().split(';')
    
    for entry in name_entries:
        if not entry.strip():
            continue
        name_dict = {}
        # Split each entry by '|' to get fields
        fields = entry.strip().split('|')
        for field in fields:
            if not field.strip():
                continue
            key, value = field.strip().split(':', 1)
            # Map the key to full field names
            if key == "N_F":
                name_dict["NAME_FIRST"] = value
            elif key == "N_M":
                name_dict["NAME_MIDDLE"] = value
            elif key == "N_L":
                name_dict["NAME_LAST"] = value
            elif key == "N_T":
                name_dict["NAME_TYPE"] = value
        result["NAME_LIST"].append(name_dict)
    
    return result


if __name__ == "__main__":
    # Example input string
    input_data = "N_F:JOHN|N_M:DAVID|N_L:SMITH|N_T:PRIMARY; N_F:JON|N_L:SMITH|N_T:PRIMARY"
    
    # Parse it
    parsed_output = parse_name_string(input_data)
    
    # Pretty print the output
    import pprint
    pprint.pprint(parsed_output)