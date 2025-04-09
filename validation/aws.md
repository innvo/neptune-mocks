## AWSValidations

## Account Info

### Account ID

```
aws sts get-caller-identity 
```

### Detailed Account Information

aws organizations describe-account --account-id YOUR\_ACCOUNT\_ID

## S3

### List all S3 buckets 

```
aws s3 ls
```

### Access to a specifc bucket 

```
aws s3api get-bucket-acl --bucket deam-neptune
```

### Check bucket policy

```
ws s3api get-bucket-policy --bucket deam-neptune
```