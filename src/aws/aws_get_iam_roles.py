import boto3

def get_iam_roles():
    # Create an IAM client using the configured AWS credentials
    iam_client = boto3.client('iam')

    # Get the current user identity
    user = iam_client.get_user()
    print(f"Authenticated as IAM user: {user['User']['UserName']}")

    # List roles (this lists *all* IAM roles in the account, not just ones attached to user)
    roles = iam_client.list_roles()
    print("\nAvailable IAM Roles:")
    for role in roles['Roles']:
        print(f"- {role['RoleName']}")

if __name__ == "__main__":
    get_iam_roles()