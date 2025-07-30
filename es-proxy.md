
docker run --rm \
  --network=host \
  -e AWS_REGION=us-east-1 \
  abutaha/aws-es-proxy:v1.0 \
  -endpoint https://vpc-gds-neptune-odenxngk2ay2pojccmjpl6766e.us-east-1.es.amazonaws.com  \
  -listen 0.0.0.0:9200

# Run the proxy in a container
  docker run --rm \
  -p 9200:9200 \
  abutaha/aws-es-proxy:v1.0 \
  -endpoint https://vpc-gds-neptune-odenxngk2ay2pojccmjpl6766e.us-east-1.es.amazonaws.com \
  -listen 0.0.0.0:9200

# Run the proxy as executable
./aws-es-proxy \
  -endpoint https://vpc-gds-neptune-odenxngk2ay2pojccmjpl6766e.us-east-1.es.amazonaws.com \
  -listen 127.0.0.1:9200 \
  -verbose

ps aux | grep aws-es-proxy

aws sts get-caller-identity

## Get the IAM role for the instance
aws ec2 describe-instances \
  --instance-id i-0ead29d888b430b9a \
  --query "Reservations[*].Instances[*].IamInstanceProfile.Arn" \
  --output text

  # Get the managed policies attached to the role
  aws iam list-attached-role-policies \
  --role-name echasin-ec2-role

  aws iam list-attached-role-policies \
  --role-name opensearch-al2-fullaccess-role


# Get the policies attached to the role
  aws iam list-role-policies \
  --role-name echasin-ec2-role

  aws iam list-role-policies \
  --role-name opensearch-al2-fullaccess-role



  ##  Get IAM Role Metadata from EC2 (IMDSv2)
  TOKEN=$(curl -X PUT "http://169.254.169.254/latest/api/token" \
  -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")


  curl -H "X-aws-ec2-metadata-token: $TOKEN" \
  http://169.254.169.254/latest/meta-data/iam/info



✅ What You Should Use Going Forward
Always include the token when accessing metadata. Here's a reusable snippet:

bash
Copy
Edit
TOKEN=$(curl -sX PUT "http://169.254.169.254/latest/api/token" \
  -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")

curl -sH "X-aws-ec2-metadata-token: $TOKEN" \
  http://169.254.169.254/latest/meta-data/iam/info
🧠 Bonus: Access IAM credentials from EC2
bash
Copy
Edit
ROLE=$(curl -sH "X-aws-ec2-metadata-token: $TOKEN" \
  http://169.254.169.254/latest/meta-data/iam/security-credentials/)

curl -sH "X-aws-ec2-metadata-token: $TOKEN" \
  http://169.254.169.254/latest/meta-data/iam/security-credentials/$ROLE
You’ll get access key, secret key, and session token used for aws-es-proxy.





# Opensearch Domain
'''
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::244081531951:role/opensearch-al2-fullaccess-role"
      },
      "Action": "es:*",
      "Resource": "arn:aws:es:us-east-1:244081531951:domain/gds-neptune/*"
    }
  ]
}
'''

aws opensearch describe-domain \
  --domain-name gds-neptune \
  --query "DomainStatus.AccessPolicies"

## grants full OpenSearch access (es:*) to all resources, which is sufficient in most cases — but OpenSearch still enforces domain-level access.

 curl -v -X GET "http://localhost:9200/_cluster/health"

 curl -v -X GET "http://localhost:9200/_cat/indices"


 curl -v -X GET https://vpc-gds-neptune-odenxngk2ay2pojccmjpl6766e.us-east-1.es.amazonaws.com/_cat/indices

 cat > access-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::244081531951:role/echasin-ec2-role"
      },
      "Action": "es:*",
      "Resource": "arn:aws:es:us-east-1:244081531951:domain/gds-neptune/*"
    }
  ]
}
EOF

cat access-policy.json

aws opensearch update-domain-config \
  --domain-name gds-neptune \
  --access-policies file://access-policy.json


aws opensearch update-domain-config \
  --domain-name gds-neptune \
  --access-policies "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Principal\":{\"AWS\":\"arn:aws:iam::244081531951:role/echasin-ec2-role\"},\"Action\":\"es:*\",\"Resource\":\"arn:aws:es:us-east-1:244081531951:domain/gds-neptune/*\"}]}"


COLLECTION DEBUGGING

aws opensearchserverless batch-get-collection --names gds-neptune-aoss-test --region us-east-1