# 子模块开发指南 (Module Development Guide)

---

## 模块结构 (Module Structure)

每个子模块是一个文件夹，位于配置的 `mod_dir`（默认 `../mod`）下。模块必须包含一个 `api.py` 文件，其中暴露一个 FastAPI 的 `APIRouter` 实例。

Each module is a folder placed in the `mod_dir` (default `../mod`). It must contain an `api.py` file that exposes a FastAPI `APIRouter` instance.

示例 (Example)：

```python
# mod/my_module/api.py
from fastapi import APIRouter, Depends
from app.core.dependencies import get_current_user_from_token

# 推荐设置 tags，便于元数据分组 (Recommended: set tags for metadata grouping)
router = APIRouter(prefix="/my", tags=["my_module"])

@router.get("/hello")
async def hello(user=Depends(get_current_user_from_token)):
    return {"msg": "Hello from module"}
```

## 元数据生成 (Metadata Generation)
框架会自动收集模块的端点信息，并通过 /api/modules/{module_id}/endpoints 和 /api/modules/{module_id}/openapi 提供。为了获得最佳元数据，建议：

The framework automatically collects module endpoint information and provides it via /api/modules/{module_id}/endpoints and /api/modules/{module_id}/openapi. For optimal metadata:

在 router 中使用 tags 参数 (Use tags in your router)

为请求/响应定义 Pydantic 模型 (Define Pydantic models for request/response bodies)

在路由函数中使用文档字符串 (Use docstrings for summaries and descriptions)

## 模块加载 (Loading Modules)
模块可以通过 UI（模块管理页面）或 API 加载。模块路径必须在配置的 module_allowed_paths 白名单内。

Modules can be loaded via the UI (Modules Management page) or via API. The module path must be in the module_allowed_paths whitelist.

## 卸载与重载 (Unloading and Reloading)
模块可以动态卸载和重载，无需重启服务。注意：卸载时路由会从应用中移除，但可能需要刷新前端页面以更新路由缓存。

Modules can be unloaded and reloaded dynamically without restarting the server. Note: routes are removed from the application, but you may need to refresh the frontend page to update route caches.