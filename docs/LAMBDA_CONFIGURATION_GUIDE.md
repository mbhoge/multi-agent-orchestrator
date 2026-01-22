# Lambda Configuration Guide for Multi-Agent Orchestrator

> **Deprecated:** The AWS Agent Core Lambda handlers have been removed. The system now runs an
> AgentCore-compatible HTTP server that exposes `/invocations` and `/ping` on port `8080`.
> Use `agentcore dev` or `python -m aws_agent_core.api` for local runs.

This guide is kept for historical reference only and no longer reflects the current runtime flow.

## Table of Contents

1. [Lambda Configuration Overview](#lambda-configuration-overview)
2. [Configuration Breakdown](#configuration-breakdown)
3. [AWS Console Configuration Steps](#aws-console-configuration-steps)
4. [IAM Role Setup](#iam-role-setup)
5. [Security Group Configuration](#security-group-configuration)
6. [Deployment Package Creation](#deployment-package-creation)
7. [Verification and Testing](#verification-and-testing)
8. [Common Issues and Solutions](#common-issues-and-solutions)
9. [Best Practices](#best-practices)

---

## Lambda Configuration Overview

The Lambda-based architecture uses AWS Lambda functions as the entry point from API Gateway. These Lambda functions then communicate with containerized ECS services via VPC and service discovery.

### Architecture Flow

```
API Gateway → Lambda Function → VPC → ECS Services (via Service Discovery)
```

### Key Lambda Functions

1. **query_handler** - Processes `/api/v1/query` requests
2. **teams_webhook_handler** - Processes `/api/teams/webhook` requests
3. **health_handler** - Health check endpoint
4. **metrics_handler** - Metrics endpoint

---

## Configuration Breakdown

### Complete Terraform Configuration Example

```hcl
resource "aws_lambda_function" "query_handler" {
  filename         = "lambda_deployments/query_handler.zip"
  function_name    = "${var.project_name}-query-handler"
  role            = aws_iam_role.lambda_role.arn
  handler         = "aws_agent_core.lambda_handlers.query_handler.lambda_handler"
  runtime         = "python3.11"
  timeout         = 300  # 5 minutes
  memory_size     = 512
  
  # VPC Configuration (to access ECS services)
  vpc_config {
    subnet_ids         = aws_subnet.private[*].id
    security_group_ids = [aws_security_group.lambda_sg.id]
  }
  
  environment {
    variables = {
      LANGGRAPH_ENDPOINT = "http://langgraph.multi-agent-orchestrator.local:8001"
      SNOWFLAKE_ENDPOINT = "http://snowflake-cortex.multi-agent-orchestrator.local:8002"
      AWS_REGION        = var.aws_region
    }
  }
}
```

### Configuration Parameters Explained

#### 1. Basic Function Configuration

| Parameter | Value | Description |
|-----------|-------|-------------|
| `filename` | `"lambda_deployments/query_handler.zip"` | Path to the deployment package (ZIP file) containing your code and dependencies |
| `function_name` | `"${var.project_name}-query-handler"` | Unique name for the Lambda function (e.g., `multi-agent-orchestrator-query-handler`) |
| `role` | `aws_iam_role.lambda_role.arn` | IAM execution role ARN that grants permissions to the function |
| `handler` | `"aws_agent_core.lambda_handlers.query_handler.lambda_handler"` | Entry point: `module.path.to.function_name` |
| `runtime` | `"python3.11"` | Python runtime version |
| `timeout` | `300` | Maximum execution time in seconds (max 900 = 15 minutes) |
| `memory_size` | `512` | Memory allocation in MB (128-10240, affects CPU proportionally) |

**Key Points:**
- **Handler Format**: `package.module.function_name`
  - Package: `aws_agent_core`
  - Module: `lambda_handlers.query_handler`
  - Function: `lambda_handler`
- **Timeout**: Set to 300 seconds (5 minutes) to allow for ECS service calls
- **Memory**: 512 MB provides balanced CPU and memory for HTTP calls

#### 2. VPC Configuration

```hcl
vpc_config {
  subnet_ids         = aws_subnet.private[*].id
  security_group_ids = [aws_security_group.lambda_sg.id]
}
```

**Purpose:**
- Allows Lambda to access private ECS services in the VPC
- Enables service discovery DNS resolution
- Provides secure network isolation

**Parameters:**
- `subnet_ids`: Private subnets where Lambda ENIs are created (minimum 2 for HA)
- `security_group_ids`: Security group controlling Lambda's network access

**Important Notes:**
- Lambda creates ENIs (Elastic Network Interfaces) in these subnets
- ENI creation adds ~10-15 seconds to cold starts
- Requires IAM permissions for ENI management
- Subnets must have available IP addresses

#### 3. Environment Variables

```hcl
environment {
  variables = {
    LANGGRAPH_ENDPOINT = "http://langgraph.multi-agent-orchestrator.local:8001"
    SNOWFLAKE_ENDPOINT = "http://snowflake-cortex.multi-agent-orchestrator.local:8002"
    AWS_REGION        = var.aws_region
  }
}
```

**Purpose:**
- Service discovery endpoints for ECS services
- AWS region for SDK configuration
- Configuration without code changes

**Service Discovery DNS:**
- Uses AWS Cloud Map private DNS namespaces
- Format: `service-name.namespace.local`
- Automatically resolves to ECS task IPs

---

## AWS Console Configuration Steps

### Step 1: Create the Lambda Function

1. **Navigate to Lambda Console**
   - Go to AWS Console → Services → Lambda
   - Click **"Create function"**

2. **Choose Authoring Option**
   - Select **"Author from scratch"**
   - (Do not use templates or container images)

3. **Basic Information**
   - **Function name**: `multi-agent-orchestrator-query-handler`
   - **Runtime**: `Python 3.11`
   - **Architecture**: `x86_64`
   - Click **"Create function"**

### Step 2: Upload Deployment Package

1. **Navigate to Code Tab**
   - In the function page, go to **"Code"** tab
   - Click **"Upload from"** dropdown
   - Select **".zip file"**

2. **Upload ZIP File**
   - Click **"Upload"** button
   - Select your `query_handler.zip` file
   - Click **"Save"**

**Note**: See [Deployment Package Creation](#deployment-package-creation) section for creating the ZIP file.

### Step 3: Configure Basic Settings

1. **Navigate to Configuration**
   - Click **"Configuration"** tab
   - Click **"General configuration"** → **"Edit"**

2. **Configure Settings**
   - **Description**: `Query handler for multi-agent orchestrator`
   - **Timeout**: `5 min 0 sec` (300 seconds)
   - **Memory**: `512 MB`
   - **Ephemeral storage**: `512 MB` (default)

3. **Save Changes**
   - Click **"Save"**

**Why These Settings:**
- **Timeout**: 5 minutes allows time for ECS service calls and processing
- **Memory**: 512 MB provides adequate CPU for HTTP operations
- **Ephemeral storage**: Default is sufficient for most use cases

### Step 4: Configure IAM Role

1. **Navigate to Permissions**
   - Click **"Configuration"** tab
   - Click **"Permissions"** → **"Edit"**

2. **Select Execution Role**
   - **Execution role**: Choose **"Use an existing role"**
   - **Existing role**: Select `multi-agent-orchestrator-lambda-role`
   - (If role doesn't exist, see [IAM Role Setup](#iam-role-setup) section)

3. **Save Changes**
   - Click **"Save"**

**Alternative**: Create new role from template
- Select **"Create a new role from AWS policy templates"**
- Role name: `multi-agent-orchestrator-lambda-role`
- Policy templates: Select `Basic Lambda@Edge permissions` (for basic execution)

### Step 5: Configure VPC Settings

1. **Navigate to VPC Configuration**
   - Click **"Configuration"** tab
   - Click **"VPC"** → **"Edit"**

2. **Configure VPC**
   - **VPC**: Select your VPC (e.g., `multi-agent-orchestrator-vpc`)
   - **Subnets**: Select **at least 2 private subnets** across different Availability Zones
     - Example: `private-subnet-1a`, `private-subnet-1b`
   - **Security groups**: Select `multi-agent-orchestrator-lambda-sg`
     - (If security group doesn't exist, see [Security Group Configuration](#security-group-configuration) section)

3. **Save Changes**
   - Click **"Save"**
   - **Note**: This will create ENIs (Elastic Network Interfaces) in the selected subnets

**Important:**
- Select subnets in **private subnets** (not public)
- Select **at least 2 subnets** in different AZs for high availability
- Ensure subnets have available IP addresses

### Step 6: Configure Environment Variables

1. **Navigate to Environment Variables**
   - Click **"Configuration"** tab
   - Click **"Environment variables"** → **"Edit"**

2. **Add Environment Variables**
   Click **"Add environment variable"** for each:
   
   - **Key**: `LANGGRAPH_ENDPOINT`
     **Value**: `http://langgraph.multi-agent-orchestrator.local:8001`
   
   - **Key**: `SNOWFLAKE_ENDPOINT`
     **Value**: `http://snowflake-cortex.multi-agent-orchestrator.local:8002`
   
   - **Key**: `AWS_REGION`
     **Value**: `us-east-1` (or your region)

3. **Save Changes**
   - Click **"Save"**

**Service Discovery DNS Format:**
- Format: `http://service-name.namespace.local:port`
- Namespace: `multi-agent-orchestrator.local` (from Cloud Map)
- Ports:
  - LangGraph: `8001`
  - Snowflake Cortex: `8002`
  - Langfuse: `3000` (if needed)

### Step 7: Configure Handler

1. **Navigate to Runtime Settings**
   - Click **"Code"** tab
   - Scroll to **"Runtime settings"** section
   - Click **"Edit"**

2. **Set Handler**
   - **Handler**: `aws_agent_core.lambda_handlers.query_handler.lambda_handler`
   - **Runtime**: `Python 3.11` (should already be set)

3. **Save Changes**
   - Click **"Save"**

**Handler Format:**
- Format: `package.module.function_name`
- Example: `aws_agent_core.lambda_handlers.query_handler.lambda_handler`
  - Package: `aws_agent_core`
  - Module: `lambda_handlers.query_handler`
  - Function: `lambda_handler`

---

## IAM Role Setup

### Step 1: Create Execution Role

1. **Navigate to IAM Console**
   - Go to AWS Console → Services → IAM
   - Click **"Roles"** → **"Create role"**

2. **Select Trusted Entity**
   - **Trusted entity type**: `AWS service`
   - **Use case**: `Lambda`
   - Click **"Next"**

3. **Attach Permissions**
   - Search and select:
     - `AWSLambdaBasicExecutionRole` (for CloudWatch Logs)
     - `AWSLambdaVPCAccessExecutionRole` (for VPC access)
   - Click **"Next"**

4. **Name and Create**
   - **Role name**: `multi-agent-orchestrator-lambda-role`
   - **Description**: `Execution role for multi-agent orchestrator Lambda functions`
   - Click **"Create role"**

### Step 2: Add Custom Permissions

1. **Open the Role**
   - Click on `multi-agent-orchestrator-lambda-role`
   - Click **"Add permissions"** → **"Create inline policy"**

2. **Create Inline Policy**
   - Click **"JSON"** tab
   - Paste the following policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ec2:CreateNetworkInterface",
        "ec2:DescribeNetworkInterfaces",
        "ec2:DeleteNetworkInterface",
        "ec2:AssignPrivateIpAddresses",
        "ec2:UnassignPrivateIpAddresses"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeAgent",
        "bedrock:InvokeModel",
        "bedrock-agent-runtime:InvokeAgent"
      ],
      "Resource": "*"
    }
  ]
}
```

3. **Review and Create**
   - Click **"Next"**
   - **Policy name**: `LambdaVPCPermissions`
   - Click **"Create policy"**

**Policy Breakdown:**
- **Logs permissions**: Write to CloudWatch Logs
- **EC2 permissions**: Create/manage ENIs for VPC access
- **Bedrock permissions**: Invoke AWS Bedrock Agent Core SDK

---

## Security Group Configuration

### Create Lambda Security Group

1. **Navigate to VPC Console**
   - Go to AWS Console → Services → VPC
   - Click **"Security Groups"** → **"Create security group"**

2. **Basic Details**
   - **Name**: `multi-agent-orchestrator-lambda-sg`
   - **Description**: `Security group for Lambda functions to access ECS services`
   - **VPC**: Select your VPC (e.g., `multi-agent-orchestrator-vpc`)

3. **Configure Outbound Rules**
   
   **Rule 1: ECS Services**
   - Click **"Add rule"**
   - **Type**: `Custom TCP`
   - **Port range**: `8000-8002`
   - **Destination**: Select `Custom` → Enter VPC CIDR (e.g., `10.0.0.0/16`)
   - **Description**: `Allow Lambda to call ECS services`

   **Rule 2: HTTPS (Internet)**
   - Click **"Add rule"**
   - **Type**: `HTTPS`
   - **Port**: `443`
   - **Destination**: `0.0.0.0/0`
   - **Description**: `Allow Lambda to access internet (for Snowflake, etc.)`

   **Rule 3: DNS**
   - Click **"Add rule"**
   - **Type**: `Custom UDP`
   - **Port**: `53`
   - **Destination**: VPC CIDR (e.g., `10.0.0.0/16`)
   - **Description**: `Allow DNS resolution for service discovery`

4. **Create Security Group**
   - Click **"Create security group"**

**Security Group Rules Summary:**

| Type | Protocol | Port | Destination | Purpose |
|------|----------|------|-------------|---------|
| Outbound | TCP | 8000-8002 | VPC CIDR | Access ECS services |
| Outbound | TCP | 443 | 0.0.0.0/0 | HTTPS (Snowflake, APIs) |
| Outbound | UDP | 53 | VPC CIDR | DNS resolution |

---

## Deployment Package Creation

### Package Structure

Your `query_handler.zip` should contain:

```
query_handler.zip
├── aws_agent_core/
│   ├── __init__.py
│   ├── lambda_handlers/
│   │   ├── __init__.py
│   │   ├── query_handler.py
│   │   └── utils.py
│   ├── orchestrator.py
│   └── runtime/
│       └── sdk_client.py
├── shared/
│   ├── __init__.py
│   ├── config/
│   ├── models/
│   └── utils/
├── boto3/
├── botocore/
└── (other dependencies from requirements.txt)
```

### Creating the Deployment Package

#### Option 1: Manual Creation

```bash
# 1. Create deployment directory
mkdir -p lambda_deployments
cd lambda_deployments

# 2. Install dependencies
pip install -r ../requirements.txt -t .

# 3. Copy application code
cp -r ../aws_agent_core .
cp -r ../shared .

# 4. Create ZIP file
zip -r ../query_handler.zip .
cd ..
```

#### Option 2: Using Script

Create `scripts/build_lambda_package.sh`:

```bash
#!/bin/bash
set -e

SERVICE=$1
if [ -z "$SERVICE" ]; then
    echo "Usage: $0 <service_name>"
    echo "Example: $0 query_handler"
    exit 1
fi

PACKAGE_DIR="lambda_deployments"
ZIP_FILE="${PACKAGE_DIR}/${SERVICE}.zip"

echo "Building Lambda package for $SERVICE..."

# Clean and create directory
rm -rf $PACKAGE_DIR
mkdir -p $PACKAGE_DIR

# Install dependencies
pip install -r requirements.txt -t $PACKAGE_DIR/

# Copy application code
cp -r aws_agent_core $PACKAGE_DIR/
cp -r shared $PACKAGE_DIR/

# Create ZIP (excluding unnecessary files)
cd $PACKAGE_DIR
zip -r ../${SERVICE}.zip . -x "*.pyc" "__pycache__/*" "*.git*" "*.md"
cd ..

echo "Package created: ${SERVICE}.zip"
```

**Usage:**
```bash
chmod +x scripts/build_lambda_package.sh
./scripts/build_lambda_package.sh query_handler
```

### Package Size Considerations

- **Lambda package limit**: 50 MB (zipped), 250 MB (unzipped)
- **If package is too large**:
  - Use Lambda Layers for dependencies
  - Exclude unnecessary files (tests, docs, etc.)
  - Use `.zip` compression

### Using Lambda Layers

For large dependencies, use Lambda Layers:

1. **Create Layer Package**
```bash
mkdir -p lambda_layer/python
pip install -r requirements.txt -t lambda_layer/python/
cd lambda_layer
zip -r ../lambda_layer.zip .
```

2. **Upload Layer**
   - Lambda Console → Layers → Create layer
   - Upload `lambda_layer.zip`
   - Note the Layer ARN

3. **Attach to Function**
   - Function → Layers → Add a layer
   - Select your layer

---

## Verification and Testing

### Step 1: Test Function Locally

1. **Navigate to Test Tab**
   - Lambda function → **"Test"** tab
   - Click **"Create new test event"**

2. **Create Test Event**
   - **Event name**: `test-query-request`
   - **Event JSON**:

```json
{
  "httpMethod": "POST",
  "path": "/api/v1/query",
  "body": "{\"query\": \"What are the total sales?\", \"session_id\": \"test-123\", \"context\": {\"data_type\": \"structured\"}}",
  "requestContext": {
    "http": {
      "method": "POST",
      "path": "/api/v1/query"
    }
  },
  "queryStringParameters": null,
  "headers": {
    "Content-Type": "application/json"
  }
}
```

3. **Run Test**
   - Click **"Test"**
   - Review execution result

### Step 2: Check CloudWatch Logs

1. **Navigate to Logs**
   - Lambda function → **"Monitor"** tab
   - Click **"View CloudWatch logs"**

2. **Review Logs**
   - Check for:
     - Function invocations
     - Errors or exceptions
     - VPC ENI creation messages
     - Service discovery DNS resolution
     - HTTP calls to ECS services

3. **Common Log Messages**
   - `START RequestId: ...` - Function started
   - `Creating network interface...` - VPC ENI creation
   - `Invoking LangGraph at http://langgraph...` - Service call
   - `END RequestId: ...` - Function completed

### Step 3: Verify VPC Connectivity

1. **Check Network Interfaces**
   - VPC Console → **"Network Interfaces"**
   - Filter by: `Description` contains `lambda`
   - Verify ENIs are created in correct subnets

2. **Check Security Groups**
   - Verify Lambda security group allows outbound to ECS ports
   - Verify ECS security group allows inbound from Lambda security group

3. **Test DNS Resolution**
   - Add test code to Lambda:
   ```python
   import socket
   hostname = "langgraph.multi-agent-orchestrator.local"
   ip = socket.gethostbyname(hostname)
   print(f"Resolved {hostname} to {ip}")
   ```

### Step 4: Test End-to-End Flow

1. **Get API Gateway URL**
   - API Gateway Console → Your API → Stages
   - Copy the Invoke URL

2. **Test via API Gateway**
```bash
curl -X POST https://your-api-gateway-url/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the total sales?",
    "session_id": "test-123"
  }'
```

3. **Verify Response**
   - Check response status (200 OK)
   - Verify response contains expected data
   - Check Lambda logs for execution flow

---

## Common Issues and Solutions

### Issue 1: VPC ENI Creation Timeout

**Symptoms:**
- Function times out on first invocation
- Error: `Task timed out after X seconds`
- Cold start takes > 30 seconds

**Solutions:**
1. **Check Subnet IP Availability**
   ```bash
   # Check available IPs in subnets
   aws ec2 describe-subnets --subnet-ids subnet-xxx
   ```

2. **Verify IAM Permissions**
   - Ensure Lambda role has `ec2:CreateNetworkInterface` permission
   - Check role policies

3. **Use Provisioned Concurrency**
   - Lambda → Configuration → Provisioned concurrency
   - Keeps ENIs warm, eliminates cold start

4. **Reduce Subnet Selection**
   - Select only necessary subnets (minimum 2 for HA)

### Issue 2: Cannot Resolve Service Discovery DNS

**Symptoms:**
- `NameResolutionError` or `socket.gaierror`
- Connection timeout to service discovery endpoints
- DNS lookup fails

**Solutions:**
1. **Verify VPC Configuration**
   - Ensure Lambda is in same VPC as service discovery
   - Check VPC DNS settings are enabled

2. **Check DNS Resolution**
   - VPC → Your VPC → Actions → Edit DNS resolution
   - Ensure "Enable DNS resolution" is checked

3. **Verify Service Discovery Setup**
   - Cloud Map Console → Namespaces
   - Verify namespace exists: `multi-agent-orchestrator.local`
   - Check services are registered

4. **Test DNS Resolution**
   ```python
   import socket
   try:
       ip = socket.gethostbyname("langgraph.multi-agent-orchestrator.local")
       print(f"DNS resolved to: {ip}")
   except socket.gaierror as e:
       print(f"DNS resolution failed: {e}")
   ```

5. **Check Security Group**
   - Ensure Lambda security group allows UDP port 53 (DNS)

### Issue 3: Cannot Connect to ECS Services

**Symptoms:**
- Connection refused errors
- Timeout connecting to ECS services
- `ConnectionError` or `ConnectTimeout`

**Solutions:**
1. **Verify ECS Security Group**
   - ECS security group must allow inbound from Lambda security group
   - Ports: 8000 (aws-agent-core), 8001 (langgraph), 8002 (snowflake-cortex)

2. **Check ECS Tasks are Running**
   - ECS Console → Clusters → Your cluster → Services
   - Verify tasks are running and healthy

3. **Verify Service Discovery Registration**
   - Cloud Map → Services
   - Check services are registered and healthy
   - Verify DNS records exist

4. **Test Connectivity**
   - Add test code to Lambda:
   ```python
   import httpx
   try:
       response = httpx.get("http://langgraph.multi-agent-orchestrator.local:8001/health", timeout=5.0)
       print(f"Connection successful: {response.status_code}")
   except Exception as e:
       print(f"Connection failed: {e}")
   ```

5. **Check Network Path**
   - Ensure Lambda and ECS are in same VPC
   - Verify subnets have route tables configured
   - Check NAT Gateway for outbound internet (if needed)

### Issue 4: Lambda Package Too Large

**Symptoms:**
- Upload fails with size error
- Package exceeds 50 MB (zipped) or 250 MB (unzipped)

**Solutions:**
1. **Use Lambda Layers**
   - Move dependencies to Lambda Layer
   - Keep only application code in function package

2. **Exclude Unnecessary Files**
   - Use `.dockerignore`-like patterns
   - Exclude: `__pycache__`, `*.pyc`, `tests/`, `docs/`

3. **Optimize Dependencies**
   - Only include required packages
   - Use minimal dependency versions

4. **Split Functions**
   - Create separate functions for different handlers
   - Share common code via Layers

### Issue 5: Cold Start Performance

**Symptoms:**
- First invocation takes 10-30 seconds
- Subsequent invocations are fast

**Solutions:**
1. **Use Provisioned Concurrency**
   - Lambda → Configuration → Provisioned concurrency
   - Keeps functions warm

2. **Optimize Package Size**
   - Smaller packages = faster cold starts
   - Use Lambda Layers

3. **Optimize Imports**
   - Lazy load heavy dependencies
   - Import only what's needed

4. **Warm-up Strategy**
   - Use CloudWatch Events to ping function periodically
   - Keep at least one instance warm

---

## Best Practices

### 1. VPC Configuration

- ✅ **Use Private Subnets**: Place Lambda ENIs in private subnets
- ✅ **Multiple AZs**: Select subnets in at least 2 Availability Zones
- ✅ **IP Address Management**: Monitor subnet IP availability
- ✅ **Security Groups**: Use least-privilege security group rules

### 2. Timeout and Memory

- ✅ **Appropriate Timeout**: Set based on expected execution time (300s for this use case)
- ✅ **Memory Optimization**: Start with 512 MB, adjust based on metrics
- ✅ **Monitor Metrics**: Use CloudWatch to track duration and memory usage

### 3. Environment Variables

- ✅ **Use Environment Variables**: Store configuration in environment variables
- ✅ **Service Discovery**: Use DNS names for service endpoints
- ✅ **Sensitive Data**: Use AWS Secrets Manager for secrets (not environment variables)

### 4. Error Handling

- ✅ **Comprehensive Logging**: Log all important operations
- ✅ **Error Responses**: Return proper error responses to API Gateway
- ✅ **Retry Logic**: Implement retry logic for transient failures
- ✅ **Dead Letter Queues**: Configure DLQ for failed invocations

### 5. Monitoring and Observability

- ✅ **CloudWatch Logs**: Enable detailed logging
- ✅ **CloudWatch Metrics**: Monitor invocation count, duration, errors
- ✅ **X-Ray Tracing**: Enable AWS X-Ray for distributed tracing
- ✅ **Custom Metrics**: Publish custom metrics for business logic

### 6. Security

- ✅ **IAM Least Privilege**: Grant only necessary permissions
- ✅ **VPC Isolation**: Use private subnets and security groups
- ✅ **Encryption**: Enable encryption at rest and in transit
- ✅ **Secrets Management**: Use AWS Secrets Manager for sensitive data

### 7. Deployment

- ✅ **Version Control**: Use Lambda versions and aliases
- ✅ **CI/CD Integration**: Automate deployments via CI/CD pipelines
- ✅ **Testing**: Test functions before deployment
- ✅ **Rollback Strategy**: Keep previous versions for quick rollback

---

## Configuration Reference Table

| Configuration | Terraform Parameter | AWS Console Location | Default Value |
|--------------|---------------------|---------------------|---------------|
| Function Name | `function_name` | Function name (Step 1) | - |
| Runtime | `runtime` | Runtime settings | Python 3.11 |
| Handler | `handler` | Runtime settings → Handler | - |
| Timeout | `timeout` | General configuration → Timeout | 3 seconds |
| Memory | `memory_size` | General configuration → Memory | 128 MB |
| IAM Role | `role` | Permissions → Execution role | - |
| VPC | `vpc_config.subnet_ids` | VPC → VPC, Subnets | - |
| Security Group | `vpc_config.security_group_ids` | VPC → Security groups | - |
| Environment Variables | `environment.variables` | Environment variables | - |

---

## Quick Reference Commands

### Create Deployment Package
```bash
./scripts/build_lambda_package.sh query_handler
```

### Update Lambda Function Code
```bash
aws lambda update-function-code \
  --function-name multi-agent-orchestrator-query-handler \
  --zip-file fileb://query_handler.zip
```

### Update Lambda Configuration
```bash
aws lambda update-function-configuration \
  --function-name multi-agent-orchestrator-query-handler \
  --timeout 300 \
  --memory-size 512 \
  --environment Variables="{LANGGRAPH_ENDPOINT=http://langgraph.multi-agent-orchestrator.local:8001}"
```

### Test Lambda Function
```bash
aws lambda invoke \
  --function-name multi-agent-orchestrator-query-handler \
  --payload file://test-event.json \
  response.json
```

### View Lambda Logs
```bash
aws logs tail /aws/lambda/multi-agent-orchestrator-query-handler --follow
```

---

## Summary

This guide covers:

1. ✅ **Complete Lambda configuration** with VPC and service discovery
2. ✅ **Step-by-step AWS Console setup** instructions
3. ✅ **IAM role and security group** configuration
4. ✅ **Deployment package creation** process
5. ✅ **Verification and testing** procedures
6. ✅ **Common issues and solutions**
7. ✅ **Best practices** for production deployment

Following this guide will enable your Lambda functions to successfully communicate with containerized ECS services via VPC and service discovery in the multi-agent orchestrator architecture.

---

**Last Updated**: 2024  
**Maintained By**: Multi-Agent Orchestrator Team
