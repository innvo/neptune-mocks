# Basic bulk load concurrency test
python neptune_bulk_load_test.py \
  your-cluster.cluster-xxx.us-east-1.neptune.amazonaws.com \
  us-east-1 \
  your-s3-bucket \
  arn:aws:iam::123456789012:role/NeptuneLoadFromS3Role

# Create sample data and run comprehensive test
python src/generate/gremlin/tests/neptune_bulk_load_concurrency_test.py \
  localhost \
  us-east-1 \
  deam-neptune \
  arn:aws:iam::244081531951:role/NeptuneLoadFromS3 \
  --create-sample-data \
  --monitor-completion \
  --max-concurrency 30 \
  --parallelism HIGH

# Test with more data files and higher concurrency
python neptune_bulk_load_test.py \
  your-cluster.cluster-xxx.us-east-1.neptune.amazonaws.com \
  us-east-1 \
  your-s3-bucket \
  arn:aws:iam::123456789012:role/NeptuneLoadFromS3Role \
  --data-files 20 \
  --records-per-file 5000 \
  --max-concurrency 50 \
  --step 10

  # Create sample data and run comprehensive test
python src/generate/gremlin/tests/neptune_bulk_load_concurrency_test.py \
  localhost \
  us-east-1 \
  deam-neptune \
  arn:aws:iam::244081531951:role/NeptuneLoadFromS3 
