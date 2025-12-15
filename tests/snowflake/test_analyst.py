"""Standalone test script for Snowflake Cortex AI Analyst."""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from shared.config.settings import settings
from shared.utils.logging import setup_logging
from snowflake_cortex.tools.analyst import CortexAnalyst
import logging

# Setup logging
setup_logging(log_level="INFO")
logger = logging.getLogger(__name__)


async def test_analyst():
    """Test Cortex AI Analyst functionality."""
    print("=" * 60)
    print("Testing Snowflake Cortex AI Analyst")
    print("=" * 60)
    
    # Check configuration
    if not all([
        settings.snowflake.snowflake_account,
        settings.snowflake.snowflake_user,
        settings.snowflake.snowflake_password,
        settings.snowflake.snowflake_warehouse,
        settings.snowflake.snowflake_database
    ]):
        print("\n❌ ERROR: Snowflake configuration is incomplete!")
        print("Please set the following environment variables:")
        print("  - SNOWFLAKE_ACCOUNT")
        print("  - SNOWFLAKE_USER")
        print("  - SNOWFLAKE_PASSWORD")
        print("  - SNOWFLAKE_WAREHOUSE")
        print("  - SNOWFLAKE_DATABASE")
        print("\nYou can set them in .env file or export them:")
        print("  export SNOWFLAKE_ACCOUNT=your-account")
        print("  export SNOWFLAKE_USER=your-user")
        print("  export SNOWFLAKE_PASSWORD=your-password")
        print("  export SNOWFLAKE_WAREHOUSE=your-warehouse")
        print("  export SNOWFLAKE_DATABASE=your-database")
        return False
    
    print("\n✓ Snowflake configuration found")
    print(f"  Account: {settings.snowflake.snowflake_account}")
    print(f"  User: {settings.snowflake.snowflake_user}")
    print(f"  Warehouse: {settings.snowflake.snowflake_warehouse}")
    print(f"  Database: {settings.snowflake.snowflake_database}")
    print(f"  Schema: {settings.snowflake.snowflake_schema}")
    
    analyst = None
    try:
        # Initialize analyst
        print("\n" + "-" * 60)
        print("Initializing Cortex AI Analyst...")
        analyst = CortexAnalyst()
        print("✓ Analyst initialized")
        
        # Test queries
        test_queries = [
            "What are the total sales?",
            "Count the number of customers",
            "Show me the average order value",
            "List all products",
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n{'=' * 60}")
            print(f"Test Query {i}: {query}")
            print("=" * 60)
            
            try:
                result = await analyst.analyze_query(
                    query=query,
                    session_id=f"test-session-{i}",
                    context={}
                )
                
                print(f"\n✓ Query processed successfully")
                print(f"\nGenerated SQL:")
                print(f"  {result.get('sql_query', 'N/A')}")
                print(f"\nResponse:")
                print(f"  {result.get('response', 'N/A')}")
                print(f"\nSources:")
                for source in result.get('sources', []):
                    print(f"  - {source}")
                
            except Exception as e:
                print(f"\n❌ Error processing query: {str(e)}")
                logger.exception("Query processing error")
        
        print("\n" + "=" * 60)
        print("All tests completed!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        logger.exception("Test error")
        return False
        
    finally:
        if analyst:
            analyst.close_session()


if __name__ == "__main__":
    success = asyncio.run(test_analyst())
    sys.exit(0 if success else 1)

