# Use default role ARN (hardcoded)
python src/generate/opensearch/load_csv_opensearch.py --test --root-only

# Use default role ARN (hardcoded)
python src/generate/opensearch/load_csv_opensearch.py  --root-only

# Override with a different role ARN
python src/generate/opensearch/load_csv_opensearch.py --role-arn "arn:aws:iam::123456789012:role/other-role" --test

# Check permissions with the new role
python src/generate/opensearch/load_csv_opensearch.py --check-permissions