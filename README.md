## Create SSH Tunnel

```
ssh  -L 8182:neptune-dev.cluster-cz7fmvtxsrei.us-east-1.neptune.amazonaws.com:8182 -i neptune-bastion-dev.pem ec2-user@35.170.107.253

```
### Check Neptune Status
Not seeing endpoint

```
curl -k -X GET https://localhost:8182/status
```
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