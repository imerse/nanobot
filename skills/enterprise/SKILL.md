---
name: enterprise-info
description: Get enterprise information and user details (requires authentication).
metadata: {"nanobot":{"emoji":"🏢","requires":{}}}
---

# Enterprise Information

This skill provides access to enterprise information.

## User Info

Get current user information:
```bash
echo "User: $NANOBOT_USER_ID, Tenant: $NANOBOT_TENANT_ID"
```

## Tenant Info

Get tenant configuration:
```bash
echo "Tenant: $NANOBOT_TENANT_ID"
```
