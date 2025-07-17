#!/bin/bash

# Script to run S3 file discovery for Neptune bulk loading
# This script helps you see what files would be processed

echo "🔍 Neptune S3 File Discovery Tool"
echo "=================================="

# Default values
S3_BUCKET="deam-neptune"
REGION="us-east-1"
EXTENSIONS=".csv"

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -b, --bucket BUCKET     S3 bucket name (default: deam-neptune)"
    echo "  -r, --region REGION     AWS region (default: us-east-1)"
    echo "  -e, --extensions EXT    File extensions to search (default: .csv)"
    echo "  -q, --quiet             Quiet mode (summary only)"
    echo "  -o, --output FILE       Export results to JSON file"
    echo "  -h, --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                    # List all CSV files in default bucket"
    echo "  $0 -b my-bucket                       # List CSV files in my-bucket"
    echo "  $0 -e .csv .json                      # List CSV and JSON files"
    echo "  $0 -q -o results.json                 # Quiet mode with JSON export"
    echo "  $0 -b my-bucket -r us-west-2          # Custom bucket and region"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -b|--bucket)
            S3_BUCKET="$2"
            shift 2
            ;;
        -r|--region)
            REGION="$2"
            shift 2
            ;;
        -e|--extensions)
            EXTENSIONS="$2"
            shift 2
            ;;
        -q|--quiet)
            QUIET="--quiet"
            shift
            ;;
        -o|--output)
            OUTPUT="--export $2"
            shift 2
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Check if Python script exists
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/list_s3_files_for_processing.py"

if [[ ! -f "$PYTHON_SCRIPT" ]]; then
    echo "❌ Error: Python script not found at $PYTHON_SCRIPT"
    exit 1
fi

# Check if boto3 is installed
if ! python3 -c "import boto3" 2>/dev/null; then
    echo "❌ Error: boto3 is not installed. Please install it with:"
    echo "   pip install boto3"
    exit 1
fi

echo "📁 S3 Bucket: $S3_BUCKET"
echo "🌍 Region: $REGION"
echo "📄 Extensions: $EXTENSIONS"
echo ""

# Build the command
CMD="python3 $PYTHON_SCRIPT --s3-bucket $S3_BUCKET --region $REGION --extensions $EXTENSIONS"

if [[ -n "$QUIET" ]]; then
    CMD="$CMD $QUIET"
fi

if [[ -n "$OUTPUT" ]]; then
    CMD="$CMD $OUTPUT"
fi

echo "🚀 Running: $CMD"
echo ""

# Execute the command
eval $CMD

echo ""
echo "✅ File discovery complete!" 