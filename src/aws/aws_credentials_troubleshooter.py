#!/usr/bin/env python3
"""
AWS Credentials Troubleshooter
Helps diagnose and fix common AWS credential issues including signature methods
"""

import os
import sys
import datetime
import subprocess
import configparser
import getpass
from pathlib import Path
import re
import ntplib
import boto3
import hashlib
import hmac
import base64
import urllib.parse
import requests

def clear_screen():
    """Clear the terminal screen in a cross-platform way"""
    os.system('cls' if os.name == 'nt' else 'clear')

def check_time_sync():
    """Check if system time is synchronized with NTP servers"""
    try:
        c = ntplib.NTPClient()
        response = c.request('pool.ntp.org', version=3)
        system_time = datetime.datetime.now()
        ntp_time = datetime.datetime.fromtimestamp(response.tx_time)
        offset = abs((system_time - ntp_time).total_seconds())
        
        print(f"System time: {system_time}")
        print(f"NTP time:    {ntp_time}")
        print(f"Offset:      {offset:.2f} seconds")
        
        if offset > 30:
            print("WARNING: Your system clock is off by more than 30 seconds!")
            print("This could cause AWS authentication failures.")
            if sys.platform == 'darwin':  # macOS
                print("\nTo fix on macOS, run:")
                print("sudo sntp -sS pool.ntp.org")
            elif sys.platform.startswith('linux'):
                print("\nTo fix on Linux, run:")
                print("sudo apt-get install ntpdate && sudo ntpdate pool.ntp.org")
            return False
        else:
            print("✓ System clock is properly synchronized.")
            return True
    except Exception as e:
        print(f"Could not check time synchronization: {e}")
        print("Please ensure your system time is correct.")
        return False

def check_credentials_file():
    """Check AWS credentials file for issues"""
    aws_dir = os.path.expanduser("~/.aws")
    credentials_file = os.path.join(aws_dir, "credentials")
    
    if not os.path.exists(credentials_file):
        print("❌ AWS credentials file not found.")
        return False
    
    print(f"Found credentials file: {credentials_file}")
    
    # Check file permissions
    permissions = oct(os.stat(credentials_file).st_mode)[-3:]
    if permissions != '600':
        print(f"⚠️ Credentials file has permissions {permissions}, should be 600.")
        fix = input("Fix permissions now? (y/n): ")
        if fix.lower() == 'y':
            os.chmod(credentials_file, 0o600)
            print("✓ Permissions fixed.")
    else:
        print("✓ File permissions are correct (600).")
    
    # Check file contents
    config = configparser.ConfigParser()
    config.read(credentials_file)
    
    if len(config.sections()) == 0:
        print("❌ No profiles found in credentials file.")
        return False
    
    # Ask which profile to check
    if len(config.sections()) == 1:
        profile = config.sections()[0]
    else:
        print("\nAvailable profiles:")
        for i, section in enumerate(config.sections(), 1):
            print(f"{i}. {section}")
        choice = input("\nSelect profile to check (number or name): ")
        try:
            if choice.isdigit() and 1 <= int(choice) <= len(config.sections()):
                profile = config.sections()[int(choice) - 1]
            elif choice in config.sections():
                profile = choice
            else:
                print("Invalid selection, using first profile.")
                profile = config.sections()[0]
        except:
            print("Invalid selection, using first profile.")
            profile = config.sections()[0]
    
    print(f"\nChecking profile: {profile}")
    
    if not config.has_option(profile, 'aws_access_key_id'):
        print("❌ Missing aws_access_key_id in profile.")
        return False
    
    if not config.has_option(profile, 'aws_secret_access_key'):
        print("❌ Missing aws_secret_access_key in profile.")
        return False
    
    # Check access key format (usually starts with 'AKIA')
    access_key = config[profile]['aws_access_key_id']
    if not re.match(r'^[A-Z0-9]{20}$', access_key) or not access_key.startswith(('AKIA', 'ASIA')):
        print("⚠️ Access key ID may be invalid. It should be 20 characters and start with AKIA or ASIA.")
    else:
        print(f"✓ Access key ID format looks valid: {access_key[:4]}...{access_key[-4:]}")
    
    # Check secret key format
    secret_key = config[profile]['aws_secret_access_key']
    if len(secret_key) != 40 or not re.match(r'^[A-Za-z0-9/+]{40}$', secret_key):
        print("⚠️ Secret access key may be invalid. It should be 40 characters.")
        reenter = input("Would you like to re-enter your secret key? (y/n): ")
        if reenter.lower() == 'y':
            new_secret = getpass.getpass("Enter AWS Secret Access Key: ")
            if new_secret != secret_key:
                config[profile]['aws_secret_access_key'] = new_secret
                with open(credentials_file, 'w') as f:
                    config.write(f)
                print("✓ Secret key updated.")
    else:
        print(f"✓ Secret key format looks valid: {secret_key[:3]}...{secret_key[-3:]}")
    
    return profile

def test_aws_cli(profile=None):
    """Test AWS CLI with the given profile"""
    cmd = ['aws', 'sts', 'get-caller-identity']
    if profile:
        cmd.extend(['--profile', profile])
    
    print(f"\nTesting AWS CLI with command: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ AWS CLI test successful!")
            print(result.stdout)
            return True
        else:
            print(f"❌ AWS CLI test failed: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"Error running AWS CLI: {str(e)}")
        return False

def test_sigv4_signing(profile=None):
    """Test AWS SigV4 signature calculation with the given profile"""
    print("\n=== Testing AWS Signature Version 4 (SigV4) ===")
    print("AWS uses Signature Version 4 (SigV4) for API request authentication")
    
    try:
        # Create session with specific profile if provided
        if profile:
            session = boto3.Session(profile_name=profile)
        else:
            session = boto3.Session()
        
        credentials = session.get_credentials()
        if not credentials:
            print("❌ Could not get credentials from session.")
            return False
        
        # Get resolved credentials
        access_key = credentials.access_key
        secret_key = credentials.secret_key
        
        # Print credentials format (partial)
        print(f"Access Key ID: {access_key[:4]}...{access_key[-4:]}")
        print(f"Secret Access Key: {secret_key[:3]}...{secret_key[-3:]}")
        
        # Get region
        region = session.region_name or 'us-east-1'
        print(f"Region: {region}")
        
        # Perform a simple SigV4 signature test with STS
        service = 'sts'
        host = f"{service}.{region}.amazonaws.com"
        endpoint = f"https://{host}"
        
        print(f"\nTesting signature with endpoint: {endpoint}")
        
        # Get current date for signing
        amz_date = datetime.datetime.now(datetime.UTC).strftime('%Y%m%dT%H%M%SZ')
        datestamp = datetime.datetime.now(datetime.UTC).strftime('%Y%m%d')
        
        # Create a canonical request
        method = 'GET'
        canonical_uri = '/'
        canonical_querystring = 'Action=GetCallerIdentity&Version=2011-06-15'
        
        canonical_headers = f'host:{host}\nx-amz-date:{amz_date}\n'
        signed_headers = 'host;x-amz-date'
        
        payload_hash = hashlib.sha256(b'').hexdigest()
        
        canonical_request = f"{method}\n{canonical_uri}\n{canonical_querystring}\n{canonical_headers}\n{signed_headers}\n{payload_hash}"
        
        # Create string to sign
        algorithm = 'AWS4-HMAC-SHA256'
        credential_scope = f"{datestamp}/{region}/{service}/aws4_request"
        string_to_sign = f"{algorithm}\n{amz_date}\n{credential_scope}\n{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"
        
        # Calculate signature
        def sign(key, msg):
            return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()
        
        def get_signature_key(key, date_stamp, region_name, service_name):
            k_date = sign(('AWS4' + key).encode('utf-8'), date_stamp)
            k_region = sign(k_date, region_name)
            k_service = sign(k_region, service_name)
            k_signing = sign(k_service, 'aws4_request')
            return k_signing
        
        signing_key = get_signature_key(secret_key, datestamp, region, service)
        signature = hmac.new(signing_key, string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()
        
        # Create authorization header
        authorization_header = f"{algorithm} Credential={access_key}/{credential_scope}, SignedHeaders={signed_headers}, Signature={signature}"
        
        # Create headers for request
        headers = {
            'Host': host,
            'X-Amz-Date': amz_date,
            'Authorization': authorization_header
        }
        
        # Make request
        request_url = f"{endpoint}?{canonical_querystring}"
        print("\nSending test request with calculated signature...")
        response = requests.get(request_url, headers=headers)
        
        if response.status_code == 200:
            print("✓ SigV4 signature test successful!")
            return True
        else:
            print(f"❌ SigV4 signature test failed: {response.status_code} {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error testing SigV4 signature: {str(e)}")
        return False

def main():
    clear_screen()
    print("=== AWS Credentials Troubleshooter ===\n")
    
    # Check time synchronization
    print("\n=== Checking System Time ===")
    time_ok = check_time_sync()
    
    # Check credentials file
    print("\n=== Checking AWS Credentials File ===")
    profile = check_credentials_file()
    
    # Test AWS CLI
    if profile:
        test_aws_cli(profile)
        
    # Test SigV4 signing
    if profile:
        test_sigv4_signing(profile)
    
    # Additional suggestions
    print("\n=== AWS Authentication Information ===")
    print("AWS uses Signature Version 4 (SigV4) for API request authentication.")
    print("This algorithm uses:")
    print("1. Your AWS access key ID")
    print("2. Your AWS secret access key")
    print("3. The current time (must be within 15 minutes of AWS servers)")
    print("4. A canonical request format that includes headers and request parameters")
    
    print("\n=== Common Causes of SignatureDoesNotMatch Errors ===")
    print("1. Incorrect or corrupted secret key (most common)")
    print("2. System clock not synchronized with AWS servers")
    print("3. Using the wrong region for the request")
    print("4. Special characters in credentials not properly escaped")
    print("5. Using different signature versions (AWS4-HMAC-SHA256 is current standard)")
    
    print("\n=== Additional Suggestions ===")
    print("1. Try setting credentials via environment variables:")
    print("   export AWS_ACCESS_KEY_ID=your_access_key")
    print("   export AWS_SECRET_ACCESS_KEY=your_secret_key")
    print("   export AWS_DEFAULT_REGION=us-east-1")
    
    print("\n2. Try using credentials via boto3 directly:")
    print("   python -c \"import boto3; sts = boto3.client('sts'); print(sts.get_caller_identity())\"")
    
    print("\n3. Check if your AWS account or IAM user has restrictions (IP-based or MFA required)")
    
    print("\n4. Verify that your credentials haven't been rotated in the AWS console")
    
    print("\n5. Regenerate your access keys in the AWS Management Console")

if __name__ == "__main__":
    main()