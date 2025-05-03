# Opensearch Config

## SignatureAWS SigV4 Proxy
```
https://github.com/awslabs/aws-sigv4-proxy
```

## Managed Domain

*   endpoint: https://search-sts-deam-es-iam-s5lekmvl3ssmabtrxj74t5aa2i.us-east-1.es.amazonaws.com
*   access: public\]
*   Fine -grained access control
    *   ,Set IAM ARN as master user:  arn:aws:iam::244081531951:user/echasin
*   security config:
    *   domain level access policy

```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "*"
      },
      "Action": "es:*",
      "Resource": [
        "arn:aws:es:us-east-1:244081531951:domain/sts-deam-es-iam/*",
      ]
    }
  ]
}
```

### Start Proxy for Managed Domain

```
docker run --rm -ti \
-v ~/.aws:/root/.aws -e AWS_SDK_LOAD_CONFIG=true \
-e AWS_PROFILE=default \
-e AWS_REGION=us-east-1 \
-p 8080:8080 abutaha/aws-es-proxy \
-endpoint https://search-sts-deam-es-iam-s5lekmvl3ssmabtrxj74t5aa2i.us-east-1.es.amazonaws.com  \
-listen 0.0.0.0:8080 \
-verbose \
-debug
```

### Test Proxy  
```  
curl "http://localhost:8080/_cluster/health?pretty"
```

## Serverless
