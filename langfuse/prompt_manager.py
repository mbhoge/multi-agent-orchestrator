"""Langfuse prompt management functionality."""

import logging
from typing import Dict, Any, Optional, List
import httpx
from shared.config.settings import LangfuseSettings
from shared.utils.exceptions import ObservabilityError

logger = logging.getLogger(__name__)


class LangfusePromptManager:
    """Manages prompts using Langfuse prompt management."""
    
    def __init__(self, langfuse_settings: LangfuseSettings):
        """
        Initialize Langfuse prompt manager.
        
        Args:
            langfuse_settings: Langfuse configuration settings
        """
        self.settings = langfuse_settings
        self.base_url = langfuse_settings.langfuse_host
        self.public_key = langfuse_settings.langfuse_public_key
        self.secret_key = langfuse_settings.langfuse_secret_key
        self.project_id = langfuse_settings.langfuse_project_id
        self.prompt_cache: Dict[str, Dict[str, Any]] = {}
        logger.info(f"Initialized Langfuse Prompt Manager: {self.base_url}")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get authentication headers for Langfuse API."""
        return {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json",
            "X-Langfuse-Public-Key": self.public_key or "",
        }
    
    async def get_prompt(
        self,
        prompt_name: str,
        version: Optional[int] = None,
        labels: Optional[List[str]] = None,
        use_cache: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Get a prompt from Langfuse.
        
        Args:
            prompt_name: Name of the prompt
            version: Optional specific version number
            labels: Optional list of labels to filter by
            use_cache: Whether to use cached prompts
        
        Returns:
            Prompt dictionary with name, prompt, config, etc., or None if not found
        """
        try:
            # Check cache first
            cache_key = f"{prompt_name}:{version or 'latest'}"
            if use_cache and cache_key in self.prompt_cache:
                logger.debug(f"Returning cached prompt: {prompt_name}")
                return self.prompt_cache[cache_key]
            
            if not self.public_key or not self.secret_key:
                logger.warning("Langfuse credentials not configured, cannot fetch prompt")
                return None
            
            logger.debug(f"Fetching prompt from Langfuse: {prompt_name}, version={version}")
            
            # Build query parameters
            params = {"name": prompt_name}
            if version:
                params["version"] = version
            if labels:
                params["labels"] = ",".join(labels)
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                # In production, this would use the Langfuse Python SDK or API
                # response = await client.get(
                #     f"{self.base_url}/api/public/prompts",
                #     params=params,
                #     headers=self._get_headers()
                # )
                # response.raise_for_status()
                # prompt_data = response.json()
                
                # Placeholder implementation
                prompt_data = {
                    "name": prompt_name,
                    "prompt": self._get_default_prompt(prompt_name),
                    "version": version or 1,
                    "config": {},
                    "labels": labels or []
                }
                
                # Cache the prompt
                if use_cache:
                    self.prompt_cache[cache_key] = prompt_data
                
                logger.debug(f"Fetched prompt: {prompt_name}, version={prompt_data.get('version')}")
                return prompt_data
                
        except Exception as e:
            logger.error(f"Error fetching prompt from Langfuse: {str(e)}")
            # Return default prompt on error
            return self._get_fallback_prompt(prompt_name)
    
    async def create_prompt(
        self,
        prompt_name: str,
        prompt: str,
        config: Optional[Dict[str, Any]] = None,
        labels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a new prompt in Langfuse.
        
        Args:
            prompt_name: Name of the prompt
            prompt: Prompt text/template
            config: Optional prompt configuration
            labels: Optional list of labels
        
        Returns:
            Created prompt data
        """
        try:
            if not self.public_key or not self.secret_key:
                logger.warning("Langfuse credentials not configured, cannot create prompt")
                return {}
            
            logger.info(f"Creating prompt in Langfuse: {prompt_name}")
            
            payload = {
                "name": prompt_name,
                "prompt": prompt,
                "config": config or {},
                "labels": labels or []
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                # In production, this would use the Langfuse Python SDK or API
                # response = await client.post(
                #     f"{self.base_url}/api/public/prompts",
                #     json=payload,
                #     headers=self._get_headers()
                # )
                # response.raise_for_status()
                # return response.json()
                
                # Placeholder implementation
                prompt_data = {
                    "name": prompt_name,
                    "prompt": prompt,
                    "version": 1,
                    "config": config or {},
                    "labels": labels or []
                }
                
                logger.debug(f"Created prompt: {prompt_name}")
                return prompt_data
                
        except Exception as e:
            logger.error(f"Error creating prompt in Langfuse: {str(e)}")
            raise ObservabilityError(f"Failed to create prompt: {str(e)}") from e
    
    async def update_prompt(
        self,
        prompt_name: str,
        prompt: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        labels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Update an existing prompt in Langfuse.
        
        Args:
            prompt_name: Name of the prompt
            prompt: Optional new prompt text
            config: Optional new configuration
            labels: Optional new labels
        
        Returns:
            Updated prompt data
        """
        try:
            if not self.public_key or not self.secret_key:
                logger.warning("Langfuse credentials not configured, cannot update prompt")
                return {}
            
            logger.info(f"Updating prompt in Langfuse: {prompt_name}")
            
            payload = {}
            if prompt:
                payload["prompt"] = prompt
            if config:
                payload["config"] = config
            if labels:
                payload["labels"] = labels
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                # In production, this would use the Langfuse Python SDK or API
                # response = await client.patch(
                #     f"{self.base_url}/api/public/prompts/{prompt_name}",
                #     json=payload,
                #     headers=self._get_headers()
                # )
                # response.raise_for_status()
                # return response.json()
                
                # Placeholder implementation
                existing = await self.get_prompt(prompt_name, use_cache=False)
                if existing:
                    updated = existing.copy()
                    if prompt:
                        updated["prompt"] = prompt
                    if config:
                        updated["config"].update(config)
                    if labels:
                        updated["labels"] = labels
                    updated["version"] = existing.get("version", 1) + 1
                    return updated
                
                return {}
                
        except Exception as e:
            logger.error(f"Error updating prompt in Langfuse: {str(e)}")
            raise ObservabilityError(f"Failed to update prompt: {str(e)}") from e
    
    def render_prompt(
        self,
        prompt_template: str,
        variables: Dict[str, Any]
    ) -> str:
        """
        Render a prompt template with variables.
        
        Args:
            prompt_template: Prompt template string
            variables: Dictionary of variables to substitute
        
        Returns:
            Rendered prompt string
        """
        try:
            rendered = prompt_template
            for key, value in variables.items():
                placeholder = f"{{{key}}}"
                rendered = rendered.replace(placeholder, str(value))
            return rendered
        except Exception as e:
            logger.error(f"Error rendering prompt: {str(e)}")
            return prompt_template
    
    def clear_cache(self, prompt_name: Optional[str] = None):
        """
        Clear prompt cache.
        
        Args:
            prompt_name: Optional specific prompt to clear, or all if None
        """
        if prompt_name:
            keys_to_remove = [k for k in self.prompt_cache.keys() if k.startswith(f"{prompt_name}:")]
            for key in keys_to_remove:
                del self.prompt_cache[key]
            logger.debug(f"Cleared cache for prompt: {prompt_name}")
        else:
            self.prompt_cache.clear()
            logger.debug("Cleared all prompt cache")
    
    def _get_default_prompt(self, prompt_name: str) -> str:
        """Get default prompt template for a prompt name."""
        default_prompts = {
            "orchestrator_query": "You are a multi-agent orchestrator. Process the following query: {query}",
            "supervisor_routing": "Analyze the following query and determine the best agent to handle it: {query}\n\nContext: {context}",
            "agent_response": "Generate a response for the following query: {query}\n\nContext: {context}\n\nPrevious results: {previous_results}",
            "snowflake_cortex_analyst": "Convert the following natural language query to SQL: {query}\n\nSemantic model context: {semantic_model}",
            "snowflake_cortex_search": "Search for information related to: {query}\n\nSearch context: {context}",
            "snowflake_cortex_combined": "Process the following query using both structured and unstructured data: {query}\n\nContext: {context}",
        }
        return default_prompts.get(prompt_name, f"Default prompt for: {prompt_name}")
    
    def _get_fallback_prompt(self, prompt_name: str) -> Dict[str, Any]:
        """Get fallback prompt when Langfuse is unavailable."""
        return {
            "name": prompt_name,
            "prompt": self._get_default_prompt(prompt_name),
            "version": 1,
            "config": {},
            "labels": []
        }


# Global prompt manager instance
_prompt_manager: Optional[LangfusePromptManager] = None


def get_prompt_manager(langfuse_settings: Optional[LangfuseSettings] = None) -> LangfusePromptManager:
    """Get or create global prompt manager instance."""
    global _prompt_manager
    if _prompt_manager is None:
        from shared.config.settings import settings
        _prompt_manager = LangfusePromptManager(langfuse_settings or settings.langfuse)
    return _prompt_manager

