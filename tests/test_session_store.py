"""
Session Store Tests

Tests for PostgreSQL session storage.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.session_store import InMemorySessionStore, SessionData


class TestInMemorySessionStore:
    """In-Memory Session Store Tests"""
    
    @pytest.fixture
    def store(self):
        return InMemorySessionStore()
    
    @pytest.mark.asyncio
    async def test_create_session(self, store):
        """Test creating a session"""
        session = await store.create(
            session_id="sess_001",
            tenant_id="tenant_a",
            user_id="user_001",
            channel="telegram"
        )
        
        assert session is not None
        assert session.id == "sess_001"
        assert session.tenant_id == "tenant_a"
        assert session.user_id == "user_001"
        assert session.status == "active"
    
    @pytest.mark.asyncio
    async def test_get_session(self, store):
        """Test getting a session"""
        await store.create("sess_001", "tenant_a", "user_001")
        
        session = await store.get("sess_001")
        
        assert session is not None
        assert session.id == "sess_001"
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_session(self, store):
        """Test getting non-existent session"""
        session = await store.get("nonexistent")
        assert session is None
    
    @pytest.mark.asyncio
    async def test_update_session(self, store):
        """Test updating a session"""
        await store.create("sess_001", "tenant_a", "user_001")
        
        result = await store.update("sess_001", status="closed")
        
        assert result is True
        session = await store.get("sess_001")
        assert session.status == "closed"
    
    @pytest.mark.asyncio
    async def test_delete_session(self, store):
        """Test deleting a session"""
        await store.create("sess_001", "tenant_a", "user_001")
        
        result = await store.delete("sess_001")
        
        assert result is True
        session = await store.get("sess_001")
        assert session is None
    
    @pytest.mark.asyncio
    async def test_list_sessions_by_tenant(self, store):
        """Test listing sessions by tenant"""
        await store.create("sess_001", "tenant_a", "user_001")
        await store.create("sess_002", "tenant_a", "user_002")
        await store.create("sess_003", "tenant_b", "user_003")
        
        sessions = await store.list(tenant_id="tenant_a")
        
        assert len(sessions) == 2
    
    @pytest.mark.asyncio
    async def test_list_sessions_by_status(self, store):
        """Test listing sessions by status"""
        await store.create("sess_001", "tenant_a", "user_001")
        await store.create("sess_002", "tenant_a", "user_002")
        await store.update("sess_001", status="closed")
        
        active = await store.list(status="active")
        closed = await store.list(status="closed")
        
        assert len(active) == 1
        assert len(closed) == 1
    
    @pytest.mark.asyncio
    async def test_count_sessions(self, store):
        """Test counting sessions"""
        await store.create("sess_001", "tenant_a", "user_001")
        await store.create("sess_002", "tenant_a", "user_002")
        await store.create("sess_003", "tenant_b", "user_003")
        
        total = await store.count()
        tenant_a = await store.count(tenant_id="tenant_a")
        
        assert total == 3
        assert tenant_a == 2


class TestSessionData:
    """Session Data Tests"""
    
    def test_create_session_data(self):
        """Test creating session data"""
        from datetime import datetime
        session = SessionData(
            id="sess_001",
            tenant_id="tenant_a",
            user_id="user_001",
            channel="telegram",
            status="active",
            messages=[],
            metadata={"key": "value"},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        assert session.id == "sess_001"
        assert session.tenant_id == "tenant_a"
        assert session.status == "active"
        assert session.metadata["key"] == "value"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
