"""
Skill Market Tests

Tests for Phase 4: Skill registry and market.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from skills.market import SkillRegistry, SkillMarket, Skill


class TestSkillRegistry:
    """Skill Registry Tests"""
    
    @pytest.fixture
    def registry(self):
        return SkillRegistry()
    
    def test_register_skill(self, registry):
        """Test registering a skill"""
        skill = registry.register(
            tenant_id="tenant_a",
            name="weather",
            manifest="# Weather Skill",
            description="Get weather info",
            namespace="default",
            version="1.0.0"
        )
        
        assert skill is not None
        assert skill.name == "weather"
        assert skill.tenant_id == "tenant_a"
        assert skill.is_active is True
    
    def test_get_skill(self, registry):
        """Test getting a skill"""
        skill = registry.register(
            tenant_id="tenant_a",
            name="test_skill",
            manifest="# Test"
        )
        
        result = registry.get(skill.id)
        
        assert result is not None
        assert result.id == skill.id
    
    def test_get_by_name(self, registry):
        """Test getting skill by name"""
        registry.register(
            tenant_id="tenant_a",
            name="my_skill",
            manifest="# Test"
        )
        
        result = registry.get_by_name("tenant_a", "my_skill")
        
        assert result is not None
        assert result.name == "my_skill"
    
    def test_update_skill(self, registry):
        """Test updating a skill"""
        skill = registry.register(
            tenant_id="tenant_a",
            name="test_skill",
            manifest="# Original"
        )
        
        result = registry.update(
            skill.id,
            manifest="# Updated",
            version="2.0.0"
        )
        
        assert result is True
        
        updated = registry.get(skill.id)
        assert updated.manifest == "# Updated"
        assert updated.version == "2.0.0"
    
    def test_delete_skill(self, registry):
        """Test deleting a skill"""
        skill = registry.register(
            tenant_id="tenant_a",
            name="test_skill",
            manifest="# Test"
        )
        
        result = registry.delete(skill.id)
        
        assert result is True
        assert registry.get(skill.id) is None
    
    def test_list_skills_by_tenant(self, registry):
        """Test listing skills by tenant"""
        registry.register("tenant_a", "skill_1", "# Test 1")
        registry.register("tenant_a", "skill_2", "# Test 2")
        registry.register("tenant_b", "skill_3", "# Test 3")
        
        skills = registry.list(tenant_id="tenant_a")
        
        assert len(skills) == 2
    
    def test_list_public_skills(self, registry):
        """Test listing public skills"""
        registry.register("tenant_a", "public_skill", "# Public", is_public=True)
        registry.register("tenant_a", "private_skill", "# Private", is_public=False)
        
        public = registry.list(include_public=True)
        
        assert any(s.is_public for s in public)
    
    def test_search_skills(self, registry):
        """Test searching skills"""
        registry.register("tenant_a", "weather", "# Weather skill", description="Get weather")
        registry.register("tenant_a", "news", "# News skill", description="Get news")
        
        results = registry.search(tenant_id="tenant_a", query="weather")
        
        assert len(results) >= 1
        assert any("weather" in s.name.lower() for s in results)
    
    def test_check_permission(self, registry):
        """Test permission checking"""
        skill = registry.register(
            "tenant_a",
            "admin_skill",
            "# Admin",
            required_permissions=["admin"]
        )
        
        assert registry.check_permission(skill.id, ["admin"]) is True
        assert registry.check_permission(skill.id, ["user"]) is False
    
    def test_tenant_isolation(self, registry):
        """Test tenant isolation"""
        registry.register("tenant_a", "skill_1", "# Test", namespace="ns1")
        registry.register("tenant_b", "skill_2", "# Test", namespace="ns2")
        
        tenant_a_skills = registry.list(tenant_id="tenant_a")
        tenant_b_skills = registry.list(tenant_id="tenant_b")
        
        assert len(tenant_a_skills) == 1
        assert len(tenant_b_skills) == 1
    
    def test_skill_versioning(self, registry):
        """Test skill versioning"""
        skill = registry.register(
            "tenant_a",
            "versioned_skill",
            "# V1",
            version="1.0.0"
        )
        
        registry.update(skill.id, version="1.1.0")
        
        updated = registry.get(skill.id)
        assert updated.version == "1.1.0"
    
    def test_skill_tags(self, registry):
        """Test skill tags"""
        skill = registry.register(
            "tenant_a",
            "tagged_skill",
            "# Test",
            tags=["utility", "api"]
        )
        
        results = registry.list(tenant_id="tenant_a", tags=["utility"])
        
        assert len(results) == 1
        assert "utility" in results[0].tags
    
    def test_count_skills(self, registry):
        """Test counting skills"""
        registry.register("tenant_a", "skill_1", "# Test")
        registry.register("tenant_a", "skill_2", "# Test")
        registry.register("tenant_b", "skill_3", "# Test")
        
        count_a = registry.count("tenant_a")
        count_b = registry.count("tenant_b")
        
        assert count_a == 2
        assert count_b == 1


class TestSkillMarket:
    """Skill Market Tests"""
    
    @pytest.fixture
    def registry(self):
        return SkillRegistry()
    
    @pytest.fixture
    def market(self, registry):
        return SkillMarket(registry)
    
    def test_browse_skills(self, market, registry):
        """Test browsing skills"""
        registry.register("tenant_a", "skill_1", "# Test")
        registry.register("tenant_a", "skill_2", "# Test")
        
        results = market.browse(tenant_id="tenant_a")
        
        assert len(results) == 2
    
    def test_install_public_skill(self, market, registry):
        """Test installing public skill"""
        # Create public skill
        source = registry.register(
            "tenant_a",
            "public_skill",
            "# Public",
            is_public=True
        )
        
        # Install to tenant_b
        installed = market.install(source.id, "tenant_b")
        
        assert installed is not None
        assert installed.tenant_id == "tenant_b"
        assert installed.name == "public_skill"
    
    def test_install_already_installed(self, market, registry):
        """Test installing already installed skill"""
        source = registry.register(
            "tenant_a",
            "shared_skill",
            "# Shared",
            is_public=True
        )
        
        # First install
        installed1 = market.install(source.id, "tenant_b")
        
        # Second install (should return existing)
        installed2 = market.install(source.id, "tenant_b")
        
        assert installed1.id == installed2.id
    
    def test_uninstall_skill(self, market, registry):
        """Test uninstalling skill"""
        skill = registry.register("tenant_a", "to_delete", "# Test")
        
        result = market.uninstall("tenant_a", skill.id)
        
        assert result is True
        assert registry.get(skill.id) is None
    
    def test_browse_by_category(self, market, registry):
        """Test browsing by category/tags"""
        registry.register("tenant_a", "utility_skill", "# Test", tags=["utility"])
        registry.register("tenant_a", "api_skill", "# Test", tags=["api"])
        
        results = market.browse(tenant_id="tenant_a", category="utility")
        
        assert len(results) == 1


class TestSkill:
    """Skill Entity Tests"""
    
    def test_create_skill(self):
        """Test creating skill"""
        skill = Skill(
            id="test_001",
            tenant_id="tenant_a",
            name="test_skill",
            description="Test description",
            version="1.0.0",
            manifest="# Test",
            is_public=True
        )
        
        assert skill.id == "test_001"
        assert skill.name == "test_skill"
        assert skill.is_public is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
