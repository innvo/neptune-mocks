1. Stream Enabled: Check if Neptune streams are enabled on the cluster.
2.  Check Your Stream Poller (Lambda or EC2) (FAILED)
    - If you're using a Lambda function or EC2 instance to poll the stream and forward to OpenSearch:
        - Check CloudWatch Logs for errors in polling or pushing to OpenSearch. 
        - Validate that the function is pulling changes using GetStreamRecords.