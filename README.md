## Create SSH Tunnel

```
ssh  -L 8182:neptune-dev.cluster-cz7fmvtxsrei.us-east-1.neptune.amazonaws.com:8182 -i neptune-bastion-dev.pem ec2-user@35.170.107.253

```
### Check Neptune Status
Not seeing endpoint

```
curl -k -X GET http://localhost:8182/status
```