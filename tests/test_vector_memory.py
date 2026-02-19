"""
Vector Memory Tests

Tests for Phase 3: Vector memory store.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from memory.vector import VectorMemoryStore, MemoryItem


class TestVectorMemoryStore:
    """Vector Memory Store Tests"""
    
    @pytest.fixture
    def store(self):
        return VectorMemoryStore()
    
    @pytest.mark.asyncio
    async def test_add_memory(self, store):
        """Test adding a memory"""
        memory = await store.add(
            tenant_id="tenant_a",
            user_id="user_001",
            content="Important meeting notes",
            memory_type="long_term",
            tags=["meeting", "work"],
            importance=8
        )
        
        assert memory is not None
        assert memory.tenant_id == "tenant_a"
        assert memory.content == "Important meeting notes"
        assert memory.tags == ["meeting", "work"]
        assert memory.importance == 8
    
    @pytest.mark.asyncio
    async def test_get_memory(self, store):
        """Test getting a memory"""
        memory = await store.add(
            tenant_id="tenant_a",
            user_id="user_001",
            content="Test memory"
        )
        
        result = await store.get(memory.id)
        
        assert result is not None
        assert result.id == memory.id
    
    @pytest.mark.asyncio
    async def test_update_memory(self, store):
        """Test updating a memory"""
        memory = await store.add(
            tenant_id="tenant_a",
            user_id="user_001",
            content="Original content"
        )
        
        result = await store.update(
            memory.id,
            content="Updated content",
            importance=10
        )
        
        assert result is True
        
        updated = await store.get(memory.id)
        assert updated.content == "Updated content"
        assert updated.importance == 10
    
    @pytest.mark.asyncio
    async def test_delete_memory(self, store):
        """Test deleting a memory"""
        memory = await store.add(
            tenant_id="tenant_a",
            user_id="user_001",
            content="To be deleted"
        )
        
        result = await store.delete(memory.id)
        
        assert result is True
        assert await store.get(memory.id) is None
    
    @pytest.mark.asyncio
    async def test_search_by_keyword(self, store):
        """Test keyword search"""
        await store.add("tenant_a", "user_001", "Python programming tips")
        await store.add("tenant_a", "user_001", "JavaScript tutorials")
        await store.add("tenant_a", "user_001", "Python best practices")
        
        results = await store.search(tenant_id="tenant_a", query="Python")
        
        assert len(results) == 2
        assert all("Python" in m.content for m in results)
    
    @pytest.mark.asyncio
    async def test_search_by_user(self, store):
        """Test filtering by user"""
        await store.add("tenant_a", "user_001", "User 1 memory")
        await store.add("tenant_a", "user_002", "User 2 memory")
        
        results = await store.search(tenant_id="tenant_a", user_id="user_001")
        
        assert len(results) == 1
        assert results[0].user_id == "user_001"
    
    @pytest.mark.asyncio
    async def test_search_by_type(self, store):
        """Test filtering by memory type"""
        await store.add("tenant_a", "user_001", "Long term info", memory_type="long_term")
        await store.add("tenant_a", "user_001", "Daily log", memory_type="daily_log")
        
        results = await store.search(tenant_id="tenant_a", memory_type="long_term")
        
        assert len(results) == 1
        assert results[0].memory_type == "long_term"
    
    @pytest.mark.asyncio
    async def test_search_by_tags(self, store):
        """Test filtering by tags"""
        await store.add("tenant_a", "user_001", "Work task", tags=["work", "urgent"])
        await store.add("tenant_a", "user_001", "Personal note", tags=["personal"])
        
        results = await store.search(tenant_id="tenant_a", tags=["work"])
        
        assert len(results) == 1
        assert "work" in results[0].tags
    
    @pytest.mark.asyncio
    async def test_tenant_isolation(self, store):
        """Test tenant isolation"""
        await store.add("tenant_a", "user_001", "Tenant A memory")
        await store.add("tenant_b", "user_001", "Tenant B memory")
        
        results_a = await store.search(tenant_id="tenant_a", query="Tenant")
        results_b = await store.search(tenant_id="tenant_b", query="Tenant")
        
        assert len(results_a) == 1
        assert len(results_b) == 1
        assert results_a[0].tenant_id == "tenant_a"
        assert results_b[0].tenant_id == "tenant_b"
    
    @pytest.mark.asyncio
    async def test_get_by_user(self, store):
        """Test getting all memories for a user"""
        await store.add("tenant_a", "user_001", "Memory 1")
        await store.add("tenant_a", "user_001", "Memory 2")
        await store.add("tenant_a", "user_002", "Memory 3")
        
        results = await store.get_by_user("tenant_a", "user_001")
        
        assert len(results) == 2
    
    @pytest.mark.asyncio
    async def test_count_memories(self, store):
        """Test counting memories"""
        await store.add("tenant_a", "user_001", "Memory 1")
        await store.add("tenant_a", "user_001", "Memory 2")
        await store.add("tenant_a", "user_002", "Memory 3")
        
        total = await store.count(tenant_id="tenant_a")
        user_count = await store.count(tenant_id="tenant_a", user_id="user_001")
        
        assert total == 3
        assert user_count == 2
    
    @pytest.mark.asyncio
    async def test_clear_user_memories(self, store):
        """Test clearing all user memories"""
        await store.add("tenant_a", "user_001", "Memory 1")
        await store.add("tenant_a", "user_001", "Memory 2")
        await store.add("tenant_a", "user_002", "Memory 3")
        
        deleted = await store.clear_user_memories("tenant_a", "user_001")
        
        assert deleted == 2
        assert await store.count(tenant_id="tenant_a", user_id="user_001") == 0
        assert await store.count(tenant_id="tenant_a", user_id="user_002") == 1
    
    @pytest.mark.asyncio
    async def test_pin_memory(self, store):
        """Test pinning memory"""
        memory = await store.add("tenant_a", "user_001", "Normal memory")
        
        await store.update(memory.id, is_pinned=True)
        
        updated = await store.get(memory.id)
        assert updated.is_pinned is True
    
    @pytest.mark.asyncio
    async def test_search_limit(self, store):
        """Test search limit"""
        for i in range(20):
            await store.add("tenant_a", "user_001", f"Memory {i}")
        
        results = await store.search(tenant_id="tenant_a", limit=5)
        
        assert len(results) == 5


class TestMemoryItem:
    """Memory Item Tests"""
    
    def test_create_memory_item(self):
        """Test creating memory item"""
        memory = MemoryItem(
            id="test_001",
            tenant_id="tenant_a",
            user_id="user_001",
            content="Test content",
            memory_type="long_term",
            tags=["test"],
            importance=5
        )
        
        assert memory.id == "test_001"
        assert memory.tenant_id == "tenant_a"
        assert memory.content == "Test content"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
