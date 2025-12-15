"""Cortex AI Search for unstructured data queries."""

import logging
from typing import Dict, Any, Optional, List
from shared.config.settings import settings
from shared.utils.exceptions import SnowflakeCortexError

logger = logging.getLogger(__name__)


class CortexSearch:
    """Cortex AI Search for querying unstructured data in Snowflake stages."""
    
    def __init__(self):
        """Initialize the Cortex Search."""
        self.snowflake_config = settings.snowflake
        logger.info("Initialized Cortex AI Search")
    
    async def search_query(
        self,
        query: str,
        session_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Search unstructured data using Cortex AI Search.
        
        Args:
            query: Search query
            session_id: Session identifier
            context: Optional context information
        
        Returns:
            Search results
        
        Raises:
            SnowflakeCortexError: If search fails
        """
        try:
            logger.info(f"Searching unstructured data with Cortex Search: session={session_id}")
            
            # In production, this would use Snowflake Cortex AI Search
            # to search documents in Snowflake stages (PDFs, PPTs, etc.)
            
            # Get stage path from context or use default
            stage_path = context.get("stage_path") if context else None
            
            # Perform search
            search_results = await self._perform_search(query, stage_path)
            
            # Format response
            response = self._format_search_results(search_results, query)
            
            return {
                "response": response,
                "sources": [
                    {
                        "type": "unstructured_data",
                        "file": result.get("file"),
                        "score": result.get("score")
                    }
                    for result in search_results
                ],
                "agent_type": "cortex_search"
            }
            
        except Exception as e:
            logger.error(f"Error in Cortex Search: {str(e)}")
            raise SnowflakeCortexError(f"Search failed: {str(e)}") from e
    
    async def _perform_search(
        self,
        query: str,
        stage_path: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform search in Snowflake stages.
        
        Args:
            query: Search query
            stage_path: Optional specific stage path
        
        Returns:
            List of search results
        """
        try:
            logger.debug(f"Performing search: {query[:50]}...")
            
            # In production, this would use Snowflake Cortex AI Search API
            # Example:
            # from snowflake.snowpark import Session
            # session = Session.builder.configs(...).create()
            # results = session.sql(
            #     f"SELECT * FROM TABLE(SNOWFLAKE.CORTEX.SEARCH("
            #     f"  '{stage_path or '@my_stage'}',"
            #     f"  '{query}'"
            #     f"))"
            # ).collect()
            
            # Placeholder results
            results = [
                {
                    "file": "document1.pdf",
                    "content": f"Relevant content matching: {query}",
                    "score": 0.95,
                    "page": 1
                },
                {
                    "file": "presentation1.pptx",
                    "content": f"Another relevant match: {query}",
                    "score": 0.87,
                    "slide": 3
                }
            ]
            
            return results
            
        except Exception as e:
            logger.error(f"Error performing search: {str(e)}")
            raise SnowflakeCortexError(f"Search execution failed: {str(e)}") from e
    
    def _format_search_results(
        self,
        results: List[Dict[str, Any]],
        original_query: str
    ) -> str:
        """
        Format search results into a natural language response.
        
        Args:
            results: Search results
            original_query: Original search query
        
        Returns:
            Formatted response string
        """
        if not results:
            return f"No documents found matching: {original_query}"
        
        response = f"Found {len(results)} document(s) matching your search:\n\n"
        
        for i, result in enumerate(results, 1):
            response += f"{i}. {result.get('file', 'Unknown file')} "
            response += f"(relevance: {result.get('score', 0):.2%})\n"
            response += f"   {result.get('content', '')[:100]}...\n\n"
        
        return response

