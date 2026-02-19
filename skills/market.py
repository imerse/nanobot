"""
Skill Registry & Market

Enterprise skill registry and market.
"""

from typing import Optional, List
from datetime import datetime
from dataclasses import dataclass, field
import hashlib
import json


@dataclass
class Skill:
    """Skill definition"""
    id: str
    tenant_id: str
    name: str
    namespace: str = "default"
    description: str = ""
    version: str = "1.0.0"
    manifest: str = ""  # Markdown content
    is_active: bool = True
    is_public: bool = False
    required_permissions: List[str] = field(default_factory=list)
    author: str = ""
    tags: List[str] = field(default_factory=list)
    config: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


class SkillRegistry:
    """
    Enterprise skill registry.
    
    Features:
    - Multi-tenant isolation
    - Skill versioning
    - Public/private skills
    - Permission-based access
    """
    
    def __init__(self):
        self._skills = {}
        self._tenant_index = {}
    
    def _generate_id(self, tenant_id: str, name: str) -> str:
        """Generate skill ID"""
        key = f"{tenant_id}:{name}"
        return hashlib.md5(key.encode()).hexdigest()[:16]
    
    def register(
        self,
        tenant_id: str,
        name: str,
        manifest: str,
        namespace: str = "default",
        description: str = "",
        version: str = "1.0.0",
        is_public: bool = False,
        required_permissions: List[str] = None,
        author: str = "",
        tags: List[str] = None,
        config: dict = None
    ) -> Skill:
        """Register a new skill"""
        skill_id = self._generate_id(tenant_id, name)
        
        skill = Skill(
            id=skill_id,
            tenant_id=tenant_id,
            name=name,
            namespace=namespace,
            description=description,
            version=version,
            manifest=manifest,
            is_public=is_public,
            required_permissions=required_permissions or [],
            author=author,
            tags=tags or [],
            config=config or {}
        )
        
        self._skills[skill_id] = skill
        
        # Index by tenant
        if tenant_id not in self._tenant_index:
            self._tenant_index[tenant_id] = {}
        self._tenant_index[tenant_id][skill_id] = skill
        
        return skill
    
    def get(self, skill_id: str) -> Optional[Skill]:
        """Get skill by ID"""
        return self._skills.get(skill_id)
    
    def get_by_name(self, tenant_id: str, name: str, namespace: str = "default") -> Optional[Skill]:
        """Get skill by name"""
        skill_id = self._generate_id(tenant_id, name)
        skill = self._skills.get(skill_id)
        
        if skill and skill.namespace == namespace:
            return skill
        
        return None
    
    def update(
        self,
        skill_id: str,
        manifest: str = None,
        description: str = None,
        version: str = None,
        is_active: bool = None,
        is_public: bool = None,
        tags: List[str] = None,
        config: dict = None
    ) -> bool:
        """Update skill"""
        skill = self._skills.get(skill_id)
        if not skill:
            return False
        
        if manifest:
            skill.manifest = manifest
        if description:
            skill.description = description
        if version:
            skill.version = version
        if is_active is not None:
            skill.is_active = is_active
        if is_public is not None:
            skill.is_public = is_public
        if tags:
            skill.tags = tags
        if config:
            skill.config = config
        
        skill.updated_at = datetime.now()
        return True
    
    def delete(self, skill_id: str) -> bool:
        """Delete skill"""
        if skill_id not in self._skills:
            return False
        
        skill = self._skills[skill_id]
        tenant_id = skill.tenant_id
        
        del self._skills[skill_id]
        
        if tenant_id in self._tenant_index:
            del self._tenant_index[tenant_id][skill_id]
        
        return True
    
    def list(
        self,
        tenant_id: str = None,
        namespace: str = None,
        is_active: bool = None,
        include_public: bool = False,
        tags: List[str] = None,
        limit: int = 100
    ) -> List[Skill]:
        """List skills with filters"""
        results = []
        
        # Get all skills (tenant + public)
        if tenant_id:
            # Tenant's skills
            tenant_skills = self._tenant_index.get(tenant_id, {})
            results.extend(tenant_skills.values())
            
            # Public skills from other tenants
            if include_public:
                for skill in self._skills.values():
                    if skill.is_public and skill.tenant_id != tenant_id:
                        results.append(skill)
        else:
            # All public skills
            if include_public:
                results = [s for s in self._skills.values() if s.is_public]
        
        # Filter
        filtered = []
        for skill in results:
            if namespace and skill.namespace != namespace:
                continue
            if is_active is not None and skill.is_active != is_active:
                continue
            if tags and not any(t in skill.tags for t in tags):
                continue
            filtered.append(skill)
        
        # Sort by update time
        filtered.sort(key=lambda s: s.updated_at, reverse=True)
        
        return filtered[:limit]
    
    def search(
        self,
        tenant_id: str = None,
        query: str = None,
        tags: List[str] = None,
        limit: int = 10
    ) -> List[Skill]:
        """Search skills"""
        # Get all relevant skills
        all_skills = self.list(tenant_id=tenant_id, include_public=True, limit=999)
        
        results = []
        for skill in all_skills:
            # Filter by query
            if query:
                query_lower = query.lower()
                if query_lower not in skill.name.lower() and query_lower not in skill.description.lower():
                    continue
            
            # Filter by tags
            if tags and not any(t in skill.tags for t in tags):
                continue
            
            results.append(skill)
        
        return results[:limit]
    
    def check_permission(self, skill_id: str, user_permissions: List[str]) -> bool:
        """Check if user has required permissions"""
        skill = self._skills.get(skill_id)
        if not skill:
            return False
        
        if not skill.required_permissions:
            return True
        
        return any(p in user_permissions for p in skill.required_permissions)
    
    def count(self, tenant_id: str = None) -> int:
        """Count skills"""
        if not tenant_id:
            return len(self._skills)
        
        return len(self._tenant_index.get(tenant_id, {}))


class SkillMarket:
    """
    Skill market for browsing and installing skills.
    """
    
    def __init__(self, registry: SkillRegistry):
        self.registry = registry
    
    def browse(
        self,
        tenant_id: str = None,
        category: str = None,
        query: str = None,
        limit: int = 20
    ) -> List[dict]:
        """Browse available skills"""
        skills = self.registry.list(
            tenant_id=tenant_id,
            include_public=True,
            is_active=True,
            tags=[category] if category else None,
            limit=limit
        )
        
        if query:
            skills = self.registry.search(
                tenant_id=tenant_id,
                query=query,
                limit=limit
            )
        
        return [
            {
                "id": s.id,
                "name": s.name,
                "namespace": s.namespace,
                "description": s.description,
                "version": s.version,
                "author": s.author,
                "tags": s.tags,
                "is_public": s.is_public,
                "tenant_id": s.tenant_id
            }
            for s in skills
        ]
    
    def install(
        self,
        source_skill_id: str,
        target_tenant_id: str,
        namespace: str = "default"
    ) -> Optional[Skill]:
        """Install a public skill to tenant"""
        source = self.registry.get(source_skill_id)
        if not source or not source.is_public:
            return None
        
        # Check if already installed
        existing = self.registry.get_by_name(target_tenant_id, source.name, namespace)
        if existing:
            return existing
        
        # Install copy
        return self.registry.register(
            tenant_id=target_tenant_id,
            name=source.name,
            namespace=namespace,
            manifest=source.manifest,
            description=source.description,
            version=source.version,
            is_public=False,
            required_permissions=source.required_permissions,
            author=source.author,
            tags=source.tags,
            config=source.config
        )
    
    def uninstall(self, tenant_id: str, skill_id: str) -> bool:
        """Uninstall a skill"""
        skill = self.registry.get(skill_id)
        if not skill or skill.tenant_id != tenant_id:
            return False
        
        return self.registry.delete(skill_id)
