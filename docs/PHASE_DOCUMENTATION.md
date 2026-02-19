# Nanobot 企业版 - 功能文档

## 概述

本文档详细说明 Nanobot 企业版的各个功能模块和使用方法。

---

## Phase 1: 基础 Fork

### 已完成
- ✅ Fork Nanobot 到私有仓库
- ✅ 配置 MiniMax 模型
- ✅ 55个上游测试通过
- ✅ CI/CD 流水线

### 使用方法

```bash
# 运行测试
cd nanobot
python -m pytest tests/ -v

# 运行对话
nanobot agent -m "Hello"
```

---

## Phase 2: 企业化核心

### 2.1 多租户认证系统

**模块**: `enterprise/auth.py`

```python
from enterprise.auth import AuthManager, Tenant, User
from datetime import datetime

# 创建认证管理器
am = AuthManager()

# 注册租户
tenant = Tenant(
    id="company_a",
    name="Chip Company",
    created_at=datetime.now(),
    settings={"active": True}
)
am.register_tenant(tenant)

# 注册用户
user = User(
    id="user_001",
    tenant_id="company_a",
    name="Alice",
    email="alice@chip.com",
    permissions=["read", "write"],
    created_at=datetime.now()
)
am.register_user(user)

# 认证
result = am.authenticate("user_001", "company_a")
print(result.name)  # Alice

# 检查权限
has_perm = am.check_permission(user, "write")  # True
```

### 2.2 租户管理

**模块**: `enterprise/tenant.py`

```python
from enterprise.tenant import TenantManager, TenantConfig

tm = TenantManager()

# 创建租户
config = TenantConfig(
    id="company_a",
    name="Chip Company",
    llm_provider="minimax",
    llm_model="minimax-m2.5",
    max_users=100,
    max_conversations=1000,
    features={"api_access": True}
)
tm.create_tenant(config)

# 获取租户
tenant = tm.get_tenant("company_a")
print(tenant.name)
```

### 2.3 License 管理

**模块**: `enterprise/license.py`

```python
from enterprise.license import LicenseManager, LicenseType

lm = LicenseManager()

# 创建 License
license, key = lm.create_license(
    tenant_id="company_a",
    license_type=LicenseType.PROFESSIONAL,
    max_users=100,
    max_conversations=10000,
    days=365,
    features={"vector_search": True}
)

print(f"License Key: {key}")
print(f"Is Valid: {license.is_valid()}")
print(f"Days Remaining: {license.days_remaining()}")

# 验证使用量
is_valid = lm.validate_usage(license.id, 50, 5000)  # True
```

### 2.4 PostgreSQL 会话存储

**模块**: `storage/session_store.py`

```python
from storage.session_store import InMemorySessionStore

store = InMemorySessionStore()

# 创建会话
session = await store.create(
    session_id="sess_001",
    tenant_id="company_a",
    user_id="user_001",
    channel="telegram"
)

# 获取会话
session = await store.get("sess_001")

# 列出会话
sessions = await store.list(tenant_id="company_a", status="active")

# 统计
count = await store.count(tenant_id="company_a")
```

---

## Phase 3: 记忆系统升级

### 3.1 向量记忆存储

**模块**: `memory/vector.py`

```python
from memory.vector import VectorMemoryStore

store = VectorMemoryStore()

# 添加记忆
memory = await store.add(
    tenant_id="company_a",
    user_id="user_001",
    content="User prefers Python over Java",
    memory_type="long_term",
    tags=["preference", "language"],
    importance=8
)

# 搜索记忆
results = await store.search(
    tenant_id="company_a",
    query="Python",
    memory_type="long_term",
    limit=10
)

# 按用户获取
memories = await store.get_by_user("company_a", "user_001")

# 统计
count = await store.count(tenant_id="company_a", user_id="user_001")
```

### 功能特性
- ✅ 多租户隔离
- ✅ 关键词搜索
- ✅ 标签过滤
- ✅ 重要性排序
- ✅ 记忆固定

---

## Phase 4: Skill 市场

### 4.1 Skill 注册中心

**模块**: `skills/market.py`

```python
from skills.market import SkillRegistry, SkillMarket

registry = SkillRegistry()

# 注册 Skill
skill = registry.register(
    tenant_id="company_a",
    name="weather",
    manifest="# Weather Skill\n...",
    description="Get weather info",
    namespace="default",
    version="1.0.0",
    is_public=True,
    required_permissions=["read"],
    tags=["utility", "api"]
)

# 获取 Skill
skill = registry.get(skill_id)

# 列出 Skills
skills = registry.list(
    tenant_id="company_a",
    namespace="default",
    is_active=True
)

# 搜索
results = registry.search(tenant_id="company_a", query="weather")

# 检查权限
has_perm = registry.check_permission(skill_id, ["admin", "read"])
```

### 4.2 Skill 市场

```python
market = SkillMarket(registry)

# 浏览市场
skills = market.browse(
    tenant_id="company_a",
    category="utility"
)

# 安装公共 Skill
installed = market.install(source_skill_id, "company_b")

# 卸载 Skill
market.uninstall("company_a", skill_id)
```

---

## Phase 5: 持续集成

### 5.1 自动同步上游

**文件**: `.github/workflows/sync-upstream.yml`

```yaml
name: Sync Upstream

on:
  schedule:
    - cron: '0 3 * * 0'  # 每周日凌晨3点
  workflow_dispatch:

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Add upstream remote
        run: |
          git remote add upstream https://github.com/HKUDS/nanobot.git
          git fetch upstream
      - name: Merge upstream
        run: git merge upstream/main --no-edit
      - name: Run tests
        run: pytest tests/
      - name: Create Pull Request
        uses: actions/create-pull-request@v6
```

---

## 测试

### 运行所有测试
```bash
python -m pytest tests/ -v
```

### 测试覆盖

| 模块 | 测试数 |
|------|--------|
| 上游测试 | 55 |
| 企业模块 | 20 |
| 会话存储 | 9 |
| 向量记忆 | 15 |
| Skill 市场 | 18 |
| **总计** | **118** |

---

## 文件结构

```
nanobot/
├── enterprise/           # 企业化模块
│   ├── auth.py         # 认证
│   ├── tenant.py       # 租户管理
│   └── license.py      # License
├── storage/            # 存储模块
│   ├── database.py     # 数据库连接
│   ├── models/         # SQLAlchemy模型
│   └── session_store.py # 会话存储
├── memory/             # 记忆系统
│   └── vector.py       # 向量记忆
├── skills/             # Skills
│   ├── market.py       # Skill市场
│   └── enterprise/     # 企业Skill
└── tests/              # 测试
    ├── test_enterprise.py
    ├── test_session_store.py
    ├── test_vector_memory.py
    └── test_skill_market.py
```

---

## 总结

所有 5 个 Phase 已完成：
- ✅ Phase 1: 基础 Fork
- ✅ Phase 2: 企业化核心
- ✅ Phase 3: 记忆系统升级
- ✅ Phase 4: Skill 市场
- ✅ Phase 5: 持续集成

**测试总数**: 118 个测试全部通过
