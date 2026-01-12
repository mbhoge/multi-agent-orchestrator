"""Standalone test script for Snowflake Cortex AI Agent Gateway."""

import asyncio
import sys
import httpx
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from shared.config.settings import settings
from shared.utils.logging import setup_logging
import logging

# Setup logging
setup_logging(log_level="INFO")
logger = logging.getLogger(__name__)

GATEWAY_URL = "http://localhost:8002"

def _env(name: str, default: str) -> str:
    val = os.getenv(name)
    return val.strip() if isinstance(val, str) and val.strip() else default


def get_agent_names() -> dict:
    """
    Resolve Snowflake Cortex Agent object names from env vars.
    These should match the Snowflake agent object names created in your DB/SCHEMA.
    """
    return {
        "analyst": _env("SNOWFLAKE_CORTEX_AGENT_NAME_ANALYST", "CORTEX_ANALYST_AGENT"),
        "search": _env("SNOWFLAKE_CORTEX_AGENT_NAME_SEARCH", "CORTEX_SEARCH_AGENT"),
        "combined": _env("SNOWFLAKE_CORTEX_AGENT_NAME_COMBINED", _env("SNOWFLAKE_CORTEX_AGENT_NAME", "CORTEX_COMBINED_AGENT")),
    }


async def test_gateway_health():
    """Test gateway health endpoint."""
    print("Testing Gateway Health Endpoint...")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{GATEWAY_URL}/health")
            response.raise_for_status()
            data = response.json()
            print(f"✓ Health check passed: {data}")
            return True
    except Exception as e:
        print(f"❌ Health check failed: {str(e)}")
        return False


async def test_analyst_agent():
    """Test Cortex Analyst agent via gateway."""
    print("\n" + "=" * 60)
    print("Testing Cortex Analyst Agent")
    print("=" * 60)
    
    agent_names = get_agent_names()
    test_query = {
        "agent_name": agent_names["analyst"],
        "query": "What are the total sales?",
        "session_id": "test-session-analyst",
        "context": {}
    }
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            print(f"\nSending request to {GATEWAY_URL}/agents/invoke")
            print(f"Query: {test_query['query']}")
            
            response = await client.post(
                f"{GATEWAY_URL}/agents/invoke",
                json=test_query
            )
            response.raise_for_status()
            result = response.json()
            
            print(f"\n✓ Request successful")
            print(f"\nResponse:")
            print(f"  {result.get('response', 'N/A')}")
            print(f"\nSQL Query:")
            print(f"  {result.get('sql_query', 'N/A')}")
            print(f"\nSources: {len(result.get('sources', []))}")
            for source in result.get('sources', []):
                print(f"  - {source}")
            
            return True
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        logger.exception("Analyst agent test error")
        return False


async def test_search_agent():
    """Test Cortex Search agent via gateway."""
    print("\n" + "=" * 60)
    print("Testing Cortex Search Agent")
    print("=" * 60)
    
    agent_names = get_agent_names()
    test_query = {
        "agent_name": agent_names["search"],
        "query": "machine learning",
        "session_id": "test-session-search",
        "context": {
            "stage_path": "@my_stage"
        }
    }
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            print(f"\nSending request to {GATEWAY_URL}/agents/invoke")
            print(f"Query: {test_query['query']}")
            
            response = await client.post(
                f"{GATEWAY_URL}/agents/invoke",
                json=test_query
            )
            response.raise_for_status()
            result = response.json()
            
            print(f"\n✓ Request successful")
            print(f"\nResponse:")
            print(f"  {result.get('response', 'N/A')}")
            print(f"\nSources: {len(result.get('sources', []))}")
            for i, source in enumerate(result.get('sources', []), 1):
                print(f"  {i}. {source.get('file', 'Unknown')} (score: {source.get('score', 0):.2%})")
            
            return True
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        logger.exception("Search agent test error")
        return False


async def test_combined_agent():
    """Test Combined agent via gateway."""
    print("\n" + "=" * 60)
    print("Testing Combined Agent")
    print("=" * 60)
    
    agent_names = get_agent_names()
    test_query = {
        "agent_name": agent_names["combined"],
        "query": "Show me sales data and related documents",
        "session_id": "test-session-combined",
        "context": {}
    }
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            print(f"\nSending request to {GATEWAY_URL}/agents/invoke")
            print(f"Query: {test_query['query']}")
            
            response = await client.post(
                f"{GATEWAY_URL}/agents/invoke",
                json=test_query
            )
            response.raise_for_status()
            result = response.json()
            
            print(f"\n✓ Request successful")
            print(f"\nResponse:")
            print(f"  {result.get('response', 'N/A')[:500]}...")
            print(f"\nSources: {len(result.get('sources', []))}")
            
            return True
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        logger.exception("Combined agent test error")
        return False


async def test_prompt_endpoints():
    """Test prompt management endpoints."""
    print("\n" + "=" * 60)
    print("Testing Prompt Management Endpoints")
    print("=" * 60)
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Test getting a prompt
            print("\n1. Testing GET /prompts/supervisor_routing")
            response = await client.get(f"{GATEWAY_URL}/prompts/supervisor_routing")
            if response.status_code == 200:
                prompt_data = response.json()
                print(f"✓ Prompt retrieved: {prompt_data.get('name', 'N/A')}")
            else:
                print(f"⚠ Prompt not found (status: {response.status_code})")
            
            return True
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False


async def run_all_tests():
    """Run all gateway tests."""
    print("=" * 60)
    print("Snowflake Cortex AI Agent Gateway Tests")
    print("=" * 60)
    
    print("\n⚠ Make sure the gateway is running:")
    print(f"  The gateway now runs as AWS Lambda functions via API Gateway")
    print(f"  Update GATEWAY_URL to point to your API Gateway endpoint")
    
    input("\nPress Enter to continue...")
    
    results = []
    
    # Test health
    results.append(("Health Check", await test_gateway_health()))
    
    # Test agents
    results.append(("Analyst Agent", await test_analyst_agent()))
    results.append(("Search Agent", await test_search_agent()))
    results.append(("Combined Agent", await test_combined_agent()))
    
    # Test prompts
    results.append(("Prompt Endpoints", await test_prompt_endpoints()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    for test_name, success in results:
        status = "✓ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(result[1] for result in results)
    print(f"\n{'All tests passed!' if all_passed else 'Some tests failed'}")
    
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)

