## Create SSH Tunnel

```
ssh -i neptune-bastion-dev.pem -L 8182:neptune-dev-instance-1.cz7fmvtxsrei.us-east-1.neptune.amazonaws.com:8182 ec2-user@35.170.107.253


ssh -v -i neptune-bastion-dev.pem -L 8182:neptune-dev.cluster-cz7fmvtxsrei.us-east-1.neptune.amazonaws.com:8182 ec2-user@35.170.107.253

```
### Check Neptune Status
Not seeing endpoint

```
curl -X GET http://localhost:8182/status
```