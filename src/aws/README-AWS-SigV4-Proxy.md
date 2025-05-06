# Opensearch Config

## SignatureAWS SigV4 Proxy
```
https://github.com/awslabs/aws-sigv4-proxy
```

## Managed Domain

*   endpoint: https://search-sts-deam-es-iam-s5lekmvl3ssmabtrxj74t5aa2i.us-east-1.es.amazonaws.com
*   access: public\
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
-p 9200:9200 abutaha/aws-es-proxy \
-endpoint https://search-sts-deam-es-iam-s5lekmvl3ssmabtrxj74t5aa2i.us-east-1.es.amazonaws.com  \
-listen 0.0.0.0:9200 \
-verbose \
-debug
```

### Test Proxy  
```  
curl "http://localhost:9200/_cluster/health?pretty"
```

## Serverless

*   endpoint: https://utrkg13gnjqpmyz93250.us-east-1.aoss.amazonaws.com
*   access: public
*   Fine -grained access control
    *   Set IAM ARN as master user:  arn:aws:iam::244081531951:user/echasin
*   security config:
    *   domain level access policy

### Data access policy
- Access policy name: sts-deam-opensearch-serverless
```
[
  {
    "Rules": [
      {
        "Resource": [
          "collection/sts-deam-es-serverless"
        ],
        "Permission": [
          "aoss:*",
          "aoss:CreateCollectionItems",
          "aoss:DeleteCollectionItems",
          "aoss:UpdateCollectionItems",
          "aoss:DescribeCollectionItems"
        ],
        "ResourceType": "collection"
      },
      {
        "Resource": [
          "index/sts-deam-es-serverless/*"
        ],
        "Permission": [
          "aoss:*",
          "aoss:CreateIndex",
          "aoss:DeleteIndex",
          "aoss:UpdateIndex",
          "aoss:DescribeIndex",
          "aoss:ReadDocument",
          "aoss:WriteDocument"
        ],
        "ResourceType": "index"
      }
    ],
    "Principal": [
      "arn:aws:iam::244081531951:user/echasin"
    ],
    "Description": "Grant Access to echasin"
  }
]
```

### Start Proxy for Serverless

```
docker run --rm -ti \
-v ~/.aws:/root/.aws -e AWS_SDK_LOAD_CONFIG=true \
-e AWS_PROFILE=default \
-e AWS_REGION=us-east-1 \
-p 9200:9200 abutaha/aws-es-proxy \
-endpoint https://utrkg13gnjqpmyz93250.us-east-1.aoss.amazonaws.com  \
-listen 0.0.0.0:9200 \
-verbose \
-debug
```

### Test Proxy  
```  
curl -XGET "http://localhost:9200/_search?pretty"
```