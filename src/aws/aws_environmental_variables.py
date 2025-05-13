import os

aws_access_key = os.environ.get('AWS_ACCESS_KEY_ID')
aws_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
aws_session_token = os.environ.get('AWS_SESSION_TOKEN')  # optional, used for temporary credentials

print("AWS_ACCESS_KEY_ID:", aws_access_key)
print("AWS_SECRET_ACCESS_KEY:", "(set)" if aws_secret_key else None)
print("AWS_SESSION_TOKEN:", "(set)" if aws_session_token else None)
