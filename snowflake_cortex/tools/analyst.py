"""Cortex AI Analyst for structured data queries."""

import logging
from typing import Dict, Any, Optional, List
from snowflake.snowpark import Session
from shared.config.settings import settings
from shared.utils.exceptions import SnowflakeCortexError
from snowflake_cortex.semantic_models.loader import SemanticModelLoader

logger = logging.getLogger(__name__)


class CortexAnalyst:
    """Cortex AI Analyst for querying structured data using semantic models."""
    
    def __init__(self):
        """Initialize the Cortex Analyst."""
        self.snowflake_config = settings.snowflake
        self.semantic_loader = SemanticModelLoader()
        self._session: Optional[Session] = None
        logger.info("Initialized Cortex AI Analyst")
    
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
                logger.info("Created Snowflake Snowpark session")
            except Exception as e:
                logger.error(f"Failed to create Snowflake session: {str(e)}")
                raise SnowflakeCortexError(f"Failed to connect to Snowflake: {str(e)}") from e
        
        return self._session
    
    async def analyze_query(
        self,
        query: str,
        session_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze a query and convert it to SQL using semantic models.
        
        Args:
            query: Natural language query
            session_id: Session identifier
            context: Optional context information
        
        Returns:
            Analysis results with SQL and data
        
        Raises:
            SnowflakeCortexError: If analysis fails
        """
        try:
            logger.info(f"Analyzing query with Cortex Analyst: session={session_id}")
            
            # Load semantic model
            semantic_model = await self.semantic_loader.load_semantic_model(
                context.get("semantic_model") if context else None
            )
            
            # Convert natural language to SQL using semantic model
            sql_query = await self._convert_to_sql(query, semantic_model)
            
            # Execute SQL query
            results = await self._execute_query(sql_query)
            
            # Format response
            response = self._format_response(results, query)
            
            return {
                "response": response,
                "sql_query": sql_query,
                "sources": [{"type": "structured_data", "query": sql_query}],
                "agent_type": "cortex_analyst"
            }
            
        except Exception as e:
            logger.error(f"Error in Cortex Analyst: {str(e)}")
            raise SnowflakeCortexError(f"Analysis failed: {str(e)}") from e
    
    async def _convert_to_sql(
        self,
        query: str,
        semantic_model: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Convert natural language query to SQL using Snowflake Cortex AI Analyst.
        
        Args:
            query: Natural language query
            semantic_model: Optional semantic model YAML
        
        Returns:
            SQL query string
        """
        try:
            logger.debug(f"Converting query to SQL using Cortex AI Analyst: {query[:50]}...")
            
            session = self._get_snowflake_session()
            
            # Build semantic model context if available
            semantic_context = ""
            if semantic_model:
                tables_info = []
                for table in semantic_model.get("tables", []):
                    table_name = table.get("name", "")
                    table_desc = table.get("description", "")
                    columns = table.get("columns", [])
                    col_info = ", ".join([f"{col.get('name')} ({col.get('type')})" for col in columns])
                    tables_info.append(f"Table: {table_name} - {table_desc}\nColumns: {col_info}")
                semantic_context = "\n\n".join(tables_info)
            
            # Use Snowflake Cortex AI Analyst to convert NL to SQL
            # The ANALYZE function in Snowflake Cortex AI can convert natural language to SQL
            try:
                # Method 1: Using SNOWFLAKE.CORTEX.ANALYZE function
                analyze_query = f"""
                SELECT SNOWFLAKE.CORTEX.ANALYZE(
                    '{query}',
                    {f"'{semantic_context}'" if semantic_context else "NULL"}
                ) AS sql_query
                """
                
                result = session.sql(analyze_query).collect()
                
                if result and len(result) > 0:
                    sql_query = result[0]["SQL_QUERY"]
                    logger.debug(f"Generated SQL: {sql_query[:100]}...")
                    return sql_query
                
            except Exception as analyze_error:
                logger.warning(f"Cortex AI Analyst function not available: {str(analyze_error)}")
                # Fallback: Try using COMPLETE function for SQL generation
                try:
                    complete_query = f"""
                    SELECT SNOWFLAKE.CORTEX.COMPLETE(
                        'snowflake-snowflake-arctic-sql',
                        CONCAT('Convert this natural language query to SQL: {query}', 
                               {f"', Context: {semantic_context}'" if semantic_context else "''"})
                    ) AS sql_query
                    """
                    result = session.sql(complete_query).collect()
                    if result and len(result) > 0:
                        sql_query = result[0]["SQL_QUERY"]
                        logger.debug(f"Generated SQL (fallback): {sql_query[:100]}...")
                        return sql_query
                except Exception as complete_error:
                    logger.warning(f"Cortex AI Complete function not available: {str(complete_error)}")
            
            # Final fallback: Simple pattern-based SQL generation
            logger.warning("Using fallback SQL generation")
            query_lower = query.lower()
            
            # Simple keyword-based SQL generation
            if "count" in query_lower or "how many" in query_lower:
                sql = "SELECT COUNT(*) as count FROM table_name;"
            elif "sum" in query_lower or "total" in query_lower:
                sql = "SELECT SUM(amount) as total FROM table_name;"
            elif "average" in query_lower or "avg" in query_lower:
                sql = "SELECT AVG(amount) as average FROM table_name;"
            else:
                sql = f"SELECT * FROM table_name WHERE column_name LIKE '%{query}%' LIMIT 10;"
            
            return sql
            
        except Exception as e:
            logger.error(f"Error converting query to SQL: {str(e)}")
            raise SnowflakeCortexError(f"SQL conversion failed: {str(e)}") from e
    
    async def _execute_query(self, sql_query: str) -> List[Dict[str, Any]]:
        """
        Execute SQL query in Snowflake.
        
        Args:
            sql_query: SQL query string
        
        Returns:
            Query results as list of dictionaries
        """
        try:
            logger.debug(f"Executing SQL query: {sql_query[:100]}...")
            
            session = self._get_snowflake_session()
            
            # Execute query using Snowpark
            df = session.sql(sql_query)
            results = df.collect()
            
            # Convert Snowpark Row objects to dictionaries
            if results:
                # Get column names from the first row
                column_names = [col for col in results[0].asDict().keys()]
                
                # Convert to list of dictionaries
                result_list = []
                for row in results:
                    row_dict = row.asDict()
                    result_list.append(row_dict)
                
                logger.info(f"Query executed successfully. Returned {len(result_list)} rows")
                return result_list
            else:
                logger.info("Query executed successfully but returned no rows")
                return []
            
        except Exception as e:
            logger.error(f"Error executing SQL query: {str(e)}")
            raise SnowflakeCortexError(f"SQL execution failed: {str(e)}") from e
    
    def close_session(self):
        """Close Snowflake session."""
        if self._session:
            try:
                self._session.close()
                self._session = None
                logger.info("Closed Snowflake session")
            except Exception as e:
                logger.warning(f"Error closing session: {str(e)}")
    
    def _format_response(self, results: list, original_query: str) -> str:
        """
        Format query results into a natural language response.
        
        Args:
            results: Query results
            original_query: Original user query
        
        Returns:
            Formatted response string
        """
        if not results:
            return f"No results found for: {original_query}"
        
        response = f"Found {len(results)} result(s) for your query:\n\n"
        
        # Format results (simplified)
        for i, row in enumerate(results[:10], 1):  # Limit to 10 results
            response += f"Result {i}: {row}\n"
        
        if len(results) > 10:
            response += f"\n... and {len(results) - 10} more results"
        
        return response

