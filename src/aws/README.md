# Cluster Helath Check
Error checking cluster health: 403
{"error":{"root_cause":[{"type":"security_exception","reason":"no permissions for [cluster:monitor/health] and User [name=arn:aws:iam::244081531951:user/echasin, backend_roles=[], requestedTenant=null]"}],"type":"security_exception","reason":"no permissions for [cluster:monitor/health] and User [name=arn:aws:iam::244081531951:user/echasin, backend_roles=[], requestedTenant=null]"},"status":403}

Based on the error message, you need the cluster:monitor/health permission to check the OpenSearch cluster health. This is a specific OpenSearch permission that needs to be added to your IAM user or role.
You'll need to add the following policy to your IAM user or role:

{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "es:ESHttpGet"
            ],
            "Resource": "arn:aws:es:us-east-1:244081531951:domain/sts-deam-es-3z4qexncsuhwmwt2tdyc7cfjyq/*"
        }
    ]
}