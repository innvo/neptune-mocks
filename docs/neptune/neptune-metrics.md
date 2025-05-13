aws cloudwatch get-metric-statistics \
  --namespace "AWS/Neptune" \
  --metric-name "DBCapacityUnits" \
  --dimensions Name=DBClusterIdentifier,Value=neptune-dev \
  --start-time $(date -u -d '-5 minutes' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 60 \
  --statistics Average \
  --region us-east-1
