# AWS SDK Setup Guide for Multi-Agent Orchestrator

This guide provides step-by-step instructions for setting up the AWS SDK (Boto3) and configuring prerequisites for the AWS Agent Core SDK integration.

## Table of Contents

1. [Prerequisites Overview](#prerequisites-overview)
2. [Python Environment Setup](#python-environment-setup)
3. [AWS SDK Installation](#aws-sdk-installation)
4. [AWS Account Configuration](#aws-account-configuration)
5. [IAM Permissions Setup](#iam-permissions-setup)
6. [AWS Region Configuration](#aws-region-configuration)
7. [AWS Credentials Configuration](#aws-credentials-configuration)
8. [Verification and Testing](#verification-and-testing)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites Overview

Before setting up the AWS SDK, ensure you have:

- ✅ **AWS Account**: An active AWS account with appropriate access
- ✅ **Python 3.11+**: Python installed on your development machine
- ✅ **pip**: Python package manager
- ✅ **Internet Connection**: For downloading packages and accessing AWS services
- ✅ **IAM Permissions**: Appropriate permissions for AWS Agent Core and related services
- ✅ **Supported AWS Region**: A region that supports AWS Agent Core

---

## Python Environment Setup

### 1. Check Python Version

Verify that Python 3.11 or higher is installed:

```bash
python3 --version
# Should output: Python 3.11.x or higher
```

If Python is not installed or the version is too old:

**On Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip
```

**On macOS (using Homebrew):**
```bash
brew install python@3.11
```

**On Windows:**
Download and install from [python.org](https://www.python.org/downloads/)

### 2. Set Up Virtual Environment (Recommended)

It's recommended to use a virtual environment to isolate project dependencies:

```bash
# Navigate to project directory
cd multi-agent-orchestrator

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Verify pip Installation

```bash
python3 -m pip --version
```

If pip is not installed:

```bash
# On Linux/macOS:
python3 -m ensurepip --upgrade

# Or install via package manager:
sudo apt install python3-pip  # Ubuntu/Debian
brew install pip              # macOS
```

---

## AWS SDK Installation

### Option 1: Using the Installation Script (Recommended)

#### Python Script

```bash
# Make script executable (if needed)
chmod +x scripts/install_aws_sdk.py

# Basic installation
python3 scripts/install_aws_sdk.py

# Upgrade existing packages
python3 scripts/install_aws_sdk.py --upgrade

# Check installation status only
python3 scripts/install_aws_sdk.py --check-only

# Install from requirements.txt
python3 scripts/install_aws_sdk.py --from-requirements

# Install with optional packages (AWS CLI)
python3 scripts/install_aws_sdk.py --install-optional
```

#### Shell Script

```bash
# Make script executable
chmod +x scripts/install_aws_sdk.sh

# Basic installation
./scripts/install_aws_sdk.sh

# Upgrade existing packages
./scripts/install_aws_sdk.sh --upgrade

# Check installation status only
./scripts/install_aws_sdk.sh --check-only

# Install from requirements.txt
./scripts/install_aws_sdk.sh --from-requirements

# Install with optional packages
./scripts/install_aws_sdk.sh --install-optional
```

### Option 2: Manual Installation

#### Install from requirements.txt

```bash
# Install all dependencies including AWS SDK
pip install -r requirements.txt
```

#### Install Individual Packages

```bash
# Install boto3 and botocore
pip install boto3>=1.29.0 botocore>=1.32.0

# Or install specific versions
pip install boto3==1.29.7 botocore==1.32.7
```

#### Install AWS CLI (Optional but Recommended)

The AWS CLI is useful for testing and manual operations:

```bash
# Install AWS CLI
pip install awscli

# Or use standalone installer (recommended for system-wide installation)
# On Linux:
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# On macOS:
brew install awscli

# On Windows:
# Download and run the MSI installer from AWS website
```

### Verify Installation

Test that the AWS SDK is properly installed:

```bash
python3 -c "import boto3; import botocore; print('AWS SDK installed successfully')"
```

Or use the installation script in check mode:

```bash
python3 scripts/install_aws_sdk.py --check-only
```

---

## AWS Account Configuration

### 1. Create or Access AWS Account

If you don't have an AWS account:

1. Go to [AWS Sign Up](https://aws.amazon.com/)
2. Follow the registration process
3. Complete account verification

### 2. Access AWS Console

1. Log in to the [AWS Management Console](https://console.aws.amazon.com/)
2. Navigate to the region where you plan to use AWS Agent Core

### 3. Enable Required Services

Ensure the following services are enabled in your AWS account:

- **AWS Agent Core** (Bedrock Agent Core)
- **Amazon Bedrock**
- **Amazon Cognito** (if using for authentication)
- **AWS IAM** (for permissions management)

---

## IAM Permissions Setup

### Required IAM Permissions

Your AWS user or role needs the following permissions:

#### 1. AWS Agent Core Permissions

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeAgent",
        "bedrock:InvokeModel",
        "bedrock:ListFoundationModels",
        "bedrock:GetFoundationModel",
        "bedrock-agent:CreateAgent",
        "bedrock-agent:GetAgent",
        "bedrock-agent:UpdateAgent",
        "bedrock-agent:DeleteAgent",
        "bedrock-agent:ListAgents",
        "bedrock-agent:CreateAgentAlias",
        "bedrock-agent:GetAgentAlias",
        "bedrock-agent:UpdateAgentAlias",
        "bedrock-agent:DeleteAgentAlias",
        "bedrock-agent:ListAgentAliases"
      ],
      "Resource": "*"
    }
  ]
}
```

#### 2. Amazon Bedrock Permissions

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:ListFoundationModels",
        "bedrock:GetFoundationModel"
      ],
      "Resource": "*"
    }
  ]
}
```

#### 3. Cognito Permissions (if applicable)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cognito-idp:DescribeUserPool",
        "cognito-idp:AdminGetUser",
        "cognito-idp:AdminInitiateAuth"
      ],
      "Resource": "*"
    }
  ]
}
```

### Setting Up IAM Permissions

#### Option 1: Using AWS Console

1. Navigate to [IAM Console](https://console.aws.amazon.com/iam/)
2. Go to **Users** or **Roles** (depending on your setup)
3. Select your user/role
4. Click **Add permissions** → **Attach policies directly**
5. Either:
   - Use existing managed policies (e.g., `AmazonBedrockFullAccess`)
   - Create a custom policy with the permissions above

#### Option 2: Using AWS CLI

```bash
# Create a policy document
cat > bedrock-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:*",
        "bedrock-agent:*"
      ],
      "Resource": "*"
    }
  ]
}
EOF

# Create the policy
aws iam create-policy \
  --policy-name BedrockAgentCorePolicy \
  --policy-document file://bedrock-policy.json

# Attach policy to user
aws iam attach-user-policy \
  --user-name YOUR_USERNAME \
  --policy-arn arn:aws:iam::YOUR_ACCOUNT_ID:policy/BedrockAgentCorePolicy
```

#### Option 3: Using Terraform (if using infrastructure as code)

```hcl
resource "aws_iam_policy" "bedrock_agent_core" {
  name        = "BedrockAgentCorePolicy"
  description = "Policy for AWS Agent Core SDK access"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:*",
          "bedrock-agent:*"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_user_policy_attachment" "bedrock_agent_core" {
  user       = aws_iam_user.developer.name
  policy_arn = aws_iam_policy.bedrock_agent_core.arn
}
```

### Best Practices

- **Principle of Least Privilege**: Only grant the minimum permissions necessary
- **Use IAM Roles**: For applications running on AWS infrastructure, use IAM roles instead of access keys
- **Rotate Credentials**: Regularly rotate access keys and review permissions
- **Use Separate Accounts**: Consider using separate AWS accounts for development, staging, and production

---

## AWS Region Configuration

### Supported Regions

AWS Agent Core is not available in all AWS regions. Check the [AWS Bedrock Service Availability](https://aws.amazon.com/about-aws/global-infrastructure/regional-product-services/) page for current region support.

Common supported regions include:
- `us-east-1` (N. Virginia)
- `us-west-2` (Oregon)
- `eu-west-1` (Ireland)
- `ap-southeast-1` (Singapore)

### Set Default Region

#### Option 1: Environment Variable

```bash
# Linux/macOS
export AWS_DEFAULT_REGION=us-east-1

# Windows (PowerShell)
$env:AWS_DEFAULT_REGION="us-east-1"

# Windows (CMD)
set AWS_DEFAULT_REGION=us-east-1
```

#### Option 2: AWS Config File

```bash
# Configure AWS CLI
aws configure set region us-east-1
```

This updates `~/.aws/config`:

```ini
[default]
region = us-east-1
```

#### Option 3: In Application Code

```python
import boto3

# Create session with specific region
session = boto3.Session(region_name='us-east-1')

# Or set default region
boto3.setup_default_session(region_name='us-east-1')
```

#### Option 4: Environment File (.env)

Add to your `.env` file:

```bash
AWS_REGION=us-east-1
AWS_DEFAULT_REGION=us-east-1
```

---

## AWS Credentials Configuration

### Option 1: AWS CLI Configuration (Recommended for Development)

```bash
# Configure AWS credentials
aws configure

# You'll be prompted for:
# - AWS Access Key ID
# - AWS Secret Access Key
# - Default region name
# - Default output format (json, text, table)
```

This creates/updates:
- `~/.aws/credentials` (access keys)
- `~/.aws/config` (region and output format)

### Option 2: Environment Variables

```bash
# Linux/macOS
export AWS_ACCESS_KEY_ID=your_access_key_id
export AWS_SECRET_ACCESS_KEY=your_secret_access_key
export AWS_DEFAULT_REGION=us-east-1

# Windows (PowerShell)
$env:AWS_ACCESS_KEY_ID="your_access_key_id"
$env:AWS_SECRET_ACCESS_KEY="your_secret_access_key"
$env:AWS_DEFAULT_REGION="us-east-1"
```

### Option 3: IAM Role (For EC2/ECS/Lambda)

If running on AWS infrastructure, use IAM roles instead of access keys:

```python
import boto3

# Boto3 automatically uses the IAM role attached to the instance
session = boto3.Session()
```

### Option 4: Credentials File (Programmatic Access)

Create `~/.aws/credentials`:

```ini
[default]
aws_access_key_id = YOUR_ACCESS_KEY_ID
aws_secret_access_key = YOUR_SECRET_ACCESS_KEY

[profile-name]
aws_access_key_id = ANOTHER_ACCESS_KEY_ID
aws_secret_access_key = ANOTHER_SECRET_ACCESS_KEY
```

Use a specific profile:

```python
import boto3

session = boto3.Session(profile_name='profile-name')
```

### Option 5: Application Configuration

Store credentials in your application's configuration:

```python
# config/aws_config.py
import os
import boto3

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')

# Create session
session = boto3.Session(
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)
```

### Creating Access Keys

1. Go to [IAM Console](https://console.aws.amazon.com/iam/)
2. Navigate to **Users** → Select your user
3. Go to **Security credentials** tab
4. Click **Create access key**
5. Choose use case (e.g., "Application running outside AWS")
6. Download or copy the access key ID and secret access key
7. **Important**: Store the secret access key securely - it won't be shown again

### Security Best Practices

- ✅ **Never commit credentials to version control**
- ✅ **Use IAM roles when possible** (for applications on AWS infrastructure)
- ✅ **Rotate access keys regularly**
- ✅ **Use separate credentials for different environments**
- ✅ **Restrict permissions using IAM policies**
- ✅ **Use AWS Secrets Manager** for production applications
- ✅ **Enable MFA** for AWS console access

---

## Verification and Testing

### 1. Verify AWS SDK Installation

```bash
# Using the installation script
python3 scripts/install_aws_sdk.py --check-only

# Or manually
python3 -c "import boto3; print(boto3.__version__)"
python3 -c "import botocore; print(botocore.__version__)"
```

### 2. Verify AWS Credentials

```bash
# Using AWS CLI
aws sts get-caller-identity

# Expected output:
# {
#     "UserId": "AIDAXXXXXXXXXXXXXXXXX",
#     "Account": "123456789012",
#     "Arn": "arn:aws:iam::123456789012:user/username"
# }
```

### 3. Test AWS SDK Connection

```python
# test_aws_connection.py
import boto3
import sys

try:
    # Create a session
    session = boto3.Session()
    
    # Get caller identity
    sts = session.client('sts')
    identity = sts.get_caller_identity()
    
    print("✅ AWS connection successful!")
    print(f"Account: {identity['Account']}")
    print(f"User ARN: {identity['Arn']}")
    print(f"Region: {session.region_name}")
    
except Exception as e:
    print(f"❌ AWS connection failed: {e}")
    sys.exit(1)
```

Run the test:

```bash
python3 test_aws_connection.py
```

### 4. Test Bedrock Access

```python
# test_bedrock_access.py
import boto3
import sys

try:
    session = boto3.Session()
    bedrock = session.client('bedrock', region_name='us-east-1')
    
    # List available foundation models
    models = bedrock.list_foundation_models()
    
    print("✅ Bedrock access successful!")
    print(f"Found {len(models.get('modelSummaries', []))} foundation models")
    
except Exception as e:
    print(f"❌ Bedrock access failed: {e}")
    print("Check:")
    print("1. Region supports Bedrock")
    print("2. IAM permissions are correct")
    print("3. Bedrock is enabled in your account")
    sys.exit(1)
```

### 5. Test Agent Core Access

```python
# test_agent_core_access.py
import boto3
import sys

try:
    session = boto3.Session()
    bedrock_agent = session.client('bedrock-agent', region_name='us-east-1')
    
    # List agents (may be empty if none created)
    agents = bedrock_agent.list_agents()
    
    print("✅ Agent Core access successful!")
    print(f"Found {len(agents.get('agentSummaries', []))} agents")
    
except Exception as e:
    print(f"❌ Agent Core access failed: {e}")
    print("Check:")
    print("1. Region supports Agent Core")
    print("2. IAM permissions include bedrock-agent:*")
    print("3. Agent Core is enabled in your account")
    sys.exit(1)
```

---

## Troubleshooting

### Common Issues and Solutions

#### 1. "No module named 'boto3'"

**Solution:**
```bash
# Reinstall boto3
pip install boto3

# Or use the installation script
python3 scripts/install_aws_sdk.py
```

#### 2. "Unable to locate credentials"

**Solution:**
- Configure AWS credentials using `aws configure`
- Set environment variables `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`
- Check that `~/.aws/credentials` exists and is readable

#### 3. "Access Denied" or "UnauthorizedOperation"

**Solution:**
- Verify IAM permissions are correctly attached
- Check that the access key has the required permissions
- Ensure the region supports the service you're trying to use

#### 4. "Region not supported"

**Solution:**
- Check [AWS Service Availability](https://aws.amazon.com/about-aws/global-infrastructure/regional-product-services/)
- Switch to a supported region (e.g., `us-east-1`, `us-west-2`)
- Update your region configuration

#### 5. "Bedrock is not enabled"

**Solution:**
- Go to [AWS Bedrock Console](https://console.aws.amazon.com/bedrock/)
- Enable Bedrock in your account
- Accept the terms of service if prompted

#### 6. Python Version Issues

**Solution:**
```bash
# Check Python version
python3 --version

# If version is too old, upgrade:
# Ubuntu/Debian:
sudo apt install python3.11

# macOS:
brew install python@3.11
```

#### 7. pip Installation Fails

**Solution:**
```bash
# Upgrade pip
python3 -m pip install --upgrade pip

# Use --user flag if permission issues
pip install --user boto3

# Or use virtual environment
python3 -m venv venv
source venv/bin/activate
pip install boto3
```

### Getting Help

- **AWS Documentation**: [AWS SDK for Python (Boto3) Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- **AWS Agent Core**: [AWS Bedrock Agent Core Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html)
- **AWS Support**: [AWS Support Center](https://console.aws.amazon.com/support/)
- **Stack Overflow**: Tag questions with `[aws]`, `[boto3]`, `[bedrock]`

---

## Next Steps

After completing the AWS SDK setup:

1. ✅ **Review the project README** for application-specific configuration
2. ✅ **Set up environment variables** in `.env` file
3. ✅ **Configure agent settings** in `config/agents.yaml`
4. ✅ **Run the application** and test AWS Agent Core integration
5. ✅ **Set up monitoring** and observability (CloudWatch, Langfuse)

For more information, see:
- [Project README](../README.md)
- [Architecture Documentation](../ARCHITECTURE.md)
- [Setup Guide](../SETUP_GUIDE.md)

---

## Summary Checklist

- [ ] Python 3.11+ installed
- [ ] pip installed and up to date
- [ ] Virtual environment created (recommended)
- [ ] AWS SDK (boto3) installed
- [ ] AWS account created and accessible
- [ ] IAM permissions configured
- [ ] AWS credentials configured
- [ ] AWS region set (supported region)
- [ ] AWS connection verified
- [ ] Bedrock access verified
- [ ] Agent Core access verified

---

**Last Updated**: 2024
**Maintained By**: Multi-Agent Orchestrator Team
