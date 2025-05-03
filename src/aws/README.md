# Opensearch Config

##  Signature Proxy


docker run --rm -ti \
  -e AWS_ACCESS_KEY_ID=AKIATRVDETQXTK3GPWX \
  -e AWS_SECRET_ACCESS_KEY=ysSfLSbJOORB5N4vt5+oGuzdXg93aXIpHC76h0i5R \
  -p 8080:8080 \
  aws-sigv4-proxy \
  --name aoss-proxy \
  --port :8080 \
  --host utrkg13gnjqpmyz93250.us-east-1.aoss.amazonaws.com \
  --region us-east-1
  --service es
  --verbose \
  --log-signing-process \
  --log-failed-requests


# 403 Forbidden

docker run --rm -ti \
  -e AWS_ACCESS_KEY_ID=AKIATRVDETQXTK3GPWX \
  -e AWS_SECRET_ACCESS_KEY=ysSfLSbJOORB5N4vt5+oGuzdXg93aXIpHC76h0i5R \
  -e AWS_PROFILE=default \
  -p 8080:8080 \
  aws-sigv4-proxy \
  --name aoss-proxy \
  --port :8080 \
  --host search-sts-deam-es-iam-s5lekmvl3ssmabtrxj74t5aa2i.us-east-1.es.amazonaws.com \
  --region us-east-1
  --service es
  --verbose \
  --log-signing-process \
  --log-failed-requests


THIS 

docker run --rm -ti \
-v ~/.aws:/root/.aws -e AWS_SDK_LOAD_CONFIG=true -e AWS_PROFILE=default -e AWS_REGION=us-east-1 -p 8080:8080 abutaha/aws-es-proxy -endpoint https://search-sts-deam-es-iam-s5lekmvl3ssmabtrxj74t5aa2i.us-east-1.es.amazonaws.com -listen 0.0.0.0:8080 -verbose -debug

END 

## Start Proxy for Managed Domain
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
``



docker run --rm -ti \
-e AWS_ACCESS_KEY_ID=AKIATRVDETQXTK3GPWX \
-e AWS_SECRET_ACCESS_KEY=ysSfLSbJOORB5N4vt5+oGuzdXg93aXIpHC76h0i5R \
-e AWS_PROFILE=default \
-p 8080:8080 \
abutaha/aws-es-proxy
--host search-sts-deam-es-iam-s5lekmvl3ssmabtrxj74t5aa2i.us-east-1.es.amazonaws.com \
--port :8080 \
--verbose \
--debug

docker run --rm -ti \
-e AWS_SDK_LOAD_CONFIG=true \
-e AWS_PROFILE=default \
-p 8080:8080 \
abutaha/aws-es-proxy \
-endpoint https://search-sts-deam-es-iam-s5lekmvl3ssmabtrxj74t5aa2i.us-east-1.es.amazonaws.com \
-listen 127.0.0.1:8080 \
-verbose \
-debug \
-service es


  -e AWS_SDK_LOAD_CONFIG=true \
  -e AWS_PROFILE=default \





docker run --rm -ti -v ~/.aws:/root/.aws -p 8080:8080 -e AWS_SDK_LOAD_CONFIG=true -e AWS_PROFILE=default aws-sigv4-proxy --name es --host search-sts-deam-es-iam-s5lekmvl3ssmabtrxj74t5aa2i.us-east-1.es.amazonaws.com --region us-east-1 --port :8080






## aws-es-proxy
1. Install go on Macos
```
brew install go
```
2. Install proxy locally
```
go install github.com/abutaha/aws-es-proxy@latest
```
3.  Make sure $GOPATH/bin is in your PATH.
```
export PATH="$PATH:$(go env GOPATH)/bin"
```
4.  Run Proxy Locally

 Managed Instance
```
AWS_PROFILE=default AWS_REGION=us-east-1 aws-es-proxy \
  -endpoint https://search-sts-deam-es-iam-s5lekmvl3ssmabtrxj74t5aa2i.us-east-1.es.amazonaws.com \
  -listen 127.0.0.1:9200
```


 Serverless
```
 AWS_REGION=us-east-1 aws-es-proxy \
  -endpoint https://utrkg13gnjqpmyz93250.us-east-1.aoss.amazonaws.com \
  -listen 127.0.0.1:9200

or

AWS_PROFILE=default AWS_REGION=us-east-1 aws-es-proxy \
  -endpoint https://utrkg13gnjqpmyz93250.us-east-1.aoss.amazonaws.com \
  -listen 127.0.0.1:9200
```
5. Test proxy
```
curl -s 'http://localhost:9200/_cat/indices?format=json'


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

Cluster Helath Check
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
                "es:*",
                "es:ESHttpGet",
                "es:ESHttpPut",
                "es:ESHttpPost",
                "es:ESHttpDelete",
                "es:ESHttpHead"
            ],
            "Resource": [
                "arn:aws:es:us-east-1:244081531951:domain/sts-deam-es-3z4qexncsuhwmwt2tdyc7cfjyq/*",
                "arn:aws:es:us-east-1:244081531951:domain/sts-deam-es-iam-s5lekmvl3ssmabtrxj74t5aa2i/*"
            ]
        }
    ]
}

This policy grants:
- Full access to all OpenSearch operations (es:*)
- Specific HTTP method permissions
- Access to both the IAM and non-IAM OpenSearch domains

docker run --rm -ti \
  -v ~/.aws:/root/.aws \
  -e AWS_SDK_LOAD_CONFIG=true \
  -e AWS_PROFILE=default \
  -e AWS_REGION=us-east-1 \
  -p 8080:8080 \
  abutaha/aws-es-proxy \
  -endpoint https://search-sts-deam-es-iam-s5lekmvl3ssmabtrxj74t5aa2i.us-east-1.es.amazonaws.com \
  -listen 0.0.0.0:8080 \
  -verbose \
  -debug

