# Microsoft Teams Integration Guide (Lambda + API Gateway)

## Quick Start

This guide covers integrating Microsoft Teams with the Multi-Agent Orchestrator using **Outgoing Webhooks** and **AWS Lambda + API Gateway**.

## Architecture

```
Teams Channel → @mention webhook → API Gateway → Lambda → Orchestrator → Response
```

## Step-by-Step Integration

### Step 1: Build Lambda Deployment Packages

```bash
cd multi-agent-orchestrator
./scripts/build_lambda_packages.sh
```

This creates:
- `lambda_layer.zip` - Python dependencies
- `lambda_deployments/query_handler.zip`
- `lambda_deployments/teams_webhook_handler.zip`
- `lambda_deployments/health_handler.zip`
- `lambda_deployments/metrics_handler.zip`

### Step 2: Deploy Infrastructure with Terraform

```bash
cd infrastructure/terraform

# Initialize Terraform
terraform init

# Plan deployment
terraform plan

# Apply (creates Lambda functions, API Gateway, IAM roles)
terraform apply
```

After deployment, note the API Gateway endpoint URL from Terraform outputs:
```bash
terraform output api_gateway_stage_url
```

### Step 3: Create Outgoing Webhook in Teams

1. **Open Microsoft Teams**
   - Navigate to the channel where you want to add the webhook
   - Click the **⋯** (three dots) next to the channel name
   - Select **Connectors**

2. **Add Outgoing Webhook**
   - Search for "Outgoing Webhook"
   - Click **Configure**
   - Fill in:
     - **Name**: `Multi-Agent Orchestrator` (or your preferred name)
     - **Callback URL**: `https://<your-api-gateway-url>/api/teams/webhook`
     - **Description**: `AI-powered data query assistant`
   - Click **Create**

3. **Save Webhook Details**
   - **Webhook URL**: Copy this (you'll need it for testing)
   - **Security Token**: Copy this (this is your `TEAMS_APP_PASSWORD` for HMAC verification)
   - ⚠️ **Important**: Save the security token immediately - you cannot view it again

### Step 4: Configure Lambda Environment Variables

Set the Teams webhook secret in Lambda environment variables:

```bash
# Get the Lambda function name from Terraform output
LAMBDA_NAME=$(terraform output -raw teams_webhook_handler_name)

# Set environment variable
aws lambda update-function-configuration \
  --function-name $LAMBDA_NAME \
  --environment "Variables={TEAMS_APP_PASSWORD=your-webhook-security-token}"
```

Or use AWS Secrets Manager (recommended for production):

```bash
# Store secret in Secrets Manager
aws secretsmanager create-secret \
  --name multi-agent-orchestrator/teams-webhook-secret \
  --secret-string "your-webhook-security-token"

# Update Lambda to use Secrets Manager (requires IAM policy update)
```

### Step 5: Test the Integration

1. **Test in Teams Channel**
   - Go to the channel where you added the webhook
   - Type: `@Multi-Agent Orchestrator What are the total sales for last month?`
   - The webhook should respond with the query result

2. **Check CloudWatch Logs**
   ```bash
   # View Lambda logs
   aws logs tail /aws/lambda/multi-agent-orchestrator-teams-webhook-handler --follow
   ```

3. **Test API Gateway Endpoint Directly**
   ```bash
   # Get API Gateway URL
   API_URL=$(terraform output -raw teams_webhook_endpoint)
   
   # Test webhook endpoint
   curl -X POST $API_URL \
     -H "Content-Type: application/json" \
     -d '{
       "text": "What are the total sales?",
       "from": {"id": "user-123", "name": "Test User"},
       "channel": {"id": "channel-123", "name": "Test Channel"},
       "tenant": {"id": "tenant-123"}
     }'
   ```

## Configuration

### Lambda Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `TEAMS_APP_PASSWORD` | Yes | Webhook security token (for HMAC verification) | `your-webhook-token` |
| `LOG_LEVEL` | No | Logging level | `INFO` |

### API Gateway Configuration

The API Gateway is configured via Terraform with:
- **CORS**: Enabled for all origins (configure restrictively for production)
- **Throttling**: 50 requests/second, burst limit of 100
- **Logging**: CloudWatch Logs enabled

## Troubleshooting

### Webhook Not Responding

1. **Check Lambda Logs**
   ```bash
   aws logs tail /aws/lambda/multi-agent-orchestrator-teams-webhook-handler --follow
   ```

2. **Verify API Gateway Integration**
   - Check API Gateway logs in CloudWatch
   - Verify Lambda permissions are correct

3. **Test HMAC Verification**
   - Ensure `TEAMS_APP_PASSWORD` matches the webhook security token
   - Check Lambda environment variables

### Timeout Issues

Teams requires responses within **10 seconds**. If your queries take longer:

1. **Increase Lambda Timeout** (in Terraform):
   ```hcl
   timeout = 30  # Allow buffer beyond 10 seconds
   ```

2. **Optimize Query Processing**
   - Consider async processing for long-running queries
   - Return immediate acknowledgment and process in background

### Signature Verification Failures

If HMAC verification fails:

1. **Verify Token Match**
   - Ensure `TEAMS_APP_PASSWORD` in Lambda exactly matches the webhook security token
   - Check for extra spaces or encoding issues

2. **Check Request Body**
   - Lambda receives the raw body string
   - Ensure body is not modified before signature verification

## Security Best Practices

1. **Use AWS Secrets Manager**
   - Store webhook secrets in Secrets Manager, not environment variables
   - Rotate secrets regularly

2. **Restrict API Gateway Access**
   - Use API keys or AWS IAM authentication
   - Configure WAF rules if needed

3. **Enable CloudWatch Logging**
   - Monitor for suspicious activity
   - Set up CloudWatch Alarms

4. **VPC Configuration** (Optional)
   - Deploy Lambda in VPC if accessing private resources
   - Configure security groups appropriately

## Next Steps

- **Add More Webhooks**: Create webhooks for different channels/teams
- **Enhanced Responses**: Format responses with markdown or simple cards
- **Error Handling**: Improve error messages for users
- **Analytics**: Track webhook usage and performance

## Reference

- [Teams Outgoing Webhooks Documentation](https://learn.microsoft.com/en-us/microsoftteams/platform/webhooks-and-connectors/how-to/add-outgoing-webhook)
- [AWS Lambda Python Guide](https://docs.aws.amazon.com/lambda/latest/dg/lambda-python.html)
- [API Gateway HTTP API](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api.html)

