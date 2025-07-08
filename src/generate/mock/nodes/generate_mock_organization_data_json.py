import pandas as pd
from faker import Faker
import json
from tqdm import tqdm
import os
import time
import platform
import hashlib
import random
import re

def clear_terminal():
    """Clear the terminal screen"""
    if platform.system() == 'Windows':
        os.system('cls')
    else:
        os.system('clear')

def generate_unique_organization_id(existing_node_ids, fake):
    """Generate a unique organization node_id that doesn't conflict with existing node_ids"""
    max_attempts = 1000
    for _ in range(max_attempts):
        organization_id = fake.uuid4()
        if organization_id not in existing_node_ids:
            return organization_id
    
    # If we can't generate a unique UUID after many attempts, use a different approach
    import time
    timestamp = int(time.time() * 1000000)  # Microsecond timestamp
    random_suffix = fake.random_int(min=1000, max=9999)
    return f"organization-{timestamp}-{random_suffix}"

def generate_duns_number_list(fake, num_duns=None):
    """Generate a list of DUNS numbers for an organization"""
    if num_duns is None:
        # Random number of DUNS numbers (1-5)
        num_duns = random.randint(1, 5)
    
    duns_list = []
    for _ in range(num_duns):
        # Generate a 9-digit DUNS number
        duns_number = str(fake.random_int(min=100000000, max=999999999))
        duns_list.append(duns_number)
    
    return duns_list

def generate_organization_type():
    """Generate a realistic NAICS organization type"""
    naics_codes = [
        "236118-Residential Remodelers",
        "238160-Roofing Contractors",
        "541511-Custom Computer Programming Services",
        "541512-Computer Systems Design Services",
        "541519-Other Computer Related Services",
        "541611-Administrative Management and General Management Consulting Services",
        "541612-Human Resources Consulting Services",
        "541613-Marketing Consulting Services",
        "541614-Process, Physical Distribution, and Logistics Consulting Services",
        "541618-Other Management Consulting Services",
        "541620-Environmental Consulting Services",
        "541690-Other Scientific and Technical Consulting Services",
        "541720-Research and Development in the Social Sciences and Humanities",
        "541810-Advertising Agencies",
        "541820-Public Relations Agencies",
        "541830-Media Buying Agencies",
        "541840-Media Representatives",
        "541850-Display Advertising",
        "541860-Direct Mail Advertising",
        "541870-Advertising Material Distribution Services",
        "541890-Other Services Related to Advertising",
        "541910-Marketing Research and Public Opinion Polling",
        "541920-Photographic Services",
        "541930-Translation and Interpretation Services",
        "541940-Veterinary Services",
        "541990-All Other Professional, Scientific, and Technical Services",
        "561110-Office Administrative Services",
        "561210-Facilities Support Services",
        "561311-Employment Placement Agencies",
        "561312-Executive Search Services",
        "561320-Temporary Help Services",
        "561330-Professional Employer Organizations",
        "561410-Document Preparation Services",
        "561421-Telephone Answering Services",
        "561422-Telemarketing Bureaus and Other Contact Centers",
        "561431-Private Mail Centers",
        "561439-Other Business Service Centers",
        "561440-Collection Agencies",
        "561450-Credit Bureaus",
        "561491-Repossession Services",
        "561492-Court Reporting and Stenotype Services",
        "561499-All Other Business Support Services",
        "561510-Travel Agencies",
        "561520-Tour Operators",
        "561591-Convention and Visitors Bureaus",
        "561599-All Other Travel Arrangement and Reservation Services",
        "561611-Investigation Services",
        "561612-Security Guards and Patrol Services",
        "561613-Armored Car Services",
        "561621-Security Systems Services (except Locksmiths)",
        "561622-Locksmiths",
        "561710-Exterminating and Pest Control Services",
        "561720-Janitorial Services",
        "561730-Landscaping Services",
        "561740-Carpet and Upholstery Cleaning Services",
        "561790-Other Services to Buildings and Dwellings",
        "561910-Packaging and Labeling Services",
        "561920-Convention and Trade Show Organizers",
        "561990-All Other Support Services",
        "562111-Solid Waste Collection",
        "562112-Hazardous Waste Collection",
        "562119-Other Waste Collection",
        "562211-Hazardous Waste Treatment and Disposal",
        "562212-Solid Waste Landfill",
        "562213-Solid Waste Combustors and Incinerators",
        "562219-Other Nonhazardous Waste Treatment and Disposal",
        "562910-Remediation Services",
        "562920-Materials Recovery Facilities",
        "562998-All Other Miscellaneous Waste Management Services",
        "562999-All Other Miscellaneous Waste Management Services",
        "611110-Elementary and Secondary Schools",
        "611210-Junior Colleges",
        "611310-Colleges, Universities, and Professional Schools",
        "611410-Business and Secretarial Schools",
        "611420-Computer Training",
        "611430-Professional and Management Development Training",
        "611511-Cosmetology and Barber Schools",
        "611512-Flight Training",
        "611513-Apprenticeship Training",
        "611519-Other Technical and Trade Schools",
        "611610-Fine Arts Schools",
        "611620-Sports and Recreation Instruction",
        "611630-Language Schools",
        "611691-Exam Preparation and Tutoring",
        "611692-Automobile Driving Schools",
        "611699-All Other Schools and Instruction",
        "611710-Educational Support Services",
        "621111-Offices of Physicians (except Mental Health Specialists)",
        "621112-Offices of Physicians, Mental Health Specialists",
        "621210-Offices of Dentists",
        "621310-Offices of Chiropractors",
        "621320-Offices of Optometrists",
        "621330-Offices of Mental Health Practitioners (except Physicians)",
        "621340-Offices of Physical, Occupational and Speech Therapists, and Audiologists",
        "621391-Offices of Podiatrists",
        "621399-Offices of All Other Miscellaneous Health Practitioners",
        "621410-Family Planning Centers",
        "621420-Outpatient Mental Health and Substance Abuse Centers",
        "621491-HMO Medical Centers",
        "621492-Kidney Dialysis Centers",
        "621493-Freestanding Ambulatory Surgical and Emergency Centers",
        "621498-All Other Outpatient Care Centers",
        "621511-Medical Laboratories",
        "621512-Diagnostic Imaging Centers",
        "621610-Home Health Care Services",
        "621910-Ambulance Services",
        "621991-Blood and Organ Banks",
        "621999-All Other Miscellaneous Ambulatory Health Care Services",
        "622110-General Medical and Surgical Hospitals",
        "622210-Psychiatric and Substance Abuse Hospitals",
        "622310-Specialty (except Psychiatric and Substance Abuse) Hospitals",
        "623110-Nursing Care Facilities (Skilled Nursing Facilities)",
        "623210-Residential Intellectual and Developmental Disability Facilities",
        "623220-Residential Mental Health and Substance Abuse Facilities",
        "623311-Continuing Care Retirement Communities",
        "623312-Assisted Living Facilities for the Elderly",
        "623990-Other Residential Care Facilities",
        "624110-Child and Youth Services",
        "624120-Services for the Elderly and Persons with Disabilities",
        "624190-Other Individual and Family Services",
        "624210-Community Food Services",
        "624221-Temporary Shelters",
        "624229-Other Community Housing Services",
        "624230-Emergency and Other Relief Services",
        "624310-Vocational Rehabilitation Services",
        "624410-Child Day Care Services",
        "711110-Theater Companies and Dinner Theaters",
        "711120-Dance Companies",
        "711130-Musical Groups and Artists",
        "711190-Other Performing Arts Companies",
        "711211-Sports Teams and Clubs",
        "711212-Racetracks",
        "711219-Other Spectator Sports",
        "711310-Promoters of Performing Arts, Sports, and Similar Events",
        "711320-Promoters of Events (except Performing Arts, Sports, and Similar Events)",
        "711410-Agents and Managers for Artists, Athletes, Entertainers, and Other Public Figures",
        "711510-Independent Artists, Writers, and Performers",
        "712110-Museums",
        "712120-Historical Sites",
        "712130-Zoos and Botanical Gardens",
        "712190-Nature Parks and Other Similar Institutions",
        "713110-Amusement and Theme Parks",
        "713120-Amusement Arcades",
        "713210-Casinos (except Casino Hotels)",
        "713290-Other Gambling Industries",
        "713910-Golf Courses and Country Clubs",
        "713920-Skiing Facilities",
        "713930-Marinas",
        "713940-Fitness and Recreational Sports Centers",
        "713950-Bowling Centers",
        "713990-All Other Amusement and Recreation Industries",
        "721110-Hotels (except Casino Hotels) and Motels",
        "721120-Casino Hotels",
        "721191-Bed-and-Breakfast Inns",
        "721199-All Other Traveler Accommodation",
        "721211-RV (Recreational Vehicle) Parks and Campgrounds",
        "721214-Recreational and Vacation Camps (except Campgrounds)",
        "721310-Rooming and Boarding Houses, Dormitories, and Workers' Camps",
        "722310-Food Service Contractors",
        "722320-Caterers",
        "722330-Mobile Food Services",
        "722410-Drinking Places (Alcoholic Beverages)",
        "722511-Full-Service Restaurants",
        "722513-Limited-Service Restaurants",
        "722514-Cafeterias, Grill Buffets, and Buffets",
        "722515-Snack and Nonalcoholic Beverage Bars",
        "722590-All Other Food and Drinking Places",
        "811111-General Automotive Repair",
        "811112-Automotive Exhaust System Repair",
        "811113-Automotive Transmission Repair",
        "811118-Other Automotive Mechanical and Electrical Repair and Maintenance",
        "811121-Automotive Body, Paint, and Interior Repair and Maintenance",
        "811122-Automotive Glass Replacement Shops",
        "811191-Automotive Oil Change and Lubrication Shops",
        "811192-Car Washes",
        "811198-All Other Automotive Repair and Maintenance",
        "811211-Electronic and Precision Equipment Repair and Maintenance",
        "811212-Computer and Office Machine Repair and Maintenance",
        "811213-Communication Equipment Repair and Maintenance",
        "811219-Other Electronic and Precision Equipment Repair and Maintenance",
        "811310-Commercial and Industrial Machinery and Equipment (except Automotive and Electronic) Repair and Maintenance",
        "811411-Home and Garden Equipment Repair and Maintenance",
        "811412-Appliance Repair and Maintenance",
        "811420-Reupholstery and Furniture Repair",
        "811430-Footwear and Leather Goods Repair",
        "811490-Other Personal and Household Goods Repair and Maintenance",
        "812111-Barber Shops",
        "812112-Beauty Salons",
        "812113-Nail Salons",
        "812191-Diet and Weight Reducing Centers",
        "812199-Other Personal Care Services",
        "812210-Funeral Homes and Funeral Services",
        "812220-Cemeteries and Crematories",
        "812310-Coin-Operated Laundries and Drycleaners",
        "812320-Drycleaning and Laundry Services (except Coin-Operated)",
        "812331-Linen Supply",
        "812332-Industrial Launderers",
        "812410-Portrait Photography Studios",
        "812910-Pet Care (except Veterinary) Services",
        "812921-Photofinishing Laboratories (except One-Hour)",
        "812922-One-Hour Photofinishing",
        "812930-Parking Lots and Garages",
        "812990-All Other Personal Services",
        "813110-Religious Organizations",
        "813211-Grantmaking Foundations",
        "813212-Voluntary Health Organizations",
        "813219-Other Grantmaking and Giving Services",
        "813311-Human Rights Organizations",
        "813312-Environment, Conservation and Wildlife Organizations",
        "813319-Other Social Advocacy Organizations",
        "813410-Civic and Social Organizations",
        "813910-Business Associations",
        "813920-Professional Organizations",
        "813930-Labor Unions and Similar Labor Organizations",
        "813940-Political Organizations",
        "813990-Other Similar Organizations (except Business, Professional, Labor, and Political Organizations)",
        "813990-Other Similar Organizations (except Business, Professional, Labor, and Political Organizations)",
        "814110-Private Households"
    ]
    return random.choice(naics_codes)

def generate_naics_list(fake, num_naics=None):
    """Generate a list of NAICS codes for an organization"""
    if num_naics is None:
        # Random number of NAICS codes (1-3)
        num_naics = random.randint(1, 3)
    
    naics_codes = [
        "236118-Residential Remodelers",
        "238160-Roofing Contractors",
        "541511-Custom Computer Programming Services",
        "541512-Computer Systems Design Services",
        "541519-Other Computer Related Services",
        "541611-Administrative Management and General Management Consulting Services",
        "541612-Human Resources Consulting Services",
        "541613-Marketing Consulting Services",
        "541614-Process, Physical Distribution, and Logistics Consulting Services",
        "541618-Other Management Consulting Services",
        "541620-Environmental Consulting Services",
        "541690-Other Scientific and Technical Consulting Services",
        "541720-Research and Development in the Social Sciences and Humanities",
        "541810-Advertising Agencies",
        "541820-Public Relations Agencies",
        "541830-Media Buying Agencies",
        "541840-Media Representatives",
        "541850-Display Advertising",
        "541860-Direct Mail Advertising",
        "541870-Advertising Material Distribution Services",
        "541890-Other Services Related to Advertising",
        "541910-Marketing Research and Public Opinion Polling",
        "541920-Photographic Services",
        "541930-Translation and Interpretation Services",
        "541940-Veterinary Services",
        "541990-All Other Professional, Scientific, and Technical Services",
        "561110-Office Administrative Services",
        "561210-Facilities Support Services",
        "561311-Employment Placement Agencies",
        "561312-Executive Search Services",
        "561320-Temporary Help Services",
        "561330-Professional Employer Organizations",
        "561410-Document Preparation Services",
        "561421-Telephone Answering Services",
        "561422-Telemarketing Bureaus and Other Contact Centers",
        "561431-Private Mail Centers",
        "561439-Other Business Service Centers",
        "561440-Collection Agencies",
        "561450-Credit Bureaus",
        "561491-Repossession Services",
        "561492-Court Reporting and Stenotype Services",
        "561499-All Other Business Support Services",
        "561510-Travel Agencies",
        "561520-Tour Operators",
        "561591-Convention and Visitors Bureaus",
        "561599-All Other Travel Arrangement and Reservation Services",
        "561611-Investigation Services",
        "561612-Security Guards and Patrol Services",
        "561613-Armored Car Services",
        "561621-Security Systems Services (except Locksmiths)",
        "561622-Locksmiths",
        "561710-Exterminating and Pest Control Services",
        "561720-Janitorial Services",
        "561730-Landscaping Services",
        "561740-Carpet and Upholstery Cleaning Services",
        "561790-Other Services to Buildings and Dwellings",
        "561910-Packaging and Labeling Services",
        "561920-Convention and Trade Show Organizers",
        "561990-All Other Support Services",
        "562111-Solid Waste Collection",
        "562112-Hazardous Waste Collection",
        "562119-Other Waste Collection",
        "562211-Hazardous Waste Treatment and Disposal",
        "562212-Solid Waste Landfill",
        "562213-Solid Waste Combustors and Incinerators",
        "562219-Other Nonhazardous Waste Treatment and Disposal",
        "562910-Remediation Services",
        "562920-Materials Recovery Facilities",
        "562998-All Other Miscellaneous Waste Management Services",
        "562999-All Other Miscellaneous Waste Management Services",
        "611110-Elementary and Secondary Schools",
        "611210-Junior Colleges",
        "611310-Colleges, Universities, and Professional Schools",
        "611410-Business and Secretarial Schools",
        "611420-Computer Training",
        "611430-Professional and Management Development Training",
        "611511-Cosmetology and Barber Schools",
        "611512-Flight Training",
        "611513-Apprenticeship Training",
        "611519-Other Technical and Trade Schools",
        "611610-Fine Arts Schools",
        "611620-Sports and Recreation Instruction",
        "611630-Language Schools",
        "611691-Exam Preparation and Tutoring",
        "611692-Automobile Driving Schools",
        "611699-All Other Schools and Instruction",
        "611710-Educational Support Services",
        "621111-Offices of Physicians (except Mental Health Specialists)",
        "621112-Offices of Physicians, Mental Health Specialists",
        "621210-Offices of Dentists",
        "621310-Offices of Chiropractors",
        "621320-Offices of Optometrists",
        "621330-Offices of Mental Health Practitioners (except Physicians)",
        "621340-Offices of Physical, Occupational and Speech Therapists, and Audiologists",
        "621391-Offices of Podiatrists",
        "621399-Offices of All Other Miscellaneous Health Practitioners",
        "621410-Family Planning Centers",
        "621420-Outpatient Mental Health and Substance Abuse Centers",
        "621491-HMO Medical Centers",
        "621492-Kidney Dialysis Centers",
        "621493-Freestanding Ambulatory Surgical and Emergency Centers",
        "621498-All Other Outpatient Care Centers",
        "621511-Medical Laboratories",
        "621512-Diagnostic Imaging Centers",
        "621610-Home Health Care Services",
        "621910-Ambulance Services",
        "621991-Blood and Organ Banks",
        "621999-All Other Miscellaneous Ambulatory Health Care Services",
        "622110-General Medical and Surgical Hospitals",
        "622210-Psychiatric and Substance Abuse Hospitals",
        "622310-Specialty (except Psychiatric and Substance Abuse) Hospitals",
        "623110-Nursing Care Facilities (Skilled Nursing Facilities)",
        "623210-Residential Intellectual and Developmental Disability Facilities",
        "623220-Residential Mental Health and Substance Abuse Facilities",
        "623311-Continuing Care Retirement Communities",
        "623312-Assisted Living Facilities for the Elderly",
        "623990-Other Residential Care Facilities",
        "624110-Child and Youth Services",
        "624120-Services for the Elderly and Persons with Disabilities",
        "624190-Other Individual and Family Services",
        "624210-Community Food Services",
        "624221-Temporary Shelters",
        "624229-Other Community Housing Services",
        "624230-Emergency and Other Relief Services",
        "624310-Vocational Rehabilitation Services",
        "624410-Child Day Care Services",
        "711110-Theater Companies and Dinner Theaters",
        "711120-Dance Companies",
        "711130-Musical Groups and Artists",
        "711190-Other Performing Arts Companies",
        "711211-Sports Teams and Clubs",
        "711212-Racetracks",
        "711219-Other Spectator Sports",
        "711310-Promoters of Performing Arts, Sports, and Similar Events",
        "711320-Promoters of Events (except Performing Arts, Sports, and Similar Events)",
        "711410-Agents and Managers for Artists, Athletes, Entertainers, and Other Public Figures",
        "711510-Independent Artists, Writers, and Performers",
        "712110-Museums",
        "712120-Historical Sites",
        "712130-Zoos and Botanical Gardens",
        "712190-Nature Parks and Other Similar Institutions",
        "713110-Amusement and Theme Parks",
        "713120-Amusement Arcades",
        "713210-Casinos (except Casino Hotels)",
        "713290-Other Gambling Industries",
        "713910-Golf Courses and Country Clubs",
        "713920-Skiing Facilities",
        "713930-Marinas",
        "713940-Fitness and Recreational Sports Centers",
        "713950-Bowling Centers",
        "713990-All Other Amusement and Recreation Industries",
        "721110-Hotels (except Casino Hotels) and Motels",
        "721120-Casino Hotels",
        "721191-Bed-and-Breakfast Inns",
        "721199-All Other Traveler Accommodation",
        "721211-RV (Recreational Vehicle) Parks and Campgrounds",
        "721214-Recreational and Vacation Camps (except Campgrounds)",
        "721310-Rooming and Boarding Houses, Dormitories, and Workers' Camps",
        "722310-Food Service Contractors",
        "722320-Caterers",
        "722330-Mobile Food Services",
        "722410-Drinking Places (Alcoholic Beverages)",
        "722511-Full-Service Restaurants",
        "722513-Limited-Service Restaurants",
        "722514-Cafeterias, Grill Buffets, and Buffets",
        "722515-Snack and Nonalcoholic Beverage Bars",
        "722590-All Other Food and Drinking Places",
        "811111-General Automotive Repair",
        "811112-Automotive Exhaust System Repair",
        "811113-Automotive Transmission Repair",
        "811118-Other Automotive Mechanical and Electrical Repair and Maintenance",
        "811121-Automotive Body, Paint, and Interior Repair and Maintenance",
        "811122-Automotive Glass Replacement Shops",
        "811191-Automotive Oil Change and Lubrication Shops",
        "811192-Car Washes",
        "811198-All Other Automotive Repair and Maintenance",
        "811211-Electronic and Precision Equipment Repair and Maintenance",
        "811212-Computer and Office Machine Repair and Maintenance",
        "811213-Communication Equipment Repair and Maintenance",
        "811219-Other Electronic and Precision Equipment Repair and Maintenance",
        "811310-Commercial and Industrial Machinery and Equipment (except Automotive and Electronic) Repair and Maintenance",
        "811411-Home and Garden Equipment Repair and Maintenance",
        "811412-Appliance Repair and Maintenance",
        "811420-Reupholstery and Furniture Repair",
        "811430-Footwear and Leather Goods Repair",
        "811490-Other Personal and Household Goods Repair and Maintenance",
        "812111-Barber Shops",
        "812112-Beauty Salons",
        "812113-Nail Salons",
        "812191-Diet and Weight Reducing Centers",
        "812199-Other Personal Care Services",
        "812210-Funeral Homes and Funeral Services",
        "812220-Cemeteries and Crematories",
        "812310-Coin-Operated Laundries and Drycleaners",
        "812320-Drycleaning and Laundry Services (except Coin-Operated)",
        "812331-Linen Supply",
        "812332-Industrial Launderers",
        "812410-Portrait Photography Studios",
        "812910-Pet Care (except Veterinary) Services",
        "812921-Photofinishing Laboratories (except One-Hour)",
        "812922-One-Hour Photofinishing",
        "812930-Parking Lots and Garages",
        "812990-All Other Personal Services",
        "813110-Religious Organizations",
        "813211-Grantmaking Foundations",
        "813212-Voluntary Health Organizations",
        "813219-Other Grantmaking and Giving Services",
        "813311-Human Rights Organizations",
        "813312-Environment, Conservation and Wildlife Organizations",
        "813319-Other Social Advocacy Organizations",
        "813410-Civic and Social Organizations",
        "813910-Business Associations",
        "813920-Professional Organizations",
        "813930-Labor Unions and Similar Labor Organizations",
        "813940-Political Organizations",
        "813990-Other Similar Organizations (except Business, Professional, Labor, and Political Organizations)",
        "813990-Other Similar Organizations (except Business, Professional, Labor, and Political Organizations)",
        "814110-Private Households"
    ]
    
    # Select random NAICS codes without duplicates
    selected_naics = random.sample(naics_codes, min(num_naics, len(naics_codes)))
    return selected_naics

def generate_fein_list(fake, num_fein=None):
    """Generate a list of FEIN numbers for an organization"""
    if num_fein is None:
        # Random number of FEIN numbers (0-2)
        num_fein = random.randint(0, 2)
    
    fein_list = []
    for _ in range(num_fein):
        # Generate a 9-digit FEIN number
        fein_number = str(fake.random_int(min=100000000, max=999999999))
        fein_list.append(fein_number)
    
    return fein_list

def generate_vibe_score():
    """Generate a VIBE score"""
    vibe_scores = ["GREEN", "YELLOW", "ORANGE", "RED"]
    return random.choice(vibe_scores)

def generate_legal_status():
    """Generate a legal status code"""
    legal_statuses = ["001", "002", "003", "004", "005", "006", "007", "008", "009", "010", "011", "012", "013", "014", "015"]
    return random.choice(legal_statuses)

def generate_child_parent():
    """Generate child/parent relationship"""
    relationships = ["parent_org", "child_org", "independent"]
    return random.choice(relationships)

def generate_foreign_relationship():
    """Generate foreign relationship indicator"""
    return random.choice(["Y", "N"])

def generate_business_activity():
    """Generate business activity indicator"""
    return random.choice(["Y", "N"])

def generate_trade_names(fake, num_trade_names=None):
    """Generate a list of trade names for an organization"""
    if num_trade_names is None:
        # Random number of trade names (0-3)
        num_trade_names = random.randint(0, 3)
    
    if num_trade_names == 0:
        return []
    
    trade_names = []
    for _ in range(num_trade_names):
        # Generate a simple trade name
        trade_name = fake.company()
        trade_names.append(trade_name)
    
    return trade_names

def generate_year_established():
    """Generate a year established (between 1900 and current year)"""
    current_year = 2024
    return random.randint(1900, current_year)

def generate_organization_name(fake):
    """Generate a realistic organization name"""
    organization_types = [
        "Corporation", "Inc.", "LLC", "Ltd.", "Company", "Enterprises", 
        "Group", "Partners", "Associates", "Consulting", "Solutions",
        "Technologies", "Systems", "Services", "Industries", "Manufacturing"
    ]
    
    # Generate company name components
    name_components = []
    
    # Add a company name (could be person name, place, or abstract)
    if random.choice([True, False]):
        # Use a person's name
        name_components.append(fake.last_name())
    else:
        # Use a place or abstract name
        place_names = [
            "Global", "National", "Regional", "Central", "Pacific", "Atlantic",
            "Northern", "Southern", "Eastern", "Western", "Metro", "Urban",
            "Digital", "Advanced", "Innovative", "Strategic", "Premier"
        ]
        name_components.append(random.choice(place_names))
    
    # Add a business type or industry
    business_types = [
        "Tech", "Data", "Software", "Hardware", "Network", "Security",
        "Finance", "Insurance", "Healthcare", "Education", "Transportation",
        "Construction", "Manufacturing", "Retail", "Wholesale", "Distribution",
        "Consulting", "Research", "Development", "Engineering"
    ]
    name_components.append(random.choice(business_types))
    
    # Add organization type
    name_components.append(random.choice(organization_types))
    
    return " ".join(name_components)

def validate_organization_data(organization_data):
    """Validate organization data for completeness and uniqueness"""
    validation_results = {
        'total_organizations': len(organization_data),
        'valid_organizations': 0,
        'invalid_organizations': 0,
        'unique_organization_names': set(),
        'unique_duns_numbers': set(),
        'missing_required_fields': 0,
        'duplicate_organization_names': 0,
        'duplicate_duns_numbers': 0
    }
    
    for org_entry in organization_data:
        org_props = org_entry['node_properties']
        
        # Check for required fields
        required_fields = ['ORGANIZATION_NAME', 'DUNS_NUMBER_LIST', 'ORGANIZATION_DETAIL_LIST']
        missing_fields = [field for field in required_fields if field not in org_props]
        
        if missing_fields:
            validation_results['missing_required_fields'] += 1
            validation_results['invalid_organizations'] += 1
            continue
        
        # Check organization name uniqueness
        org_name = org_props['ORGANIZATION_NAME']
        if org_name in validation_results['unique_organization_names']:
            validation_results['duplicate_organization_names'] += 1
        else:
            validation_results['unique_organization_names'].add(org_name)
        
        # Check DUNS numbers uniqueness
        duns_list = org_props['DUNS_NUMBER_LIST']
        for duns in duns_list:
            if duns in validation_results['unique_duns_numbers']:
                validation_results['duplicate_duns_numbers'] += 1
            else:
                validation_results['unique_duns_numbers'].add(duns)
        
        # Validate organization detail list
        if 'ORGANIZATION_DETAIL_LIST' in org_props:
            detail_list = org_props['ORGANIZATION_DETAIL_LIST']
            if isinstance(detail_list, list) and len(detail_list) > 0:
                detail = detail_list[0]  # Check first detail entry
                required_detail_fields = [
                    'ORGANIZATION_NAME', 'ORGANIZATION_TYPE', 'DUNS_NUMBER', 
                    'CHILD_PARENT', 'VIBE_SCORE', 'FRGN_RELATIONSHIP', 
                    'LEGAL_STATUS', 'NAICS', 'FEIN', 'YEAR_ESTABLISHED', 
                    'BUSINESS_ACTIVITY', 'TRADE_NAME'
                ]
                missing_detail_fields = [field for field in required_detail_fields if field not in detail]
                if missing_detail_fields:
                    validation_results['missing_required_fields'] += 1
                    validation_results['invalid_organizations'] += 1
                    continue
        
        validation_results['valid_organizations'] += 1
    
    return validation_results

def generate_mock_organization_data():
    try:
        # Clear terminal at start
        clear_terminal()
        
        start_time = time.time()
        
        # Initialize Faker
        fake = Faker()
        
        # Read organization IDs from the CSV file
        print("Reading organization IDs from CSV file...")
        csv_path = os.path.join('src', 'data', 'input', 'node_data.csv')
        
        if not os.path.exists(csv_path):
            print(f"Error: CSV file not found at {csv_path}")
            return None
        
        # Read CSV and filter for organization node_ids
        df = pd.read_csv(csv_path)
        organization_ids = df[df['node_type'] == 'organization']['node_id'].tolist()
        
        if not organization_ids:
            print("Error: No organization IDs found in the CSV file")
            return None
        
        print(f"Found {len(organization_ids)} organization IDs in the CSV file")
        
        # Get all existing node_ids to ensure uniqueness (if any exist)
        existing_node_ids = set()
        
        # Check if building data exists to avoid conflicts
        building_data_path = os.path.join('src', 'data', 'output', 'gds', 'mock_building_data.json')
        if os.path.exists(building_data_path):
            with open(building_data_path, 'r') as f:
                building_data = json.load(f)
                existing_node_ids.update({building['node_id'] for building in building_data})
        
        # Check if address data exists to avoid conflicts
        address_data_path = os.path.join('src', 'data', 'output', 'gds', 'mock_address_data.json')
        if os.path.exists(address_data_path):
            with open(address_data_path, 'r') as f:
                address_data = json.load(f)
                existing_node_ids.update({addr['node_id'] for addr in address_data})
        
        print(f"Found {len(existing_node_ids)} existing node_ids to avoid conflicts")
        
        # Initialize organization data list
        organization_data = []
        
        # Generate mock organization data using the IDs from CSV
        print(f"\nGenerating mock organization data for {len(organization_ids)} organizations...")
        for organization_id in tqdm(organization_ids, desc="Processing organization nodes"):
            # Generate organization name
            organization_name = generate_organization_name(fake)
            
            # Generate DUNS number list
            duns_number_list = generate_duns_number_list(fake)
            
            # Generate organization detail list
            organization_detail = {
                "ORGANIZATION_NAME": organization_name,
                "ORGANIZATION_TYPE": generate_organization_type(),
                "DUNS_NUMBER": duns_number_list[0] if duns_number_list else "",  # Use first DUNS as primary
                "CHILD_PARENT": generate_child_parent(),
                "VIBE_SCORE": generate_vibe_score(),
                "FRGN_RELATIONSHIP": generate_foreign_relationship(),
                "LEGAL_STATUS": generate_legal_status(),
                "NAICS": generate_naics_list(fake),
                "FEIN": generate_fein_list(fake),
                "YEAR_ESTABLISHED": generate_year_established(),
                "BUSINESS_ACTIVITY": generate_business_activity(),
                "TRADE_NAME": generate_trade_names(fake)
            }
            
            # Create node properties JSON
            node_properties = {
                'ORGANIZATION_NAME': organization_name,
                'DUNS_NUMBER_LIST': duns_number_list,
                'ORGANIZATION_DETAIL_LIST': [organization_detail]
            }
            
            # Add to organization data list
            organization_data.append({
                'node_id': organization_id,
                'node_name': organization_name,
                'node_properties': node_properties
            })
        
        # Save to JSON
        output_path = os.path.join('src', 'data', 'output', 'gds', 'mock_organization_data.json')
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(organization_data, f, indent=2)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Validate organization data
        validation_results = validate_organization_data(organization_data)
        
        # Print validation results
        print("\nOrganization Data Validation Results:")
        print(f"Total organizations generated: {validation_results['total_organizations']}")
        print(f"Valid organizations: {validation_results['valid_organizations']}")
        print(f"Invalid organizations: {validation_results['invalid_organizations']}")
        print(f"Missing required fields: {validation_results['missing_required_fields']}")
        print(f"Duplicate organization names: {validation_results['duplicate_organization_names']}")
        print(f"Duplicate DUNS numbers: {validation_results['duplicate_duns_numbers']}")
        
        print("\nOrganization Statistics:")
        print(f"Unique organization names: {len(validation_results['unique_organization_names'])}")
        print(f"Unique DUNS numbers: {len(validation_results['unique_duns_numbers'])}")
        print(f"Average DUNS numbers per organization: {len(validation_results['unique_duns_numbers']) / validation_results['total_organizations']:.1f}")
        
        print("\nOrganization Data Generation Statistics:")
        print(f"Total number of organization nodes processed: {len(organization_data)}")
        print(f"Organizations from CSV file: {len(organization_ids)}")
        print(f"Processing time: {processing_time:.2f} seconds")
        print(f"Organizations per second: {len(organization_data) / processing_time:.2f}")
        print(f"Data saved to: {output_path}")
        
        return organization_data
        
    except Exception as e:
        print(f"Error generating mock organization data: {str(e)}")
        return None

if __name__ == "__main__":
    organization_data = generate_mock_organization_data()
    if organization_data is not None:
        print("\nSample of Generated Organization Data:")
        print(json.dumps(organization_data[:3], indent=2))
