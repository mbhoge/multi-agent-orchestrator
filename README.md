# Multi-Agent Orchestrator

A containerized multi-agent orchestrator system built with AWS Agent Core, LangGraph, and Snowflake Cortex AI agents. This system provides intelligent routing and coordination of AI agents to handle both structured and unstructured data queries.

## Architecture

The system follows a three-tier architecture with integrated Langfuse prompt management:

```
User Request → AWS Agent Core (REST API) → LangGraph Supervisor → Snowflake Cortex AI Agents
                     ↓                           ↓                          ↓
              AWS Observability            Langfuse Container         TruLens Observability
                     ↓                           ↓                          ↓
              Prompt: orchestrator_query   Prompt: supervisor_routing  Prompts: cortex_* agents
                                                      ↓
                                            Langfuse Prompt Management
                                            (Centralized & Versioned)
```

### Components

1. **AWS Agent Core**: Multi-agent orchestrator using AWS Bedrock Agent Core Runtime SDK
   - REST API (FastAPI)
   - Observability and tracing via AWS Agent Core Runtime SDK
   - **Langfuse prompt management**: Uses `orchestrator_query` prompt
   - Invokes LangGraph for reasoning

2. **LangGraph**: Multi-agent supervisor with state and memory management
   - State management (short-term and long-term memory)
   - Request routing to appropriate Snowflake agents
   - **Langfuse prompt management**: Uses `supervisor_routing` prompt for routing decisions
   - Langfuse integration for observability

3. **Snowflake Cortex AI Agents**: Specialized agents for data queries
   - **Cortex AI Analyst**: Queries structured data using semantic models (YAML)
   - **Cortex AI Search**: Queries unstructured data (PDFs, PPTs) in Snowflake stages
   - **Agent Gateway**: Routes requests to appropriate agents
   - **Langfuse prompt management**: Each agent uses specific prompts (`snowflake_cortex_analyst`, `snowflake_cortex_search`, `snowflake_cortex_combined`)
   - TruLens integration for observability

4. **Langfuse**: Separate containerized service providing:
   - **Observability**: Tracing and monitoring for LangGraph
   - **Prompt Management**: Centralized prompt storage, versioning, and rendering across all components

## Project Structure

```
multi-agent-orchestrator/
├── aws_agent_core/          # AWS Agent Core orchestrator
├── langgraph/               # LangGraph supervisor and state management
├── snowflake_cortex/        # Snowflake Cortex AI agents and tools
├── langfuse/                # Langfuse configuration
├── shared/                  # Shared utilities and models
├── docker/                  # Docker configurations
├── infrastructure/          # Terraform infrastructure code
├── config/                  # Configuration files
├── tests/                   # Test suite
└── scripts/                # Setup and deployment scripts
```

## Prerequisites

- Python 3.11+
- Docker and Docker Compose
- AWS CLI configured with appropriate credentials
- Terraform >= 1.0 (for AWS deployment)
- Snowflake account with Cortex AI enabled
- Langfuse account (optional, for observability)

## Quick Start

### Local Development

1. **Clone and setup**:
   ```bash
   cd multi-agent-orchestrator
   ./scripts/setup_env.sh --dev
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Run locally with Docker Compose**:
   ```bash
   ./scripts/run_local.sh
   ```

4. **Access services**:
   - AWS Agent Core API: http://localhost:8000
   - LangGraph Supervisor: http://localhost:8001
   - Snowflake Cortex Agent: http://localhost:8002
   - Langfuse: http://localhost:3000

### Testing

```bash
# Run unit tests
pytest tests/unit/

# Run integration tests
pytest tests/integration/

# Run all tests with coverage
pytest --cov=. --cov-report=html
```

## Configuration

### Environment Variables

See `.env.example` for all configuration options. Key variables:

- **AWS**: `AWS_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
- **LangGraph**: `LANGGRAPH_ENDPOINT`, `LANGGRAPH_TIMEOUT`
- **Langfuse**: `LANGFUSE_HOST`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`
- **Snowflake**: `SNOWFLAKE_ACCOUNT`, `SNOWFLAKE_USER`, `SNOWFLAKE_PASSWORD`, etc.
- **TruLens**: `TRULENS_ENABLED`, `TRULENS_APP_ID`, `TRULENS_API_KEY`

### Agent Configuration

Edit `config/agents.yaml` to configure multiple Snowflake Cortex AI agents:

```yaml
agents:
  - name: cortex_analyst
    type: cortex_analyst
    enabled: true
    semantic_model: "default_semantic_model"
```

### Semantic Models

Semantic models (YAML files) define how natural language queries are converted to SQL. These are stored in Snowflake and referenced in the agent configuration.

## AWS Deployment

### Prerequisites

1. AWS account with appropriate permissions
2. Terraform backend configured (S3 bucket for state)
3. ECR repositories created (or use Terraform to create them)

### Deployment Steps

1. **Configure Terraform**:
   ```bash
   cd infrastructure/terraform
   # Edit variables.tf or create terraform.tfvars
   ```

2. **Deploy infrastructure**:
   ```bash
   ./infrastructure/scripts/deploy.sh
   ```

3. **Build and push Docker images**:
   ```bash
   ./infrastructure/scripts/build_and_push.sh
   ```

4. **Update ECS services** (if needed):
   ```bash
   aws ecs update-service --cluster <cluster-name> --service <service-name> --force-new-deployment
   ```

### Terraform Variables

Key variables in `infrastructure/terraform/variables.tf`:

- `aws_region`: AWS region (default: us-east-1)
- `environment`: Environment name (dev, staging, prod)
- `vpc_cidr`: VPC CIDR block
- `ecs_service_desired_count`: Number of tasks per service

## Usage

### API Endpoints

#### Process Query

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the total sales for last month?",
    "session_id": "session-123",
    "context": {"data_type": "structured"}
  }'
```

#### Health Check

```bash
curl http://localhost:8000/health
```

#### Metrics

```bash
curl http://localhost:8000/metrics
```

## Observability

### AWS Agent Core

- Uses AWS Agent Core Runtime SDK for built-in observability
- Traces available in AWS CloudWatch
- Metrics collected via CloudWatch
- Langfuse prompt management integration

### LangGraph

- Langfuse integration for tracing and monitoring
- Langfuse prompt management for routing decisions
- Access Langfuse UI at http://localhost:3000 (local) or configured endpoint

### Snowflake Cortex Agents

- TruLens integration for agent evaluation
- Response quality metrics and feedback
- Langfuse prompt management for agent-specific prompts

## Prompt Management

The system integrates Langfuse prompt management across all components:

### Available Prompts

- **orchestrator_query**: Used by AWS Agent Core orchestrator
- **supervisor_routing**: Used by LangGraph supervisor for routing decisions
- **snowflake_cortex_analyst**: Used by Cortex AI Analyst agent
- **snowflake_cortex_search**: Used by Cortex AI Search agent
- **snowflake_cortex_combined**: Used by combined Cortex AI agent

### Managing Prompts

Prompts can be managed through:

1. **Langfuse UI**: Access the Langfuse dashboard to create, update, and version prompts
2. **API Endpoints**: Use the Snowflake Gateway API endpoints:
   - `GET /prompts/{prompt_name}` - Get a prompt
   - `POST /prompts` - Create a new prompt

3. **Configuration**: Default prompts are defined in `config/prompts.yaml`

### Prompt Variables

Prompts support variable substitution using `{variable_name}` syntax. Common variables:
- `{query}` - User query
- `{context}` - Context information
- `{session_id}` - Session identifier
- `{semantic_model}` - Semantic model information (for analyst)

## Development

### Code Structure

- **Shared components**: Common utilities, models, and configuration
- **AWS Agent Core**: Orchestrator and REST API
- **LangGraph**: Supervisor, state management, memory, routing
- **Snowflake Cortex**: Agents, tools (Analyst, Search), gateway

### Adding New Agents

1. Create agent class in `snowflake_cortex/agents/`
2. Add configuration in `config/agents.yaml`
3. Update routing logic in `langgraph/reasoning/router.py`
4. Add tests in `tests/unit/test_snowflake_cortex.py`

### Adding New Tools

1. Create tool class in `snowflake_cortex/tools/`
2. Integrate with agent in `snowflake_cortex/agents/cortex_agent.py`
3. Add tests

## Troubleshooting

### Services not starting

- Check Docker logs: `docker-compose logs <service-name>`
- Verify environment variables in `.env`
- Ensure all dependencies are installed

### AWS deployment issues

- Verify AWS credentials: `aws sts get-caller-identity`
- Check Terraform state: `terraform state list`
- Review CloudWatch logs for ECS tasks

### Snowflake connection issues

- Verify Snowflake credentials in `.env`
- Check network connectivity
- Ensure Cortex AI is enabled in Snowflake account

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## References

- [AWS Agent Core Documentation](https://aws.amazon.com/bedrock/agentcore)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Snowflake Cortex AI Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex)
- [Langfuse Documentation](https://langfuse.com/docs)
- [TruLens Documentation](https://www.trulens.org/)

## Support

For issues and questions, please open an issue on the repository.

