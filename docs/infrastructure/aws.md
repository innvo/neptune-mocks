## Prerequistes

1.  AWS CLI for command-line operations
2.  boto3 for Python AWS SDK

### Create AWS config

```
aws configure
```

### This will prompt you for:

*   AWS Access Key ID
*   AWS Secret Access Key
*   Default region name (e.g., us-east-1)
*   Default output format (json)

Or you can manually edit the credentials file:

```
nano ~/.aws/credentials
```

```
aws_access_key_id = XXXXX
aws_secret_access_key = XXXXX
```