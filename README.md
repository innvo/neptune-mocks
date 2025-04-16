# Infrastructure
## Create SSH Tunnel

```
ssh  -L 8182:neptune-dev.cluster-cz7fmvtxsrei.us-east-1.neptune.amazonaws.com:8182 -i neptune-bastion-dev.pem ec2-user@35.170.107.253

```
### Check Neptune Status
Not seeing endpoint

```
curl -k -X GET https://localhost:8182/status
```

# Pipeline
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



`
## Neptune Bulk Loader
### Opencypher
```
curl -k -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "source": "s3://deam-neptune/neptune_person_nodes_opencypher.csv",
    "format": "opencypher",
    "iamRoleArn": "arn:aws:iam::244081531951:role/NeptuneLoadFromS3",
    "region": "us-east-1",
    "failOnError": "TRUE",
    "parallelism": "MEDIUM",
    "updateSingleCardinalityProperties": "FALSE",
    "queueRequest": "TRUE"
  }' \
  https://localhost:8182/loader
```
### gremlin
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

## Count of nodes with label person
```
curl -k -X POST \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"query": "MATCH (n:person) RETURN count(n) as count"}' \
  https://localhost:8182/opencypher

curl -k -X POST \
  -H "Content-Type: application/json" \
  -d '{"gremlin":"g.V().hasLabel(\"person\").count()"}' \
  https://localhost:8182/gremlin
```

## Display nodes with label person
```
curl -k -X POST \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"query": "MATCH (n:person) RETURN n LIMIT 10"}' \
  https://localhost:8182/opencypher

curl -k -X POST \
  -H "Content-Type: application/json" \
  -d '{"gremlin":"g.V().hasLabel(\"person\").limit(10)"}' \
  https://localhost:8182/gremlin
```

## Count of all nodes
```
curl -k -X POST \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"query": "MATCH (n) RETURN count(n) as count"}' \
  https://localhost:8182/opencypher
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
        "token" : "fecb1d1f-27d6-234f-e77d-5465c7b04705"
      }'

#  Delete all nodes
```
curl -k -X POST \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"query": "MATCH (n) DETACH DELETE n"}' \
  https://localhost:8182/opencypher

curl -k -X POST \
  -H "Content-Type: application/json" \
  -d '{"gremlin":"g.V().drop()"}' \
  https://localhost:8182/gremlin
```