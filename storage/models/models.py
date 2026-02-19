"""
Storage Models - SQLAlchemy Models

Using SQLAlchemy for database abstraction.
Supports SQLite (local) and PostgreSQL (production).
"""

from datetime import datetime
from typing import Optional
from enum import Enum as PyEnum
from sqlalchemy import (
    String, Integer, Boolean, DateTime, Text, ForeignKey, Enum, JSON, Index
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """Base class for all models"""
    pass


class TenantModel(Base):
    """Tenant model"""
    __tablename__ = "tenants"
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    license_id: Mapped[Optional[str]] = mapped_column(String(50), ForeignKey("licenses.id"), nullable=True)
    settings: Mapped[Optional[dict]] = mapped_column(JSON, default={})
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    license: Mapped[Optional["LicenseModel"]] = relationship("LicenseModel", back_populates="tenants")
    users: Mapped[list["UserModel"]] = relationship("UserModel", back_populates="tenant")
    sessions: Mapped[list["SessionModel"]] = relationship("SessionModel", back_populates="tenant")


class LicenseModel(Base):
    """License model"""
    __tablename__ = "licenses"
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    license_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    license_type: Mapped[str] = mapped_column(String(20), nullable=False)  # trial, standard, professional, enterprise
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")  # active, expired, suspended, revoked
    max_users: Mapped[int] = mapped_column(Integer, default=10)
    max_conversations: Mapped[int] = mapped_column(Integer, default=1000)
    features: Mapped[Optional[dict]] = mapped_column(JSON, default={})
    issued_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    tenants: Mapped[list["TenantModel"]] = relationship("TenantModel", back_populates="license")


class UserModel(Base):
    """User model"""
    __tablename__ = "users"
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(50), ForeignKey("tenants.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    permissions: Mapped[Optional[list]] = mapped_column(JSON, default=[])
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, default={})
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    tenant: Mapped["TenantModel"] = relationship("TenantModel", back_populates="users")
    sessions: Mapped[list["SessionModel"]] = relationship("SessionModel", back_populates="user")
    memories: Mapped[list["MemoryModel"]] = relationship("MemoryModel", back_populates="user")


class SessionModel(Base):
    """Conversation session model"""
    __tablename__ = "sessions"
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(50), ForeignKey("tenants.id"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(50), ForeignKey("users.id"), nullable=False, index=True)
    channel: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # telegram, feishu, etc.
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")  # active, closed
    messages_count: Mapped[int] = mapped_column(Integer, default=0)
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, default={})
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    tenant: Mapped["TenantModel"] = relationship("TenantModel", back_populates="sessions")
    user: Mapped["UserModel"] = relationship("UserModel", back_populates="sessions")
    messages: Mapped[list["MessageModel"]] = relationship("MessageModel", back_populates="session")


class MessageModel(Base):
    """Message model"""
    __tablename__ = "messages"
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(50), ForeignKey("sessions.id"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user, assistant, system
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, default={})
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    
    # Relationships
    session: Mapped["SessionModel"] = relationship("SessionModel", back_populates="messages")


class MemoryModel(Base):
    """Memory model"""
    __tablename__ = "memories"
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(50), ForeignKey("tenants.id"), nullable=False, index=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(50), ForeignKey("users.id"), nullable=True, index=True)
    session_id: Mapped[Optional[str]] = mapped_column(String(50), ForeignKey("sessions.id"), nullable=True, index=True)
    
    # Content
    content: Mapped[str] = mapped_column(Text, nullable=False)
    memory_type: Mapped[str] = mapped_column(String(20), nullable=False, default="long_term")  # long_term, daily_log, session
    
    # Metadata
    tags: Mapped[Optional[list]] = mapped_column(JSON, default=[])
    importance: Mapped[int] = mapped_column(Integer, default=0)  # 0-10
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Vector (for semantic search)
    embedding: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
    last_accessed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    user: Mapped[Optional["UserModel"]] = relationship("UserModel", back_populates="memories")
    
    # Indexes
    __table_args__ = (
        Index('idx_memory_tenant_user_type', 'tenant_id', 'user_id', 'memory_type'),
    )


class SkillModel(Base):
    """Skill model"""
    __tablename__ = "skills"
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(50), ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Skill info
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    namespace: Mapped[str] = mapped_column(String(50), nullable=False, default="default")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0.0")
    
    # Skill content (markdown)
    manifest: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)  # Public to all tenants
    
    # Permissions
    required_permissions: Mapped[Optional[list]] = mapped_column(JSON, default=[])
    
    # Metadata
    author: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    tags: Mapped[Optional[list]] = mapped_column(JSON, default=[])
    config: Mapped[Optional[dict]] = mapped_column(JSON, default={})
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_skill_tenant_namespace', 'tenant_id', 'namespace'),
    )
