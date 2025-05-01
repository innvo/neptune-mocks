# Overview

# Pre-Requistes

Existing Neptune Cluster (Source)

*   Streaming Enabled - Set in the Parameter Group
*   cluster endpoint: neptune-dev.cluster-cz7fmvtxsrei.us-east-1.neptune.amazonaws.com
*   streaming enpoint: https://neptune-dev-instance-1.cz7fmvtxsrei.us-east-1.neptune.amazonaws.com:8182/propertygraph/stream
*   parameter group: neptune-1-4-streaming-true-cluster
*   vpc: default-vpc-0580958871106d3e3
*   subnets: all sts-deam\* subnets
*   security group: sts-deam-neptune\*


Open Search Domain (Target)

1.  https://search-deam-gds-neptune-i6kvsohzrlv6xie2azrtp7c3iu.aos.us-east-1.on.aws
2.  vpc: default-vpc-0580958871106d3e3
3.  subnet: sts-deam-dev-private-us-east-1a
4.  security group: sts-deam-dev-db-sg
5.  IAM Role: sts-deam-opensearch-fullaccess
6.  1 AZ, General Purpsoe, t3.small.search, data nodes 1
7.  Version 2.19
8.  Access: public
9.  Fine-grained access control = Set IAM ARN as master user
    1.  arn:aws:iam::244081531951:role/sts-deam-opensearch-fullaccess
    2.  Require credentials (admin user/password or SigV4 signed requests).

# Testing
## Pre-Requistes
```
sudo yum install -y python3-pip
```

```
pip install aws-sigv4
```
```
which aws-sigv4
```

## Setting Up Proxy

./sigv4-proxy \
    --name es-proxy \
    --verbose \
    --region us-east-1 \
    --service es \
    --upstream https://vpc-sts-deam-gds-dev-3wznyujg7kfe5kl7np7gdgoko4.us-east-1.es.amazonaws.com 


## Testing with SigV4 from Bastion
```
aws es describe-elasticsearch-domain --domain-name sts-deam-gds-dev
```

## Testing with curl with Sigv4Signing
```
aws-sigv4 sign \
  --service es \
  --region us-east-1 \
  --host vpc-sts-deam-gds-dev-3wznyujg7kfe5kl7np7gdgoko4.us-east-1.es.amazonaws.com \
  --method GET \
  --url https://vpc-sts-deam-gds-dev-3wznyujg7kfe5kl7np7gdgoko4.us-east-1.es.amazonaws.com/_cluster/health \
  --canonical-uri "/_cluster/health" | \
curl -sS -H "Content-Type: application/json" -K -
```

./sigv4-proxy \
  --name es-proxy \
  --listen 127.0.0.1:8080 \
  --region us-east-1 \
  --service es \
  --upstream https://vpc-sts-deam-gds-dev-3wznyujg7kfe5kl7np7gdgoko4.us-east-1.es.amazonaws.com/_cluster/health


# Notes

You must sign all OpenSearch requests with your credentials (via AWS CLI or SDK).

nslookup vpc-sts-deam-gds-dev-3wznyujg7kfe5kl7np7gdgoko4.us-east-1.es.amazonaws.com

curl -k https://vpc-sts-deam-gds-dev-3wznyujg7kfe5kl7np7gdgoko4.us-east-1.es.amazonaws.com FAILS  
- added 443

dig vpc-sts-deam-gds-dev-3wznyujg7kfe5kl7np7gdgoko4.us-east-1.es.amazonaws.com


sg-089d0b1ae77cf4488 (open-to-world)


10.10.102.136

aws ec2 authorize-security-group-ingress \
    --group-id sg-opensearch-domain-id \
    --protocol tcp \
    --port 443 \
    --cidr 10.10.1.0/24

~/sigv4-proxy \
  --name es-health \
  --listen 127.0.0.1:8080 \
  --region us-east-1 \
  --service es \
  --upstream https://vpc-sts-deam-gds-dev-3wznyujg7kfe5kl7np7gdgoko4.us-east-1.es.amazonaws.com


./sigv4-proxy \
  --name es-health \
  --addr 127.0.0.1:8080 \
  --region us-east-1 \
  --service es \
  --upstream https://vpc-sts-deam-gds-dev-3wznyujg7kfe5kl7np7gdgoko4.us-east-1.es.amazonaws.com
