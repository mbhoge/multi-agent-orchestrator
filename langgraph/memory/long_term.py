"""Long-term memory management."""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from shared.models.agent_state import MemoryEntry

logger = logging.getLogger(__name__)


class LongTermMemory:
    """Manages long-term memory across sessions."""
    
    def __init__(self):
        """Initialize long-term memory."""
        self.memory: Dict[str, MemoryEntry] = {}
        logger.info("Initialized Long-Term Memory")
    
    def store(
        self,
        key: str,
        value: Any,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Store a value in long-term memory.
        
        Args:
            key: Memory key
            value: Value to store
            metadata: Optional metadata
        """
        entry = MemoryEntry(
            key=key,
            value=value,
            ttl=None,  # Long-term memory doesn't expire
            metadata=metadata or {}
        )
        
        self.memory[key] = entry
        logger.debug(f"Stored long-term memory: key={key}")
    
    def retrieve(self, key: str) -> Optional[Any]:
        """
        Retrieve a value from long-term memory.
        
        Args:
            key: Memory key
        
        Returns:
            Stored value or None if not found
        """
        if key not in self.memory:
            return None
        
        logger.debug(f"Retrieved long-term memory: key={key}")
        return self.memory[key].value
    
    def search(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search long-term memory by query.
        
        Args:
            query: Search query
            limit: Maximum number of results
        
        Returns:
            List of matching memory entries
        """
        # Simple keyword search implementation
        # In production, this could use vector search or more sophisticated methods
        query_lower = query.lower()
        results = []
        
        for key, entry in self.memory.items():
            if query_lower in key.lower() or query_lower in str(entry.value).lower():
                results.append({
                    "key": key,
                    "value": entry.value,
                    "metadata": entry.metadata,
                    "timestamp": entry.timestamp.isoformat()
                })
        
        # Sort by timestamp (most recent first)
        results.sort(key=lambda x: x["timestamp"], reverse=True)
        
        logger.debug(f"Long-term memory search: query={query}, results={len(results)}")
        return results[:limit]
    
    def get_all(self) -> Dict[str, Any]:
        """
        Get all long-term memory entries.
        
        Returns:
            Dictionary of all memory entries
        """
        return {
            key: entry.value
            for key, entry in self.memory.items()
        }
    
    def delete(self, key: str) -> bool:
        """
        Delete a memory entry.
        
        Args:
            key: Memory key
        
        Returns:
            True if deleted, False if not found
        """
        if key in self.memory:
            del self.memory[key]
            logger.debug(f"Deleted long-term memory: key={key}")
            return True
        return False


# Global long-term memory instance
long_term_memory = LongTermMemory()

