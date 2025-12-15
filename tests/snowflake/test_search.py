"""Standalone test script for Snowflake Cortex AI Search."""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from shared.config.settings import settings
from shared.utils.logging import setup_logging
from snowflake_cortex.tools.search import CortexSearch
import logging

# Setup logging
setup_logging(log_level="INFO")
logger = logging.getLogger(__name__)


async def test_search():
    """Test Cortex AI Search functionality."""
    print("=" * 60)
    print("Testing Snowflake Cortex AI Search")
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
    
    search = None
    try:
        # Initialize search
        print("\n" + "-" * 60)
        print("Initializing Cortex AI Search...")
        search = CortexSearch()
        print("✓ Search initialized")
        
        # Test queries
        test_queries = [
            "machine learning",
            "sales report",
            "product documentation",
            "customer feedback",
        ]
        
        # Get stage path from environment or use default
        stage_path = os.getenv("SNOWFLAKE_STAGE_PATH", "@my_stage")
        print(f"\nUsing stage path: {stage_path}")
        print("(Set SNOWFLAKE_STAGE_PATH environment variable to use a different stage)")
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n{'=' * 60}")
            print(f"Test Query {i}: {query}")
            print("=" * 60)
            
            try:
                result = await search.search_query(
                    query=query,
                    session_id=f"test-session-{i}",
                    context={"stage_path": stage_path}
                )
                
                print(f"\n✓ Search completed successfully")
                print(f"\nResponse:")
                print(f"  {result.get('response', 'N/A')}")
                print(f"\nSources found: {len(result.get('sources', []))}")
                for j, source in enumerate(result.get('sources', []), 1):
                    print(f"  {j}. {source.get('file', 'Unknown')} (score: {source.get('score', 0):.2%})")
                
            except Exception as e:
                print(f"\n❌ Error performing search: {str(e)}")
                logger.exception("Search error")
        
        print("\n" + "=" * 60)
        print("All tests completed!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        logger.exception("Test error")
        return False
        
    finally:
        if search:
            search.close_session()


if __name__ == "__main__":
    success = asyncio.run(test_search())
    sys.exit(0 if success else 1)

