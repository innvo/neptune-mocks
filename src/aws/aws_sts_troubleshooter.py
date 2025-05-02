import boto3

try:
    # Create a basic STS client with explicit profile
    session = boto3.Session(profile_name='default')
    sts = session.client('sts')
    
    # Make a simple call
    response = sts.get_caller_identity()
    
    # Print the results
    print("Authentication successful!")
    print(f"User ARN: {response['Arn']}")
    print(f"Account: {response['Account']}")
except Exception as e:
    print(f"Error: {e}")