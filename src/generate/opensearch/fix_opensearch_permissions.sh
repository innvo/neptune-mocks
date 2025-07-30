#!/bin/bash

# Fix OpenSearch Serverless Permissions Script
# This script helps configure data access policies for OpenSearch Serverless

echo "🔧 OpenSearch Serverless Permissions Fix"
echo "========================================"

# Get collection name
echo "📋 Available collections:"
aws opensearchserverless list-collections --output table

echo ""
echo "Please enter your collection name:"
read COLLECTION_NAME

if [ -z "$COLLECTION_NAME" ]; then
    echo "❌ No collection name provided. Exiting."
    exit 1
fi

echo ""
echo "🔐 Creating data access policy for collection: $COLLECTION_NAME"

# Create the access policy
aws opensearchserverless create-access-policy \
  --name "opensearch-loader-policy" \
  --type "data" \
  --policy "[
    {
      \"Rules\": [
        {
          \"Resource\": [\"collection/$COLLECTION_NAME\"],
          \"Permission\": [\"aoss:*\"],
          \"ResourceType\": \"collection\"
        }
      ],
      \"Principal\": [\"arn:aws:iam::244081531951:role/sts-deam-opensearch-fullaccess\"]
    }
  ]"

if [ $? -eq 0 ]; then
    echo "✅ Data access policy created successfully!"
    echo ""
    echo "🧪 Testing permissions..."
    python src/generate/opensearch/load_csv_opensearch.py --check-permissions
else
    echo "❌ Failed to create data access policy"
    echo "You may need to create it manually in the AWS Console"
fi 