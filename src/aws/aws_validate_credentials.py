#!/usr/bin/env python3
import boto3
import json
import sys

def validate_credentials(profile=None):
    """Validate AWS credentials and print user information"""
    try:
        # Create session with specific profile if provided
        if profile:
            session = boto3.Session(profile_name=profile)
        else:
            session = boto3.Session()
        
        # Get caller identity
        sts = session.client('sts')
        identity = sts.get_caller_identity()
        
        # Get more info about the user
        iam = session.client('iam')
        user_name = identity['Arn'].split('/')[-1]
        
        try:
            user_info = iam.get_user(UserName=user_name)
            user_detail = user_info['User']
        except Exception as e:
            user_detail = {"Error": str(e)}
        
        # Print results
        print("\n=== AWS Credentials Validation ===")
        print(f"Status: VALID")
        print(f"Account ID: {identity['Account']}")
        print(f"User ARN: {identity['Arn']}")
        print(f"User ID: {identity['UserId']}")
        
        if 'Error' not in user_detail:
            print("\n=== User Details ===")
            print(f"User Name: {user_detail.get('UserName', 'N/A')}")
            print(f"Created: {user_detail.get('CreateDate', 'N/A')}")
            print(f"Last Used: {user_detail.get('PasswordLastUsed', 'N/A')}")
        
        return True
    except Exception as e:
        print("\n=== AWS Credentials Validation ===")
        print(f"Status: INVALID")
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    profile = None
    if len(sys.argv) > 1:
        profile = sys.argv[1]
        print(f"Validating profile: {profile}")
    else:
        print("Validating default credentials")
    
    validate_credentials(profile)