# STS Infrastructure

<table><tbody><tr><td>Resource</td><td>Identifier</td><td>&nbsp;</td></tr><tr><td>Neptune Cluster</td><td>db-neptune-1</td><td>&nbsp;</td></tr><tr><td>S3 Bucket</td><td>deam-neptune</td><td>&nbsp;</td></tr><tr><td>IAM Role</td><td>NeptuneLoadFromS3<br>&nbsp;</td><td>&nbsp;</td></tr><tr><td>Assign Role to Cluster</td><td>&nbsp;</td><td>&nbsp;</td></tr></tbody></table>

## API Gateway to Acces Neptune

### Step 1: Ensure Prerequisites

1.  An active AWS Neptune cluster
2.  AWS CLI configured with appropriate permissions
3.  An IAM role that can access Neptune and be assumed by API Gateway/Lambda

### Step 2: Create a Lambda Function as Intermediary

API Gateway can't directly communicate with Neptune, so you'll need to use Lambda as an intermediary:

1.  Open the AWS Lambda console
2.  Click "Create function"
3.  Choose "Author from scratch"
4.  Enter a function name (e.g., "NeptuneAPIHandler")
5.  Select a runtime (Python or Node.js recommended)
6.  Choose or create an execution role with Neptune access. Create a new role with basic Lambda permissions
7.  Click "Create function"