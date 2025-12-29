# Microsoft Teams Integration Guide

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Reference Materials](#reference-materials)
4. [Prerequisites](#prerequisites)
5. [Step-by-Step Integration](#step-by-step-integration)
6. [Configuration](#configuration)
7. [Testing](#testing)
8. [Troubleshooting](#troubleshooting)

---

## Overview

The Multi-Agent Orchestrator integrates with Microsoft Teams using **Outgoing Webhooks** to enable conversational AI interactions directly within Teams channels. Users can @mention the webhook in a channel to query the orchestrator's AI agents (Snowflake Cortex AI Analyst, Search, etc.) through natural language messages.

### Key Features

- **Natural Language Queries**: Users can @mention the webhook in Teams channels to ask questions
- **Simple Integration**: Outgoing webhooks are simpler to set up than Bot Framework
- **HMAC Security**: Webhook requests are verified using HMAC signatures
- **Multi-Agent Routing**: Automatically routes queries to appropriate Snowflake Cortex AI agents
- **Error Handling**: User-friendly error messages
- **Serverless Architecture**: Runs on AWS Lambda with API Gateway for automatic scaling

---

## Architecture

### Integration Flow

```
┌─────────────────────────────────────────────────────────────┐
│  Microsoft Teams Client                                     │
│  (Channel - User @mentions webhook)                        │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        │ HTTPS POST (Outgoing Webhook)
                        │ (HTTP POST /api/teams/webhook)
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  AWS API Gateway (HTTP API v2)                             │
│  - Routes POST /api/teams/webhook                           │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        │ Lambda Invoke
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  Teams Webhook Handler Lambda                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  - Verifies HMAC signature                            │  │
│  │  - Parses Teams webhook payload                        │  │
│  │  - Transforms to AgentRequest                         │  │
│  └───────────────────┬──────────────────────────────────┘  │
└───────────────────────┼─────────────────────────────────────┘
                        │
                        │ AgentRequest
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  MultiAgentOrchestrator                                     │
│  → LangGraph Supervisor                                      │
│  → Snowflake Cortex Agents                                   │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        │ AgentResponse
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  Teams Webhook Handler Lambda                               │
│  - Formats response for Teams (text/JSON)                  │
│  - Returns via API Gateway                                  │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  Microsoft Teams Channel                                    │
│  (Response displayed in channel)                            │
└─────────────────────────────────────────────────────────────┘
```

### Components

1. **Lambda Handler** (`aws_agent_core/lambda_handlers/teams_webhook_handler.py`)
   - Handles Teams outgoing webhook requests
   - Verifies HMAC signatures
   - Transforms Teams webhook payloads ↔ AgentRequest/Response

2. **API Gateway Route**
   - `POST /api/teams/webhook`: Outgoing webhook endpoint

3. **Configuration** (`shared/config/settings.py`)
   - `TeamsSettings`: Teams webhook secret for HMAC verification

---

## Reference Materials

### Official Microsoft Documentation

1. **Outgoing Webhooks**
   - [Add an outgoing webhook to a team in Microsoft Teams](https://learn.microsoft.com/en-us/microsoftteams/platform/webhooks-and-connectors/how-to/add-outgoing-webhook)
   - [Outgoing Webhooks Overview](https://learn.microsoft.com/en-us/microsoftteams/platform/webhooks-and-connectors/how-to/add-outgoing-webhook)

2. **Webhook Security**
   - [Webhook Authentication](https://learn.microsoft.com/en-us/microsoftteams/platform/webhooks-and-connectors/how-to/add-outgoing-webhook#security-considerations)
   - HMAC signature verification for webhook requests

3. **AWS Lambda Integration**
   - [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
   - [API Gateway HTTP API](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api.html)

### Additional Resources

- [Teams Webhooks and Connectors](https://learn.microsoft.com/en-us/microsoftteams/platform/webhooks-and-connectors/what-are-webhooks-and-connectors)
- [AWS Lambda Python Runtime](https://docs.aws.amazon.com/lambda/latest/dg/lambda-python.html)

---

## Prerequisites

### 1. AWS Account

- Active AWS account with appropriate permissions
- Access to AWS Console

### 2. Microsoft Teams Access

- Teams admin permissions to create outgoing webhooks in channels
- Or channel owner permissions (for channel-specific webhooks)

### 3. Application Requirements

- Python 3.11+ (for Lambda runtime)
- AWS CLI configured
- Terraform installed (for infrastructure deployment)

### 4. AWS Services

- AWS Lambda (for function execution)
- API Gateway (HTTP API v2)
- CloudWatch (for logging)
- IAM (for permissions)

---

## Step-by-Step Integration

> **Note**: This guide has been updated for the Lambda + API Gateway architecture. For detailed Lambda deployment instructions, see [TEAMS_INTEGRATION_LAMBDA.md](TEAMS_INTEGRATION_LAMBDA.md).

### Step 1: Deploy Lambda Functions and API Gateway

1. **Navigate to Azure Portal**
   - Go to [Azure Portal](https://portal.azure.com)
   - Sign in with your Azure account

2. **Create Azure Bot Resource**
   - Click "Create a resource"
   - Search for "Azure Bot"
   - Click "Create"
   - Fill in:
     - **Subscription**: Your Azure subscription
     - **Resource Group**: Create new or use existing
     - **Bot handle**: Unique name (e.g., `multi-agent-orchestrator-bot`)
     - **Pricing tier**: F0 (Free) for development, S1 for production
     - **Microsoft App ID**: Click "Create New" (see Step 2)
   - Click "Review + create" → "Create"

3. **Note the Bot Endpoint**
   - After creation, note the **Messaging endpoint** (you'll update this later)
   - Format: `https://your-domain.com/api/teams/webhook`

### Step 2: Register Microsoft App (Bot Registration)

1. **Go to Azure Active Directory**
   - In Azure Portal, navigate to "Azure Active Directory"
   - Click "App registrations" → "New registration"

2. **Register Application**
   - **Name**: `Multi-Agent Orchestrator Bot`
   - **Supported account types**: "Accounts in any organizational directory and personal Microsoft accounts"
   - **Redirect URI**: Leave blank for now
   - Click "Register"

3. **Save Credentials**
   - **Application (client) ID**: Copy this (this is your `TEAMS_APP_ID`)
   - Click "Certificates & secrets" → "New client secret"
   - **Description**: `Bot Secret`
   - **Expires**: Choose expiration (e.g., 24 months)
   - Click "Add"
   - **Copy the secret value immediately** (this is your `TEAMS_APP_PASSWORD`)
   - ⚠️ **Important**: You cannot view this value again after leaving the page

4. **Configure API Permissions** (Optional, for advanced features)
   - Go to "API permissions"
   - Add permissions as needed (e.g., Microsoft Graph)

### Step 3: Configure Bot in Azure Bot Service

1. **Link App Registration to Bot**
   - Go back to your Azure Bot resource
   - Under "Configuration", set:
     - **Microsoft App ID**: The Application ID from Step 2
     - **Microsoft App Password**: The secret value from Step 2
   - Click "Apply"

2. **Set Messaging Endpoint**
   - **Messaging endpoint**: `https://your-domain.com/api/teams/webhook`
   - ⚠️ Must be HTTPS
   - Click "Apply"

### Step 4: Configure Teams Channel

1. **Enable Teams Channel**
   - In your Azure Bot resource, go to "Channels"
   - Click "Microsoft Teams" → "Apply"

2. **Configure Teams Settings** (Optional)
   - **Calling Webhook**: Leave blank unless using calling features
   - **Enable calling**: Toggle if needed

### Step 5: Create Teams App Manifest

1. **Download Teams App Manifest Template**
   - Use [App Studio](https://docs.microsoft.com/en-us/microsoftteams/platform/concepts/build-and-test/app-studio-overview) or create manually
   - Or use the provided template (see below)

2. **Create `manifest.json`**:
```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/teams/v1.16/MicrosoftTeams.schema.json",
  "manifestVersion": "1.16",
  "version": "1.0.0",
  "id": "YOUR-APP-ID-HERE",
  "packageName": "com.yourcompany.multiaagentorchestrator",
  "developer": {
    "name": "Your Company",
    "websiteUrl": "https://your-domain.com",
    "privacyUrl": "https://your-domain.com/privacy",
    "termsOfUseUrl": "https://your-domain.com/terms"
  },
  "name": {
    "short": "Multi-Agent Orchestrator",
    "full": "Multi-Agent Orchestrator Bot"
  },
  "description": {
    "short": "AI-powered data query bot",
    "full": "Query your data using AI agents through natural language in Microsoft Teams"
  },
  "icons": {
    "outline": "icon-outline.png",
    "color": "icon-color.png"
  },
  "accentColor": "#0078D4",
  "bots": [
    {
      "botId": "YOUR-APP-ID-HERE",
      "scopes": ["personal", "team", "groupchat"],
      "commandLists": [
        {
          "scopes": ["personal", "team", "groupchat"],
          "commands": [
            {
              "title": "help",
              "description": "Show help information"
            }
          ]
        }
      ]
    }
  ],
  "permissions": ["identity", "messageTeamMembers"],
  "validDomains": ["your-domain.com"]
}
```

3. **Replace Placeholders**
   - `YOUR-APP-ID-HERE`: Your Microsoft App ID from Step 2
   - `your-domain.com`: Your bot's domain
   - Update icons, URLs, and descriptions

### Step 6: Install Bot in Teams

1. **Upload App to Teams** (Development)
   - Open Microsoft Teams
   - Click "Apps" (left sidebar)
   - Click "Upload a custom app" (bottom)
   - Select your `manifest.json` and icon files
   - Click "Add"

2. **Or Publish to App Store** (Production)
   - Follow [Teams app publishing guide](https://docs.microsoft.com/en-us/microsoftteams/platform/concepts/deploy-and-publish/apps-publish)

### Step 7: Configure Application Environment

1. **Update `.env` file**:
```bash
# Microsoft Teams Configuration
TEAMS_ENABLED=true
TEAMS_APP_ID=your-app-id-from-azure
TEAMS_APP_PASSWORD=your-app-password-from-azure
TEAMS_TENANT_ID=your-tenant-id  # Optional, for single-tenant
TEAMS_WEBHOOK_URL=  # Optional, for incoming webhooks
```

2. **Set Environment Variables** (if not using `.env`):
```bash
export TEAMS_ENABLED=true
export TEAMS_APP_ID="your-app-id"
export TEAMS_APP_PASSWORD="your-app-password"
```

### Step 8: Deploy Application

1. **Ensure HTTPS Endpoint**
   - Your application must be accessible via HTTPS
   - Use a reverse proxy (nginx, Traefik) or cloud load balancer
   - Or deploy to Azure App Service, AWS ECS, etc.

2. **Update Bot Messaging Endpoint**
   - In Azure Bot Service, set messaging endpoint to:
     - `https://your-domain.com/api/teams/webhook`

3. **Test Webhook**
   - Use Bot Framework Emulator or send test message in Teams

### Step 9: Verify Integration

1. **Send Test Message in Teams**
   - Open Teams
   - Find your bot in "Chats" or install in a channel
   - Send a message: "What are the total sales for last month?"

2. **Check Application Logs**
   - Verify webhook is receiving requests
   - Check for any errors

---

## Configuration

### Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `TEAMS_ENABLED` | Yes | Enable Teams integration | `true` |
| `TEAMS_APP_ID` | Yes | Microsoft App ID (Bot ID) | `12345678-1234-1234-1234-123456789abc` |
| `TEAMS_APP_PASSWORD` | Yes | Microsoft App Password (Bot Secret) | `your-secret-value` |
| `TEAMS_TENANT_ID` | No | Azure AD Tenant ID (for single-tenant) | `tenant-id-guid` |
| `TEAMS_WEBHOOK_URL` | No | Incoming webhook URL (optional) | `https://...` |

### Application Settings

The Teams configuration is managed through `shared/config/settings.py`:

```python
from shared.config.settings import settings

if settings.teams.teams_enabled:
    # Teams integration is enabled
    app_id = settings.teams.teams_app_id
    app_password = settings.teams.teams_app_password
```

---

## Testing

### 1. Local Testing with Bot Framework Emulator

1. **Install Bot Framework Emulator**
   - Download from [GitHub](https://github.com/Microsoft/BotFramework-Emulator/releases)
   - Install and launch

2. **Configure Emulator**
   - Open Emulator
   - Enter bot URL: `http://localhost:8000/api/teams/webhook`
   - For local testing, you can use placeholder credentials:
     - App ID: `00000000-0000-0000-0000-000000000000`
     - App Password: (leave blank or use placeholder)

3. **Send Test Messages**
   - Type messages in the emulator
   - Verify responses

### 2. Testing in Teams (Development)

1. **Use ngrok for Local Tunneling**
   ```bash
   # Install ngrok
   ngrok http 8000
   
   # Use the HTTPS URL in Azure Bot Service messaging endpoint
   # Example: https://abc123.ngrok.io/api/teams/webhook
   ```

2. **Update Bot Endpoint**
   - In Azure Bot Service, set messaging endpoint to ngrok URL
   - Send test message in Teams

### 3. Testing Endpoints

```bash
# Health check
curl http://localhost:8000/api/teams/webhook

# Webhook verification (GET)
curl "http://localhost:8000/api/teams/webhook?validationToken=test"

# Send test activity (POST)
curl -X POST http://localhost:8000/api/teams/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "type": "message",
    "id": "test-123",
    "text": "What are the total sales?",
    "from": {"id": "user-123", "name": "Test User"},
    "conversation": {"id": "conv-123"},
    "channelId": "msteams"
  }'
```

---

## Troubleshooting

### Common Issues

1. **Webhook Not Receiving Messages**
   - ✅ Verify HTTPS endpoint is accessible
   - ✅ Check Azure Bot Service messaging endpoint configuration
   - ✅ Verify bot is installed in Teams
   - ✅ Check application logs for errors

2. **Authentication Errors**
   - ✅ Verify `TEAMS_APP_ID` and `TEAMS_APP_PASSWORD` are correct
   - ✅ Check that app registration is linked to Azure Bot Service
   - ✅ Ensure secret hasn't expired

3. **Messages Not Appearing in Teams**
   - ✅ Verify bot has permission to send messages
   - ✅ Check that bot is added to the channel/chat
   - ✅ Review Teams activity logs in Azure Portal

4. **Adaptive Cards Not Rendering**
   - ✅ Verify Adaptive Card schema version (1.4)
   - ✅ Use [Adaptive Cards Designer](https://adaptivecards.io/designer/) to validate
   - ✅ Check Teams client version (requires modern Teams client)

### Debugging Tips

1. **Enable Debug Logging**
   ```bash
   LOG_LEVEL=DEBUG
   ```

2. **Check Application Logs**
   ```bash
   docker-compose logs -f aws-agent-core
   ```

3. **Use Bot Framework Emulator**
   - Enables local testing without Teams
   - Shows detailed request/response logs

4. **Azure Bot Service Logs**
   - In Azure Portal, go to your Bot resource
   - Check "Logs" or "Application Insights" (if configured)

---

## Next Steps

- **Enhanced Features**: Add proactive messaging, file uploads, task modules
- **Authentication**: Implement SSO for Teams users
- **Analytics**: Integrate with Application Insights for usage analytics
- **Multi-Language**: Add support for multiple languages
- **Custom Commands**: Implement slash commands (e.g., `/query`, `/help`)

---

## Additional Resources

- [Bot Framework Python SDK GitHub](https://github.com/microsoft/botbuilder-python)
- [Teams Developer Portal](https://dev.teams.microsoft.com/)
- [Adaptive Cards Samples](https://adaptivecards.io/samples/)
- [Bot Framework Samples](https://github.com/microsoft/BotBuilder-Samples)

---

## Support

For issues or questions:
1. Check [Microsoft Bot Framework Documentation](https://docs.microsoft.com/en-us/azure/bot-service/)
2. Review [Teams Platform Documentation](https://docs.microsoft.com/en-us/microsoftteams/platform/)
3. Open an issue in the project repository

