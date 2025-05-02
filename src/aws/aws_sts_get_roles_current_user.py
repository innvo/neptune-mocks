import boto3
import os

# Clear terminal
os.system('cls' if os.name == 'nt' else 'clear')

try:
    # Create a basic session with explicit profile
    session = boto3.Session(profile_name='default')
    sts = session.client('sts')
    iam = session.client('iam')
    
    # Get current user identity
    response = sts.get_caller_identity()
    user_arn = response['Arn']
    
    # Extract username from ARN
    username = user_arn.split('/')[-1]
    
    # Get roles for the user
    roles = iam.list_attached_user_policies(UserName=username)
    
    # Print the results
    print("Authentication successful!")
    print(f"User ARN: {user_arn}")
    print(f"Account: {response['Account']}")
    print("\nAttached Roles/Policies:")
    for policy in roles['AttachedPolicies']:
        print(f"- {policy['PolicyName']} (ARN: {policy['PolicyArn']})")
        
except Exception as e:
    print(f"Error: {e}")