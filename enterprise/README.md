# Enterprise Extensions

企业化扩展模块目录。

## 目录结构

```
enterprise/
├── auth/           # 多租户认证鉴权
├── license/        # License管理
├── tenant/         # 租户管理
└── middleware/    # 请求中间件
```

## 使用说明

本目录用于存放企业化扩展代码，**不修改上游源码**，以便后续合并Nanobot更新。

### 添加新功能

1. 在对应子目录创建模块
2. 使用继承/扩展方式覆盖上游功能
3. 在 `enterprise/__init__.py` 中注册
