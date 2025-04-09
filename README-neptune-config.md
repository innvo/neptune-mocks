



# Connectiing to Neptune using Bastion Host
A bastion host acts as a secure entry point to your private network, allowing you to access resources like an Amazon Neptune cluster that does not have a public endpoint. Below are the step-by-step instructions to create and configure a bastion host for accessing your Neptune cluster.

# Create an EC Instance as Bastion Host
## Step 1: Create an EC2 Instance as the Bastion Host
1. Log in to the AWS Management Console.

2. Navigate to EC2 > Instances > Launch Instances.

3. Configure the EC2 instance:

- AMI: Choose an Amazon Linux 2 or Ubuntu AMI.
- Instance Type: Select a small instance type like t2.micro for testing purposes.
- Key Pair: Create or select a key pair for SSH access. "neptune-bastion.pem"
- Network Settings:
    - Select the same VPC as your Neptune cluster.
    - Place the instance in a public subnet.
    - Enable Auto-assign Public IP.
- Configure Security Group for the Bastion Host:
    - Add an inbound rule to allow SSH (TCP 22) from your IP address only (x.x.x.x/32).
    - Add an outbound rule to allow all traffic.
    - Launch the Instance.

## Step 2:  Configure Network Access
1. Modify Neptune Security Group:
    - Go to EC2 > Security Groups.
    - Find the security group attached to your Neptune cluster.
    - Add an inbound rule to allow traffic on port 8182 (Neptune) from the private IP address of the bastion host.
2. Route Neptune Traffic via Private Subnet:
    - Ensure the private subnet containing the Neptune cluster is properly configured to allow traffic from the bastion host.

## Step 3: 
- Set Correct Permissions on the Key File
```
chmod 400 /path/to/neptune-bastion.pem
```

## Step 4: SSH Forwarding for Local Access
```
ssh -i /path/to/keypair.pem -L 8182:<neptune-endpoint>:8182 ec2-user@<Bastion_Public_IP>
```

## Step 5: Testing Tunnel
```
chmod 400 /Users/ericchasin/Downloads/neptune-bastion.pem
```
```
ssh -i /Users/ericchasin/Downloads/neptune-bastion.pem ec2-user@54.242.250.198
```
```
INNVO ACCOUNT
ssh -i /Users/ericchasin/Downloads/neptune-bastion.pem -L 8182:db-neptune-dev.cluster-cr7ro0ecjzwg.us-east-1.neptune.amazonaws.com:8182 ec2-user@54.242.250.198

ssh -i /Users/ericchasin/Downloads/neptune-bastion.pem -L 8182:db-neptune-test-serverless.cluster-cr7ro0ecjzwg.us-east-1.neptune.amazonaws.com:8182 ec2-user@54.242.250.198

STS ACCOUNT
ssh -i /Users/ericchasin/Downloads/sts-echasin.pem -L 8182:db-neptune-serverless-standard-dev.cluster-cz7fmvtxsrei.us-east-1.neptune.amazonaws.com:8182 ec2-user@54.236.164.72

ssh -i /Users/ericchasin/Downloads/sts-echasin.pem -L 8182:db-neptune-dev.cluster-cz7fmvtxsrei.us-east-1.neptune.amazonaws.com:8182 ec2-user@18.207.177.7

ssh -i /Users/ericchasin/Downloads/sts-echasin.pem -L 8182:db-neptune-dev.cluster-cz7fmvtxsrei.us-east-1.neptune.amazonaws.com:8182 ec2-user@18.207.177.7

ssh -i /Users/ericchasin/Downloads/sts-echasin.pem -L 8182:db-neptune-dev-instance-1.cz7fmvtxsrei.us-east-1.neptune.amazonaws.com:8182 Ec2-user@18.207.177.7

```
 ```
curl -X POST \
-H "Content-Type: application/json" \
-d '{"query": "MATCH (n) RETURN n LIMIT 5"}' \
http://localhost:8182/openCypher
```
```
curl -k -X GET https://localhost:8182/status

curl -k -X GET https://db-neptune-test-serverless.cluster-cr7ro0ecjzwg.us-east-1.neptune.amazonaws.com:8182/status
```