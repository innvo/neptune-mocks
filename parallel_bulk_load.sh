#!/bin/bash

# Parallel Neptune Bulk Load - Individual Jobs for Each File
# This script creates separate bulk load jobs for each file so they run in parallel

# Configuration
NEPTUNE_ENDPOINT="localhost:8182"
S3_BUCKET="deam-neptune"
IAM_ROLE_ARN="arn:aws:iam::244081531951:role/NeptuneLoadFromS3"
AWS_REGION="us-east-1"

# Maximum performance settings
PARALLELISM="OVERSUBSCRIBE"
FAIL_ON_ERROR="FALSE"
QUEUE_REQUEST="TRUE"

echo "Starting parallel Neptune bulk loads for individual files in S3 bucket: $S3_BUCKET"
echo "Endpoint: $NEPTUNE_ENDPOINT"
echo "Parallelism: $PARALLELISM (Maximum Performance)"
echo "=" * 80

# Function to start a bulk load for a specific file
start_file_bulk_load() {
    local s3_path=$1
    local format_type=${2:-"csv"}
    
    echo "Starting bulk load for: s3://$S3_BUCKET/$s3_path"
    
    response=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -k \
        "https://$NEPTUNE_ENDPOINT/loader" \
        -d "{
            \"source\": \"s3://$S3_BUCKET/$s3_path\",
            \"format\": \"$format_type\",
            \"iamRoleArn\": \"$IAM_ROLE_ARN\",
            \"region\": \"$AWS_REGION\",
            \"failOnError\": \"$FAIL_ON_ERROR\",
            \"parallelism\": \"$PARALLELISM\",
            \"queueRequest\": \"$QUEUE_REQUEST\"
        }")
    
    # Extract load ID from response
    load_id=$(echo "$response" | grep -o '"loadId":"[^"]*"' | cut -d'"' -f4)
    
    if [ ! -z "$load_id" ]; then
        echo "✓ Bulk load started for $s3_path"
        echo "  Load ID: $load_id"
    else
        echo "✗ Failed to start bulk load for $s3_path"
        echo "  Response: $response"
    fi
    
    echo "-" * 50
}

# List of files to load (modify this list based on your actual S3 bucket contents)
FILES_TO_LOAD=(
    # Node files
    "nodes/person_nodes.csv"
    "nodes/address_nodes.csv"
    "nodes/organization_nodes.csv"
    "nodes/form_nodes.csv"
    "nodes/receipt_nodes.csv"
    "nodes/building_nodes.csv"
    "nodes/email_nodes.csv"
    "nodes/phone_nodes.csv"
    
    # Edge files
    "edges/person_address_edges.csv"
    "edges/person_organization_edges.csv"
    "edges/person_form_edges.csv"
    "edges/person_receipt_edges.csv"
    "edges/person_email_edges.csv"
    "edges/person_phone_edges.csv"
    "edges/organization_address_edges.csv"
    "edges/building_address_edges.csv"
    
    # Alternative file patterns (uncomment if you have these)
    # "data/person.csv"
    # "data/address.csv"
    # "data/edges.csv"
    # "output/person_nodes.csv"
    # "output/address_nodes.csv"
    # "output/person_address_edges.csv"
)

# Start bulk loads for each file individually
echo "Starting ${#FILES_TO_LOAD[@]} individual bulk load jobs..."
echo ""

job_count=0
for file_path in "${FILES_TO_LOAD[@]}"; do
    start_file_bulk_load "$file_path"
    job_count=$((job_count + 1))
    
    # Small delay between requests to avoid overwhelming the endpoint
    sleep 1
done

echo ""
echo "All $job_count bulk load jobs have been submitted!"
echo ""
echo "To monitor all jobs:"
echo "curl -k https://$NEPTUNE_ENDPOINT/loader"
echo ""
echo "To check a specific job status:"
echo "curl -k https://$NEPTUNE_ENDPOINT/loader/{load_id}"
echo ""
echo "To cancel a specific job:"
echo "curl -X DELETE -k https://$NEPTUNE_ENDPOINT/loader/{load_id}"
echo ""
echo "Each file now has its own parallel job running!" 