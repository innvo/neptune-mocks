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
    
    # Get inline policies
    inline_policies = iam.list_user_policies(UserName=username)
    
    # Get managed policies
    managed_policies = iam.list_attached_user_policies(UserName=username)
    
    # Print the results
    print("Authentication successful!")
    print(f"User ARN: {user_arn}")
    print(f"Account: {response['Account']}")
    
    print("\nInline Policies:")
    for policy in inline_policies['PolicyNames']:
        print(f"- {policy}")
    
    print("\nManaged Policies:")
    for policy in managed_policies['AttachedPolicies']:
        print(f"- {policy['PolicyName']} (ARN: {policy['PolicyArn']})")
        
except Exception as e:
    print(f"Error: {e}")