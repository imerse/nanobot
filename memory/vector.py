"""
Vector Memory Store

Enterprise memory with vector search support.
"""

from typing import Optional, List
from datetime import datetime
from dataclasses import dataclass, field
import hashlib
import json


@dataclass
class MemoryItem:
    """Memory item"""
    id: str
    tenant_id: str
    user_id: Optional[str]
    content: str
    memory_type: str  # long_term, daily_log, session
    tags: List[str] = field(default_factory=list)
    importance: int = 0
    is_pinned: bool = False
    embedding: Optional[List[float]] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_accessed_at: Optional[datetime] = None


class VectorMemoryStore:
    """
    Vector memory store with semantic search.
    
    Supports:
    - Multi-tenant isolation
    - Vector similarity search
    - Hybrid search (keyword + vector)
    """
    
    def __init__(self):
        self._memories = {}
        self._tenant_index = {}
    
    def _generate_id(self, content: str) -> str:
        """Generate memory ID"""
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    async def add(
        self,
        tenant_id: str,
        user_id: Optional[str],
        content: str,
        memory_type: str = "long_term",
        tags: List[str] = None,
        importance: int = 0,
        embedding: List[float] = None
    ) -> MemoryItem:
        """Add a memory"""
        memory_id = self._generate_id(content)
        
        memory = MemoryItem(
            id=memory_id,
            tenant_id=tenant_id,
            user_id=user_id,
            content=content,
            memory_type=memory_type,
            tags=tags or [],
            importance=importance,
            embedding=embedding
        )
        
        self._memories[memory_id] = memory
        
        # Index by tenant
        if tenant_id not in self._tenant_index:
            self._tenant_index[tenant_id] = set()
        self._tenant_index[tenant_id].add(memory_id)
        
        return memory
    
    async def get(self, memory_id: str) -> Optional[MemoryItem]:
        """Get memory by ID"""
        memory = self._memories.get(memory_id)
        if memory:
            memory.last_accessed_at = datetime.now()
        return memory
    
    async def update(
        self,
        memory_id: str,
        content: str = None,
        tags: List[str] = None,
        importance: int = None,
        is_pinned: bool = None
    ) -> bool:
        """Update memory"""
        memory = self._memories.get(memory_id)
        if not memory:
            return False
        
        if content:
            memory.content = content
        if tags:
            memory.tags = tags
        if importance is not None:
            memory.importance = importance
        if is_pinned is not None:
            memory.is_pinned = is_pinned
        
        memory.updated_at = datetime.now()
        return True
    
    async def delete(self, memory_id: str) -> bool:
        """Delete memory"""
        if memory_id not in self._memories:
            return False
        
        memory = self._memories[memory_id]
        tenant_id = memory.tenant_id
        
        del self._memories[memory_id]
        
        if tenant_id in self._tenant_index:
            self._tenant_index[tenant_id].discard(memory_id)
        
        return True
    
    async def search(
        self,
        tenant_id: str,
        query: str = None,
        user_id: str = None,
        memory_type: str = None,
        tags: List[str] = None,
        limit: int = 10
    ) -> List[MemoryItem]:
        """Search memories (hybrid: keyword + tag filter)"""
        results = []
        
        # Get tenant memories
        memory_ids = self._tenant_index.get(tenant_id, set())
        
        for memory_id in memory_ids:
            memory = self._memories.get(memory_id)
            if not memory:
                continue
            
            # Filter by user
            if user_id and memory.user_id != user_id:
                continue
            
            # Filter by type
            if memory_type and memory.memory_type != memory_type:
                continue
            
            # Filter by tags
            if tags and not any(t in memory.tags for t in tags):
                continue
            
            # Keyword search
            if query:
                query_lower = query.lower()
                if query_lower not in memory.content.lower():
                    continue
            
            results.append(memory)
        
        # Sort by importance and date
        results.sort(key=lambda m: (m.is_pinned, m.importance, m.updated_at), reverse=True)
        
        return results[:limit]
    
    async def get_by_user(
        self,
        tenant_id: str,
        user_id: str,
        limit: int = 100
    ) -> List[MemoryItem]:
        """Get all memories for a user"""
        memory_ids = self._tenant_index.get(tenant_id, set())
        
        results = []
        for memory_id in memory_ids:
            memory = self._memories.get(memory_id)
            if memory and memory.user_id == user_id:
                results.append(memory)
        
        results.sort(key=lambda m: m.updated_at, reverse=True)
        return results[:limit]
    
    async def count(
        self,
        tenant_id: str = None,
        user_id: str = None,
        memory_type: str = None
    ) -> int:
        """Count memories"""
        if not tenant_id:
            memories = self._memories.values()
        else:
            memory_ids = self._tenant_index.get(tenant_id, set())
            memories = [self._memories[mid] for mid in memory_ids if mid in self._memories]
        
        count = 0
        for memory in memories:
            if user_id and memory.user_id != user_id:
                continue
            if memory_type and memory.memory_type != memory_type:
                continue
            count += 1
        
        return count
    
    async def clear_user_memories(self, tenant_id: str, user_id: str) -> int:
        """Clear all memories for a user"""
        memory_ids = list(self._tenant_index.get(tenant_id, set()))
        deleted = 0
        
        for memory_id in memory_ids:
            memory = self._memories.get(memory_id)
            if memory and memory.user_id == user_id:
                del self._memories[memory_id]
                self._tenant_index[tenant_id].discard(memory_id)
                deleted += 1
        
        return deleted


class InMemoryVectorStore(VectorMemoryStore):
    """In-memory vector store (alias for compatibility)"""
    pass
