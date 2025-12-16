# AWS Documentation References for Multi-Agent Orchestrator

## Important Clarification

The string `"aws_agent_core.api.main:app"` in your `uvicorn.run()` call is **NOT** an AWS-specific pattern. It's a standard **Uvicorn/FastAPI** pattern for specifying the application location.

### What `"aws_agent_core.api.main:app"` Means

- **Format**: `"module.path:variable_name"`
- **Purpose**: Tells Uvicorn where to find your FastAPI app instance
- **Standard**: This is a Python/Uvicorn convention, not AWS-specific

**Documentation:**
- [Uvicorn - Application](https://www.uvicorn.org/#application)
- [FastAPI - Run Server](https://fastapi.tiangolo.com/deployment/server/)

---

## AWS Bedrock Agent Core Runtime SDK Documentation

Your project uses AWS Bedrock Agent Core Runtime SDK via boto3. Here are the relevant AWS documentation references:

### 1. AWS Bedrock Agent Core Developer Guide

**Main Documentation:**
- **URL**: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/
- **Description**: Complete developer guide for AWS Bedrock Agent Core
- **Sections**:
  - Getting Started
  - Runtime Overview
  - Invoking Agents
  - Memory Management
  - Tools and Gateways
  - Observability

### 2. AWS Bedrock Agent Core Runtime SDK (Python)

**GitHub Repository:**
- **URL**: https://github.com/aws/bedrock-agentcore-sdk-python
- **Description**: Official Python SDK for AWS Bedrock Agent Core
- **Installation**: `pip install bedrock-agentcore`

**User Guide:**
- **URL**: https://aws.github.io/bedrock-agentcore-starter-toolkit/
- **Description**: Comprehensive guide for using the SDK
- **Key Topics**:
  - Runtime Overview
  - Entrypoint Decorator (`@app.entrypoint`)
  - Memory Management
  - Tools Integration
  - Deployment

### 3. Boto3 Bedrock Agent Runtime Client

**API Reference:**
- **URL**: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-agent-runtime.html
- **Description**: Boto3 client for invoking Bedrock agents
- **Your Usage**: You're using `bedrock-agent-runtime` client (not `bedrock-agentcore`)

**Key Methods:**
- `invoke_agent()` - Invoke a Bedrock agent
- `invoke_agent_runtime()` - Invoke Agent Core runtime (newer API)

**Documentation:**
- **Invoke Agent**: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-agent-runtime/client/invoke_agent.html
- **Invoke Agent Runtime**: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-agentcore/client/invoke_agent_runtime.html

### 4. AWS Bedrock Agent Core Starter Toolkit

**Documentation:**
- **URL**: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-get-started-toolkit.html
- **GitHub**: https://github.com/aws/bedrock-agentcore-starter-toolkit
- **Description**: CLI toolkit for creating and deploying agents

**Key Commands:**
- `agentcore create` - Create a new agent
- `agentcore deploy` - Deploy agent to AWS
- `agentcore invoke` - Test your agent

---

## How Your Code Relates to AWS Documentation

### Current Implementation

Your code uses **boto3's `bedrock-agent-runtime` client**:

```python
# shared/config/aws_config.py
def get_bedrock_agent_core_client(aws_settings: AWSSettings):
    session = get_boto3_session(aws_settings)
    return session.client("bedrock-agent-runtime")  # ← This is boto3 client
```

**Documentation Reference:**
- https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-agent-runtime.html

### Alternative: Bedrock Agent Core SDK

If you want to use the newer **Bedrock Agent Core SDK** (with `@app.entrypoint`):

```python
from bedrock_agentcore import BedrockAgentCoreApp

app = BedrockAgentCoreApp()

@app.entrypoint
def my_agent(payload):
    return {"result": "response"}
```

**Documentation Reference:**
- https://aws.github.io/bedrock-agentcore-starter-toolkit/user-guide/runtime/overview.html

---

## Key AWS Documentation Links

### Core Services

1. **AWS Bedrock Agent Core Developer Guide**
   - https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/

2. **AWS Bedrock Agent Runtime API Reference**
   - https://docs.aws.amazon.com/bedrock/latest/APIReference/API_agent-runtime_InvokeAgent.html

3. **Boto3 Bedrock Agent Runtime**
   - https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-agent-runtime.html

### SDKs and Tools

4. **Bedrock Agent Core Python SDK**
   - GitHub: https://github.com/aws/bedrock-agentcore-sdk-python
   - User Guide: https://aws.github.io/bedrock-agentcore-starter-toolkit/

5. **Bedrock Agent Core Starter Toolkit**
   - GitHub: https://github.com/aws/bedrock-agentcore-starter-toolkit
   - Docs: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-get-started-toolkit.html

### Related Services

6. **AWS Bedrock (General)**
   - https://docs.aws.amazon.com/bedrock/

7. **Amazon Bedrock Runtime API**
   - https://docs.aws.amazon.com/bedrock/latest/APIReference/

---

## Understanding the Difference

### Your Current Setup (boto3 bedrock-agent-runtime)

```python
# You're using boto3 to invoke agents
client = boto3.client("bedrock-agent-runtime")
response = client.invoke_agent(
    agentId=agent_id,
    agentAliasId=agent_alias_id,
    sessionId=session_id,
    inputText=input_text
)
```

**Documentation**: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-agent-runtime/client/invoke_agent.html

### Alternative: Bedrock Agent Core SDK

```python
# This would be for BUILDING agents, not invoking them
from bedrock_agentcore import BedrockAgentCoreApp

app = BedrockAgentCoreApp()

@app.entrypoint
def my_agent(payload):
    # Your agent logic
    return {"result": "response"}
```

**Documentation**: https://aws.github.io/bedrock-agentcore-starter-toolkit/user-guide/runtime/overview.html

---

## Summary

1. **`aws_agent_core.api.main:app`** → Standard Uvicorn pattern (not AWS-specific)
   - Uvicorn docs: https://www.uvicorn.org/#application

2. **Your AWS Integration** → Uses boto3 `bedrock-agent-runtime` client
   - Boto3 docs: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-agent-runtime.html

3. **Alternative SDK** → Bedrock Agent Core SDK (for building agents)
   - SDK docs: https://aws.github.io/bedrock-agentcore-starter-toolkit/

---

## Quick Reference

| What You're Looking For | Documentation Link |
|------------------------|-------------------|
| Uvicorn app string format | https://www.uvicorn.org/#application |
| Boto3 bedrock-agent-runtime | https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-agent-runtime.html |
| Bedrock Agent Core SDK | https://aws.github.io/bedrock-agentcore-starter-toolkit/ |
| AWS Bedrock Agent Core Guide | https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/ |
| Invoke Agent API | https://docs.aws.amazon.com/bedrock/latest/APIReference/API_agent-runtime_InvokeAgent.html |
