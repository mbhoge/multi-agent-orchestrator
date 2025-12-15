"""Short-term memory management."""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from shared.models.agent_state import MemoryEntry

logger = logging.getLogger(__name__)


class ShortTermMemory:
    """Manages short-term memory for current session."""
    
    def __init__(self, default_ttl: int = 3600):
        """
        Initialize short-term memory.
        
        Args:
            default_ttl: Default time-to-live in seconds (default: 1 hour)
        """
        self.memory: Dict[str, Dict[str, MemoryEntry]] = {}
        self.default_ttl = default_ttl
        logger.info(f"Initialized Short-Term Memory with TTL: {default_ttl}s")
    
    def store(
        self,
        session_id: str,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Store a value in short-term memory.
        
        Args:
            session_id: Session identifier
            key: Memory key
            value: Value to store
            ttl: Optional time-to-live in seconds
            metadata: Optional metadata
        """
        if session_id not in self.memory:
            self.memory[session_id] = {}
        
        entry = MemoryEntry(
            key=key,
            value=value,
            ttl=ttl or self.default_ttl,
            metadata=metadata or {}
        )
        
        self.memory[session_id][key] = entry
        logger.debug(f"Stored short-term memory: session={session_id}, key={key}")
    
    def retrieve(
        self,
        session_id: str,
        key: str
    ) -> Optional[Any]:
        """
        Retrieve a value from short-term memory.
        
        Args:
            session_id: Session identifier
            key: Memory key
        
        Returns:
            Stored value or None if not found or expired
        """
        if session_id not in self.memory:
            return None
        
        if key not in self.memory[session_id]:
            return None
        
        entry = self.memory[session_id][key]
        
        # Check if expired
        if entry.ttl:
            age = (datetime.utcnow() - entry.timestamp).total_seconds()
            if age > entry.ttl:
                logger.debug(f"Short-term memory expired: session={session_id}, key={key}")
                del self.memory[session_id][key]
                return None
        
        logger.debug(f"Retrieved short-term memory: session={session_id}, key={key}")
        return entry.value
    
    def get_all(self, session_id: str) -> Dict[str, Any]:
        """
        Get all memory entries for a session.
        
        Args:
            session_id: Session identifier
        
        Returns:
            Dictionary of all memory entries
        """
        if session_id not in self.memory:
            return {}
        
        # Clean expired entries
        self._clean_expired(session_id)
        
        return {
            key: entry.value
            for key, entry in self.memory[session_id].items()
        }
    
    def clear(self, session_id: str):
        """
        Clear all memory for a session.
        
        Args:
            session_id: Session identifier
        """
        if session_id in self.memory:
            del self.memory[session_id]
            logger.debug(f"Cleared short-term memory for session {session_id}")
    
    def _clean_expired(self, session_id: str):
        """Remove expired entries for a session."""
        if session_id not in self.memory:
            return
        
        expired_keys = []
        for key, entry in self.memory[session_id].items():
            if entry.ttl:
                age = (datetime.utcnow() - entry.timestamp).total_seconds()
                if age > entry.ttl:
                    expired_keys.append(key)
        
        for key in expired_keys:
            del self.memory[session_id][key]
        
        if expired_keys:
            logger.debug(f"Cleaned {len(expired_keys)} expired entries for session {session_id}")


# Global short-term memory instance
short_term_memory = ShortTermMemory()

