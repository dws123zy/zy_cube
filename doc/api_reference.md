# API 参考 (API Reference)

---

## 认证 (Authentication)

| 端点 (Endpoint) | 方法 (Method) | 说明 (Description) |
|----------------|---------------|-------------------|
| `/api/auth/login` | POST | 登录，返回 JWT token (Login, returns JWT token) |
| `/api/auth/me` | GET | 获取当前用户信息 (Get current user info) |

**登录请求体 (Login request body)**
```json
{ "username": "admin", "password": "admin" }
```
登录响应 (Login response)

```json
{ "access_token": "...", "token_type": "bearer" }
```

## 模块管理（仅限 admin）(Modules Management, admin only)
端点 (Endpoint)	方法 (Method)	说明 (Description)
/api/modules/list	GET	列出已加载模块 (List loaded modules)
/api/modules/load	POST	加载模块 (Load a module)
/api/modules/unload?module_id=xxx	DELETE	卸载模块 (Unload a module)
/api/modules/reload?module_id=xxx	PUT	重载模块 (Reload a module)
/api/modules/{module_id}/endpoints	GET	获取模块简化端点信息 (Get simplified endpoints)
/api/modules/{module_id}/openapi	GET	获取模块 OpenAPI 片段 (Get OpenAPI fragment)
加载模块请求体 (Load module request body)

```json
{
  "module_path": "../mod/my_module",
  "module_id": "my_module",
  "api_prefix": "/api/my"
}
```

## 文件服务 (File Service)
端点 (Endpoint)	方法 (Method)	说明 (Description)
/api/files/tree?root=web	GET	获取文件树 (Get file tree)
/api/files/meta?path=...&root=web	GET	获取文件/目录元数据 (Get file/directory metadata)
/api/files/content?path=...&root=web	GET	获取文件内容（仅文本，限制扩展名）(Get file content, text only, restricted extensions)
所有文件服务端点均需要 Bearer Token 认证 (All file service endpoints require Bearer token authentication)。

## 错误码 (Error Codes)
状态码 (Status)	含义 (Meaning)
401	未认证或 Token 无效 (Unauthorized or invalid token)
403	权限不足（需要 admin 角色）(Insufficient privileges, admin required)
404	资源不存在 (Resource not found)
400	请求参数错误 (Bad request)