# AWS Services Request - Multi-Agent Orchestrator Project

## Project Overview
Multi-agent orchestrator system with AWS Agent Core, LangGraph, Snowflake Cortex AI, and Langfuse. All components run as containerized services on AWS.

---

## REQUIRED AWS SERVICES

### 1. COMPUTE & CONTAINERS

#### 1.1 Amazon ECS (Elastic Container Service) - Fargate
**Service**: ECS with Fargate launch type  
**Purpose**: Host containerized services (AWS Agent Core, LangGraph, Snowflake Cortex, Langfuse)  
**Reasoning**: Serverless container execution, no EC2 management, auto-scaling, high availability  
**Requirements**:
- 1 ECS Cluster with Container Insights enabled
- 3 ECS Services:
  - `aws-agent-core` (2 tasks, 1 vCPU, 2GB RAM each)
  - `langgraph` (2 tasks, 1 vCPU, 2GB RAM each)
  - `snowflake-cortex` (3 tasks, 1 vCPU, 2GB RAM each)
- Capacity Providers: FARGATE and FARGATE_SPOT

---

### 2. NETWORKING

#### 2.1 Amazon VPC
**Service**: Virtual Private Cloud  
**Purpose**: Isolated network for all resources  
**Reasoning**: Security, network segmentation, required for ECS  
**Requirements**:
- CIDR: `/16` (e.g., `10.0.0.0/16`)
- DNS hostnames and DNS support enabled

#### 2.2 Subnets
**Service**: VPC Subnets  
**Purpose**: Network segmentation  
**Reasoning**: Public subnets for Load Balancer, private subnets for ECS tasks  
**Requirements**:
- 2 Public subnets (one per Availability Zone)
- 2 Private subnets (one per Availability Zone)

#### 2.3 Internet Gateway
**Service**: Internet Gateway  
**Purpose**: Internet access for public resources  
**Reasoning**: Required for Load Balancer to receive internet traffic

#### 2.4 NAT Gateway (2 instances)
**Service**: NAT Gateway  
**Purpose**: Outbound internet access for ECS tasks in private subnets  
**Reasoning**: ECS tasks need internet for:
- Pulling Docker images from ECR
- Connecting to Snowflake (external service)
- Accessing external APIs
- Downloading dependencies
**Requirements**: One NAT Gateway per Availability Zone for high availability

#### 2.5 Application Load Balancer
**Service**: Application Load Balancer (ALB)  
**Purpose**: Distribute traffic to ECS tasks, single entry point  
**Reasoning**: Load balancing, health checks, high availability  
**Requirements**:
- Internet-facing ALB
- HTTP listener (port 80)
- Target Group for AWS Agent Core service (port 8000)
- Health check: `/health` endpoint

#### 2.6 Security Groups
**Service**: Security Groups  
**Purpose**: Network-level security  
**Reasoning**: Control inbound/outbound traffic  
**Requirements**:
- ALB Security Group: Allow HTTP/HTTPS from internet
- ECS Security Group: Allow traffic from ALB and inter-service communication

#### 2.7 ECS Service Discovery
**Service**: AWS Cloud Map  
**Purpose**: Service-to-service DNS-based discovery  
**Reasoning**: Services need to find each other dynamically  
**Requirements**:
- Private DNS namespace: `multi-agent-orchestrator.local`
- Service discovery for 3 services

---

### 3. STORAGE

#### 3.1 Amazon ECR (Elastic Container Registry)
**Service**: ECR  
**Purpose**: Store Docker container images  
**Reasoning**: ECS needs to pull images to run tasks  
**Requirements**:
- 3 ECR repositories:
  - `multi-agent-orchestrator-dev-aws-agent-core`
  - `multi-agent-orchestrator-dev-langgraph`
  - `multi-agent-orchestrator-dev-snowflake-cortex`
- Image scanning on push enabled
- Lifecycle policy: Keep last 10 images

#### 3.2 Amazon S3
**Service**: S3  
**Purpose**: Store Terraform state files  
**Reasoning**: Terraform requires remote state storage  
**Requirements**:
- 1 S3 bucket for Terraform state
- Versioning enabled
- Encryption enabled

---

### 4. AI/ML SERVICES

#### 4.1 Amazon Bedrock
**Service**: Amazon Bedrock  
**Purpose**: AWS Agent Core Runtime SDK, foundation model access  
**Reasoning**: Required for `bedrock-runtime:InvokeAgent` API calls  
**Requirements**:
- Bedrock access enabled in AWS account
- IAM permissions for:
  - `bedrock:InvokeModel`
  - `bedrock:InvokeModelWithResponseStream`
  - `bedrock-runtime:InvokeAgent`
  - `bedrock-runtime:InvokeModel`
  - `bedrock-runtime:InvokeModelWithResponseStream`
- Model access permissions (as needed)

---

### 5. DATABASE

#### 5.1 Amazon RDS PostgreSQL (Recommended)
**Service**: RDS for PostgreSQL  
**Purpose**: Database for Langfuse observability platform  
**Reasoning**: Langfuse requires PostgreSQL, managed service preferred  
**Requirements**:
- PostgreSQL 15+
- Instance: `db.t3.micro` (dev) or `db.t3.small` (prod)
- Multi-AZ deployment (production)
- Automated backups enabled
- Security group allowing access from ECS tasks

**Alternative**: PostgreSQL container on ECS (lower cost, more management)

---

### 6. SECURITY & IDENTITY

#### 6.1 IAM Roles and Policies
**Service**: IAM  
**Purpose**: Manage permissions for ECS tasks  
**Reasoning**: Least privilege access to AWS services  
**Requirements**:
- **ECS Task Execution Role**:
  - `AmazonECSTaskExecutionRolePolicy`
  - CloudWatch Logs permissions
  - ECR access permissions
- **ECS Task Role**:
  - Bedrock API permissions
  - Secrets Manager read permissions (if used)

#### 6.2 AWS Secrets Manager (Recommended)
**Service**: Secrets Manager  
**Purpose**: Securely store credentials (Snowflake, Langfuse, DB passwords)  
**Reasoning**: Security best practice, encrypted storage, audit trail  
**Requirements**:
- Secrets for Snowflake credentials
- Secrets for Langfuse API keys
- Secrets for database credentials
- IAM permissions for ECS tasks to read secrets

---

### 7. MONITORING & LOGGING

#### 7.1 Amazon CloudWatch Logs
**Service**: CloudWatch Logs  
**Purpose**: Centralized logging for all ECS tasks  
**Reasoning**: Required for debugging, monitoring, compliance  
**Requirements**:
- 3 Log Groups:
  - `/ecs/multi-agent-orchestrator-dev-aws-agent-core`
  - `/ecs/multi-agent-orchestrator-dev-langgraph`
  - `/ecs/multi-agent-orchestrator-dev-snowflake-cortex`
- Log retention: 7-30 days

#### 7.2 Amazon CloudWatch Metrics
**Service**: CloudWatch Metrics  
**Purpose**: Performance monitoring, resource utilization  
**Reasoning**: Monitor service health, enable auto-scaling  
**Requirements**:
- ECS Container Insights enabled
- Custom application metrics support

#### 7.3 CloudWatch Alarms (Optional)
**Service**: CloudWatch Alarms  
**Purpose**: Alert on service health issues  
**Reasoning**: Proactive issue detection  
**Requirements**:
- Alarms for CPU, memory, task failures, health checks

---

### 8. OPTIONAL BUT RECOMMENDED

#### 8.1 AWS Certificate Manager (ACM)
**Service**: ACM  
**Purpose**: SSL/TLS certificates for HTTPS  
**Reasoning**: Security best practice  
**Cost**: Free

#### 8.2 Amazon Route 53
**Service**: Route 53  
**Purpose**: DNS management (if using custom domain)  
**Reasoning**: Required for custom domain name

#### 8.3 AWS CloudTrail
**Service**: CloudTrail  
**Purpose**: API call logging, security auditing  
**Reasoning**: Compliance, audit trails, troubleshooting

---

## EXTERNAL DEPENDENCIES (Not AWS Services)

### Snowflake Account
- Snowflake account with Cortex AI enabled
- Network connectivity from AWS to Snowflake required
- Appropriate warehouse, database, and schema

---

## COST ESTIMATION

### Development Environment: ~$150-400/month
- ECS Fargate: $50-150
- NAT Gateway: $64-128
- ALB: $16-20
- RDS: $15-30
- CloudWatch: $5-30
- Other: $10-20

### Production Environment: ~$400-1000/month
- ECS Fargate (scaled): $200-500
- NAT Gateway: $64-128
- ALB: $16-20
- RDS (Multi-AZ): $100-200
- CloudWatch: $20-50
- Bedrock API: Variable (pay-per-use)
- Other: $20-50

---

## NETWORK CONNECTIVITY REQUIREMENTS

### Outbound from ECS Tasks (via NAT Gateway):
- Snowflake API endpoints
- External APIs (Langfuse if external)
- PyPI (Python packages)
- Docker Hub (if needed)

### Inbound to Load Balancer:
- HTTP/HTTPS from internet (ports 80/443)

---

## PROVISIONING PRIORITY

1. **Phase 1 - Foundation**:
   - VPC, Subnets, Internet Gateway, NAT Gateway
   - Security Groups
   - IAM Roles

2. **Phase 2 - Storage & Registry**:
   - ECR Repositories
   - S3 Bucket for Terraform state

3. **Phase 3 - Compute**:
   - ECS Cluster
   - ECS Services and Task Definitions
   - Service Discovery

4. **Phase 4 - Networking**:
   - Application Load Balancer
   - Target Groups

5. **Phase 5 - Database**:
   - RDS PostgreSQL

6. **Phase 6 - Monitoring**:
   - CloudWatch Log Groups
   - CloudWatch Metrics and Alarms

7. **Phase 7 - AI/ML**:
   - Bedrock access and permissions

---

## CONFIGURATION DETAILS

### ECS Task Specifications:
| Service | CPU | Memory | Desired Count |
|---------|-----|--------|---------------|
| AWS Agent Core | 1024 (1 vCPU) | 2048 MB | 2 |
| LangGraph | 1024 (1 vCPU) | 2048 MB | 2 |
| Snowflake Cortex | 1024 (1 vCPU) | 2048 MB | 3 |

### Ports:
- AWS Agent Core: 8000
- LangGraph: 8001
- Snowflake Cortex: 8002
- Langfuse: 3000

### Regions:
- **Primary**: `us-east-1` (N. Virginia)
- **Alternative**: `us-west-2`, `eu-west-1`

---

## SECURITY REQUIREMENTS

- All ECS tasks in private subnets
- Security groups with least privilege
- IAM roles with minimal required permissions
- Encryption at rest (ECR, RDS, S3)
- Encryption in transit (HTTPS recommended)
- Secrets in Secrets Manager (not environment variables)
- CloudTrail enabled for audit logging

---

## QUESTIONS FOR INFRASTRUCTURE TEAM

1. Which AWS region should be used?
2. What is the VPC CIDR block allocation?
3. Are there existing VPCs we should use or create new?
4. What is the budget approval for this infrastructure?
5. Are there any compliance requirements (HIPAA, SOC2, etc.)?
6. What is the preferred RDS instance size?
7. Should we use Secrets Manager or Parameter Store?
8. Are there existing IAM policies we should follow?
9. What is the backup retention policy?
10. Are there network restrictions for outbound connectivity?

---

## CONTACT & DOCUMENTATION

- **Detailed Documentation**: `docs/AWS_INFRASTRUCTURE_REQUIREMENTS.md`
- **Terraform Code**: `infrastructure/terraform/`
- **Architecture Diagram**: `ARCHITECTURE.md`

---

## APPROVAL CHECKLIST

- [ ] VPC and Networking approved
- [ ] ECS Fargate capacity approved
- [ ] RDS instance size approved
- [ ] Bedrock access approved
- [ ] Budget approved
- [ ] Security review completed
- [ ] Compliance requirements met
- [ ] Region selected
- [ ] Timeline agreed upon

---

**Prepared for**: AWS Infrastructure Provisioning Team  
**Project**: Multi-Agent Orchestrator  
**Date**: [Current Date]  
**Priority**: High

