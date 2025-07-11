import pandas as pd
import random
import json
from tqdm import tqdm
import os
import time
import platform

def clear_terminal():
    """Clear the terminal screen"""
    if platform.system() == 'Windows':
        os.system('cls')
    else:
        os.system('clear')

def validate_referential_integrity(email_data, node_df):
    """Validate referential integrity of email data against node data"""
    validation_results = {
        'total_emails': len(email_data),
        'valid_emails': 0,
        'invalid_emails': 0,
        'missing_nodes': set(),
        'node_type_stats': {
            'email': {'total': 0, 'valid': 0}
        }
    }
    
    # Get sets of valid node IDs for quick lookup
    valid_node_ids = set(node_df['node_id'].values)
    email_node_ids = set(node_df[node_df['node_type'] == 'email']['node_id'].values)
    
    for email_entry in email_data:
        node_id = email_entry['node_id']
        
        # Validate node existence and type
        node_exists = node_id in valid_node_ids
        is_email_node = node_id in email_node_ids
        
        if node_exists and is_email_node:
            validation_results['valid_emails'] += 1
            validation_results['node_type_stats']['email']['valid'] += 1
        else:
            validation_results['invalid_emails'] += 1
            if not node_exists or not is_email_node:
                validation_results['missing_nodes'].add(node_id)
    
    # Update total counts
    validation_results['node_type_stats']['email']['total'] = len(email_node_ids)
    
    return validation_results

def generate_email():
    """Generate a realistic email address"""
    # Common email domains
    domains = [
        'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'aol.com',
        'icloud.com', 'protonmail.com', 'mail.com', 'live.com', 'msn.com'
    ]
    
    # Common first names for email generation
    first_names = [
        'john', 'jane', 'mike', 'sarah', 'david', 'emma', 'chris', 'lisa',
        'james', 'mary', 'robert', 'anna', 'michael', 'jennifer', 'william',
        'linda', 'richard', 'susan', 'thomas', 'jessica', 'charles', 'ashley',
        'christopher', 'amanda', 'daniel', 'stephanie', 'matthew', 'nicole',
        'anthony', 'elizabeth', 'mark', 'helen', 'donald', 'deborah', 'steven',
        'rachel', 'paul', 'carolyn', 'andrew', 'janet', 'joshua', 'catherine',
        'kenneth', 'maria', 'kevin', 'heather', 'brian', 'diane', 'george',
        'ruth', 'edward', 'julie', 'ronald', 'joyce', 'timothy', 'virginia',
        'jason', 'victoria', 'jeffrey', 'kelly', 'ryan', 'lauren', 'jacob',
        'christine', 'gary', 'joan', 'nicholas', 'evelyn', 'eric', 'cheryl',
        'jonathan', 'megan', 'stephen', 'andrea', 'larry', 'hannah', 'justin',
        'jacqueline', 'scott', 'martha', 'brandon', 'gloria', 'benjamin',
        'teresa', 'frank', 'ann', 'gregory', 'sara', 'raymond', 'madison',
        'samuel', 'frances', 'patrick', 'kathryn', 'alexander', 'janice',
        'jack', 'jean', 'dennis', 'abigail', 'jerry', 'alice', 'tyler',
        'julia', 'aaron', 'judy', 'jose', 'sophia', 'adam', 'grace',
        'nathan', 'denise', 'henry', 'amber', 'douglas', 'doris', 'zachary',
        'angela', 'peter', 'nancy', 'kyle', 'karen', 'walter', 'betty',
        'ethan', 'helen', 'jeremy', 'sandra', 'harold', 'donna', 'carl',
        'carol', 'keith', 'ruth', 'roger', 'sharon', 'gerald', 'michelle',
        'christian', 'laura', 'terry', 'sarah', 'sean', 'kimberly', 'andrew',
        'deborah', 'edward', 'dorothy', 'carl', 'lisa', 'arthur', 'nancy',
        'ryan', 'karen', 'lawrence', 'betty', 'joe', 'helen', 'austin',
        'sandra', 'alex', 'donna', 'bruce', 'carol', 'bryan', 'ruth',
        'billy', 'sharon', 'jordan', 'michelle', 'albert', 'laura',
        'dylan', 'sarah', 'harold', 'kimberly', 'wayne', 'deborah',
        'eugene', 'dorothy', 'randy', 'lisa', 'vincent', 'nancy',
        'victor', 'karen', 'russell', 'betty', 'roy', 'helen',
        'eugene', 'sandra', 'randy', 'donna', 'vincent', 'carol',
        'victor', 'ruth', 'russell', 'sharon', 'roy', 'michelle'
    ]
    
    # Common last names for email generation
    last_names = [
        'smith', 'johnson', 'williams', 'brown', 'jones', 'garcia', 'miller',
        'davis', 'rodriguez', 'martinez', 'hernandez', 'lopez', 'gonzalez',
        'wilson', 'anderson', 'thomas', 'taylor', 'moore', 'jackson', 'martin',
        'lee', 'perez', 'thompson', 'white', 'harris', 'sanchez', 'clark',
        'ramirez', 'lewis', 'robinson', 'walker', 'young', 'allen', 'king',
        'wright', 'scott', 'torres', 'nguyen', 'hill', 'flores', 'green',
        'adams', 'nelson', 'baker', 'hall', 'rivera', 'campbell', 'mitchell',
        'carter', 'roberts', 'gomez', 'phillips', 'evans', 'turner', 'diaz',
        'parker', 'cruz', 'edwards', 'collins', 'reyes', 'stewart', 'morris',
        'morales', 'murphy', 'cook', 'rogers', 'gutierrez', 'ortiz', 'morgan',
        'cooper', 'peterson', 'bailey', 'reed', 'kelly', 'howard', 'ramos',
        'kim', 'cox', 'ward', 'richardson', 'watson', 'brooks', 'chavez',
        'wood', 'james', 'bennett', 'gray', 'mendoza', 'ruiz', 'hughes',
        'price', 'alvarez', 'castillo', 'sanders', 'patel', 'myers', 'long',
        'ross', 'foster', 'jimenez', 'powell', 'jenkins', 'perry', 'russell',
        'sullivan', 'bell', 'coleman', 'butler', 'henderson', 'barnes',
        'gonzales', 'fisher', 'vasquez', 'sims', 'romero', 'jordan', 'patterson',
        'alexander', 'hamilton', 'graham', 'reynolds', 'griffin', 'wallace',
        'moreno', 'west', 'cole', 'hayes', 'bryant', 'herrera', 'gibson',
        'ellis', 'tran', 'medina', 'aguilar', 'stevens', 'murray', 'ford',
        'castro', 'marshall', 'owens', 'harrison', 'fernandez', 'mcdonald',
        'woods', 'washington', 'kennedy', 'wells', 'vargas', 'henry', 'chen',
        'freeman', 'webb', 'tucker', 'guzman', 'burns', 'crawford', 'olson',
        'simpson', 'porter', 'hunter', 'gordon', 'mendez', 'silva', 'shaw',
        'snyder', 'mason', 'dixon', 'munoz', 'hunt', 'hicks', 'holmes',
        'palmer', 'wagner', 'black', 'robertson', 'boyd', 'rose', 'stone',
        'salazar', 'fox', 'warren', 'mills', 'meyer', 'rice', 'schmidt',
        'garza', 'daniels', 'ferguson', 'nichols', 'stephens', 'soto',
        'weaver', 'ryan', 'gardner', 'payne', 'grant', 'dunn', 'kelley',
        'spencer', 'hawkins', 'arnold', 'pierce', 'vazquez', 'hansen',
        'peters', 'santos', 'hart', 'bradley', 'knight', 'elliott', 'cunningham',
        'duncan', 'armstrong', 'hudson', 'carroll', 'lane', 'riley', 'andrews',
        'alvarado', 'ray', 'delgado', 'berry', 'perkins', 'hoffman', 'johnston',
        'matthews', 'pena', 'richards', 'contreras', 'willis', 'carpenter',
        'lawrence', 'sandoval', 'guerrero', 'george', 'chapman', 'rios',
        'estrada', 'ortega', 'watkins', 'greene', 'nunez', 'wheeler',
        'valdez', 'harper', 'burke', 'larson', 'santiago', 'maldonado',
        'morrison', 'franklin', 'carlson', 'austin', 'dominguez', 'carr',
        'lawson', 'jacobs', 'obrien', 'lynch', 'singh', 'vega', 'bishop',
        'montgomery', 'oliver', 'jensen', 'harvey', 'williamson', 'gilbert',
        'dean', 'sims', 'espinoza', 'howell', 'li', 'wong', 'reid',
        'hanson', 'le', 'mccoy', 'garrett', 'burton', 'fuller', 'castillo',
        'fowler', 'mckinney', 'keller', 'charles', 'frank', 'mitchell',
        'huffman', 'shepherd', 'allen', 'dodson', 'saunders', 'barry',
        'mckinney', 'love', 'gilbert', 'barrett', 'acosta', 'lucas',
        'holloway', 'summers', 'bryan', 'petersen', 'mckenzie', 'serrano',
        'wilcox', 'carey', 'clayton', 'poole', 'calderon', 'gallegos',
        'greer', 'rivas', 'guerra', 'decker', 'collier', 'wall', 'whitaker',
        'bass', 'flowers', 'davenport', 'conley', 'houston', 'huff',
        'copeland', 'hood', 'monroe', 'massey', 'roberson', 'combs',
        'franco', 'larsen', 'pittman', 'randall', 'skinner', 'wilkinson',
        'kirby', 'cameron', 'bridges', 'anthony', 'richard', 'kirk',
        'bruce', 'singleton', 'mathis', 'bradford', 'boone', 'abbott',
        'charles', 'allison', 'sweeney', 'atkinson', 'horn', 'jefferson',
        'rosales', 'york', 'christian', 'phelps', 'farrell', 'castaneda',
        'nash', 'dickerson', 'bond', 'wyatt', 'foley', 'chase', 'gates',
        'vincent', 'mathews', 'hodge', 'garrison', 'trevino', 'villarreal',
        'heath', 'dalton', 'valencia', 'callahan', 'hensley', 'atkins',
        'huffman', 'roy', 'boyer', 'shields', 'lin', 'cabrera', 'kirk',
        'rankin', 'mann', 'holloway', 'browning', 'kent', 'lozano',
        'bartlett', 'pratt', 'larry', 'rhodes', 'byrd', 'douglas',
        'mcdonald', 'tate', 'savage', 'hansen', 'holt', 'schwartz',
        'stevenson', 'curry', 'jefferson', 'benson', 'marsh', 'harper',
        'gilbert', 'gilmore', 'oneil', 'carlson', 'blackburn', 'dougherty',
        'pratt', 'williamson', 'gilbert', 'gilmore', 'oneil', 'carlson',
        'blackburn', 'dougherty', 'pratt', 'williamson', 'gilbert', 'gilmore'
    ]
    
    # Generate email components
    first_name = random.choice(first_names)
    last_name = random.choice(last_names)
    domain = random.choice(domains)
    
    # Create email variations
    email_variations = [
        f"{first_name}.{last_name}@{domain}",
        f"{first_name}{last_name}@{domain}",
        f"{first_name[0]}{last_name}@{domain}",
        f"{first_name}{last_name[0]}@{domain}",
        f"{first_name}_{last_name}@{domain}",
        f"{first_name}-{last_name}@{domain}",
        f"{first_name}{random.randint(1, 999)}@{domain}",
        f"{first_name}.{last_name}{random.randint(1, 99)}@{domain}"
    ]
    
    return random.choice(email_variations)

def generate_mock_email_data():
    try:
        # Clear terminal at start
        clear_terminal()
        
        start_time = time.time()
        
        # Read node_data.csv to get email nodes
        print("Reading node data...")
        node_df = pd.read_csv(os.path.join('src', 'data', 'input', 'node_data.csv'), usecols=['node_id', 'node_type'])
        
        # Print node type statistics
        print("\nNode Type Statistics:")
        print(f"Total number of nodes: {len(node_df)}")
        node_counts = node_df['node_type'].value_counts()
        for node_type, count in node_counts.items():
            print(f"{node_type}: {count} nodes")
        
        # Filter for email nodes
        email_nodes = node_df[node_df['node_type'] == 'email']
        if email_nodes.empty:
            print("Warning: No email nodes found in node_data.csv")
            return None
        
        # Initialize data list
        email_data = []
        
        # Generate mock data for each email node
        print("\nGenerating mock email data...")
        for _, node in tqdm(email_nodes.iterrows(), total=len(email_nodes), desc="Processing email nodes"):
            node_id = node['node_id']
            
            # Generate an email address
            email_value = generate_email()
            
            # Create node properties JSON
            node_properties = {
                "EMAIL_ADDRESS": email_value
            }
            
            # Add to data list
            email_data.append({
                'node_id': node_id,
                'node_name': email_value,
                'node_type': 'email',
                'node_properties': node_properties
            })
        
        # Save to JSON
        output_path = os.path.join('src', 'data', 'output', 'gds', 'mock_email_data.json')
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(email_data, f, indent=2)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Validate referential integrity
        validation_results = validate_referential_integrity(email_data, node_df)
        
        # Print validation results
        print("\nReferential Integrity Validation Results:")
        print(f"Total emails generated: {validation_results['total_emails']}")
        print(f"Valid emails: {validation_results['valid_emails']}")
        print(f"Invalid emails: {validation_results['invalid_emails']}")
        
        if validation_results['missing_nodes']:
            print(f"\nMissing or invalid email nodes: {len(validation_results['missing_nodes'])}")
            print("Sample of missing email nodes:", list(validation_results['missing_nodes'])[:5])
        
        print("\nNode Type Statistics:")
        for node_type, stats in validation_results['node_type_stats'].items():
            print(f"\n{node_type.capitalize()} Nodes:")
            print(f"  Total: {stats['total']}")
            print(f"  Used in valid emails: {stats['valid']}")
        
        # Count email addresses (basic statistics)
        print("\nEmail Data Summary:")
        print(f"Total unique email addresses generated: {len(email_data)}")
        
        print("\nEmail Data Generation Statistics:")
        print(f"Total number of email nodes processed: {len(email_data)}")
        print(f"Processing time: {processing_time:.2f} seconds")
        print(f"Emails per second: {len(email_data) / processing_time:.2f}")
        print(f"Data saved to: {output_path}")
        
        return email_data
        
    except Exception as e:
        print(f"Error generating mock email data: {str(e)}")
        return None

if __name__ == "__main__":
    email_data = generate_mock_email_data()
    if email_data is not None:
        print("\nSample of Generated Email Data:")
        print(json.dumps(email_data[:5], indent=2))
