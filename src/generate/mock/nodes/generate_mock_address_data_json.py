import pandas as pd
from faker import Faker
import json
from tqdm import tqdm
import os
import time
import platform
import hashlib

def clear_terminal():
    """Clear the terminal screen"""
    if platform.system() == 'Windows':
        os.system('cls')
    else:
        os.system('clear')

def validate_referential_integrity(address_data, node_df):
    """Validate referential integrity of address data against node data"""
    validation_results = {
        'total_addresses': len(address_data),
        'valid_addresses': 0,
        'invalid_addresses': 0,
        'missing_nodes': set(),
        'node_type_stats': {
            'address': {'total': 0, 'valid': 0}
        }
    }
    
    # Get sets of valid node IDs for quick lookup
    valid_node_ids = set(node_df['node_id'].values)
    address_node_ids = set(node_df[node_df['node_type'] == 'address']['node_id'].values)
    
    for address_entry in address_data:
        node_id = address_entry['node_id']
        
        # Validate node existence and type
        node_exists = node_id in valid_node_ids
        is_address_node = node_id in address_node_ids
        
        if node_exists and is_address_node:
            validation_results['valid_addresses'] += 1
            validation_results['node_type_stats']['address']['valid'] += 1
        else:
            validation_results['invalid_addresses'] += 1
            if not node_exists or not is_address_node:
                validation_results['missing_nodes'].add(node_id)
    
    # Update total counts
    validation_results['node_type_stats']['address']['total'] = len(address_node_ids)
    
    return validation_results

def generate_mock_address_data():
    try:
        # Clear terminal at start
        clear_terminal()
        
        start_time = time.time()
        
        # Initialize Faker
        fake = Faker()
        
        # Read node_data.csv to get address nodes
        print("Reading node data...")
        node_df = pd.read_csv(os.path.join('src', 'data', 'input', 'node_data.csv'), usecols=['node_id', 'node_type'])
        
        # Print node type statistics
        print("\nNode Type Statistics:")
        print(f"Total number of nodes: {len(node_df)}")
        node_counts = node_df['node_type'].value_counts()
        for node_type, count in node_counts.items():
            print(f"{node_type}: {count} nodes")
        
        # Filter for address nodes
        address_nodes = node_df[node_df['node_type'] == 'address']
        if address_nodes.empty:
            print("Warning: No address nodes found in node_data.csv")
            return None
        
        # Initialize data list
        address_data = []
        
        # Generate mock data for each address node
        print("\nGenerating mock address data...")
        for _, node in tqdm(address_nodes.iterrows(), total=len(address_nodes), desc="Processing address nodes"):
            node_id = node['node_id']
            
            # Generate individual address components using Faker
            street_address_line1 = fake.street_address().upper()
            
            # Generate STREET_ADDRESS_LINE2 with various secondary address types
            if fake.boolean(chance_of_getting_true=40):  # 40% chance of having a secondary address
                secondary_address_types = [
                    fake.secondary_address().upper(),
                    f"APT {fake.building_number()}",
                    f"SUITE {fake.building_number()}",
                    f"UNIT {fake.building_number()}",
                    f"FLOOR {fake.random_int(min=1, max=20)}",
                    f"BUILDING {fake.building_number()}",
                    f"ROOM {fake.random_int(min=100, max=999)}"
                ]
                street_address_line2 = fake.random_element(secondary_address_types)
            else:
                street_address_line2 = None
                
            city = fake.city().upper()
            
            # Generate state/province first, then determine country based on state/province
            state_province = fake.state_abbr().upper()
            
            # Check if the state/province is a US state and set country accordingly
            us_states = ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY']
            
            if state_province in us_states:
                country = "UNITED STATES"
            else:
                # For non-US states, generate a random country
                country = fake.country().upper()
            
            # Generate postal code with random chance of including plus 4
            base_postal_code = fake.postcode()
            zip_code_plus4 = None
            
            if fake.boolean(chance_of_getting_true=60):  # 60% chance of including plus 4
                # Generate a 4-digit extension
                plus_four = fake.random_int(min=1000, max=9999)
                postal_code = f"{base_postal_code}-{plus_four}"
                zip_code_plus4 = str(plus_four)  # Store just the plus 4 digits
            else:
                postal_code = base_postal_code
                
            zip_code5 = postal_code[:5] if len(postal_code) >= 5 else postal_code
            
            # Generate latitude and longitude based on postal code
            # US postal codes: 0-9 (0=NE, 9=CA), Canada: A-Z, Mexico: different ranges
            try:
                if country == "UNITED STATES" and len(zip_code5) == 5 and zip_code5.isdigit():
                    # US postal codes: first digit determines general latitude and longitude
                    first_digit = int(zip_code5[0])
                    if first_digit == 0:  # Northeast (ME, NH, VT, MA, RI, CT)
                        latitude = fake.random.uniform(41.0, 47.0)
                        longitude = fake.random.uniform(-75.0, -67.0)
                    elif first_digit == 1:  # Northeast (NY, PA, NJ)
                        latitude = fake.random.uniform(39.0, 45.0)
                        longitude = fake.random.uniform(-80.0, -72.0)
                    elif first_digit == 2:  # Southeast (NC, SC, GA, FL, AL, MS, TN, KY)
                        latitude = fake.random.uniform(25.0, 37.0)
                        longitude = fake.random.uniform(-88.0, -75.0)
                    elif first_digit == 3:  # Southeast (GA, FL, AL, MS, TN, KY)
                        latitude = fake.random.uniform(25.0, 37.0)
                        longitude = fake.random.uniform(-88.0, -75.0)
                    elif first_digit == 4:  # Midwest (OH, IN, MI, IL, WI, MN)
                        latitude = fake.random.uniform(41.0, 49.0)
                        longitude = fake.random.uniform(-93.0, -80.0)
                    elif first_digit == 5:  # Midwest (IA, MO, ND, SD, NE, KS, MN)
                        latitude = fake.random.uniform(36.0, 49.0)
                        longitude = fake.random.uniform(-104.0, -87.0)
                    elif first_digit == 6:  # Central (IL, MO, KS, IA, NE)
                        latitude = fake.random.uniform(36.0, 43.0)
                        longitude = fake.random.uniform(-104.0, -87.0)
                    elif first_digit == 7:  # Southeast (AR, LA, OK, TX)
                        latitude = fake.random.uniform(26.0, 37.0)
                        longitude = fake.random.uniform(-106.0, -88.0)
                    elif first_digit == 8:  # West (MT, ID, WY, UT, CO, AZ, NM)
                        latitude = fake.random.uniform(31.0, 49.0)
                        longitude = fake.random.uniform(-120.0, -104.0)
                    elif first_digit == 9:  # West (WA, OR, CA, NV, AK, HI)
                        latitude = fake.random.uniform(18.0, 49.0)
                        longitude = fake.random.uniform(-180.0, -104.0)
                    else:
                        latitude = fake.random.uniform(18.0, 49.0)  # Fallback for US
                        longitude = fake.random.uniform(-180.0, -67.0)
                elif country == "CANADA":
                    # Canadian postal codes: latitude and longitude ranges
                    latitude = fake.random.uniform(41.0, 70.0)  # Canada spans roughly 41°N to 70°N
                    longitude = fake.random.uniform(-141.0, -52.0)  # Canada spans roughly 141°W to 52°W
                elif country == "MEXICO":
                    # Mexican postal codes: latitude and longitude ranges
                    latitude = fake.random.uniform(14.0, 33.0)  # Mexico spans roughly 14°N to 33°N
                    longitude = fake.random.uniform(-118.0, -86.0)  # Mexico spans roughly 118°W to 86°W
                else:
                    # For other countries, generate random latitude and longitude
                    latitude = fake.random.uniform(-60.0, 70.0)  # Most populated areas
                    longitude = fake.random.uniform(-180.0, 180.0)  # Full longitude range
            except:
                # Fallback if any error occurs
                latitude = fake.random.uniform(18.0, 49.0)
                longitude = fake.random.uniform(-180.0, -67.0)
            
            # Generate mailability score (integer -1 to 5)
            mailability_score = fake.random_int(min=-1, max=5)
            
            # Construct full address from individual components
            address_parts = [street_address_line1]
            if street_address_line2:
                address_parts.append(street_address_line2)
            address_parts.extend([city, state_province, postal_code, country])
            full_address = ", ".join(part for part in address_parts if part is not None)
            
            # Generate SHA256 hash of the address
            address_hash = hashlib.sha256(full_address.encode('utf-8')).hexdigest()
            
            # Create node properties JSON
            node_properties = {
                "ADDRESS_FULL": full_address,
                "ADDRESS_HASH": address_hash,
                "STREET_ADDRESS_LINE1": street_address_line1
            }
            
            # Add STREET_ADDRESS_LINE2 right after STREET_ADDRESS_LINE1 if it's not None
            if street_address_line2 is not None:
                node_properties["STREET_ADDRESS_LINE2"] = street_address_line2
            
            # Add remaining properties
            node_properties.update({
                "CITY": city,
                "STATE_PROVINCE": state_province,
                "COUNTRY": country,
                "POSTAL_CODE": postal_code,
                "ZIP_CODE5": zip_code5
            })
            
            # Add ZIP_CODE_PLUS4 if it's not None
            if zip_code_plus4 is not None:
                node_properties["ZIP_CODE_PLUS4"] = zip_code_plus4
            
            # Add LATITUDE and LONGITUDE after ZIP_CODE_PLUS4
            node_properties["LATITUDE"] = round(latitude, 6)
            node_properties["LONGITUDE"] = round(longitude, 6)
            
            # Add MAILABILITY_SCORE after LONGITUDE
            node_properties["MAILABILITY_SCORE"] = mailability_score
            
            # Add to data list
            address_data.append({
                'node_id': node_id,
                'node_name': full_address,
                'node_properties': node_properties
            })
        
        # Save to JSON
        output_path = os.path.join('src', 'data', 'output', 'gds', 'mock_address_data.json')
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(address_data, f, indent=2)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Validate referential integrity
        validation_results = validate_referential_integrity(address_data, node_df)
        
        # Print validation results
        print("\nReferential Integrity Validation Results:")
        print(f"Total addresses generated: {validation_results['total_addresses']}")
        print(f"Valid addresses: {validation_results['valid_addresses']}")
        print(f"Invalid addresses: {validation_results['invalid_addresses']}")
        
        if validation_results['missing_nodes']:
            print(f"\nMissing or invalid address nodes: {len(validation_results['missing_nodes'])}")
            print("Sample of missing address nodes:", list(validation_results['missing_nodes'])[:5])
        
        print("\nNode Type Statistics:")
        for node_type, stats in validation_results['node_type_stats'].items():
            print(f"\n{node_type.capitalize()} Nodes:")
            print(f"  Total: {stats['total']}")
            print(f"  Used in valid addresses: {stats['valid']}")
        
        print("\nAddress Data Generation Statistics:")
        print(f"Total number of address nodes processed: {len(address_data)}")
        print(f"Processing time: {processing_time:.2f} seconds")
        print(f"Addresses per second: {len(address_data) / processing_time:.2f}")
        print(f"Data saved to: {output_path}")
        
        return address_data
        
    except Exception as e:
        print(f"Error generating mock address data: {str(e)}")
        return None

if __name__ == "__main__":
    address_data = generate_mock_address_data()
    if address_data is not None:
        print("\nSample of Generated Address Data:")
        print(json.dumps(address_data[:5], indent=2))
