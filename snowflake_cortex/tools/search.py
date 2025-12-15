"""Cortex AI Search for unstructured data queries."""

import logging
from typing import Dict, Any, Optional, List
from snowflake.snowpark import Session
from shared.config.settings import settings
from shared.utils.exceptions import SnowflakeCortexError

logger = logging.getLogger(__name__)


class CortexSearch:
    """Cortex AI Search for querying unstructured data in Snowflake stages."""
    
    def __init__(self):
        """Initialize the Cortex Search."""
        self.snowflake_config = settings.snowflake
        self._session: Optional[Session] = None
        self.default_stage_path = "@my_stage"  # Default stage path
        logger.info("Initialized Cortex AI Search")
    
    def _get_snowflake_session(self) -> Session:
        """Get or create Snowflake Snowpark session."""
        if self._session is None:
            if not all([
                self.snowflake_config.snowflake_account,
                self.snowflake_config.snowflake_user,
                self.snowflake_config.snowflake_password,
                self.snowflake_config.snowflake_warehouse,
                self.snowflake_config.snowflake_database
            ]):
                raise SnowflakeCortexError("Snowflake configuration is incomplete")
            
            connection_parameters = {
                "account": self.snowflake_config.snowflake_account,
                "user": self.snowflake_config.snowflake_user,
                "password": self.snowflake_config.snowflake_password,
                "warehouse": self.snowflake_config.snowflake_warehouse,
                "database": self.snowflake_config.snowflake_database,
                "schema": self.snowflake_config.snowflake_schema,
            }
            
            if self.snowflake_config.snowflake_role:
                connection_parameters["role"] = self.snowflake_config.snowflake_role
            
            try:
                self._session = Session.builder.configs(connection_parameters).create()
                logger.info("Created Snowflake Snowpark session for Search")
            except Exception as e:
                logger.error(f"Failed to create Snowflake session: {str(e)}")
                raise SnowflakeCortexError(f"Failed to connect to Snowflake: {str(e)}") from e
        
        return self._session
    
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
        Perform search in Snowflake stages using Cortex AI Search.
        
        Args:
            query: Search query
            stage_path: Optional specific stage path
        
        Returns:
            List of search results
        """
        try:
            logger.debug(f"Performing search: {query[:50]}...")
            
            session = self._get_snowflake_session()
            stage = stage_path or self.default_stage_path
            
            # Use Snowflake Cortex AI Search function
            # SNOWFLAKE.CORTEX.SEARCH searches unstructured data in stages
            try:
                search_sql = f"""
                SELECT * FROM TABLE(SNOWFLAKE.CORTEX.SEARCH(
                    '{stage}',
                    '{query}'
                ))
                """
                
                df = session.sql(search_sql)
                results = df.collect()
                
                # Convert to list of dictionaries
                search_results = []
                for row in results:
                    row_dict = row.asDict()
                    search_results.append({
                        "file": row_dict.get("FILE", row_dict.get("file", "unknown")),
                        "content": row_dict.get("CONTENT", row_dict.get("content", "")),
                        "score": float(row_dict.get("SCORE", row_dict.get("score", 0.0))),
                        "path": row_dict.get("PATH", row_dict.get("path", "")),
                        "metadata": {
                            k: v for k, v in row_dict.items() 
                            if k.upper() not in ["FILE", "CONTENT", "SCORE", "PATH"]
                        }
                    })
                
                logger.info(f"Search completed. Found {len(search_results)} results")
                return search_results
                
            except Exception as search_error:
                logger.warning(f"Cortex AI Search function not available: {str(search_error)}")
                
                # Fallback: List files in stage and perform basic search
                try:
                    list_sql = f"LIST {stage}"
                    files_df = session.sql(list_sql)
                    files = files_df.collect()
                    
                    # Basic file matching (fallback when Cortex Search is not available)
                    search_results = []
                    query_lower = query.lower()
                    
                    for file_row in files:
                        file_dict = file_row.asDict()
                        file_name = file_dict.get("name", "")
                        
                        # Simple relevance scoring based on filename match
                        if query_lower in file_name.lower():
                            search_results.append({
                                "file": file_name.split("/")[-1],  # Get filename
                                "content": f"File found in stage matching: {query}",
                                "score": 0.7,
                                "path": file_name,
                                "metadata": {"stage": stage}
                            })
                    
                    if search_results:
                        logger.info(f"Fallback search found {len(search_results)} files")
                        return search_results
                    else:
                        logger.warning("No files found matching search query")
                        return []
                        
                except Exception as list_error:
                    logger.error(f"Failed to list stage files: {str(list_error)}")
                    raise SnowflakeCortexError(f"Search failed: {str(list_error)}") from list_error
            
        except Exception as e:
            logger.error(f"Error performing search: {str(e)}")
            raise SnowflakeCortexError(f"Search execution failed: {str(e)}") from e
    
    def close_session(self):
        """Close Snowflake session."""
        if self._session:
            try:
                self._session.close()
                self._session = None
                logger.info("Closed Snowflake session for Search")
            except Exception as e:
                logger.warning(f"Error closing session: {str(e)}")
    
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

