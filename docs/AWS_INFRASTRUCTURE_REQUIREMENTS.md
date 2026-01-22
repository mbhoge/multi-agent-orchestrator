# AWS Infrastructure Requirements for Multi-Agent Orchestrator

This document provides a comprehensive list of AWS services required to provision and run the Multi-Agent Orchestrator project in the AWS environment.

## Executive Summary

The Multi-Agent Orchestrator requires the following AWS services to operate:
- **Compute**: Amazon ECS (Fargate) for containerized services
- **Networking**: VPC, Load Balancer, NAT Gateway, Security Groups
- **Storage**: ECR for container images, S3 for Terraform state
- **AI/ML**: Amazon Bedrock for Agent Core Runtime SDK
- **Database**: RDS PostgreSQL (or ECS-hosted) for Langfuse
- **Security**: IAM roles and policies, Secrets Manager
- **Monitoring**: CloudWatch Logs, Metrics, and Container Insights
- **Service Discovery**: ECS Service Discovery for inter-service communication

---

## 1. COMPUTE SERVICES

### 1.1 Amazon Elastic Container Service (ECS) - Fargate

**Service**: Amazon ECS with Fargate launch type

**Purpose**: 
- Hosts all containerized services (AWS Agent Core, LangGraph, Snowflake Cortex Agents, Langfuse)
- Provides serverless container execution without managing EC2 instances
- Enables automatic scaling and high availability

**Reasoning**:
- The project uses Docker containers for all components
- Fargate eliminates EC2 management overhead
- Supports multiple services running independently
- Provides built-in integration with other AWS services (Load Balancer, CloudWatch, etc.)

**Configuration Requirements**:
- ECS Cluster with Container Insights enabled
- Capacity Providers: FARGATE and FARGATE_SPOT
- Multiple ECS Services:
  - `aws-agent-core` service (2 tasks minimum)
  - `langgraph` service (2 tasks minimum)
  - `snowflake-cortex` service (3 tasks minimum)
- Task Definitions with CPU/Memory specifications:
  - AWS Agent Core: 1024 CPU units, 2048 MB memory
  - LangGraph: 1024 CPU units, 2048 MB memory
  - Snowflake Cortex: 1024 CPU units, 2048 MB memory

**Estimated Cost**: ~$50-150/month (depending on usage and task count)

---

## 2. NETWORKING SERVICES

### 2.1 Amazon Virtual Private Cloud (VPC)

**Service**: Amazon VPC

**Purpose**:
- Isolated network environment for all project resources
- Enables secure communication between services
- Provides network segmentation and security boundaries

**Reasoning**:
- All ECS tasks need to run in a private network
- Required for security best practices
- Enables control over network traffic flow
- Supports both public and private subnets

**Configuration Requirements**:
- CIDR block: `/16` (e.g., `10.0.0.0/16`)
- DNS hostnames and DNS support enabled
- Multiple Availability Zones for high availability

---

### 2.2 Subnets

**Service**: VPC Subnets (Public and Private)

**Purpose**:
- Public subnets: Host Load Balancer and NAT Gateways
- Private subnets: Host ECS tasks (no direct internet access)

**Reasoning**:
- Security: ECS tasks should not have public IPs
- Load Balancer needs internet access for incoming traffic
- NAT Gateway in public subnet allows outbound internet from private subnets

**Configuration Requirements**:
- 2 Public subnets (one per Availability Zone)
- 2 Private subnets (one per Availability Zone)
- Proper CIDR allocation within VPC

---

### 2.3 Internet Gateway

**Service**: Internet Gateway (IGW)

**Purpose**:
- Provides internet access for resources in public subnets
- Enables Load Balancer to receive traffic from internet

**Reasoning**:
- Required for public-facing Load Balancer
- Enables outbound internet connectivity from public subnets

---

### 2.4 NAT Gateway

**Service**: NAT Gateway (2 instances for high availability)

**Purpose**:
- Allows ECS tasks in private subnets to access internet
- Required for: downloading Docker images, accessing Snowflake, calling external APIs

**Reasoning**:
- ECS tasks need internet access for:
  - Pulling container images from ECR
  - Connecting to Snowflake (external service)
  - Accessing Langfuse API (if external)
  - Downloading Python packages during container startup
- High availability: One NAT Gateway per Availability Zone

**Estimated Cost**: ~$32-64/month per NAT Gateway (data transfer charges additional)

---

### 2.5 Route Tables

**Service**: VPC Route Tables

**Purpose**:
- Public Route Table: Routes traffic from public subnets to Internet Gateway
- Private Route Tables: Routes traffic from private subnets to NAT Gateways

**Reasoning**:
- Controls traffic flow within VPC
- Ensures proper routing for internet access

---

### 2.6 Security Groups

**Service**: Security Groups

**Purpose**:
- Controls inbound and outbound traffic to resources
- Implements network-level security

**Reasoning**:
- Load Balancer Security Group: Allows HTTP/HTTPS from internet
- ECS Service Security Group: Allows traffic from Load Balancer and inter-service communication
- Restricts unnecessary access

**Configuration Requirements**:
- ALB Security Group:
  - Inbound: Port 80 (HTTP), Port 443 (HTTPS) from allowed CIDR blocks
  - Outbound: All traffic
- ECS Security Group:
  - Inbound: Ports 8000-8002 from ALB Security Group
  - Inbound: Ports 8000-8002 from itself (inter-service communication)
  - Outbound: All traffic (for Snowflake, external APIs)

---

### 2.7 Application Load Balancer (ALB)

**Service**: Application Load Balancer

**Purpose**:
- Distributes incoming traffic to ECS tasks
- Provides health checks and automatic failover
- Enables SSL/TLS termination (if HTTPS is configured)

**Reasoning**:
- Single entry point for external traffic
- Load balancing across multiple ECS tasks
- Health checks ensure only healthy tasks receive traffic
- Required for high availability

**Configuration Requirements**:
- Internet-facing Load Balancer
- HTTP listener on port 80
- Target Group for AWS Agent Core service (port 8000)
- Health check path: `/health`
- Cross-zone load balancing enabled

**Estimated Cost**: ~$16-20/month + data transfer charges

---

### 2.8 ECS Service Discovery

**Service**: AWS Cloud Map (Service Discovery)

**Purpose**:
- Enables service-to-service communication using DNS names
- Allows services to discover each other dynamically

**Reasoning**:
- LangGraph needs to call Snowflake Cortex Agent Gateway
- Services can find each other by name instead of hardcoded IPs
- Simplifies inter-service communication

**Configuration Requirements**:
- Private DNS namespace: `multi-agent-orchestrator.local`
- Service Discovery services for:
  - `aws-agent-core`
  - `langgraph`
  - `snowflake-cortex`

**Estimated Cost**: ~$0.50/month per service

---

## 3. STORAGE SERVICES

### 3.1 Amazon Elastic Container Registry (ECR)

**Service**: Amazon ECR

**Purpose**:
- Stores Docker container images for all services
- Provides secure, scalable image storage
- Enables image scanning for vulnerabilities

**Reasoning**:
- ECS needs to pull container images to run tasks
- Centralized image management
- Image versioning and lifecycle management
- Security scanning capabilities

**Configuration Requirements**:
- 3 ECR repositories:
  - `multi-agent-orchestrator-dev-aws-agent-core`
  - `multi-agent-orchestrator-dev-langgraph`
  - `multi-agent-orchestrator-dev-snowflake-cortex`
- Image scanning on push enabled
- Lifecycle policy: Keep last 10 images
- Encryption: AES256

**Estimated Cost**: ~$0.10 per GB/month for storage + data transfer

---

### 3.2 Amazon S3

**Service**: Amazon S3

**Purpose**:
- Stores Terraform state files
- Potentially stores configuration files, logs, or backups

**Reasoning**:
- Terraform requires remote state storage
- S3 provides versioning and encryption
- Cost-effective for storing state files

**Configuration Requirements**:
- S3 bucket for Terraform state
- Versioning enabled
- Encryption enabled
- Lifecycle policies (optional)

**Estimated Cost**: ~$0.023 per GB/month (minimal for state files)

---

## 4. AI/ML SERVICES

### 4.1 Amazon Bedrock

**Service**: Amazon Bedrock

**Purpose**:
- Provides AWS Agent Core Runtime SDK functionality
- Enables invocation of Bedrock foundation models
- Supports agent orchestration capabilities

**Reasoning**:
- The project uses AWS Agent Core Runtime SDK
- Required for `bedrock-runtime:InvokeAgent` API calls
- Enables integration with Bedrock foundation models
- Provides observability and tracing capabilities

**Configuration Requirements**:
- Bedrock access enabled in the AWS account
- Appropriate IAM permissions for Bedrock APIs:
  - `bedrock:InvokeModel`
  - `bedrock:InvokeModelWithResponseStream`
  - `bedrock-runtime:InvokeAgent`
  - `bedrock-runtime:InvokeModel`
  - `bedrock-runtime:InvokeModelWithResponseStream`
- Model access permissions (if using specific models)

**Estimated Cost**: Pay-per-use based on model invocations (varies by model)

---

## 5. DATABASE SERVICES

### 5.1 Amazon RDS PostgreSQL (Option 1 - Recommended)

**Service**: Amazon RDS for PostgreSQL

**Purpose**:
- Hosts Langfuse database
- Stores observability data, traces, and prompt management data

**Reasoning**:
- Langfuse requires PostgreSQL database
- RDS provides managed database service with:
  - Automated backups
  - High availability (Multi-AZ)
  - Automatic patching
  - Monitoring and alerting
- Better for production workloads

**Configuration Requirements**:
- PostgreSQL 15 or later
- Instance type: `db.t3.micro` or `db.t3.small` (minimum)
- Multi-AZ deployment (recommended for production)
- Automated backups enabled
- Security group allowing access from ECS tasks

**Estimated Cost**: ~$15-30/month (db.t3.micro) to ~$100-200/month (db.t3.small Multi-AZ)

### 5.2 ECS-Hosted PostgreSQL (Option 2 - Alternative)

**Service**: PostgreSQL container on ECS

**Purpose**:
- Alternative to RDS for cost savings in development
- Same functionality as RDS but self-managed

**Reasoning**:
- Lower cost for development/staging environments
- More control over configuration
- Requires more operational overhead

**Configuration Requirements**:
- PostgreSQL 15 container image
- Persistent storage via EFS or EBS
- ECS task definition for PostgreSQL

**Estimated Cost**: ~$10-20/month (ECS task costs only)

---

## 6. SECURITY & IDENTITY SERVICES

### 6.1 AWS Identity and Access Management (IAM)

**Service**: IAM Roles and Policies

**Purpose**:
- Manages permissions for ECS tasks
- Controls access to AWS services (Bedrock, ECR, CloudWatch, etc.)
- Implements least privilege security model

**Reasoning**:
- ECS tasks need permissions to:
  - Pull images from ECR
  - Write logs to CloudWatch
  - Invoke Bedrock APIs
  - Access Secrets Manager (if used)
- Separate roles for task execution and task runtime

**Configuration Requirements**:
- **ECS Task Execution Role**:
  - `AmazonECSTaskExecutionRolePolicy` (managed policy)
  - CloudWatch Logs permissions
  - ECR access permissions
- **ECS Task Role**:
  - Bedrock API permissions
  - Secrets Manager permissions (if used)
  - Any other application-specific permissions

---

### 6.2 AWS Secrets Manager (Optional but Recommended)

**Service**: AWS Secrets Manager

**Purpose**:
- Securely stores sensitive credentials:
  - Snowflake credentials
  - Langfuse API keys
  - Database passwords
  - Other secrets

**Reasoning**:
- Best practice for credential management
- Automatic rotation capabilities
- Encrypted at rest
- Audit trail via CloudTrail
- Avoids hardcoding credentials in environment variables

**Configuration Requirements**:
- Secrets for:
  - Snowflake credentials
  - Langfuse keys
  - Database credentials
- IAM permissions for ECS tasks to read secrets

**Estimated Cost**: ~$0.40 per secret/month + $0.05 per 10,000 API calls

---

### 6.3 AWS Systems Manager Parameter Store (Alternative)

**Service**: SSM Parameter Store

**Purpose**:
- Alternative to Secrets Manager for non-sensitive configuration
- Stores configuration parameters

**Reasoning**:
- Lower cost than Secrets Manager
- Suitable for non-sensitive configuration
- Can be used alongside Secrets Manager

**Estimated Cost**: Free for Standard parameters, ~$0.05 per Advanced parameter/month

---

## 7. MONITORING & OBSERVABILITY SERVICES

### 7.1 Amazon CloudWatch Logs

**Service**: CloudWatch Logs

**Purpose**:
- Centralized logging for all ECS tasks
- Log aggregation and retention
- Enables log analysis and troubleshooting

**Reasoning**:
- All services generate logs that need to be collected
- Required for debugging and monitoring
- Integration with ECS is seamless
- Enables log-based alerting

**Configuration Requirements**:
- Log Groups for each service:
  - `/ecs/multi-agent-orchestrator-dev-aws-agent-core`
  - `/ecs/multi-agent-orchestrator-dev-langgraph`
  - `/ecs/multi-agent-orchestrator-dev-snowflake-cortex`
- Log retention: 7-30 days (configurable)
- Log streaming from ECS tasks

**Estimated Cost**: ~$0.50 per GB ingested + $0.03 per GB stored/month

---

### 7.2 Amazon CloudWatch Metrics

**Service**: CloudWatch Metrics

**Purpose**:
- Collects performance metrics from ECS tasks
- Tracks CPU, memory, network usage
- Custom application metrics

**Reasoning**:
- Required for monitoring service health
- Enables auto-scaling based on metrics
- Performance optimization insights

**Configuration Requirements**:
- ECS Container Insights enabled
- Custom metrics from applications
- Metric retention: 15 months (standard)

**Estimated Cost**: First 10 custom metrics free, then $0.30 per metric/month

---

### 7.3 Amazon CloudWatch Container Insights

**Service**: CloudWatch Container Insights

**Purpose**:
- Provides detailed container and task-level metrics
- Performance monitoring for ECS tasks
- Resource utilization tracking

**Reasoning**:
- Enhanced visibility into container performance
- Helps with capacity planning
- Identifies performance bottlenecks

**Configuration Requirements**:
- Enabled at ECS cluster level
- Automatic metric collection

**Estimated Cost**: Included with CloudWatch Metrics

---

### 7.4 Amazon CloudWatch Alarms (Optional)

**Service**: CloudWatch Alarms

**Purpose**:
- Alerts on service health issues
- Notifications for critical events

**Reasoning**:
- Proactive issue detection
- Enables rapid response to problems

**Configuration Requirements**:
- Alarms for:
  - High CPU utilization
  - High memory usage
  - Task failures
  - Health check failures

**Estimated Cost**: $0.10 per alarm/month

---

## 8. ADDITIONAL SERVICES

### 8.1 AWS Certificate Manager (ACM) - Optional but Recommended

**Service**: AWS Certificate Manager

**Purpose**:
- Provides SSL/TLS certificates for HTTPS
- Free SSL certificates for Load Balancer

**Reasoning**:
- Security best practice
- Required for HTTPS on Load Balancer
- Free managed certificates

**Configuration Requirements**:
- Certificate for domain (if using custom domain)
- Certificate attached to Load Balancer listener

**Estimated Cost**: Free

---

### 8.2 Amazon Route 53 - Optional

**Service**: Amazon Route 53

**Purpose**:
- DNS management for custom domain
- Health checks and DNS failover

**Reasoning**:
- Required if using custom domain name
- Provides DNS resolution for Load Balancer

**Configuration Requirements**:
- Hosted zone for domain
- A record pointing to Load Balancer

**Estimated Cost**: ~$0.50 per hosted zone/month + $0.40 per million queries

---

### 8.3 AWS CloudTrail - Recommended

**Service**: AWS CloudTrail

**Purpose**:
- Logs all API calls and actions
- Security auditing and compliance

**Reasoning**:
- Security best practice
- Required for audit trails
- Helps with troubleshooting

**Configuration Requirements**:
- CloudTrail enabled for the AWS account
- Logs stored in S3

**Estimated Cost**: First trail free, then $2 per 100,000 events

---

## 9. EXTERNAL DEPENDENCIES (Not AWS Services)

### 9.1 Snowflake Account

**Service**: Snowflake (External)

**Purpose**:
- Data warehouse for structured data queries
- Cortex AI Analyst and Search functionality
- Storage for semantic models

**Reasoning**:
- Core component of the system
- Provides Cortex AI capabilities
- Not an AWS service but required for the project

**Requirements**:
- Snowflake account with Cortex AI enabled
- Appropriate warehouse, database, and schema
- Network connectivity from AWS to Snowflake

---

### 9.2 Langfuse Account (If External)

**Service**: Langfuse (External SaaS or Self-Hosted)

**Purpose**:
- Observability and prompt management
- Can be self-hosted on ECS or external SaaS

**Reasoning**:
- Required for LangGraph observability
- Prompt management functionality
- Can run on ECS or use external service

---

## 10. SERVICE DEPENDENCIES MATRIX

| Component | Required AWS Services | Purpose |
|-----------|----------------------|---------|
| **AWS Agent Core** | ECS Fargate, ECR, ALB, CloudWatch, IAM, Bedrock | Container hosting, image storage, load balancing, monitoring, AI capabilities |
| **LangGraph** | ECS Fargate, ECR, CloudWatch, IAM, Service Discovery | Container hosting, monitoring, inter-service communication |
| **Snowflake Cortex** | ECS Fargate, ECR, CloudWatch, IAM, NAT Gateway, Service Discovery | Container hosting, monitoring, external connectivity to Snowflake |
| **Langfuse** | ECS Fargate (or RDS), ECR, CloudWatch, IAM | Container hosting, database (if self-hosted), monitoring |
| **FastAPI** | ECS Fargate, ALB | All services use FastAPI, hosted on ECS |
| **Docker** | ECR, ECS | Container images stored in ECR, executed on ECS |

---

## 11. COST ESTIMATION SUMMARY

### Monthly Cost Estimate (Development Environment)

| Service Category | Estimated Monthly Cost |
|-----------------|----------------------|
| ECS Fargate (7 tasks) | $50-150 |
| NAT Gateway (2) | $64-128 |
| Application Load Balancer | $16-20 |
| RDS PostgreSQL (db.t3.micro) | $15-30 |
| ECR Storage | $1-5 |
| CloudWatch Logs | $5-20 |
| CloudWatch Metrics | $0-10 |
| S3 (Terraform state) | $0.10 |
| Secrets Manager | $1-2 |
| **Total Estimated** | **$152-374/month** |

### Monthly Cost Estimate (Production Environment)

| Service Category | Estimated Monthly Cost |
|-----------------|----------------------|
| ECS Fargate (scaled) | $200-500 |
| NAT Gateway (2) | $64-128 |
| Application Load Balancer | $16-20 |
| RDS PostgreSQL (Multi-AZ) | $100-200 |
| ECR Storage | $5-10 |
| CloudWatch Logs | $20-50 |
| CloudWatch Metrics | $10-30 |
| S3 | $1-5 |
| Secrets Manager | $2-5 |
| Bedrock API calls | Variable (pay-per-use) |
| **Total Estimated** | **$418-958/month + Bedrock costs** |

*Note: Costs vary based on usage, region, and actual resource consumption*

---

## 12. PROVISIONING CHECKLIST

### Infrastructure Team Should Provision:

- [ ] **VPC** with CIDR block `/16`
- [ ] **2 Public Subnets** (one per AZ)
- [ ] **2 Private Subnets** (one per AZ)
- [ ] **Internet Gateway**
- [ ] **2 NAT Gateways** (one per AZ)
- [ ] **Route Tables** (1 public, 2 private)
- [ ] **Security Groups** (ALB, ECS)
- [ ] **Application Load Balancer** (internet-facing)
- [ ] **Target Group** for AWS Agent Core service
- [ ] **ECS Cluster** with Container Insights
- [ ] **ECS Capacity Providers** (FARGATE, FARGATE_SPOT)
- [ ] **3 ECR Repositories** (aws-agent-core, langgraph, snowflake-cortex)
- [ ] **ECS Task Execution Role** with required policies
- [ ] **ECS Task Role** with Bedrock permissions
- [ ] **CloudWatch Log Groups** (3 groups)
- [ ] **Service Discovery Namespace** and services
- [ ] **RDS PostgreSQL** instance (or ECS task)
- [ ] **S3 Bucket** for Terraform state
- [ ] **Secrets Manager** secrets (optional)
- [ ] **Bedrock Access** enabled in account
- [ ] **IAM Permissions** for Bedrock APIs

### Configuration Required:

- [ ] ECS Task Definitions (3 definitions)
- [ ] ECS Services (3 services)
- [ ] Load Balancer Listener configuration
- [ ] Security Group rules
- [ ] CloudWatch Log retention policies
- [ ] ECR Lifecycle policies
- [ ] Service Discovery configuration

---

## 13. NETWORK CONNECTIVITY REQUIREMENTS

### Outbound Connections Required:

1. **From ECS Tasks to Internet** (via NAT Gateway):
   - Snowflake API endpoints
   - External Langfuse (if not self-hosted)
   - Python package repositories (PyPI)
   - Docker Hub (if pulling base images)

2. **From ECS Tasks to AWS Services**:
   - ECR (for pulling images)
   - CloudWatch Logs (for log streaming)
   - Bedrock API endpoints
   - Secrets Manager (if used)
   - S3 (if used for storage)

3. **From Load Balancer**:
   - Internet (for receiving traffic)

### Inbound Connections:

1. **To Load Balancer**:
   - HTTP/HTTPS from internet (port 80/443)

2. **To ECS Tasks** (from Load Balancer):
   - Port 8080 (AWS Agent Core)
   - Port 8001 (LangGraph)
   - Port 8002 (Snowflake Cortex)

---

## 14. SECURITY CONSIDERATIONS

### Network Security:
- ECS tasks run in private subnets (no direct internet access)
- Security groups restrict traffic to necessary ports only
- Load Balancer in public subnet with restricted access

### Access Control:
- IAM roles follow least privilege principle
- Separate roles for task execution and runtime
- Bedrock access restricted to specific APIs

### Data Security:
- Secrets stored in Secrets Manager (encrypted)
- ECR images encrypted at rest
- RDS encryption enabled
- CloudWatch Logs encrypted

### Compliance:
- CloudTrail enabled for audit trails
- All actions logged and traceable

---

## 15. SCALABILITY CONSIDERATIONS

### Auto-Scaling:
- ECS Service Auto Scaling can be configured based on:
  - CPU utilization
  - Memory utilization
  - Request count (via ALB metrics)
  - Custom CloudWatch metrics

### High Availability:
- Services distributed across 2 Availability Zones
- NAT Gateways in each AZ
- RDS Multi-AZ deployment (production)
- Load Balancer with health checks

### Capacity Planning:
- Initial: 2-3 tasks per service
- Can scale to 10+ tasks per service based on load
- Fargate supports up to 120 vCPU and 512 GB memory per task

---

## 16. MONITORING & ALERTING REQUIREMENTS

### Key Metrics to Monitor:
- ECS Task CPU and Memory utilization
- Request count and latency (via ALB)
- Error rates
- Bedrock API call success/failure rates
- Database connection pool usage
- Log error rates

### Recommended Alarms:
- High CPU utilization (>80%)
- High memory utilization (>80%)
- Task failures
- Health check failures
- Database connection failures
- Bedrock API errors

---

## 17. DISASTER RECOVERY & BACKUP

### Backup Requirements:
- RDS automated backups (7-35 days retention)
- ECR image versioning
- Terraform state in S3 with versioning
- CloudWatch Logs retention

### Recovery Procedures:
- RDS point-in-time recovery
- ECS service rollback to previous task definition
- ECR image rollback capability

---

## 18. REGION SELECTION

### Recommended Regions:
- **Primary**: `us-east-1` (N. Virginia) - Best service availability
- **Alternative**: `us-west-2` (Oregon), `eu-west-1` (Ireland)

### Considerations:
- Bedrock model availability varies by region
- Snowflake region should be close to AWS region for low latency
- Cost may vary by region

---

## 19. COMPLIANCE & GOVERNANCE

### Required for Compliance:
- CloudTrail for audit logging
- IAM access logging
- Resource tagging for cost allocation
- Encryption at rest and in transit
- VPC Flow Logs (optional but recommended)

---

## 20. SUPPORT & MAINTENANCE

### AWS Support Plan:
- **Development**: Basic Support (included)
- **Production**: Business or Enterprise Support (recommended)

### Maintenance Windows:
- RDS maintenance windows
- ECS service updates during low-traffic periods
- Regular security patching

---

## CONCLUSION

This multi-agent orchestrator project requires a comprehensive AWS infrastructure setup including compute, networking, storage, AI/ML, database, security, and monitoring services. The architecture is designed for scalability, high availability, and security.

**Key Takeaways for Infrastructure Team:**
1. Primary services: ECS Fargate, VPC, ALB, ECR, RDS, Bedrock
2. Estimated monthly cost: $150-400 (dev) to $400-1000 (prod)
3. All services should be provisioned in the same region
4. Network connectivity to Snowflake is critical
5. Bedrock access must be enabled and properly configured

**Next Steps:**
1. Review and approve this infrastructure plan
2. Provision services in order: VPC → ECR → ECS → ALB → RDS → Monitoring
3. Configure IAM roles and policies
4. Set up CloudWatch monitoring
5. Test connectivity and service integration

For detailed Terraform configurations, refer to `infrastructure/terraform/` directory in the project.

