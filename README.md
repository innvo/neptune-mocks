# STS Infrastructure

<table><tbody><tr><td>Resource</td><td>Identifier</td><td>Notes</td></tr><tr><td>Bastion Host</td><td>35.170.107.253</td><td>bastion-neptune.pem</td></tr><tr><td>Neptune Cluster</td><td>db-neptune-1</td><td>vpc-0b2d09a26d2da7fa8</td></tr><tr><td>S3 Bucket</td><td>deam-neptune</td><td>&nbsp;</td></tr><tr><td>IAM Role</td><td>NeptuneLoadFromS3<br>&nbsp;</td><td>&nbsp;</td></tr><tr><td>Assign Role to Cluster</td><td>&nbsp;</td><td>&nbsp;</td></tr></tbody></table>

## Jumpbox Access to Neptune

**Create ssh tunnel to jumpbox**

```

ssh -v -i /Users/ericchasin/keys/neptune-bastion-dev.pem ec2-user@35.170.107.25
```

```
ssh -v -i /Users/ericchasin/keys/neptune-bastion-dev.pem -L 8182:neptune-dev.cluster-cz7fmvtxsrei.us-east-1.neptune.amazonaws.com:8182 ec2-user@35.170.107.253
```