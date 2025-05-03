# Prerquistes
1. Install python dependencies
```
pip install -r requirements.txt
```
2. Install mermaid dependencies
```

```

# Infrastructure
1. Accessing AWS Neptune requires a SSH Tunnel
2. AWS Neptune requires:
  - Database Cluster: neptune-dev.cluster-cz7fmvtxsrei.us-east-1.neptune.amazonaws.com
  - IAM role to all the cluster to access S3. arn:aws:iam::244081531951:role/NeptuneLoadFromS3
  - VPC Endpoint to allow Neptune to access S3
  - S3 Bucket to store Neptune data loading csv files

## Create SSH Tunnel
```
ssh  -L 8182:neptune-dev.cluster-cz7fmvtxsrei.us-east-1.neptune.amazonaws.com:8182 -i neptune-bastion-dev.pem ec2-user@35.170.107.253

ssh -L 5601:vpc-sts-deam-gds-dev-3wznyujg7kfe5kl7np7gdgoko4.us-east-1.es.amazonaws.com:443 \
    -i neptune-bastion-dev.pem ec2-user@35.170.107.253


```
### Check Neptune Status
```
curl -k -X GET https://localhost:8182/status
```

# Pipeline to generate fake Neptune data (04/15/2025 is only persons)
1. run src/generate/node/generate_node_data.py
 - This creates base nodes of varying types (address,email,onlineaccount,person,phone,receipt).  Variable to set the number of records. 
2. run src/generate/mock/generate_mock_person_data.py
  - This simuates a GDS person node. As of 4/5/2025 it only include limited set of node_properties.  
  - Reads src/data/input/node_data.csv
3. run src/generate/neptune/generate_neptune_person_gemlin_csv.py
  - This create AWS neptune gremlin load file
  - reads src/data/output/gds/mock_person_data.csv
4. run src/utils/load_data_output_neptune_to_s3-deam-neptune.py
  - uploades csv files to S3 bucket
5. Clean out vertices or fast rest neptune (optional)
6. run curl command to execute neptune bulkloader (gremlin)
```
curl -k -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "source": "s3://deam-neptune/neptune_person_nodes_gremlin.csv",
    "format": "csv",
    "iamRoleArn": "arn:aws:iam::244081531951:role/NeptuneLoadFromS3",
    "region": "us-east-1",
    "failOnError": "TRUE",
    "parallelism": "MEDIUM",
    "updateSingleCardinalityProperties": "FALSE",
    "queueRequest": "TRUE"
  }' \
  https://localhost:8182/loader
```
7. User opencypher or gremlin.pynb to check data load


# Validation
## Count of all nodes
### Opencphyer
```
curl -k -X POST \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"query": "MATCH (n) RETURN count(n) as count"}' \
  https://localhost:8182/opencypher
```
### Grelimn
```
curl -k -X POST \
     -H "Content-Type: application/json" \
     https://localhost:8182/gremlin \
     -d '{"gremlin": "g.V().fold().project(\"vertix_cnt\").by(count(local))"}' | jq
```

## Reset Neptune
curl -k -X POST \
  -H 'Content-Type: application/json' \
      https://localhost:8182/system \
  -d '{ "action" : "initiateDatabaseReset" }'

curl -k -X POST \
  -H 'Content-Type: application/json' \
      https://localhost:8182/system \
  -d '{
        "action" : "performDatabaseReset",
        "token" : "e8cb4a2f-fe10-212c-d74d-8ce4b29dc161"
      }'
