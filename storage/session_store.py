"""
PostgreSQL Session Storage

Enterprise session storage with PostgreSQL.
"""

from typing import Optional, List
from datetime import datetime
from dataclasses import dataclass
import json


@dataclass
class SessionData:
    """Session data"""
    id: str
    tenant_id: str
    user_id: str
    channel: Optional[str]
    status: str
    messages: list
    metadata: dict
    created_at: datetime
    updated_at: datetime


class PostgreSQLSessionStore:
    """
    PostgreSQL-based session storage.
    
    Replaces the default file-based session storage.
    """
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    async def create(
        self,
        session_id: str,
        tenant_id: str,
        user_id: str,
        channel: str = None
    ) -> SessionData:
        """Create a new session"""
        from storage.models.models import SessionModel
        
        session = SessionModel(
            id=session_id,
            tenant_id=tenant_id,
            user_id=user_id,
            channel=channel,
            status="active",
            messages_count=0,
            metadata={}
        )
        
        with self.db.get_session() as db:
            db.add(session)
            db.commit()
        
        return SessionData(
            id=session_id,
            tenant_id=tenant_id,
            user_id=user_id,
            channel=channel,
            status="active",
            messages=[],
            metadata={},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    async def get(self, session_id: str) -> Optional[SessionData]:
        """Get session by ID"""
        from storage.models.models import SessionModel
        
        with self.db.get_session() as db:
            session = db.query(SessionModel).filter_by(id=session_id).first()
            if not session:
                return None
            
            return SessionData(
                id=session.id,
                tenant_id=session.tenant_id,
                user_id=session.user_id,
                channel=session.channel,
                status=session.status,
                messages=[],
                metadata=session.metadata or {},
                created_at=session.created_at,
                updated_at=session.updated_at
            )
    
    async def update(
        self,
        session_id: str,
        status: str = None,
        metadata: dict = None
    ) -> bool:
        """Update session"""
        from storage.models.models import SessionModel
        
        with self.db.get_session() as db:
            session = db.query(SessionModel).filter_by(id=session_id).first()
            if not session:
                return False
            
            if status:
                session.status = status
            if metadata:
                session.metadata = metadata
            
            db.commit()
            return True
    
    async def delete(self, session_id: str) -> bool:
        """Delete session"""
        from storage.models.models import SessionModel
        
        with self.db.get_session() as db:
            session = db.query(SessionModel).filter_by(id=session_id).first()
            if not session:
                return False
            
            db.delete(session)
            db.commit()
            return True
    
    async def list(
        self,
        tenant_id: str = None,
        user_id: str = None,
        status: str = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[SessionData]:
        """List sessions with filters"""
        from storage.models.models import SessionModel
        
        with self.db.get_session() as db:
            query = db.query(SessionModel)
            
            if tenant_id:
                query = query.filter_by(tenant_id=tenant_id)
            if user_id:
                query = query.filter_by(user_id=user_id)
            if status:
                query = query.filter_by(status=status)
            
            sessions = query.offset(offset).limit(limit).all()
            
            return [
                SessionData(
                    id=s.id,
                    tenant_id=s.tenant_id,
                    user_id=s.user_id,
                    channel=s.channel,
                    status=s.status,
                    messages=[],
                    metadata=s.metadata or {},
                    created_at=s.created_at,
                    updated_at=s.updated_at
                )
                for s in sessions
            ]
    
    async def count(
        self,
        tenant_id: str = None,
        user_id: str = None,
        status: str = None
    ) -> int:
        """Count sessions"""
        from storage.models.models import SessionModel
        
        with self.db.get_session() as db:
            query = db.query(SessionModel)
            
            if tenant_id:
                query = query.filter_by(tenant_id=tenant_id)
            if user_id:
                query = query.filter_by(user_id=user_id)
            if status:
                query = query.filter_by(status=status)
            
            return query.count()


class InMemorySessionStore:
    """
    In-memory session store (for testing).
    """
    
    def __init__(self):
        self._sessions = {}
    
    async def create(
        self,
        session_id: str,
        tenant_id: str,
        user_id: str,
        channel: str = None
    ) -> SessionData:
        session = SessionData(
            id=session_id,
            tenant_id=tenant_id,
            user_id=user_id,
            channel=channel,
            status="active",
            messages=[],
            metadata={},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        self._sessions[session_id] = session
        return session
    
    async def get(self, session_id: str) -> Optional[SessionData]:
        return self._sessions.get(session_id)
    
    async def update(
        self,
        session_id: str,
        status: str = None,
        metadata: dict = None
    ) -> bool:
        if session_id not in self._sessions:
            return False
        if status:
            self._sessions[session_id].status = status
        if metadata:
            self._sessions[session_id].metadata = metadata
        return True
    
    async def delete(self, session_id: str) -> bool:
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False
    
    async def list(
        self,
        tenant_id: str = None,
        user_id: str = None,
        status: str = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[SessionData]:
        results = list(self._sessions.values())
        
        if tenant_id:
            results = [s for s in results if s.tenant_id == tenant_id]
        if user_id:
            results = [s for s in results if s.user_id == user_id]
        if status:
            results = [s for s in results if s.status == status]
        
        return results[offset:offset+limit]
    
    async def count(
        self,
        tenant_id: str = None,
        user_id: str = None,
        status: str = None
    ) -> int:
        sessions = await self.list(tenant_id, user_id, status, limit=999999)
        return len(sessions)
