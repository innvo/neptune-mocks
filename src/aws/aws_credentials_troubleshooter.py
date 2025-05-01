#!/usr/bin/env python3
"""
AWS Credentials Troubleshooter
Helps diagnose and fix common AWS credential issues
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

def main():
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
    
    # Additional suggestions
    print("\n=== Additional Suggestions ===")
    print("1. Try setting credentials via environment variables:")
    print("   export AWS_ACCESS_KEY_ID=your_access_key")
    print("   export AWS_SECRET_ACCESS_KEY=your_secret_key")
    print("   export AWS_DEFAULT_REGION=us-east-1")
    
    print("\n2. Try using credentials via boto3 directly:")
    print("   python -c \"import boto3; sts = boto3.client('sts'); print(sts.get_caller_identity())\"")
    
    print("\n3. Check if your AWS account or IAM user has restrictions (IP-based or MFA required)")
    
    print("\n4. Verify that your credentials haven't been rotated in the AWS console")

if __name__ == "__main__":
    main()